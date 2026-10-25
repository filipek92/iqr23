"""Binary sensors of the iQ R23 integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import DIGITAL_OUTPUTS, DigitalOutput
from .coordinator import IQR23ConfigEntry, IQR23Coordinator
from .entity import IQR23Entity, async_module_descriptions
from .modules import Module

PARALLEL_UPDATES = 0


def _is_one(value: str) -> bool:
    return value == "1"


def _is_fault(value: str) -> bool:
    """Protection inputs: '1' is OK, '4' means the input is disabled in the controller."""
    return value not in ("1", "4")


def _pump_running(value: str) -> bool:
    """Pump status icons use '3' for a running pump."""
    return value == "3"


@dataclass(frozen=True, kw_only=True)
class IQR23BinarySensorEntityDescription(BinarySensorEntityDescription):
    """Binary sensor read from a single raw controller value."""

    raw_key: str
    module: Module | None = None
    is_on_fn: Callable[[str], bool] = _is_one


BINARY_SENSORS: tuple[IQR23BinarySensorEntityDescription, ...] = (
    IQR23BinarySensorEntityDescription(
        key="tank_upper_heating",
        module=Module.TANK,
        raw_key="_ico101",
        translation_key="tank_upper_heating",
        device_class=BinarySensorDeviceClass.HEAT,
    ),
    IQR23BinarySensorEntityDescription(
        key="tank_lower_heating",
        module=Module.TANK,
        raw_key="_ico102",
        translation_key="tank_lower_heating",
        device_class=BinarySensorDeviceClass.HEAT,
    ),
    IQR23BinarySensorEntityDescription(
        key="safety_thermostat",
        raw_key="col201",
        translation_key="safety_thermostat",
        device_class=BinarySensorDeviceClass.PROBLEM,
        is_on_fn=_is_fault,
    ),
    IQR23BinarySensorEntityDescription(
        key="system_pressure",
        raw_key="col202",
        translation_key="system_pressure",
        device_class=BinarySensorDeviceClass.PROBLEM,
        is_on_fn=_is_fault,
    ),
    IQR23BinarySensorEntityDescription(
        key="tank_upper_overcurrent",
        module=Module.TANK,
        raw_key="col204",
        translation_key="tank_upper_overcurrent",
        device_class=BinarySensorDeviceClass.PROBLEM,
        is_on_fn=_is_fault,
    ),
    IQR23BinarySensorEntityDescription(
        key="tank_lower_overcurrent",
        module=Module.TANK,
        raw_key="col205",
        translation_key="tank_lower_overcurrent",
        device_class=BinarySensorDeviceClass.PROBLEM,
        is_on_fn=_is_fault,
    ),
    IQR23BinarySensorEntityDescription(
        key="circuit_1_demand",
        module=Module.CIRCUIT_1,
        raw_key="col206",
        translation_key="circuit_1_demand",
        device_class=BinarySensorDeviceClass.HEAT,
    ),
    IQR23BinarySensorEntityDescription(
        key="circuit_1_setback",
        module=Module.CIRCUIT_1,
        raw_key="col115",
        translation_key="circuit_1_setback",
    ),
    IQR23BinarySensorEntityDescription(
        key="circuit_1_pump",
        module=Module.CIRCUIT_1,
        raw_key="_ico107",
        translation_key="circuit_1_pump",
        device_class=BinarySensorDeviceClass.RUNNING,
        is_on_fn=_pump_running,
    ),
    IQR23BinarySensorEntityDescription(
        key="circuit_2_demand",
        module=Module.CIRCUIT_2,
        raw_key="col207",
        translation_key="circuit_2_demand",
        device_class=BinarySensorDeviceClass.HEAT,
    ),
    IQR23BinarySensorEntityDescription(
        key="circuit_2_setback",
        module=Module.CIRCUIT_2,
        raw_key="col116",
        translation_key="circuit_2_setback",
    ),
    IQR23BinarySensorEntityDescription(
        key="circuit_2_pump",
        module=Module.CIRCUIT_2,
        raw_key="_ico108",
        translation_key="circuit_2_pump",
        device_class=BinarySensorDeviceClass.RUNNING,
        is_on_fn=_pump_running,
    ),
    IQR23BinarySensorEntityDescription(
        key="fireplace_pump",
        module=Module.FIREPLACE,
        raw_key="_ico104",
        translation_key="fireplace_pump",
        device_class=BinarySensorDeviceClass.RUNNING,
        is_on_fn=_pump_running,
    ),
    IQR23BinarySensorEntityDescription(
        key="hot_water_circulation",
        module=Module.TANK,
        raw_key="col106",
        translation_key="hot_water_circulation",
        device_class=BinarySensorDeviceClass.RUNNING,
    ),
    IQR23BinarySensorEntityDescription(
        key="low_tariff",
        raw_key="col203",
        translation_key="low_tariff",
    ),
    IQR23BinarySensorEntityDescription(
        key="ups",
        raw_key="col211",
        translation_key="ups",
    ),
    IQR23BinarySensorEntityDescription(
        key="pool_pump",
        module=Module.POOL,
        raw_key="col213",
        translation_key="pool_pump",
        device_class=BinarySensorDeviceClass.RUNNING,
    ),
    IQR23BinarySensorEntityDescription(
        key="pool_tank_ready",
        module=Module.POOL,
        raw_key="col292",
        translation_key="pool_tank_ready",
    ),
    IQR23BinarySensorEntityDescription(
        key="pool_solar_ready",
        module=Module.POOL,
        raw_key="col293",
        translation_key="pool_solar_ready",
    ),
    IQR23BinarySensorEntityDescription(
        key="pool_error",
        module=Module.POOL,
        raw_key="col294",
        translation_key="pool_error",
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
)

# Digital input states as shown on the controller's input page, in fixed strides of 5.
DIGITAL_INPUTS: tuple[IQR23BinarySensorEntityDescription, ...] = tuple(
    IQR23BinarySensorEntityDescription(
        key=f"digital_input_{key}",
        raw_key=f"col{col}",
        translation_key="digital_input",
        translation_placeholders={"input": label},
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    )
    for key, label, col in (
        ("t95", "T95", 300),
        ("pressure", "Tlak", 305),
        ("low_tariff", "NT", 310),
        ("np1", "NP1", 315),
        ("np2", "NP2", 320),
        ("to1", "TO1", 325),
        ("to2", "TO2", 330),
        ("def", "DEF", 335),
        ("ups", "UPS", 340),
        ("tc", "T/C", 345),
        ("pru", "PRU", 350),
        ("tf1", "TF1", 355),
        ("tf2", "TF2", 360),
        ("tf3", "TF3", 365),
        ("plo", "PLo", 375),
        ("phi", "PHi", 380),
        ("tto", "TTo", 385),
        ("tch", "TCh", 390),
        ("as1", "AS1", 395),
    )
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: IQR23ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    entities: list[BinarySensorEntity] = [
        IQR23BinarySensor(coordinator, description)
        for description in async_module_descriptions(
            hass, entry, Platform.BINARY_SENSOR, (*BINARY_SENSORS, *DIGITAL_INPUTS)
        )
        if description.raw_key in coordinator.data
    ]
    entities.extend(
        IQR23OutputBinarySensor(coordinator, output)
        for output in DIGITAL_OUTPUTS.values()
        if output.state_key in coordinator.data
    )
    async_add_entities(entities)


class IQR23BinarySensor(IQR23Entity, BinarySensorEntity):
    """Binary state of the controller."""

    entity_description: IQR23BinarySensorEntityDescription

    def __init__(
        self, coordinator: IQR23Coordinator, description: IQR23BinarySensorEntityDescription
    ) -> None:
        super().__init__(coordinator, description, description.raw_key)

    @property
    def is_on(self) -> bool | None:
        if (value := self.raw_value) is None:
            return None
        return self.entity_description.is_on_fn(value)


class IQR23OutputBinarySensor(IQR23Entity, BinarySensorEntity):
    """Actual relay state of a digital output."""

    _attr_device_class = BinarySensorDeviceClass.RUNNING

    def __init__(self, coordinator: IQR23Coordinator, output: DigitalOutput) -> None:
        description = BinarySensorEntityDescription(
            key=f"output_{output.key}",
            translation_key="output_running",
            translation_placeholders={"output": output.name},
        )
        super().__init__(coordinator, description, output.state_key)

    @property
    def is_on(self) -> bool | None:
        if (value := self.raw_value) is None:
            return None
        return value == "1"
