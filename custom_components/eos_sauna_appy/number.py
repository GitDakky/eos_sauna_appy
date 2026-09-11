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
    API_KEY_TARGET_TEMP_DESIRED,
    API_KEY_TARGET_HUMIDITY_DESIRED,
    DEFAULT_HEATING_PERIOD_HOURS,
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
        EosSaunaHeatingPeriodNumber(settings_coordinator, entry, client),
    ]
    async_add_entities(numbers)


class EosSaunaBaseNumber(CoordinatorEntity, NumberEntity):
    """Base class for EOS Sauna number entities."""

    _attr_mode = NumberMode.BOX

    def __init__(
        self,
        coordinator,
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
        self._data_key = data_key
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
            await self._set_value_service_call(int(value))
            await self.coordinator.async_request_refresh()
        except Exception as e:
            LOGGER.error(f"Error setting {self.name} to {value}: {e}")


class EosSaunaTargetTemperatureNumber(EosSaunaBaseNumber):
    """Representation of a Target Temperature number entity."""

    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_native_min_value = 30
    _attr_native_max_value = 115
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


def _decimal_hours_to_hm(value: float) -> tuple[int, int]:
    """Convert decimal hours to whole hours and minutes."""
    total_minutes = int(round(value * 60))
    return divmod(total_minutes, 60)


class EosSaunaHeatingPeriodNumber(CoordinatorEntity, NumberEntity):
    """EOS auto-stop heating period in decimal hours (HA-side desired value)."""

    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = 3.0
    _attr_native_max_value = 8.0
    _attr_native_step = 0.5
    _attr_native_unit_of_measurement = "h"
    _attr_icon = "mdi:timer-outline"

    def __init__(
        self,
        coordinator,
        config_entry: ConfigEntry,
        client: EosSaunaApiClient,
    ):
        """Initialize heating period number."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._client = client
        self._configured_hours = DEFAULT_HEATING_PERIOD_HOURS
        self._attr_name = (
            f"{INTEGRATION_NAME} {self._config_entry.data.get('sauna_ip', '')} "
            "Heating Period"
        )
        self._attr_unique_id = f"{config_entry.entry_id}_heating_period"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": f"{INTEGRATION_NAME} ({config_entry.data.get('sauna_ip', '')})",
            "manufacturer": MANUFACTURER,
            "model": "Web API Controlled Sauna",
        }

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return super().available and self.coordinator.data is not None

    @property
    def native_value(self) -> float:
        """Return configured heating period in decimal hours."""
        return self._configured_hours

    async def async_set_native_value(self, value: float) -> None:
        """Update heating period on the sauna controller."""
        hours, minutes = _decimal_hours_to_hm(value)
        LOGGER.debug(f"Setting heating period to {hours}h {minutes}m via API call.")
        try:
            await self._client.async_set_heating_period(hours, minutes)
            self._configured_hours = value
            self.async_write_ha_state()
            await self.coordinator.async_request_refresh()
        except Exception as e:
            LOGGER.error(f"Error setting heating period to {value}: {e}")


class EosSaunaTargetHumidityNumber(EosSaunaBaseNumber):
    """Representation of a Target Humidity number entity."""

    _attr_device_class = NumberDeviceClass.HUMIDITY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1.0
    _attr_icon = "mdi:water-percent-alert"

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
