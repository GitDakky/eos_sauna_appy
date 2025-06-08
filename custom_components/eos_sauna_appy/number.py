"""Number platform for EOS Sauna Appy."""
from homeassistant.components.number import NumberEntity, NumberDeviceClass, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import UnitOfTemperature, PERCENTAGE

from .const import (
    DOMAIN,
    LOGGER,
    API_KEY_TARGET_TEMP_DESIRED,  # Td
    API_KEY_TARGET_HUMIDITY_DESIRED,  # Hd
    MANUFACTURER,
    NAME as INTEGRATION_NAME,
)
from .api import EosSaunaApiClient


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the number platform."""
    data = hass.data[DOMAIN][entry.entry_id]
    settings_coordinator = data["settings_coordinator"]
    client = data["client"]

    numbers = [
        EosSaunaTargetTemperatureNumber(
            settings_coordinator,
            entry,
            client,
            "Target Temperature",
            API_KEY_TARGET_TEMP_DESIRED,
        ),
        EosSaunaTargetHumidityNumber(
            settings_coordinator,
            entry,
            client,
            "Target Humidity",
            API_KEY_TARGET_HUMIDITY_DESIRED,
        ),
    ]
    async_add_entities(numbers)


class EosSaunaBaseNumber(CoordinatorEntity, NumberEntity):
    """Base class for EOS Sauna number entities."""

    _attr_mode = NumberMode.BOX  # Or NumberMode.SLIDER

    def __init__(
        self,
        coordinator, # settings_coordinator
        config_entry: ConfigEntry,
        client: EosSaunaApiClient,
        name_suffix: str,
        data_key: str,
        set_value_service_call,
    ):
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._client = client
        self._data_key = data_key # Key from /usr/eos/setdev
        self._set_value_service_call = set_value_service_call

        self._attr_name = f"{INTEGRATION_NAME} {self._config_entry.data.get('sauna_ip', '')} {name_suffix}"
        self._attr_unique_id = f"{config_entry.entry_id}_{data_key}_number"
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
    def native_value(self) -> float | None:
        """Return the current value."""
        if self.available:
            value = self.coordinator.data.get(self._data_key)
            if value is not None:
                try:
                    return float(value)
                except (ValueError, TypeError):
                    LOGGER.warning(f"Could not parse number value for {self.name}: {value}")
                    return None
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        LOGGER.debug(f"Setting {self.name} to {value} via API call.")
        try:
            await self._set_value_service_call(int(value)) # API expects int
            await self.coordinator.async_request_refresh()
        except Exception as e:
            LOGGER.error(f"Error setting {self.name} to {value}: {e}")


class EosSaunaTargetTemperatureNumber(EosSaunaBaseNumber):
    """Representation of a Target Temperature number entity."""

    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_native_min_value = 30  # Based on HTML form validation
    _attr_native_max_value = 115 # Based on HTML form validation
    _attr_native_step = 1.0
    _attr_icon = "mdi:thermometer-plus"


    def __init__(
        self,
        coordinator,
        config_entry: ConfigEntry,
        client: EosSaunaApiClient,
        name_suffix: str,
        data_key: str,
    ):
        """Initialize the target temperature number entity."""
        super().__init__(
            coordinator,
            config_entry,
            client,
            name_suffix,
            data_key,
            client.async_set_target_temperature,
        )


class EosSaunaTargetHumidityNumber(EosSaunaBaseNumber):
    """Representation of a Target Humidity number entity."""

    _attr_device_class = NumberDeviceClass.HUMIDITY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1.0
    _attr_icon = "mdi:water-percent-alert" # Using alert icon to indicate it's a target

    def __init__(
        self,
        coordinator,
        config_entry: ConfigEntry,
        client: EosSaunaApiClient,
        name_suffix: str,
        data_key: str,
    ):
        """Initialize the target humidity number entity."""
        super().__init__(
            coordinator,
            config_entry,
            client,
            name_suffix,
            data_key,
            client.async_set_target_humidity,
        )