"""Light platform for EOS Sauna Appy."""
import asyncio
from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    LOGGER,
    API_KEY_LIGHT_STATE_DESIRED,  # Lxd
    API_KEY_LIGHT_INTENSITY_DESIRED,  # Ld
    MANUFACTURER,
    NAME as INTEGRATION_NAME,
)
from .api import EosSaunaApiClient


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the light platform."""
    data = hass.data[DOMAIN][entry.entry_id]
    # Lights will use the settings_coordinator to reflect the desired state
    # and the client to send commands.
    settings_coordinator = data["settings_coordinator"]
    client = data["client"]

    lights = [
        EosSaunaLight(
            settings_coordinator,
            entry,
            client,
            "Sauna Light",
        )
    ]
    async_add_entities(lights)


class EosSaunaLight(CoordinatorEntity, LightEntity):
    """Representation of an EOS Sauna light."""

    _attr_color_mode = ColorMode.BRIGHTNESS # Supports brightness
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}

    def __init__(
        self,
        coordinator, # This will be the settings_coordinator
        config_entry: ConfigEntry,
        client: EosSaunaApiClient,
        name_suffix: str,
    ):
        """Initialize the light."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._client = client

        self._attr_name = f"{INTEGRATION_NAME} {self._config_entry.data.get('sauna_ip', '')} {name_suffix}"
        self._attr_unique_id = f"{config_entry.entry_id}_light"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": f"{INTEGRATION_NAME} ({config_entry.data.get('sauna_ip', '')})",
            "manufacturer": MANUFACTURER,
            "model": "Web API Controlled Sauna",
        }
        self._attr_icon = "mdi:lightbulb"

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            super().available
            and self.coordinator.data is not None
            and API_KEY_LIGHT_STATE_DESIRED in self.coordinator.data
            and API_KEY_LIGHT_INTENSITY_DESIRED in self.coordinator.data
        )

    @property
    def is_on(self) -> bool | None:
        """Return true if light is on."""
        if self.available:
            # API uses "1" for ON and "0" for OFF for Lxd
            return str(self.coordinator.data[API_KEY_LIGHT_STATE_DESIRED]) == "1"
        return None

    @property
    def brightness(self) -> int | None:
        """Return the brightness of this light between 0..255."""
        if self.available:
            # API provides brightness as 0-100 (Ld key)
            # Home Assistant expects 0-255
            api_brightness = self.coordinator.data[API_KEY_LIGHT_INTENSITY_DESIRED]
            if api_brightness is not None:
                return round(int(api_brightness) * 2.55)
        return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on."""
        LOGGER.debug(f"Turning ON {self.name} with kwargs: {kwargs}")
        try:
            if ATTR_BRIGHTNESS in kwargs:
                # HA brightness is 0-255, API is 0-100
                ha_brightness = kwargs[ATTR_BRIGHTNESS]
                api_brightness = round(ha_brightness / 2.55)
                await self._client.async_set_light_intensity(api_brightness)
            
            # Always ensure light is set to ON state if brightness is also set or if no brightness
            # This handles cases where light might be off but brightness is adjusted
            if not self.is_on or ATTR_BRIGHTNESS not in kwargs:
                 await self._client.async_set_light_onoff(True)

            await self.coordinator.async_request_refresh()
        except Exception as e:
            LOGGER.error(f"Error turning ON {self.name}: {e}")

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        LOGGER.debug(f"Turning OFF {self.name}")
        try:
            await self._client.async_set_light_onoff(False)
            # Add a small delay to allow the device to process the command
            await asyncio.sleep(5) # Wait 5 seconds
            await self.coordinator.async_request_refresh()
        except Exception as e:
            LOGGER.error(f"Error turning OFF {self.name}: {e}")