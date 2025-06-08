"""EOS Sauna Appy API Client."""
import asyncio
import socket
import aiohttp
import async_timeout

from .const import (
    LOGGER,
    API_ENDPOINT_STATUS,
    API_ENDPOINT_SETTINGS,
    API_ENDPOINT_CONTROL,
)

TIMEOUT = 10


class EosSaunaApiClientError(Exception):
    """Exception to indicate a general API error."""


class EosSaunaApiCommunicationError(EosSaunaApiClientError):
    """Exception to indicate a communication error."""


class EosSaunaApiAuthError(EosSaunaApiClientError):
    """Exception to indicate an authentication error."""


class EosSaunaApiClient:
    """EOS Sauna API Client."""

    def __init__(self, sauna_ip: str, session: aiohttp.ClientSession) -> None:
        """Initialize API client."""
        self._sauna_ip = sauna_ip
        self._session = session
        self._base_url = f"http://{self._sauna_ip}"

    async def _api_wrapper(
        self, method: str, url: str, data: dict | None = None, headers: dict | None = None
    ) -> any:
        """Wrap API calls."""
        try:
            async with async_timeout.timeout(TIMEOUT):
                response = await self._session.request(
                    method=method,
                    url=f"{self._base_url}{url}",
                    headers=headers,
                    json=data,
                )
                if response.status in (401, 403):
                    raise EosSaunaApiAuthError(
                        f"Invalid credentials for {url}: {response.status}"
                    )
                response.raise_for_status()
                return await response.json()
        except asyncio.TimeoutError as exception:
            raise EosSaunaApiCommunicationError(
                f"Timeout error fetching data from {url}: {exception}"
            ) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            raise EosSaunaApiCommunicationError(
                f"Error fetching data from {url}: {exception}"
            ) from exception
        except Exception as exception:
            LOGGER.error(f"Something really wrong happened! - {exception}")
            raise EosSaunaApiClientError(
                f"Something really wrong happened! - {exception}"
            ) from exception

    async def async_get_status(self) -> dict:
        """Get the actual status from the sauna."""
        return await self._api_wrapper("get", API_ENDPOINT_STATUS)

    async def async_get_settings(self) -> dict:
        """Get the desired/device settings from the sauna."""
        return await self._api_wrapper("get", API_ENDPOINT_SETTINGS)

    async def async_set_control_value(self, key: str, value: any) -> dict:
        """Set a control value on the sauna."""
        payload = {key: value}
        LOGGER.debug(f"Sending control payload: {payload}")
        return await self._api_wrapper("post", API_ENDPOINT_CONTROL, data=payload)

    async def async_set_light_onoff(self, is_on: bool) -> dict:
        """Turn the light on or off."""
        return await self.async_set_control_value("Lxc", 1 if is_on else 0)

    async def async_set_sauna_onoff(self, is_on: bool) -> dict:
        """Turn the sauna on or off."""
        return await self.async_set_control_value("Sxc", 1 if is_on else 0)

    async def async_set_vapor_onoff(self, is_on: bool) -> dict:
        """Turn the vaporizer on or off."""
        return await self.async_set_control_value("Vxc", 1 if is_on else 0)

    async def async_set_light_intensity(self, intensity: int) -> dict:
        """Set the light intensity."""
        if not 0 <= intensity <= 100:
            raise ValueError("Light intensity must be between 0 and 100.")
        return await self.async_set_control_value("Lc", intensity)

    async def async_set_target_temperature(self, temperature: int) -> dict:
        """Set the target temperature."""
        # Assuming a reasonable range, e.g., 30-115 C based on HTML
        if not 30 <= temperature <= 115:
            raise ValueError("Target temperature must be between 30 and 115.")
        return await self.async_set_control_value("Tc", temperature)

    async def async_set_target_humidity(self, humidity: int) -> dict:
        """Set the target humidity."""
        if not 0 <= humidity <= 100:
            raise ValueError("Target humidity must be between 0 and 100.")
        return await self.async_set_control_value("Hc", humidity)