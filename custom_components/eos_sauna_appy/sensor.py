"""Sensor platform for EOS Sauna Appy."""
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import UnitOfTemperature, PERCENTAGE, UnitOfTime

from .const import (
    DOMAIN,
    API_KEY_CURRENT_TEMP,
    API_KEY_BENCH_TEMP,
    API_KEY_TARGET_TEMP_DESIRED,
    API_KEY_CURRENT_HUMIDITY,
    API_KEY_TARGET_HUMIDITY_DESIRED,
    API_KEY_SAUNA_STATE_ACTUAL,
    API_KEY_HEATING_REMAINING_H,
    API_KEY_HEATING_REMAINING_M,
    API_KEY_HEATING_REMAINING_S,
    SAUNA_STATUS_MAP,
    MANUFACTURER,
    NAME as INTEGRATION_NAME,
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the sensor platform."""
    data = hass.data[DOMAIN][entry.entry_id]
    status_coordinator = data["status_coordinator"]
    settings_coordinator = data["settings_coordinator"]

    sensors = [
        EosSaunaStatusSensor(status_coordinator, entry, "Sauna Status", API_KEY_SAUNA_STATE_ACTUAL),
        EosSaunaTemperatureSensor(status_coordinator, entry, "Current Temperature", API_KEY_CURRENT_TEMP, False),
        EosSaunaTemperatureSensor(status_coordinator, entry, "Bench Temperature", API_KEY_BENCH_TEMP, False),
        EosSaunaTemperatureSensor(settings_coordinator, entry, "Target Temperature", API_KEY_TARGET_TEMP_DESIRED, True),
        EosSaunaHumiditySensor(status_coordinator, entry, "Current Humidity", API_KEY_CURRENT_HUMIDITY, False),
        EosSaunaHumiditySensor(settings_coordinator, entry, "Target Humidity", API_KEY_TARGET_HUMIDITY_DESIRED, True),
        EosSaunaHeatingRemainingSensor(status_coordinator, entry),
    ]
    async_add_entities(sensors)


class EosSaunaBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for EOS Sauna sensors."""

    def __init__(self, coordinator, config_entry: ConfigEntry, name_suffix: str, data_key: str, is_setting: bool):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._data_key = data_key
        self._name_suffix = name_suffix
        self._is_setting = is_setting

        self._attr_name = f"{INTEGRATION_NAME} {self._config_entry.data.get('sauna_ip', '')} {name_suffix}"
        self._attr_unique_id = f"{config_entry.entry_id}_{data_key}"
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
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data and self._data_key in self.coordinator.data:
            return self.coordinator.data[self._data_key]
        return None


class EosSaunaStatusSensor(EosSaunaBaseSensor):
    """Representation of the Sauna Status sensor."""

    def __init__(self, coordinator, config_entry: ConfigEntry, name_suffix: str, data_key: str):
        """Initialize the status sensor."""
        super().__init__(coordinator, config_entry, name_suffix, data_key, False)
        self._attr_icon = "mdi:sauna"
        self._attr_device_class = SensorDeviceClass.ENUM
        self._attr_options = list(SAUNA_STATUS_MAP.values())

    @property
    def native_value(self):
        """Return the state of the sensor."""
        raw_status = super().native_value
        if raw_status is not None:
            return SAUNA_STATUS_MAP.get(raw_status, f"Unknown ({raw_status})")
        return "Unknown"


class EosSaunaTemperatureSensor(EosSaunaBaseSensor):
    """Representation of a Sauna Temperature sensor."""

    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, config_entry: ConfigEntry, name_suffix: str, data_key: str, is_setting: bool):
        """Initialize the temperature sensor."""
        super().__init__(coordinator, config_entry, name_suffix, data_key, is_setting)
        self._attr_icon = "mdi:thermometer"


class EosSaunaHeatingRemainingSensor(CoordinatorEntity, SensorEntity):
    """Remaining auto-stop time while sauna is heating (THOnH/M/S)."""

    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:timer-sand"

    def __init__(self, status_coordinator, config_entry: ConfigEntry):
        """Initialize remaining heating timer sensor."""
        super().__init__(status_coordinator)
        self._config_entry = config_entry
        self._attr_name = (
            f"{INTEGRATION_NAME} {self._config_entry.data.get('sauna_ip', '')} "
            "Heating Remaining"
        )
        self._attr_unique_id = f"{config_entry.entry_id}_heating_remaining"
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

    @staticmethod
    def _sauna_is_heating(status_data: dict) -> bool:
        raw_status = status_data.get(API_KEY_SAUNA_STATE_ACTUAL)
        return raw_status in (1, 2, 3)

    @property
    def native_value(self) -> int | None:
        """Remaining seconds while heating; otherwise None."""
        status_data = self.coordinator.data or {}
        if not self._sauna_is_heating(status_data):
            return None
        hours = status_data.get(API_KEY_HEATING_REMAINING_H)
        minutes = status_data.get(API_KEY_HEATING_REMAINING_M)
        seconds = status_data.get(API_KEY_HEATING_REMAINING_S)
        if hours is None or minutes is None or seconds is None:
            return None
        try:
            return int(hours) * 3600 + int(minutes) * 60 + int(seconds)
        except (TypeError, ValueError):
            return None


class EosSaunaHumiditySensor(EosSaunaBaseSensor):
    """Representation of a Sauna Humidity sensor."""

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, config_entry: ConfigEntry, name_suffix: str, data_key: str, is_setting: bool):
        """Initialize the humidity sensor."""
        super().__init__(coordinator, config_entry, name_suffix, data_key, is_setting)
        self._attr_icon = "mdi:water-percent"
