"""Switches for the PowerPlant: unit power and the outlet zones."""

from __future__ import annotations

import asyncio
from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import PowerPlantError
from .const import DOMAIN, POST_COMMAND_DELAY
from .coordinator import PowerPlantConfigEntry, PowerPlantCoordinator
from .entity import PowerPlantEntity
from .parser import P20_ZONES, Zone

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PowerPlantConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the power switch and one switch per zone."""
    coordinator = entry.runtime_data.coordinator
    entities: list[SwitchEntity] = [PowerPlantPowerSwitch(coordinator)]
    entities.extend(PowerPlantZoneSwitch(coordinator, zone) for zone in P20_ZONES)
    async_add_entities(entities)


class _CommandSwitch(PowerPlantEntity, SwitchEntity):
    """Sends a command, waits briefly, then asks the coordinator to re-read."""

    _attr_device_class = SwitchDeviceClass.OUTLET

    async def _async_send(self, on: bool) -> None:
        raise NotImplementedError

    async def _async_switch(self, on: bool) -> None:
        try:
            await self._async_send(on)
        except PowerPlantError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="command_failed",
                translation_placeholders={"error": str(err)},
            ) from err
        await asyncio.sleep(POST_COMMAND_DELAY)
        await self.coordinator.async_request_refresh()

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._async_switch(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._async_switch(False)


class PowerPlantPowerSwitch(_CommandSwitch):
    """Unit power: on, or off meaning standby."""

    _attr_translation_key = "power"
    _attr_device_class = SwitchDeviceClass.SWITCH

    def __init__(self, coordinator: PowerPlantCoordinator) -> None:
        super().__init__(coordinator, "power")

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.is_on

    async def _async_send(self, on: bool) -> None:
        await self.coordinator.client.async_set_power(on)


class PowerPlantZoneSwitch(_CommandSwitch):
    """One zone (A-E). The unit switches all outlets in a zone together."""

    def __init__(self, coordinator: PowerPlantCoordinator, zone: Zone) -> None:
        super().__init__(coordinator, f"zone_{zone.letter}")
        self._zone = zone
        self._attr_translation_key = f"zone_{zone.letter}"

    @property
    def suggested_object_id(self) -> str:
        # Keep entity ids short (switch.p20_zone_d) even though the high
        # current zones are named "Zone D (HC)".
        return f"zone {self._zone.letter}"

    @property
    def available(self) -> bool:
        return super().available and bool(self.coordinator.data.zone_outlets(self._zone))

    @property
    def is_on(self) -> bool | None:
        return self.coordinator.data.zone_is_on(self._zone)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        outlets = self.coordinator.data.zone_outlets(self._zone)
        return {
            "outlets": list(self._zone.outlets),
            "outlet_states": {str(o.number): "on" if o.is_on else "off" for o in outlets},
            "high_current": self._zone.high_current,
            "delay_mode": outlets[0].delay_mode if outlets else None,
        }

    async def _async_send(self, on: bool) -> None:
        await self.coordinator.client.async_set_outlet(self._zone.command_outlet, on)
