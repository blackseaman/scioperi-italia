"""Sensor platform per Scioperi Italia V2."""
import logging
from datetime import datetime

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    SECTORS,
    ATTR_STRIKES,
    ATTR_SECTOR,
    ATTR_REGION,
    ATTR_START_DATE,
    ATTR_END_DATE,
    ATTR_MODALITY,
    ATTR_RELEVANCE,
    ATTR_DISTANCE,
    ATTR_IN_RADIUS,
    ICON_DEFAULT,
    ICON_BUS,
    ICON_TRAIN,
    ICON_AIRPLANE,
    ICON_SHIP,
    ICON_TRUCK,
    ICON_LOCATION,
)
from .coordinator import ScioperiCoordinator
from .utils import format_distance

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Scioperi Italia sensors V2."""
    coordinator: ScioperiCoordinator = hass.data[DOMAIN][entry.entry_id]

    sensors = []
    
    # Main sensors
    sensors.append(ScioperiCountSensor(coordinator))
    sensors.append(ScioperiTodaySensor(coordinator))
    sensors.append(ScioperiTomorrowSensor(coordinator))
    sensors.append(ScioperiNextSensor(coordinator))
    
    # NEW: Location-aware sensors
    sensors.append(ScioperiNearbySensor(coordinator))
    sensors.append(ScioperiNextNearbySensor(coordinator))
    sensors.append(ScioperiiFavoritesSensor(coordinator))
    
    # Sector-specific sensors
    for sector in SECTORS:
        if sector != "Tutti":
            sensors.append(ScioperiSectorSensor(coordinator, sector))
    
    async_add_entities(sensors)


class ScioperiBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for Scioperi Italia sensors."""

    _attr_state_class = None

    def __init__(self, coordinator: ScioperiCoordinator, name: str, icon: str) -> None:
        """Initialize base sensor."""
        super().__init__(coordinator)
        self._attr_name = f"Scioperi {name}"
        self._attr_icon = icon
        self._attr_unique_id = f"{DOMAIN}_{name.lower().replace(' ', '_')}"
        self._attr_has_entity_name = False


