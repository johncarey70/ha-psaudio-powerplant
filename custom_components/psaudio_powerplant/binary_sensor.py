"""Binary sensors for the PowerPlant: per-outlet status and diagnostics."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import PowerPlantConfigEntry, PowerPlantCoordinator
from .entity import PowerPlantEntity
from .parser import P20_ZONES, PowerPlantStatus, Zone

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class PowerPlantBinarySensorDescription(BinarySensorEntityDescription):
    """Binary sensor description with a function that reads the status."""

    value_fn: Callable[[PowerPlantStatus], bool | None]


BINARY_SENSORS: tuple[PowerPlantBinarySensorDescription, ...] = (
    # Raw "umov" flag. It reads 1 on a healthy unit; its exact meaning is not
    # documented, so no device class is claimed.
    PowerPlantBinarySensorDescription(
        key="mov_status",
        translation_key="mov_status",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda s: s.mov_ok,
    ),
    PowerPlantBinarySensorDescription(
        key="unit_lockout",
        translation_key="unit_lockout",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda s: s.locked,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PowerPlantConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the diagnostic flags and one read-only status per outlet."""
    coordinator = entry.runtime_data.coordinator
    entities: list[BinarySensorEntity] = [
        PowerPlantBinarySensor(coordinator, d) for d in BINARY_SENSORS
    ]
    entities.extend(
        PowerPlantOutletStatus(coordinator, zone, number)
        for zone in P20_ZONES
        for number in zone.outlets
    )
    async_add_entities(entities)


class PowerPlantBinarySensor(PowerPlantEntity, BinarySensorEntity):
    """A flag read from the status dump."""

    entity_description: PowerPlantBinarySensorDescription

    def __init__(
        self,
        coordinator: PowerPlantCoordinator,
        description: PowerPlantBinarySensorDescription,
    ) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        return self.entity_description.value_fn(self.coordinator.data)


class PowerPlantOutletStatus(PowerPlantEntity, BinarySensorEntity):
    """Read-only power state of one outlet.

    Outlets cannot be switched on their own (the zone switches do that); this
    entity exists so each outlet can be renamed after what is plugged into it.
    """

    _attr_device_class = BinarySensorDeviceClass.POWER
    _attr_translation_key = "outlet"

    def __init__(self, coordinator: PowerPlantCoordinator, zone: Zone, number: int) -> None:
        # Distinct from the 0.1.0 outlet switches' "<mac>_outlet_<n>" ids.
        super().__init__(coordinator, f"outlet_{number}_status")
        self._zone = zone
        self._number = number
        self._attr_translation_placeholders = {"number": str(number)}

    @property
    def available(self) -> bool:
        return super().available and self._number in self.coordinator.data.outlets

    @property
    def is_on(self) -> bool | None:
        outlet = self.coordinator.data.outlets.get(self._number)
        return outlet.is_on if outlet else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"zone": self._zone.letter.upper(), "outlet_number": self._number}
