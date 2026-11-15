"""Polling coordinator for the PowerPlant."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import PowerPlantClient, PowerPlantError
from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN, scan_interval_from_seconds
from .parser import PowerPlantStatus

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class PowerPlantRuntimeData:
    """Objects kept on the config entry while it is loaded."""

    client: PowerPlantClient
    coordinator: PowerPlantCoordinator


type PowerPlantConfigEntry = ConfigEntry[PowerPlantRuntimeData]


class PowerPlantCoordinator(DataUpdateCoordinator[PowerPlantStatus]):
    """Fetches the status dump once per interval with a single request."""

    config_entry: PowerPlantConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: PowerPlantConfigEntry,
        client: PowerPlantClient,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN} {client.host}",
            update_interval=scan_interval_from_seconds(
                entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
            ),
        )
        self.client = client

    async def _async_update_data(self) -> PowerPlantStatus:
        try:
            return await self.client.async_get_status()
        except PowerPlantError as err:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="update_failed",
                translation_placeholders={"error": str(err)},
            ) from err
