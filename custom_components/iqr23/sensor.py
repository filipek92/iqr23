"""Sensors of the iQ R23 integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, Platform, UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import parse_counter_hours, parse_percent, parse_temperature
from .coordinator import IQR23ConfigEntry, IQR23Coordinator
from .entity import IQR23Entity, async_module_descriptions
from .modules import Module

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class IQR23SensorEntityDescription(SensorEntityDescription):
    """Sensor read from a single raw controller value."""

    raw_key: str
    module: Module | None = None
    value_fn: Callable[[str], float | int | None] = parse_temperature


def _temperature(
    key: str, raw_key: str, module: Module | None = None
) -> IQR23SensorEntityDescription:
    return IQR23SensorEntityDescription(
        key=key,
        raw_key=raw_key,
        translation_key=key,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        module=module,
    )


def _heating_time(key: str, raw_key: str, module: Module) -> IQR23SensorEntityDescription:
    return IQR23SensorEntityDescription(
        key=key,
        raw_key=raw_key,
        translation_key=key,
        module=module,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfTime.HOURS,
        value_fn=parse_counter_hours,
    )


def _mixing(key: str, raw_key: str, module: Module) -> IQR23SensorEntityDescription:
    return IQR23SensorEntityDescription(
        key=key,
        raw_key=raw_key,
        translation_key=key,
        module=module,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=parse_percent,
    )


SENSORS: tuple[IQR23SensorEntityDescription, ...] = (
    _temperature("outdoor_temperature", "txt113"),
    _temperature("outdoor_temperature_min", "txt714"),
    _temperature("outdoor_temperature_max", "txt715"),
    _temperature("outdoor_temperature_mean", "txt713"),
    _temperature("tank_upper", "txt101", Module.TANK),
    _temperature("tank_upper_target", "txt501", Module.TANK),
    _heating_time("tank_upper_heating_time", "txt740", Module.TANK),
    _temperature("tank_middle", "txt102", Module.TANK),
    _temperature("tank_lower", "txt106", Module.TANK),
    _temperature("tank_lower_target", "txt502", Module.TANK),
    _heating_time("tank_lower_heating_time", "txt741", Module.TANK),
    _temperature("circuit_1", "txt111", Module.CIRCUIT_1),
    _temperature("circuit_1_target", "txt520", Module.CIRCUIT_1),
    _mixing("circuit_1_mixing", "txt521", Module.CIRCUIT_1),
    _temperature("circuit_2", "txt112", Module.CIRCUIT_2),
    _temperature("circuit_2_target", "txt526", Module.CIRCUIT_2),
    _mixing("circuit_2_mixing", "txt527", Module.CIRCUIT_2),
    _temperature("fireplace", "txt104", Module.FIREPLACE),
    _temperature("solar", "txt105", Module.SOLAR),
    _temperature("cooling", "txt109", Module.COOLING),
    _temperature("pool_filtration", "txt107", Module.POOL),
    _temperature("pool_exchanger", "txt108", Module.POOL),
    _temperature("pool_min", "txt730", Module.POOL),
    _temperature("pool_max", "txt731", Module.POOL),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: IQR23ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        IQR23Sensor(coordinator, description)
        for description in async_module_descriptions(hass, entry, Platform.SENSOR, SENSORS)
        if description.raw_key in coordinator.data
    )


class IQR23Sensor(IQR23Entity, SensorEntity):
    """Numeric value of the controller."""

    entity_description: IQR23SensorEntityDescription

    def __init__(
        self, coordinator: IQR23Coordinator, description: IQR23SensorEntityDescription
    ) -> None:
        super().__init__(coordinator, description, description.raw_key)

    @property
    def native_value(self) -> float | int | None:
        if (value := self.raw_value) is None:
            return None
        try:
            return self.entity_description.value_fn(value)
        except ValueError:
            return None
