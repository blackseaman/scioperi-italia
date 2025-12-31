"""Config flow per Scioperi Italia V2."""
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv

from .const import (
    DOMAIN,
    CONF_RADIUS,
    CONF_FAVORITE_SECTORS,
    CONF_ENABLE_NOTIFICATIONS,
    CONF_NOTIFICATION_TIME,
    CONF_WORK_LOCATION,
    RADIUS_OPTIONS,
    DEFAULT_RADIUS,
    SECTORS,
    NOTIFICATION_TIMES,
    DEFAULT_NOTIFICATION_TIME,
)
from .utils import get_home_coordinates

_LOGGER = logging.getLogger(__name__)


class ScioperiItaliaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle config flow."""

    VERSION = 2

    async def async_step_user(self, user_input=None):
        """Handle initial step."""
        errors = {}

        if user_input is not None:
            # Ottieni coordinate casa automaticamente
            home_coords = get_home_coordinates(self.hass)
            
            if not home_coords:
                errors["base"] = "no_home_coordinates"
            else:
                # Salva configurazione
                return self.async_create_entry(
                    title="Scioperi Italia",
                    data={
                        "home_latitude": home_coords[0],
                        "home_longitude": home_coords[1],
                    },
                    options=user_input,
                )

        # Schema configurazione iniziale
        data_schema = vol.Schema({
            vol.Optional(
                CONF_RADIUS,
                default=DEFAULT_RADIUS
            ): vol.In(RADIUS_OPTIONS),
            vol.Optional(
                CONF_FAVORITE_SECTORS,
                default=[]
            ): cv.multi_select({sector: sector for sector in SECTORS if sector != "Tutti"}),
            vol.Optional(
                CONF_ENABLE_NOTIFICATIONS,
                default=True
            ): bool,
            vol.Optional(
                CONF_NOTIFICATION_TIME,
                default=DEFAULT_NOTIFICATION_TIME
            ): vol.In(NOTIFICATION_TIMES),
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "home_location": f"📍 Casa rilevata automaticamente dalle impostazioni Home Assistant"
            }
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get options flow handler."""
        return ScioperiItaliaOptionsFlow(config_entry)


class ScioperiItaliaOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Schema opzioni
        options_schema = vol.Schema({
            vol.Optional(
                CONF_RADIUS,
                default=self.config_entry.options.get(CONF_RADIUS, DEFAULT_RADIUS)
            ): vol.In(RADIUS_OPTIONS),
            vol.Optional(
                CONF_FAVORITE_SECTORS,
                default=self.config_entry.options.get(CONF_FAVORITE_SECTORS, [])
            ): cv.multi_select({sector: sector for sector in SECTORS if sector != "Tutti"}),
            vol.Optional(
                CONF_ENABLE_NOTIFICATIONS,
                default=self.config_entry.options.get(CONF_ENABLE_NOTIFICATIONS, True)
            ): bool,
            vol.Optional(
                CONF_NOTIFICATION_TIME,
                default=self.config_entry.options.get(CONF_NOTIFICATION_TIME, DEFAULT_NOTIFICATION_TIME)
            ): vol.In(NOTIFICATION_TIMES),
            vol.Optional(
                CONF_WORK_LOCATION,
                description={"suggested_value": self.config_entry.options.get(CONF_WORK_LOCATION, "")}
            ): str,
        })

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
            description_placeholders={
                "home_location": f"🏠 Casa: {self.config_entry.data.get('home_latitude'):.4f}, {self.config_entry.data.get('home_longitude'):.4f}",
                "radius_info": f"🎯 Raggio attuale: {self.config_entry.options.get(CONF_RADIUS, DEFAULT_RADIUS)}km",
            }
        )
