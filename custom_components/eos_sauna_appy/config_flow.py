"""Config flow for EOS Sauna Appy."""
import voluptuous as vol
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.config_entries import ConfigFlow, OptionsFlow, ConfigEntry
from homeassistant.core import callback
from homeassistant.const import CONF_HOST

from .api import EosSaunaApiClient, EosSaunaApiCommunicationError, EosSaunaApiAuthError
from .const import DOMAIN, LOGGER, CONF_SAUNA_IP


class EosSaunaAppyConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for EOS Sauna Appy."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            try:
                # Validate the IP address format (basic check)
                cv.string(user_input[CONF_SAUNA_IP])

                # Test connection to the sauna
                session = async_get_clientsession(self.hass)
                client = EosSaunaApiClient(user_input[CONF_SAUNA_IP], session)
                await client.async_get_status()  # Try to fetch status to confirm connectivity

                await self.async_set_unique_id(user_input[CONF_SAUNA_IP])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"EOS Sauna ({user_input[CONF_SAUNA_IP]})",
                    data={CONF_SAUNA_IP: user_input[CONF_SAUNA_IP]},
                )
            except EosSaunaApiCommunicationError:
                errors["base"] = "cannot_connect"
                LOGGER.error(f"Failed to connect to sauna at {user_input[CONF_SAUNA_IP]}")
            except EosSaunaApiAuthError: # Should not happen with this API, but good practice
                errors["base"] = "invalid_auth"
                LOGGER.error("Authentication error with sauna API (unexpected)")
            except vol.Invalid:
                errors[CONF_SAUNA_IP] = "invalid_ip"
                LOGGER.error(f"Invalid IP address format: {user_input[CONF_SAUNA_IP]}")
            except Exception as e:  # pylint: disable=broad-except
                LOGGER.exception(f"Unexpected exception: {e}")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_SAUNA_IP): str}),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry):
        """Get the options flow for this handler."""
        return EosSaunaAppyOptionsFlowHandler(config_entry)


class EosSaunaAppyOptionsFlowHandler(OptionsFlow):
    """Handle an options flow for EOS Sauna Appy."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        # Options flow can be expanded later if needed (e.g., scan interval)
        # For now, we don't have any configurable options post-setup.
        return self.async_show_form(step_id="init", data_schema=None)