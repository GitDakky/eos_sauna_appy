# EOS Sauna Appy - Home Assistant Custom Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

Control your EOS Sauna with Home Assistant using its local HTTP API.

This custom integration allows you to monitor and control various aspects of your EOS sauna, including:
*   Current temperature and humidity
*   Target temperature and humidity
*   Sauna power (on/off)
*   Vaporizer power (on/off)
*   Sauna light (on/off and brightness)
*   Overall sauna status

## Prerequisites

*   An EOS sauna controller that exposes a local web interface (typically accessible via its IP address on your network). This integration interacts with the same API used by that web interface.
*   Home Assistant instance.
*   HACS installed (recommended for easy installation and updates).

## Installation

### Via HACS (Recommended)

1.  Ensure HACS is installed.
2.  Open HACS in Home Assistant.
3.  Go to "Integrations".
4.  Click the three dots in the top right and select "Custom repositories".
5.  Enter `https://github.com/GitDakky/eos_sauna_appy` in the "Repository" field.
6.  Select "Integration" as the category.
7.  Click "Add".
8.  The "EOS Sauna Appy" integration should now appear. Click "Install".
9.  Follow the on-screen instructions and restart Home Assistant when prompted.

### Manual Installation

1.  Using a tool like Samba, SSH, or VSCode, navigate to the `custom_components` directory in your Home Assistant configuration folder. If it doesn't exist, create it.
2.  Create a new folder named `eos_sauna_appy` inside `custom_components`.
3.  Download all the files from the `custom_components/eos_sauna_appy/` directory of this repository.
4.  Place these downloaded files into the newly created `eos_sauna_appy` folder on your Home Assistant instance.
5.  Restart Home Assistant.

## Configuration

1.  Go to **Settings** -> **Devices & Services** in Home Assistant.
2.  Click the **+ ADD INTEGRATION** button in the bottom right.
3.  Search for "EOS Sauna Appy" and select it.
4.  You will be prompted to enter the IP address of your EOS Sauna controller.
    *   Example: `192.168.1.101`
5.  Click "Submit".

The integration will attempt to connect to your sauna and automatically add the relevant entities to Home Assistant.

## Entities Provided

Once configured, the integration will create the following entities:

*   **Climate:**
    *   `climate.eos_sauna_appy_[sauna_ip]_sauna_climate`: Main control for sauna heating and target temperature.
*   **Sensors:**
    *   `sensor.eos_sauna_appy_[sauna_ip]_sauna_status`: Current operational status (e.g., Inactive, Finnish Mode, Fault).
    *   `sensor.eos_sauna_appy_[sauna_ip]_current_temperature`: Current sauna temperature (°C).
    *   `sensor.eos_sauna_appy_[sauna_ip]_target_temperature`: Target sauna temperature (°C).
    *   `sensor.eos_sauna_appy_[sauna_ip]_current_humidity`: Current sauna humidity (%).
    *   `sensor.eos_sauna_appy_[sauna_ip]_target_humidity`: Target sauna humidity (%).
*   **Switches:**
    *   `switch.eos_sauna_appy_[sauna_ip]_sauna_power`: Turn the main sauna heating element on/off.
    *   `switch.eos_sauna_appy_[sauna_ip]_vaporizer_power`: Turn the vaporizer on/off.
*   **Light:**
    *   `light.eos_sauna_appy_[sauna_ip]_sauna_light`: Control the sauna light (on/off and brightness).
*   **Numbers:**
    *   `number.eos_sauna_appy_[sauna_ip]_target_temperature_number`: Set the target sauna temperature.
    *   `number.eos_sauna_appy_[sauna_ip]_target_humidity_number`: Set the target sauna humidity.

*(Note: `[sauna_ip]` in the entity IDs will be replaced with the IP address you configured, with dots replaced by underscores).*

## API Details

This integration communicates with the local HTTP API of the EOS Sauna controller. Key endpoints used:
*   `http://[SAUNA_IP]/__/usr/eos/is` (GET): For current status.
*   `http://[SAUNA_IP]/__/usr/eos/setdev` (GET): For desired/device settings.
*   `http://[SAUNA_IP]/__/usr/eos/setcld` (POST): For sending control commands.

## Contributions

Contributions are welcome! Please open an issue or submit a pull request on the [GitHub repository](https://github.com/GitDakky/eos_sauna_appy).

## Disclaimer

This is an unofficial integration. It relies on the local web API of the EOS Sauna controller, which may change without notice. Use at your own risk. The developer (`@GitDakky`) is not affiliated with EOS Saunatechnik GmbH.

## License

This project is licensed under the Apache 2.0 License - see the `LICENSE` file for details (once created).