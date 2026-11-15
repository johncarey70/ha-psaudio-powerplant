"""Base entity for the PowerPlant."""

from __future__ import annotations

from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import PowerPlantCoordinator


class PowerPlantEntity(CoordinatorEntity[PowerPlantCoordinator]):
    """Shared device info and unique-id scheme."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: PowerPlantCoordinator, key: str) -> None:
        super().__init__(coordinator)
        entry = coordinator.config_entry
        # unique_id of the entry is the unit's MAC address.
        device_id = entry.unique_id or entry.entry_id
        self._attr_unique_id = f"{device_id}_{key}"

        status = coordinator.data
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            connections={(CONNECTION_NETWORK_MAC, status.mac)} if status.mac else set(),
            manufacturer=MANUFACTURER,
            model=status.unit_type.upper(),
            name=entry.title,
            sw_version=status.firmware,
        )
