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
from homeassistant.const import UnitOfTemperature, PERCENTAGE

from .const import (
    DOMAIN,
    LOGGER,
    API_KEY_CURRENT_TEMP,
    API_KEY_TARGET_TEMP_DESIRED,
    API_KEY_CURRENT_HUMIDITY,
    API_KEY_TARGET_HUMIDITY_DESIRED,
    API_KEY_SAUNA_STATE_ACTUAL,
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
    client = data["client"] # Though not directly used by sensors, good to have if needed

    sensors = [
        EosSaunaStatusSensor(status_coordinator, entry, "Sauna Status", API_KEY_SAUNA_STATE_ACTUAL),
        EosSaunaTemperatureSensor(status_coordinator, entry, "Current Temperature", API_KEY_CURRENT_TEMP, False),
        EosSaunaTemperatureSensor(settings_coordinator, entry, "Target Temperature", API_KEY_TARGET_TEMP_DESIRED, True),
        EosSaunaHumiditySensor(status_coordinator, entry, "Current Humidity", API_KEY_CURRENT_HUMIDITY, False),
        EosSaunaHumiditySensor(settings_coordinator, entry, "Target Humidity", API_KEY_TARGET_HUMIDITY_DESIRED, True),
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
        self._is_setting = is_setting # Differentiates between actual status and desired setting sensors

        self._attr_name = f"{INTEGRATION_NAME} {self._config_entry.data.get('sauna_ip', '')} {name_suffix}"
        self._attr_unique_id = f"{config_entry.entry_id}_{data_key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": f"{INTEGRATION_NAME} ({config_entry.data.get('sauna_ip', '')})",
            "manufacturer": MANUFACTURER,
            "model": "Web API Controlled Sauna", # Can be improved if model info is available
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


class EosSaunaHumiditySensor(EosSaunaBaseSensor):
    """Representation of a Sauna Humidity sensor."""

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, config_entry: ConfigEntry, name_suffix: str, data_key: str, is_setting: bool):
        """Initialize the humidity sensor."""
        super().__init__(coordinator, config_entry, name_suffix, data_key, is_setting)
        self._attr_icon = "mdi:water-percent"