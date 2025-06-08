"""Switch platform for EOS Sauna Appy."""
from homeassistant.components.switch import SwitchEntity, SwitchDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    LOGGER,
    API_KEY_SAUNA_STATE_DESIRED, # Sxd
    API_KEY_VAPOR_STATE_DESIRED, # Vxd
    MANUFACTURER,
    NAME as INTEGRATION_NAME,
)
from .api import EosSaunaApiClient


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the switch platform."""
    data = hass.data[DOMAIN][entry.entry_id]
    # Switches will use the settings_coordinator to reflect the desired state
    # and the client to send commands.
    settings_coordinator = data["settings_coordinator"]
    client = data["client"]

    switches = [
        EosSaunaControlSwitch(
            settings_coordinator,
            entry,
            client,
            "Sauna Power",
            API_KEY_SAUNA_STATE_DESIRED,
            client.async_set_sauna_onoff,
            "mdi:radiator" # Using radiator icon as a generic heater
        ),
        EosSaunaControlSwitch(
            settings_coordinator,
            entry,
            client,
            "Vaporizer Power",
            API_KEY_VAPOR_STATE_DESIRED,
            client.async_set_vapor_onoff,
            "mdi:water-boiler" # Using water-boiler for vaporizer
        ),
    ]
    async_add_entities(switches)


class EosSaunaControlSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of an EOS Sauna control switch."""

    _attr_device_class = SwitchDeviceClass.SWITCH

    def __init__(
        self,
        coordinator,
        config_entry: ConfigEntry,
        client: EosSaunaApiClient,
        name_suffix: str,
        data_key: str,
        turn_on_off_service_call, # e.g., client.async_set_sauna_onoff
        icon: str = "mdi:toggle-switch"
    ):
        """Initialize the switch."""
        super().__init__(coordinator) # Using settings_coordinator
        self._config_entry = config_entry
        self._client = client
        self._data_key = data_key # This key comes from /usr/eos/setdev
        self._turn_on_off_service_call = turn_on_off_service_call
        self._attr_icon = icon

        self._attr_name = f"{INTEGRATION_NAME} {self._config_entry.data.get('sauna_ip', '')} {name_suffix}"
        self._attr_unique_id = f"{config_entry.entry_id}_{data_key}_switch"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": f"{INTEGRATION_NAME} ({config_entry.data.get('sauna_ip', '')})",
            "manufacturer": MANUFACTURER,
            "model": "Web API Controlled Sauna",
        }

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return super().available and self.coordinator.data is not None and self._data_key in self.coordinator.data

    @property
    def is_on(self) -> bool | None:
        """Return true if the switch is on."""
        if self.coordinator.data and self._data_key in self.coordinator.data:
            # API uses "1" for ON and "0" for OFF for these desired states
            return str(self.coordinator.data[self._data_key]) == "1"
        return None

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the entity on."""
        LOGGER.debug(f"Turning ON {self.name} via API call.")
        try:
            await self._turn_on_off_service_call(True)
            # After sending command, refresh the coordinator that holds the desired state
            await self.coordinator.async_request_refresh()
        except Exception as e:
            LOGGER.error(f"Error turning ON {self.name}: {e}")

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the entity off."""
        LOGGER.debug(f"Turning OFF {self.name} via API call.")
        try:
            await self._turn_on_off_service_call(False)
            # After sending command, refresh the coordinator that holds the desired state
            await self.coordinator.async_request_refresh()
        except Exception as e:
            LOGGER.error(f"Error turning OFF {self.name}: {e}")