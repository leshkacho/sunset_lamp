import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME

DOMAIN = "sunset_lamp"

CONF_MAC = "mac_address"

@config_entries.HANDLERS.register(DOMAIN)
class SunsetLampConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Sunset Lamp."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            # Валидация MAC-адреса
            if len(user_input[CONF_MAC]) != 17:  # Пример валидации
                errors["base"] = "invalid_mac"
            else:
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data=user_input,
                )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default="Sunset Lamp"): str,
                vol.Required(CONF_MAC): str,
            }
        )
        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )
