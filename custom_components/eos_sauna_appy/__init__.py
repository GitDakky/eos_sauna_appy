"""Custom integration to integrate EOS Sauna Appy with Home Assistant.

For more details about this integration, please refer to
https://github.com/GitDakky/eos_sauna_appy
"""
import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import EosSaunaApiClient
from .const import (
    DOMAIN,
    PLATFORMS,
    STARTUP_MESSAGE,
    SCAN_INTERVAL_STATUS,
    SCAN_INTERVAL_SETTINGS,
)

_LOGGER = logging.getLogger(__name__)


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

    for platform in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    unloaded = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)