class ScioperiCountSensor(ScioperiBaseSensor):
    """Sensor for total strike count."""

    def __init__(self, coordinator: ScioperiCoordinator) -> None:
        """Initialize sensor."""
        super().__init__(coordinator, "Totali", ICON_DEFAULT)

    @property
    def native_value(self) -> int:
        """Return the state."""
        return len(self.coordinator.strikes)

    @property
    def native_unit_of_measurement(self) -> str:
        """Return unit."""
        return "scioperi"

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes."""
        strikes = self.coordinator.strikes[:10]
        
        return {
            ATTR_STRIKES: [
                {
                    "sector": s.get(ATTR_SECTOR, ""),
                    "region": s.get(ATTR_REGION, ""),
                    "start_date": s.get("start_date_str", ""),
                    "distance": format_distance(s.get(ATTR_DISTANCE, 0)),
                    "in_radius": s.get(ATTR_IN_RADIUS, False),
                }
                for s in strikes
            ],
            "last_update": self.coordinator.data.get("last_update"),
            "home_location": f"{self.coordinator.home_lat:.4f}, {self.coordinator.home_lon:.4f}",
            "radius_km": self.coordinator.radius,
        }


class ScioperiTodaySensor(ScioperiBaseSensor):
    """Sensor for today's strikes."""

    def __init__(self, coordinator: ScioperiCoordinator) -> None:
        """Initialize sensor."""
        super().__init__(coordinator, "Oggi", "mdi:calendar-today")

    @property
    def native_value(self) -> int:
        """Return the state."""
        return len(self.coordinator.today_strikes)

    @property
    def native_unit_of_measurement(self) -> str:
        """Return unit."""
        return "scioperi"

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes."""
        strikes = self.coordinator.today_strikes
        
        return {
            ATTR_STRIKES: [
                {
                    "sector": s.get(ATTR_SECTOR, ""),
                    "region": s.get(ATTR_REGION, ""),
                    "modality": s.get(ATTR_MODALITY, ""),
                    "distance": format_distance(s.get(ATTR_DISTANCE, 0)),
                }
                for s in strikes
            ]
        }


class ScioperiTomorrowSensor(ScioperiBaseSensor):
    """Sensor for tomorrow's strikes."""

    def __init__(self, coordinator: ScioperiCoordinator) -> None:
        """Initialize sensor."""
        super().__init__(coordinator, "Domani", "mdi:calendar-tomorrow")

    @property
    def native_value(self) -> int:
        """Return the state."""
        return len(self.coordinator.tomorrow_strikes)

    @property
    def native_unit_of_measurement(self) -> str:
        """Return unit."""
        return "scioperi"

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes."""
        strikes = self.coordinator.tomorrow_strikes
        
        return {
            ATTR_STRIKES: [
                {
                    "sector": s.get(ATTR_SECTOR, ""),
                    "region": s.get(ATTR_REGION, ""),
                    "modality": s.get(ATTR_MODALITY, ""),
                    "distance": format_distance(s.get(ATTR_DISTANCE, 0)),
                    "in_radius": s.get(ATTR_IN_RADIUS, False),
                }
                for s in strikes
            ]
        }


class ScioperiNextSensor(ScioperiBaseSensor):
    """Sensor for next upcoming strike."""

    def __init__(self, coordinator: ScioperiCoordinator) -> None:
        """Initialize sensor."""
        super().__init__(coordinator, "Prossimo", "mdi:calendar-clock")

    @property
    def native_value(self) -> str:
        """Return the state."""
        next_strike = self.coordinator.get_next_strike()
        if not next_strike:
            return "Nessuno"
        
        start = next_strike.get("start_date")
        if start:
            return start.strftime("%d/%m/%Y")
        return "Sconosciuto"

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes."""
        next_strike = self.coordinator.get_next_strike()
        if not next_strike:
            return {}
        
        return {
            ATTR_SECTOR: next_strike.get(ATTR_SECTOR, ""),
            ATTR_REGION: next_strike.get(ATTR_REGION, ""),
            "province": next_strike.get("province", ""),
            ATTR_START_DATE: next_strike.get("start_date_str", ""),
            ATTR_END_DATE: next_strike.get("end_date_str", ""),
            ATTR_MODALITY: next_strike.get(ATTR_MODALITY, ""),
            ATTR_RELEVANCE: next_strike.get(ATTR_RELEVANCE, ""),
            "unions": next_strike.get("unions", ""),
            "category": next_strike.get("category", ""),
            ATTR_DISTANCE: format_distance(next_strike.get(ATTR_DISTANCE, 0)),
            ATTR_IN_RADIUS: next_strike.get(ATTR_IN_RADIUS, False),
        }


class ScioperiNearbySensor(ScioperiBaseSensor):
    """Sensor for nearby strikes (in radius)."""

    def __init__(self, coordinator: ScioperiCoordinator) -> None:
        """Initialize sensor."""
        super().__init__(coordinator, "Vicini", ICON_LOCATION)

    @property
    def native_value(self) -> int:
        """Return the state."""
        return len(self.coordinator.nearby_strikes)

    @property
    def native_unit_of_measurement(self) -> str:
        """Return unit."""
        return "scioperi"

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes."""
        strikes = self.coordinator.nearby_strikes[:10]
        
        return {
            "radius_km": self.coordinator.radius,
            "home_location": f"{self.coordinator.home_lat:.4f}, {self.coordinator.home_lon:.4f}",
            ATTR_STRIKES: [
                {
                    "sector": s.get(ATTR_SECTOR, ""),
                    "region": s.get(ATTR_REGION, ""),
                    "start_date": s.get("start_date_str", ""),
                    "distance": format_distance(s.get(ATTR_DISTANCE, 0)),
                    "modality": s.get(ATTR_MODALITY, ""),
                }
                for s in strikes
            ]
        }


class ScioperiNextNearbySensor(ScioperiBaseSensor):
    """Sensor for next nearby strike."""

    def __init__(self, coordinator: ScioperiCoordinator) -> None:
        """Initialize sensor."""
        super().__init__(coordinator, "Prossimo Vicino", ICON_LOCATION)

    @property
    def native_value(self) -> str:
        """Return the state."""
        next_strike = self.coordinator.get_next_nearby_strike()
        if not next_strike:
            return "Nessuno"
        
        start = next_strike.get("start_date")
        if start:
            distance = next_strike.get(ATTR_DISTANCE, 0)
            return f"{start.strftime('%d/%m/%Y')} ({format_distance(distance)})"
        return "Sconosciuto"

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes."""
        next_strike = self.coordinator.get_next_nearby_strike()
        if not next_strike:
            return {"radius_km": self.coordinator.radius}
        
        return {
            ATTR_SECTOR: next_strike.get(ATTR_SECTOR, ""),
            ATTR_REGION: next_strike.get(ATTR_REGION, ""),
            ATTR_START_DATE: next_strike.get("start_date_str", ""),
            ATTR_MODALITY: next_strike.get(ATTR_MODALITY, ""),
            ATTR_DISTANCE: format_distance(next_strike.get(ATTR_DISTANCE, 0)),
            "distance_km": next_strike.get(ATTR_DISTANCE, 0),
            "radius_km": self.coordinator.radius,
            "unions": next_strike.get("unions", ""),
        }


