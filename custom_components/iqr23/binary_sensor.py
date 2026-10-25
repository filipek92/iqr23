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


# Keys are kept from 1.x so that existing entities keep their unique IDs.
BINARY_SENSORS: tuple[IQR23BinarySensorEntityDescription, ...] = (
    IQR23BinarySensorEntityDescription(
        key="watertankUpperHeating",
        module=Module.TANK,
        raw_key="_ico101",
        translation_key="tank_upper_heating",
        device_class=BinarySensorDeviceClass.HEAT,
    ),
    IQR23BinarySensorEntityDescription(
        key="watertankLowerHeating",
        module=Module.TANK,
        raw_key="_ico102",
        translation_key="tank_lower_heating",
        device_class=BinarySensorDeviceClass.HEAT,
    ),
    IQR23BinarySensorEntityDescription(
        key="watertankSafetySensor",
        raw_key="col201",
        translation_key="safety_thermostat",
        device_class=BinarySensorDeviceClass.PROBLEM,
        is_on_fn=_is_fault,
    ),
    IQR23BinarySensorEntityDescription(
        key="watertankPressure",
        raw_key="col202",
        translation_key="pressure",
        device_class=BinarySensorDeviceClass.PROBLEM,
        is_on_fn=_is_fault,
    ),
    IQR23BinarySensorEntityDescription(
        key="watertankUpperOvercurrent",
        module=Module.TANK,
        raw_key="col204",
        translation_key="overcurrent_sp1",
        device_class=BinarySensorDeviceClass.PROBLEM,
        is_on_fn=_is_fault,
    ),
    IQR23BinarySensorEntityDescription(
        key="watertankLowerOvercurrent",
        module=Module.TANK,
        raw_key="col205",
        translation_key="overcurrent_sp2",
        device_class=BinarySensorDeviceClass.PROBLEM,
        is_on_fn=_is_fault,
    ),
    IQR23BinarySensorEntityDescription(
        key="lowerFloorActive",
        module=Module.CIRCUIT_1,
        raw_key="col206",
        translation_key="floor_lower_demand",
        device_class=BinarySensorDeviceClass.HEAT,
    ),
    IQR23BinarySensorEntityDescription(
        key="lowerFloorLimiting",
        module=Module.CIRCUIT_1,
        raw_key="col115",
        translation_key="floor_lower_setback",
    ),
    IQR23BinarySensorEntityDescription(
        key="lowerFloorCirculation",
        module=Module.CIRCUIT_1,
        raw_key="_ico107",
        translation_key="floor_lower_pump",
        device_class=BinarySensorDeviceClass.RUNNING,
        is_on_fn=_pump_running,
    ),
    IQR23BinarySensorEntityDescription(
        key="upperFloorActive",
        module=Module.CIRCUIT_2,
        raw_key="col207",
        translation_key="floor_upper_demand",
        device_class=BinarySensorDeviceClass.HEAT,
    ),
    IQR23BinarySensorEntityDescription(
        key="upperFloorLimiting",
        module=Module.CIRCUIT_2,
        raw_key="col116",
        translation_key="floor_upper_setback",
    ),
    IQR23BinarySensorEntityDescription(
        key="upperFloorCirculation",
        module=Module.CIRCUIT_2,
        raw_key="_ico108",
        translation_key="floor_upper_pump",
        device_class=BinarySensorDeviceClass.RUNNING,
        is_on_fn=_pump_running,
    ),
    IQR23BinarySensorEntityDescription(
        key="fireplaceCirculation",
        module=Module.FIREPLACE,
        raw_key="_ico104",
        translation_key="fireplace_pump",
        device_class=BinarySensorDeviceClass.RUNNING,
        is_on_fn=_pump_running,
    ),
    IQR23BinarySensorEntityDescription(
        key="waterCirculation",
        module=Module.TANK,
        raw_key="col106",
        translation_key="hot_water_circulation",
        device_class=BinarySensorDeviceClass.RUNNING,
    ),
    IQR23BinarySensorEntityDescription(
        key="lowTariff",
        raw_key="col203",
        translation_key="low_tariff",
    ),
    IQR23BinarySensorEntityDescription(
        key="UPS",
        raw_key="col211",
        translation_key="ups",
    ),
    IQR23BinarySensorEntityDescription(
        key="poolFiltrationCirculation",
        module=Module.POOL,
        raw_key="col213",
        translation_key="pool_pump",
        device_class=BinarySensorDeviceClass.RUNNING,
    ),
    IQR23BinarySensorEntityDescription(
        key="poolAzTemperatureReady",
        module=Module.POOL,
        raw_key="col292",
        translation_key="pool_tank_ready",
    ),
    IQR23BinarySensorEntityDescription(
        key="poolSolarTemperatureReady",
        module=Module.POOL,
        raw_key="col293",
        translation_key="pool_solar_ready",
    ),
    IQR23BinarySensorEntityDescription(
        key="poolError",
        module=Module.POOL,
        raw_key="col294",
        translation_key="pool_error",
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
)

# Digital input states as shown on the controller's input page, in fixed strides of 5.
DIGITAL_INPUTS: tuple[IQR23BinarySensorEntityDescription, ...] = tuple(
    IQR23BinarySensorEntityDescription(
        key=f"digitalInput{key}",
        raw_key=f"col{col}",
        translation_key="digital_input",
        translation_placeholders={"input": label},
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    )
    for key, label, col in (
        ("T95", "T95", 300),
        ("Pressure", "Tlak", 305),
        ("LowTariff", "NT", 310),
        ("NP1", "NP1", 315),
        ("NP2", "NP2", 320),
        ("TO1", "TO1", 325),
        ("TO2", "TO2", 330),
        ("DEF", "DEF", 335),
        ("UPS", "UPS", 340),
        ("TC", "T/C", 345),
        ("PRU", "PRU", 350),
        ("TF1", "TF1", 355),
        ("TF2", "TF2", 360),
        ("TF3", "TF3", 365),
        ("PLo", "PLo", 375),
        ("PHi", "PHi", 380),
        ("TTo", "TTo", 385),
        ("TCh", "TCh", 390),
        ("AS1", "AS1", 395),
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
            key=f"{output.key}_running",
            translation_key="output_running",
            translation_placeholders={"output": output.key},
        )
        super().__init__(coordinator, description, output.state_key)

    @property
    def is_on(self) -> bool | None:
        if (value := self.raw_value) is None:
            return None
        return value == "1"
