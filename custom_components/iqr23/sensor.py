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
    key: str, raw_key: str, translation_key: str, module: Module | None = None
) -> IQR23SensorEntityDescription:
    return IQR23SensorEntityDescription(
        key=key,
        raw_key=raw_key,
        translation_key=translation_key,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        module=module,
    )


def _heating_time(
    key: str, raw_key: str, translation_key: str, module: Module
) -> IQR23SensorEntityDescription:
    return IQR23SensorEntityDescription(
        key=key,
        raw_key=raw_key,
        translation_key=translation_key,
        module=module,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfTime.HOURS,
        value_fn=parse_counter_hours,
    )


def _mixing(
    key: str, raw_key: str, translation_key: str, module: Module
) -> IQR23SensorEntityDescription:
    return IQR23SensorEntityDescription(
        key=key,
        raw_key=raw_key,
        translation_key=translation_key,
        module=module,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=parse_percent,
    )


# Keys are kept from 1.x so that existing entities keep their unique IDs.
SENSORS: tuple[IQR23SensorEntityDescription, ...] = (
    _temperature("outdoorTemp", "txt113", "outdoor_temperature"),
    _temperature("outdoorTempMin", "txt714", "outdoor_temperature_min"),
    _temperature("outdoorTempMax", "txt715", "outdoor_temperature_max"),
    _temperature("outdoorTempMean", "txt713", "outdoor_temperature_mean"),
    _temperature("watertankUpper", "txt101", "tank_upper", Module.TANK),
    _temperature("watertankUpperRequest", "txt501", "tank_upper_target", Module.TANK),
    _heating_time("watertankUpperHeatingTime", "txt740", "tank_upper_heating_time", Module.TANK),
    _temperature("watertankMiddle", "txt102", "tank_middle", Module.TANK),
    _temperature("watertankLower", "txt106", "tank_lower", Module.TANK),
    _temperature("watertankLowerRequest", "txt502", "tank_lower_target", Module.TANK),
    _heating_time("watertankLowerHeatingTime", "txt741", "tank_lower_heating_time", Module.TANK),
    _temperature("lowerFloor", "txt111", "floor_lower", Module.CIRCUIT_1),
    _temperature("lowerFloorRequest", "txt520", "floor_lower_target", Module.CIRCUIT_1),
    _mixing("lowerFloorMixing", "txt521", "floor_lower_mixing", Module.CIRCUIT_1),
    _temperature("upperFloor", "txt112", "floor_upper", Module.CIRCUIT_2),
    _temperature("upperFloorRequest", "txt526", "floor_upper_target", Module.CIRCUIT_2),
    _mixing("upperFloorMixing", "txt527", "floor_upper_mixing", Module.CIRCUIT_2),
    _temperature("fireplace", "txt104", "fireplace", Module.FIREPLACE),
    _temperature("solarTemperature", "txt105", "solar", Module.SOLAR),
    _temperature("coolingTankTemperature", "txt109", "cooling", Module.COOLING),
    _temperature("poolTemperatureFilter", "txt107", "pool_filter", Module.POOL),
    _temperature("poolTemperatureExchanger", "txt108", "pool_exchanger", Module.POOL),
    _temperature("poolTemperatureMin", "txt730", "pool_min", Module.POOL),
    _temperature("poolTemperatureMax", "txt731", "pool_max", Module.POOL),
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