class ScioperiiFavoritesSensor(ScioperiBaseSensor):
    """Sensor for favorite sectors strikes."""

    def __init__(self, coordinator: ScioperiCoordinator) -> None:
        """Initialize sensor."""
        super().__init__(coordinator, "Preferiti", "mdi:star")

    @property
    def native_value(self) -> int:
        """Return the state."""
        return len(self.coordinator.favorite_strikes)

    @property
    def native_unit_of_measurement(self) -> str:
        """Return unit."""
        return "scioperi"

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes."""
        strikes = self.coordinator.favorite_strikes[:10]
        
        return {
            "favorite_sectors": self.coordinator.favorite_sectors,
            ATTR_STRIKES: [
                {
                    "sector": s.get(ATTR_SECTOR, ""),
                    "region": s.get(ATTR_REGION, ""),
                    "start_date": s.get("start_date_str", ""),
                    "distance": format_distance(s.get(ATTR_DISTANCE, 0)),
                    "in_radius": s.get(ATTR_IN_RADIUS, False),
                }
                for s in strikes
            ]
        }


class ScioperiSectorSensor(ScioperiBaseSensor):
    """Sensor for specific sector strikes."""

    def __init__(self, coordinator: ScioperiCoordinator, sector: str) -> None:
        """Initialize sector sensor."""
        self.sector = sector
        super().__init__(
            coordinator, 
            sector.replace("Trasporto pubblico locale", "TPL"),
            self._get_sector_icon(sector)
        )

    @staticmethod
    def _get_sector_icon(sector: str) -> str:
        """Get icon for sector."""
        icons = {
            "Trasporto pubblico locale": ICON_BUS,
            "Aereo": ICON_AIRPLANE,
            "Ferroviario": ICON_TRAIN,
            "Trasporto merci e logistica": ICON_TRUCK,
            "Marittimo": ICON_SHIP,
        }
        return icons.get(sector, ICON_DEFAULT)

    @property
    def native_value(self) -> int:
        """Return the state."""
        return len(self.coordinator.get_strikes_by_sector(self.sector))

    @property
    def native_unit_of_measurement(self) -> str:
        """Return unit."""
        return "scioperi"

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes."""
        strikes = self.coordinator.get_strikes_by_sector(self.sector)[:5]
        
        return {
            ATTR_SECTOR: self.sector,
            ATTR_STRIKES: [
                {
                    "region": s.get(ATTR_REGION, ""),
                    "start_date": s.get("start_date_str", ""),
                    "modality": s.get(ATTR_MODALITY, ""),
                    "distance": format_distance(s.get(ATTR_DISTANCE, 0)),
                    "in_radius": s.get(ATTR_IN_RADIUS, False),
                }
                for s in strikes
            ]
        }
