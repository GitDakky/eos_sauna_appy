"""Constants for EOS Sauna Appy."""
from logging import Logger, getLogger
from datetime import timedelta

LOGGER: Logger = getLogger(__package__)

NAME = "EOS Sauna Appy"
DOMAIN = "eos_sauna_appy"
VERSION = "0.1.0"
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
API_ENDPOINT_STATUS = "/__//usr/eos/is" # Actual status
API_ENDPOINT_SETTINGS = "/__//usr/eos/setdev" # Desired/device settings
API_ENDPOINT_CONTROL = "/__//usr/eos/setcld" # Control endpoint

# API Keys from /usr/eos/is (Actual Status)
API_KEY_SAUNA_STATE_ACTUAL = "S" # 0: Inactive, 1: Finnish, 2: BIO, 3: After burner, 4: Fault
API_KEY_LIGHT_STATE_ACTUAL = "L" # 0: Off, 1: On (seems to be binary from example)
API_KEY_CURRENT_TEMP = "T"
API_KEY_CURRENT_HUMIDITY = "H"
# Other keys from /usr/eos/is: E, R, BT, TNowH, TNowM, TAHM, TAHS, THOnH, THOnM, THOnS

# API Keys from /usr/eos/setdev (Desired/Device Settings)
API_KEY_LIGHT_STATE_DESIRED = "Lxd" # 0: Off, 1: On
API_KEY_SAUNA_STATE_DESIRED = "Sxd" # 0: Off, 1: On
API_KEY_VAPOR_STATE_DESIRED = "Vxd" # 0: Off, 1: On
API_KEY_LIGHT_INTENSITY_DESIRED = "Ld" # Percentage
API_KEY_TARGET_TEMP_DESIRED = "Td" # Celsius
API_KEY_TARGET_HUMIDITY_DESIRED = "Hd" # Percentage
# Other keys from /usr/eos/setdev: Cxd, AHxd, SOnAck, TStHd, TStMd

# API Keys for /usr/eos/setcld (Control)
API_KEY_CONTROL_LIGHT_ONOFF = "Lxc" # 1 for ON, 0 for OFF
API_KEY_CONTROL_SAUNA_ONOFF = "Sxc" # 1 for ON, 0 for OFF
API_KEY_CONTROL_VAPOR_ONOFF = "Vxc" # 1 for ON, 0 for OFF
API_KEY_CONTROL_LIGHT_INTENSITY = "Lc" # Percentage
API_KEY_CONTROL_TARGET_TEMP = "Tc" # Celsius
API_KEY_CONTROL_TARGET_HUMIDITY = "Hc" # Percentage

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