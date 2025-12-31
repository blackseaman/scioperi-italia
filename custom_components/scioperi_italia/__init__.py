"""Integrazione Scioperi Italia V2 per Home Assistant."""
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
import voluptuous as vol

from .const import (
    DOMAIN,
    SERVICE_CHECK_ROUTE,
    SERVICE_NOTIFY,
    SERVICE_REFRESH,
)
from .coordinator import ScioperiCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "calendar"]

# Service schemas
SERVICE_CHECK_ROUTE_SCHEMA = vol.Schema({
    vol.Required("destination_lat"): cv.latitude,
    vol.Required("destination_lon"): cv.longitude,
    vol.Optional("radius_km", default=5): cv.positive_int,
})

SERVICE_NOTIFY_SCHEMA = vol.Schema({
    vol.Optional("title"): cv.string,
    vol.Optional("message"): cv.string,
})


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Scioperi Italia from a config entry."""
    coordinator = ScioperiCoordinator(hass, entry)
    
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services
    async def handle_check_route(call: ServiceCall) -> None:
        """Handle check_route service."""
        dest_lat = call.data["destination_lat"]
        dest_lon = call.data["destination_lon"]
        radius = call.data.get("radius_km", 5)
        
        from .utils import calculate_distance
        
        # Trova scioperi lungo il percorso
        nearby_strikes = []
        for strike in coordinator.nearby_strikes:
            strike_lat = strike.get("latitude")
            strike_lon = strike.get("longitude")
            
            if not strike_lat or not strike_lon:
                continue
            
            # Calcola distanza da destinazione
            dist_to_dest = calculate_distance(
                strike_lat, strike_lon,
                dest_lat, dest_lon
            )
            
            if dist_to_dest <= radius:
                nearby_strikes.append({
                    "sector": strike.get("sector"),
                    "region": strike.get("region"),
                    "start_date": strike.get("start_date_str"),
                    "distance_from_destination": dist_to_dest,
                })
        
        _LOGGER.info(
            "Route check: found %d strikes near destination",
            len(nearby_strikes)
        )
        
        # Fire event con risultati
        hass.bus.async_fire(
            f"{DOMAIN}_route_check_result",
            {
                "destination": f"{dest_lat}, {dest_lon}",
                "radius_km": radius,
                "strikes_found": len(nearby_strikes),
                "strikes": nearby_strikes,
            }
        )
    
    async def handle_notify(call: ServiceCall) -> None:
        """Handle notify service."""
        title = call.data.get("title", "⚠️ Scioperi")
        message = call.data.get("message")
        
        if not message:
            # Generate automatic message
            nearby_count = len(coordinator.nearby_strikes)
            today_count = len(coordinator.today_strikes)
            tomorrow_count = len(coordinator.tomorrow_strikes)
            
            if today_count > 0:
                message = f"🚨 {today_count} sciopero/i OGGI nel raggio di {coordinator.radius}km"
            elif tomorrow_count > 0:
                message = f"📅 {tomorrow_count} sciopero/i DOMANI nel raggio di {coordinator.radius}km"
            elif nearby_count > 0:
                next_strike = coordinator.get_next_nearby_strike()
                date_str = next_strike.get("start_date_str", "")
                message = f"📍 Prossimo sciopero vicino: {date_str}"
            else:
                message = "✅ Nessuno sciopero vicino nei prossimi giorni"
        
        # Send notification using Home Assistant notify service
        await hass.services.async_call(
            "notify",
            "persistent_notification",
            {
                "title": title,
                "message": message,
            }
        )
        
        _LOGGER.info("Sent notification: %s", message)
    
    async def handle_refresh(call: ServiceCall) -> None:
        """Handle refresh service."""
        await coordinator.async_refresh()
        _LOGGER.info("Manual refresh triggered")
    
    # Register services
    hass.services.async_register(
        DOMAIN,
        SERVICE_CHECK_ROUTE,
        handle_check_route,
        schema=SERVICE_CHECK_ROUTE_SCHEMA,
    )
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_NOTIFY,
        handle_notify,
        schema=SERVICE_NOTIFY_SCHEMA,
    )
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_REFRESH,
        handle_refresh,
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        
        # Unregister services if this was the last entry
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_CHECK_ROUTE)
            hass.services.async_remove(DOMAIN, SERVICE_NOTIFY)
            hass.services.async_remove(DOMAIN, SERVICE_REFRESH)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
