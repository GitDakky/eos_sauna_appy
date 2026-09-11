"""Custom integration to integrate EOS Sauna Appy with Home Assistant.

For more details about this integration, please refer to
https://github.com/GitDakky/eos_sauna_appy
"""
import logging
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import homeassistant.helpers.config_validation as cv

from .api import EosSaunaApiClient
from .const import (
    DOMAIN,
    PLATFORMS,
    STARTUP_MESSAGE,
    SCAN_INTERVAL_STATUS,
    SCAN_INTERVAL_SETTINGS,
)

_LOGGER = logging.getLogger(__name__)

SERVICE_CLEAR_SCHEDULED_START = "clear_scheduled_start"
SERVICE_SCHEMA = vol.Schema({vol.Optional("config_entry_id"): cv.string})


@callback
def _async_find_entry_id(hass: HomeAssistant, call: ServiceCall) -> str | None:
    """Resolve config entry for a service call."""
    if call.data.get("config_entry_id"):
        return call.data["config_entry_id"]
    entries = hass.config_entries.async_entries(DOMAIN)
    if len(entries) == 1:
        return entries[0].entry_id
    return None


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up this integration using UI."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})
        _LOGGER.info(STARTUP_MESSAGE)

    sauna_ip = entry.data.get("sauna_ip")

    session = async_get_clientsession(hass)
    client = EosSaunaApiClient(sauna_ip, session)

    # Coordinator for actual status (/usr/eos/is)
    status_coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="eos_sauna_status",
        update_method=client.async_get_status,
        update_interval=SCAN_INTERVAL_STATUS,
    )

    # Coordinator for desired/device settings (/usr/eos/setdev)
    settings_coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="eos_sauna_settings",
        update_method=client.async_get_settings,
        update_interval=SCAN_INTERVAL_SETTINGS,
    )

    await status_coordinator.async_refresh()
    await settings_coordinator.async_refresh()

    if not status_coordinator.last_update_success or not settings_coordinator.last_update_success:
        raise UpdateFailed("Initial data fetch failed")

    hass.data[DOMAIN][entry.entry_id] = {
        "client": client,
        "status_coordinator": status_coordinator,
        "settings_coordinator": settings_coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    if not hass.services.has_service(DOMAIN, SERVICE_CLEAR_SCHEDULED_START):

        async def clear_scheduled_start(call: ServiceCall) -> None:
            entry_id = _async_find_entry_id(hass, call)
            if not entry_id or entry_id not in hass.data[DOMAIN]:
                _LOGGER.error("clear_scheduled_start: no EOS Sauna config entry found")
                return
            client = hass.data[DOMAIN][entry_id]["client"]
            await client.async_clear_scheduled_start()
            settings_coordinator = hass.data[DOMAIN][entry_id]["settings_coordinator"]
            await settings_coordinator.async_request_refresh()

        hass.services.async_register(
            DOMAIN,
            SERVICE_CLEAR_SCHEDULED_START,
            clear_scheduled_start,
            schema=SERVICE_SCHEMA,
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)