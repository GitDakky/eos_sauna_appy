"""Constants for EOS Sauna Appy."""
from logging import Logger, getLogger
from datetime import timedelta

LOGGER: Logger = getLogger(__package__)

NAME = "EOS Sauna Appy"
DOMAIN = "eos_sauna_appy"
VERSION = "0.1.2"
ATTRIBUTION = "Data provided by EOS Sauna HTTP API"

# Platforms
PLATFORMS = ["sensor", "switch", "light", "number", "climate"]

# Configuration and options
CONF_SAUNA_IP = "sauna_ip"

# Defaults
DEFAULT_NAME = DOMAIN

# Intervals
SCAN_INTERVAL_STATUS = timedelta(seconds=10)
SCAN_INTERVAL_SETTINGS = timedelta(seconds=30)


STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom integration for EOS Saunas using their local HTTP API!
If you have any issues with this you need to open an issue here:
https://github.com/GitDakky/eos_sauna_appy/issues
-------------------------------------------------------------------
"""

# API Endpoints
API_ENDPOINT_STATUS = "/__/usr/eos/is" # Actual status
API_ENDPOINT_SETTINGS = "/__/usr/eos/setdev" # Desired/device settings
API_ENDPOINT_CONTROL = "/__/usr/eos/setcld" # Control endpoint

# API Keys from /usr/eos/is (Actual Status)
API_KEY_SAUNA_STATE_ACTUAL = "S" # 0: Inactive, 1: Finnish, 2: BIO, 3: After burner, 4: Fault
API_KEY_LIGHT_STATE_ACTUAL = "L" # 0: Off, 1: On (seems to be binary from example)
API_KEY_CURRENT_TEMP = "T"
# Bench sensor (Bankfühler) above the rear bench — present only when cfg.SBT = 1.
# With a bench sensor installed the controller regulates on BT; T (heater sensor
# above the stove) only acts as a limiter above ~120 °C.
API_KEY_BENCH_TEMP = "BT"
API_KEY_CURRENT_HUMIDITY = "H"
# Wall-clock on the controller (/usr/eos/is) — NOT a heating timer.
API_KEY_DEVICE_TIME_H = "TNowH"
API_KEY_DEVICE_TIME_M = "TNowM"
# Remaining auto-stop countdown while heating (/usr/eos/is).
API_KEY_HEATING_REMAINING_H = "THOnH"
API_KEY_HEATING_REMAINING_M = "THOnM"
API_KEY_HEATING_REMAINING_S = "THOnS"
# Other keys from /usr/eos/is: E, R, BT, TAHM, TAHS

# API Keys from /usr/eos/setdev (Desired/Device Settings)
API_KEY_LIGHT_STATE_DESIRED = "Lxd" # 0: Off, 1: On
API_KEY_SAUNA_STATE_DESIRED = "Sxd" # 0: Off, 1: On
API_KEY_VAPOR_STATE_DESIRED = "Vxd" # 0: Off, 1: On
API_KEY_LIGHT_INTENSITY_DESIRED = "Ld" # Percentage
API_KEY_TARGET_TEMP_DESIRED = "Td" # Celsius
API_KEY_TARGET_HUMIDITY_DESIRED = "Hd" # Percentage
# Delayed start (Vorwahl / timer J) — 99:99 = disabled (--:--).
API_KEY_SCHEDULED_START_H = "TStHd"
API_KEY_SCHEDULED_START_M = "TStMd"
# Auto-stop period desired values from /usr/eos/setdev (often 0 = profile default).
API_KEY_AUTO_STOP_DESIRED_H = "Cxd"
API_KEY_AUTO_STOP_DESIRED_ALT_H = "AHxd"
# Other keys from /usr/eos/setdev: SOnAck

# API Keys for /usr/eos/setcld (Control)
API_KEY_CONTROL_LIGHT_ONOFF = "Lxc" # 1 for ON, 0 for OFF
API_KEY_CONTROL_SAUNA_ONOFF = "Sxc" # 1 for ON, 0 for OFF
API_KEY_CONTROL_VAPOR_ONOFF = "Vxc" # 1 for ON, 0 for OFF
API_KEY_CONTROL_LIGHT_INTENSITY = "Lc" # Percentage
API_KEY_CONTROL_TARGET_TEMP = "Tc" # Celsius
API_KEY_CONTROL_TARGET_HUMIDITY = "Hc" # Percentage
API_KEY_CONTROL_SCHEDULED_START_H = "TStHc"
API_KEY_CONTROL_SCHEDULED_START_M = "TStMc"
API_KEY_CONTROL_AUTO_STOP_H = "Cxc"
API_KEY_CONTROL_AUTO_STOP_ALT_H = "AHxc"
API_KEY_CONTROL_AUTO_STOP_M = "AHmc"

# Sentinel in setdev when delayed start is disabled.
SCHEDULED_START_DISABLED = 99

# Default auto-stop period (hours) when nothing was configured yet.
DEFAULT_HEATING_PERIOD_HOURS = 5.0

# Sauna Status Mapping
SAUNA_STATUS_MAP = {
    0: "Inactive",
    1: "Finnish Mode",
    2: "BIO Mode",
    3: "After Burner Mode",
    4: "Fault",
    250: "Error 250",
    251: "Error 251",
    252: "Error: Invalid Write Frame",
    253: "Error: Read-Only Frame",
    254: "Error: No Read/Write Frame",
    255: "Error: No Status Info",
}

# Device Info
MANUFACTURER = "EOS Saunatechnik GmbH"