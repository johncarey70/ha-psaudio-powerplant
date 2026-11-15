"""Small async client for the PowerPlant web interface."""

from __future__ import annotations

import asyncio
import re
import time

import aiohttp
from yarl import URL

from .const import MIN_REQUEST_GAP, REQUEST_TIMEOUT
from .parser import PowerPlantParseError, PowerPlantStatus, parse_status

# Commands are sent unencoded (e.g. ``UP=ON``, ``ZP=3,OFF``); only allow the
# characters these commands use so nothing odd can reach the URL.
_SAFE_COMMAND = re.compile(r"^[A-Z]{2}(=[A-Z0-9,]+)?$")


class PowerPlantError(Exception):
    """Base error for the PowerPlant client."""


class PowerPlantConnectionError(PowerPlantError):
    """The unit could not be reached or did not answer in time."""


class PowerPlantResponseError(PowerPlantError):
    """The unit answered with something unexpected."""


class PowerPlantClient:
    """Talks to one PowerPlant, one request at a time.

    All requests share one lock and are spaced at least MIN_REQUEST_GAP
    seconds apart, because the unit's network side can freeze under load.
    Nothing is retried here; the coordinator simply tries again next poll.
    """

    def __init__(self, session: aiohttp.ClientSession, host: str) -> None:
        self._session = session
        self._host = host.strip()
        self._lock = asyncio.Lock()
        self._last_request = 0.0

    @property
    def host(self) -> str:
        """Host name or IP address of the unit."""
        return self._host

    async def async_get_status(self) -> PowerPlantStatus:
        """Read the full status dump (``RA``)."""
        text = await self._async_command("RA")
        try:
            return parse_status(text)
        except PowerPlantParseError as err:
            raise PowerPlantResponseError(str(err)) from err

    async def async_set_power(self, on: bool) -> None:
        """Turn the unit on, or put it in standby."""
        await self._async_command("UP=ON" if on else "UP=OFF")

    async def async_set_outlet(self, number: int, on: bool) -> None:
        """Switch the zone containing outlet ``number`` on or off."""
        if not 1 <= number <= 99:
            raise ValueError(f"Invalid outlet number: {number}")
        await self._async_command(f"ZP={number},{'ON' if on else 'OFF'}")

    async def _async_command(self, command: str) -> str:
        if not _SAFE_COMMAND.match(command):
            raise ValueError(f"Refusing unexpected command: {command!r}")
        # encoded=True keeps the '=' and ',' literal, as the unit expects.
        url = URL(f"http://{self._host}/commands.cgi?command={command}", encoded=True)

        async with self._lock:
            wait = MIN_REQUEST_GAP - (time.monotonic() - self._last_request)
            if wait > 0:
                await asyncio.sleep(wait)
            try:
                async with self._session.get(
                    url, timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
                ) as resp:
                    if resp.status != 200:
                        raise PowerPlantResponseError(f"HTTP {resp.status} for {command}")
                    return await resp.text(errors="replace")
            except (TimeoutError, aiohttp.ClientError) as err:
                raise PowerPlantConnectionError(f"Could not reach {self._host}: {err!r}") from err
            finally:
                self._last_request = time.monotonic()
