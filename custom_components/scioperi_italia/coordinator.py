"""Data coordinator per Scioperi Italia V2."""
import logging
from datetime import timedelta, datetime

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    UPDATE_INTERVAL_SECONDS,
    DEFAULT_RSS_URL,
    CONF_RADIUS,
    CONF_FAVORITE_SECTORS,
    CONF_ENABLE_NOTIFICATIONS,
    CONF_NOTIFICATION_TIME,
    DEFAULT_RADIUS,
    DEFAULT_NOTIFICATION_TIME,
    EVENT_STRIKE_TOMORROW,
    EVENT_STRIKE_NEARBY,
)
from .parser import ScioperoParser
from .utils import is_strike_nearby, should_notify, extract_coordinates

_LOGGER = logging.getLogger(__name__)


class ScioperiCoordinator(DataUpdateCoordinator):
    """Coordinator per gestire aggiornamenti scioperi V2."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize coordinator."""
        self.entry = entry
        self.rss_url = DEFAULT_RSS_URL
        
        # Coordinate casa da config
        self.home_lat = entry.data.get("home_latitude")
        self.home_lon = entry.data.get("home_longitude")
        
        # Opzioni utente
        self.radius = entry.options.get(CONF_RADIUS, DEFAULT_RADIUS)
        self.favorite_sectors = entry.options.get(CONF_FAVORITE_SECTORS, [])
        self.enable_notifications = entry.options.get(CONF_ENABLE_NOTIFICATIONS, True)
        self.notification_time = entry.options.get(CONF_NOTIFICATION_TIME, DEFAULT_NOTIFICATION_TIME)
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL_SECONDS),
        )
        
        # Listen for options updates
        self.entry.add_update_listener(self._async_update_options)

    async def _async_update_options(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Update options."""
        self.radius = entry.options.get(CONF_RADIUS, DEFAULT_RADIUS)
        self.favorite_sectors = entry.options.get(CONF_FAVORITE_SECTORS, [])
        self.enable_notifications = entry.options.get(CONF_ENABLE_NOTIFICATIONS, True)
        self.notification_time = entry.options.get(CONF_NOTIFICATION_TIME, DEFAULT_NOTIFICATION_TIME)
        await self.async_refresh()

    def _enrich_strike_with_location(self, strike: dict) -> dict:
        """Arricchisci sciopero con info location."""
        # Calcola distanza
        is_nearby, distance = is_strike_nearby(
            strike,
            self.home_lat,
            self.home_lon,
            self.radius
        )
        
        strike["in_radius"] = is_nearby
        strike["distance"] = distance
        
        # Aggiungi coordinate se disponibili
        coords = extract_coordinates(strike)
        if coords:
            strike["latitude"] = coords[0]
            strike["longitude"] = coords[1]
        
        return strike

    def _check_and_fire_events(self, strikes: list) -> None:
        """Controlla scioperi e lancia eventi se necessario."""
        if not self.enable_notifications:
            return
        
        now = datetime.now()
        tomorrow = (now + timedelta(days=1)).date()
        
        for strike in strikes:
            start_date = strike.get("start_date")
            if not start_date:
                continue
            
            # Evento sciopero domani
            if start_date.date() == tomorrow and strike.get("in_radius"):
                self.hass.bus.async_fire(
                    EVENT_STRIKE_TOMORROW,
                    {
                        "sector": strike.get("sector"),
                        "region": strike.get("region"),
                        "distance": strike.get("distance"),
                        "modality": strike.get("modality"),
                    }
                )
                _LOGGER.info("Fired event: strike tomorrow - %s", strike.get("sector"))
            
            # Evento sciopero vicino rilevato
            if strike.get("in_radius") and should_notify(strike, self.notification_time):
                self.hass.bus.async_fire(
                    EVENT_STRIKE_NEARBY,
                    {
                        "sector": strike.get("sector"),
                        "region": strike.get("region"),
                        "distance": strike.get("distance"),
                        "start_date": start_date.strftime("%d/%m/%Y"),
                        "hours_before": self.notification_time,
                    }
                )
                strike["notification_sent"] = True
                _LOGGER.info("Fired event: strike nearby - %s at %dkm", 
                           strike.get("sector"), strike.get("distance"))

    async def _async_update_data(self) -> dict:
        """Fetch data from RSS feed."""
        try:
            # Parse feed
            strikes = await self.hass.async_add_executor_job(
                ScioperoParser.parse_feed, self.rss_url
            )
            
            # Arricchisci ogni sciopero con info location
            enriched_strikes = [
                self._enrich_strike_with_location(s) for s in strikes
            ]
            
            now = datetime.now()
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
            tomorrow = today + timedelta(days=1)
            
            # Future strikes
            future_strikes = [
                s for s in enriched_strikes
                if s.get("start_date") and s["start_date"] >= today
            ]
            
            # Today's strikes
            today_strikes = [
                s for s in future_strikes
                if s["start_date"].date() == today.date()
            ]
            
            # Tomorrow's strikes
            tomorrow_strikes = [
                s for s in future_strikes
                if s["start_date"].date() == tomorrow.date()
            ]
            
            # Nearby strikes (in radius)
            nearby_strikes = [
                s for s in future_strikes
                if s.get("in_radius", False)
            ]
            
            # Favorite sectors strikes
            favorite_strikes = [
                s for s in future_strikes
                if s.get("sector") in self.favorite_sectors
            ] if self.favorite_sectors else []
            
            # Group by sector
            by_sector = {}
            for strike in future_strikes:
                sector = strike.get("sector", "Altro")
                if sector not in by_sector:
                    by_sector[sector] = []
                by_sector[sector].append(strike)
            
            # Check notifications
            self._check_and_fire_events(nearby_strikes)
            
            data = {
                "all_strikes": enriched_strikes,
                "future_strikes": future_strikes,
                "today_strikes": today_strikes,
                "tomorrow_strikes": tomorrow_strikes,
                "nearby_strikes": nearby_strikes,
                "favorite_strikes": favorite_strikes,
                "by_sector": by_sector,
                "last_update": now,
                "home_coordinates": (self.home_lat, self.home_lon),
                "radius": self.radius,
            }
            
            _LOGGER.info(
                "Updated: %d total, %d nearby, %d today, %d tomorrow",
                len(future_strikes),
                len(nearby_strikes),
                len(today_strikes),
                len(tomorrow_strikes)
            )
            
            return data
            
        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}")
    
    @property
    def strikes(self) -> list[dict]:
        """Return all future strikes."""
        return self.data.get("future_strikes", []) if self.data else []
    
    @property
    def today_strikes(self) -> list[dict]:
        """Return today's strikes."""
        return self.data.get("today_strikes", []) if self.data else []
    
    @property
    def tomorrow_strikes(self) -> list[dict]:
        """Return tomorrow's strikes."""
        return self.data.get("tomorrow_strikes", []) if self.data else []
    
    @property
    def nearby_strikes(self) -> list[dict]:
        """Return nearby strikes."""
        return self.data.get("nearby_strikes", []) if self.data else []
    
    @property
    def favorite_strikes(self) -> list[dict]:
        """Return favorite sectors strikes."""
        return self.data.get("favorite_strikes", []) if self.data else []
    
    def get_strikes_by_sector(self, sector: str) -> list[dict]:
        """Get strikes for specific sector."""
        if not self.data:
            return []
        return self.data.get("by_sector", {}).get(sector, [])
    
    def get_next_strike(self) -> dict | None:
        """Get next upcoming strike."""
        if not self.strikes:
            return None
        return self.strikes[0] if self.strikes else None
    
    def get_next_nearby_strike(self) -> dict | None:
        """Get next nearby strike."""
        if not self.nearby_strikes:
            return None
        return self.nearby_strikes[0] if self.nearby_strikes else None
