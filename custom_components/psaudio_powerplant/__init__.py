"""PS Audio PowerPlant integration."""

from __future__ import annotations

from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import PowerPlantClient
from .coordinator import PowerPlantConfigEntry, PowerPlantCoordinator, PowerPlantRuntimeData

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.SENSOR, Platform.SWITCH]


async def async_setup_entry(hass: HomeAssistant, entry: PowerPlantConfigEntry) -> bool:
    """Set up a PowerPlant from a config entry."""
    client = PowerPlantClient(async_get_clientsession(hass), entry.data[CONF_HOST])
    coordinator = PowerPlantCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = PowerPlantRuntimeData(client=client, coordinator=coordinator)
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: PowerPlantConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_options_updated(hass: HomeAssistant, entry: PowerPlantConfigEntry) -> None:
    """Reload so a new scan interval takes effect."""
    await hass.config_entries.async_reload(entry.entry_id)
