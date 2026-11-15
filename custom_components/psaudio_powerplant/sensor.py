"""Measurement and setting sensors for the PowerPlant."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import PowerPlantConfigEntry, PowerPlantCoordinator
from .entity import PowerPlantEntity
from .parser import PowerPlantStatus

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class PowerPlantSensorDescription(SensorEntityDescription):
    """Sensor description with a function that reads the status."""

    value_fn: Callable[[PowerPlantStatus], float | int | str | None]


def _measurement(
    key: str,
    value_fn: Callable[[PowerPlantStatus], float | None],
    device_class: SensorDeviceClass | None,
    unit: str | None,
    precision: int | None = None,
) -> PowerPlantSensorDescription:
    return PowerPlantSensorDescription(
        key=key,
        translation_key=key,
        device_class=device_class,
        native_unit_of_measurement=unit,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=precision,
        value_fn=value_fn,
    )


SENSORS: tuple[PowerPlantSensorDescription, ...] = (
    _measurement(
        "input_voltage",
        lambda s: s.input_voltage,
        SensorDeviceClass.VOLTAGE,
        UnitOfElectricPotential.VOLT,
        1,
    ),
    _measurement(
        "output_voltage",
        lambda s: s.output_voltage,
        SensorDeviceClass.VOLTAGE,
        UnitOfElectricPotential.VOLT,
        1,
    ),
    _measurement("input_thd", lambda s: s.input_thd, None, PERCENTAGE, 1),
    _measurement("output_thd", lambda s: s.output_thd, None, PERCENTAGE, 1),
    _measurement(
        "output_current",
        lambda s: s.output_current,
        SensorDeviceClass.CURRENT,
        UnitOfElectricCurrent.AMPERE,
        2,
    ),
    # Output volts x amps (see PowerPlantStatus.output_power); the key is
    # unchanged from 0.1.0 so the sensor keeps its history.
    _measurement(
        "output_power", lambda s: s.output_power, SensorDeviceClass.POWER, UnitOfPower.WATT, 0
    ),
    PowerPlantSensorDescription(
        # The unit's own watts field, kept only for comparison: it is
        # unreliable on the P20.
        key="reported_watts",
        translation_key="reported_watts",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda s: s.reported_watts,
    ),
    _measurement(
        "frequency", lambda s: s.frequency, SensorDeviceClass.FREQUENCY, UnitOfFrequency.HERTZ, 1
    ),
    _measurement(
        "temperature_1",
        lambda s: s.temperature_1,
        SensorDeviceClass.TEMPERATURE,
        UnitOfTemperature.CELSIUS,
        0,
    ),
    _measurement(
        "temperature_2",
        lambda s: s.temperature_2,
        SensorDeviceClass.TEMPERATURE,
        UnitOfTemperature.CELSIUS,
        0,
    ),
    PowerPlantSensorDescription(
        # Unit of the DC offset reading is not documented, so none is given.
        key="dc_offset",
        translation_key="dc_offset",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda s: s.dc_offset,
    ),
    PowerPlantSensorDescription(
        key="voltage_setting",
        translation_key="voltage_setting",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda s: s.voltage_setting,
    ),
    PowerPlantSensorDescription(
        key="multiwave_strength",
        translation_key="multiwave_strength",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda s: s.multiwave_strength,
    ),
    # Free text rather than an enum: only "reg" and "sine" have been seen, and
    # an unknown value must not break the entity.
    PowerPlantSensorDescription(
        key="regulation_mode",
        translation_key="regulation_mode",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda s: s.regulation_mode,
    ),
    PowerPlantSensorDescription(
        key="waveform",
        translation_key="waveform",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda s: s.waveform,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PowerPlantConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the sensors."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(PowerPlantSensor(coordinator, d) for d in SENSORS)


class PowerPlantSensor(PowerPlantEntity, SensorEntity):
    """A value read from the status dump."""

    entity_description: PowerPlantSensorDescription

    def __init__(
        self, coordinator: PowerPlantCoordinator, description: PowerPlantSensorDescription
    ) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> float | int | str | None:
        return self.entity_description.value_fn(self.coordinator.data)
