"""Climate platform for EOS Sauna Appy."""
import asyncio
from typing import Any, List, Optional

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature, ATTR_TEMPERATURE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    LOGGER,
    API_KEY_SAUNA_STATE_ACTUAL, # S (for current HVAC action)
    API_KEY_SAUNA_STATE_DESIRED, # Sxd (for HVAC mode)
    API_KEY_CURRENT_TEMP, # T
    API_KEY_TARGET_TEMP_DESIRED, # Td
    MANUFACTURER,
    NAME as INTEGRATION_NAME,
    SAUNA_STATUS_MAP,
)
from .api import EosSaunaApiClient


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the climate platform."""
    data = hass.data[DOMAIN][entry.entry_id]
    status_coordinator = data["status_coordinator"] # For current temp and actual state
    settings_coordinator = data["settings_coordinator"] # For target temp and desired state
    client = data["client"]

    climates = [
        EosSaunaClimate(
            status_coordinator,
            settings_coordinator,
            entry,
            client,
            "Sauna Climate",
        )
    ]
    async_add_entities(climates)


class EosSaunaClimate(CoordinatorEntity, ClimateEntity):
    """Representation of an EOS Sauna climate entity."""

    # Use settings_coordinator as the primary for desired states
    # but will need status_coordinator for current temperature and actual hvac_action
    def __init__(
        self,
        status_coordinator, # For current temperature and actual hvac_action
        settings_coordinator, # For target temperature and hvac_mode (desired state)
        config_entry: ConfigEntry,
        client: EosSaunaApiClient,
        name_suffix: str,
    ):
        """Initialize the climate entity."""
        super().__init__(settings_coordinator) # Primary coordinator for desired state
        self.status_coordinator = status_coordinator
        self._config_entry = config_entry
        self._client = client

        self._attr_name = f"{INTEGRATION_NAME} {self._config_entry.data.get('sauna_ip', '')} {name_suffix}"
        self._attr_unique_id = f"{config_entry.entry_id}_climate"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": f"{INTEGRATION_NAME} ({config_entry.data.get('sauna_ip', '')})",
            "manufacturer": MANUFACTURER,
            "model": "Web API Controlled Sauna",
        }

        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT] # Sauna is primarily for heating
        self._attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
        self._attr_min_temp = 30  # Based on HTML form validation
        self._attr_max_temp = 115 # Based on HTML form validation
        self._attr_target_temperature_step = 1.0
        self._attr_icon = "mdi:sauna"


    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            super().available # Checks settings_coordinator
            and self.status_coordinator.last_update_success
            and self.coordinator.data is not None
            and self.status_coordinator.data is not None
            and API_KEY_SAUNA_STATE_DESIRED in self.coordinator.data # From settings_coordinator
            and API_KEY_TARGET_TEMP_DESIRED in self.coordinator.data # From settings_coordinator
            and API_KEY_CURRENT_TEMP in self.status_coordinator.data # From status_coordinator
            and API_KEY_SAUNA_STATE_ACTUAL in self.status_coordinator.data # From status_coordinator
        )

    @property
    def hvac_mode(self) -> HVACMode | None:
        """Return current HVAC mode."""
        if self.available:
            # Sxd: 0 for OFF, 1 for ON (heating)
            if str(self.coordinator.data.get(API_KEY_SAUNA_STATE_DESIRED)) == "1":
                return HVACMode.HEAT
            return HVACMode.OFF
        return None

    @property
    def hvac_action(self) -> HVACMode | None:
        """Return the current running hvac operation if supported.
        Need to map sauna status S to HVACAction.
        S: 0: Inactive, 1: Finnish mode, 2: BIO mode, 3: After burner mode, 4: Fault
        """
        if self.available:
            sauna_status_actual = self.status_coordinator.data.get(API_KEY_SAUNA_STATE_ACTUAL)
            if sauna_status_actual in [1, 2, 3]: # Finnish, BIO, After burner
                return HVACMode.HEATING
            elif sauna_status_actual == 0: # Inactive
                 return HVACMode.OFF
            elif sauna_status_actual == 4: # Fault
                return HVACMode.OFF # Or some other state if HA supports error state for HVACAction
            # If Sxd is 1 (HEAT desired) but actual status is 0 (Inactive), it might be idle
            if str(self.coordinator.data.get(API_KEY_SAUNA_STATE_DESIRED)) == "1" and sauna_status_actual == 0:
                return HVACMode.IDLE
        return HVACMode.OFF # Default to OFF if unknown

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        if self.available:
            temp = self.status_coordinator.data.get(API_KEY_CURRENT_TEMP)
            if temp is not None:
                try:
                    return float(temp)
                except (ValueError, TypeError):
                    LOGGER.warning(f"Could not parse current temperature: {temp}")
        return None

    @property
    def target_temperature(self) -> float | None:
        """Return the temperature we try to reach."""
        if self.available:
            temp = self.coordinator.data.get(API_KEY_TARGET_TEMP_DESIRED)
            if temp is not None:
                try:
                    return float(temp)
                except (ValueError, TypeError):
                    LOGGER.warning(f"Could not parse target temperature: {temp}")
        return None

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        LOGGER.debug(f"Setting target temperature to {temperature}°C via API call.")
        try:
            await self._client.async_set_target_temperature(int(temperature))
            # Refresh both coordinators as target temp might affect actual status eventually
            await self.coordinator.async_request_refresh()
            await self.status_coordinator.async_request_refresh()
        except Exception as e:
            LOGGER.error(f"Error setting target temperature: {e}")

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        LOGGER.debug(f"Setting HVAC mode to {hvac_mode} via API call.")
        try:
            if hvac_mode == HVACMode.HEAT:
                await self._client.async_set_sauna_onoff(True)
            elif hvac_mode == HVACMode.OFF:
                await self._client.async_set_sauna_onoff(False)
                # Add a small delay to allow the device to process the command
                await asyncio.sleep(5) # Wait 5 seconds
            else:
                LOGGER.warning(f"Unsupported HVAC mode: {hvac_mode}")
                return
            # Refresh both coordinators
            await self.coordinator.async_request_refresh() # This is settings_coordinator
            await self.status_coordinator.async_request_refresh()
        except Exception as e:
            LOGGER.error(f"Error setting HVAC mode: {e}")