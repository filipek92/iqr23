"""Setpoint numbers of the iQ R23 integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.const import PERCENTAGE, EntityCategory, Platform, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import SETPOINTS, IQR23Error, Setpoint
from .const import DOMAIN
from .coordinator import IQR23ConfigEntry, IQR23Coordinator
from .entity import IQR23Entity, async_module_descriptions
from .modules import Module

# The controller handles a single login at a time.
PARALLEL_UPDATES = 1


@dataclass(frozen=True, kw_only=True)
class IQR23NumberEntityDescription(NumberEntityDescription):
    """Setpoint changed by pressing the controller's -/+ buttons."""

    setpoint: Setpoint
    module: Module


# Setpoints adjusted in everyday use; the rest are tuned once when commissioning the system.
CONTROLS = {"tank_base", "circuit_1_shift", "circuit_2_shift", "pool_on", "pool_off"}


def _number(
    key: str,
    module: Module,
    unit: str | None = UnitOfTemperature.CELSIUS,
    device_class: NumberDeviceClass | None = None,
) -> IQR23NumberEntityDescription:
    setpoint = SETPOINTS[key]
    return IQR23NumberEntityDescription(
        key=key,
        translation_key=key,
        setpoint=setpoint,
        module=module,
        native_min_value=setpoint.min_value,
        native_max_value=setpoint.max_value,
        native_step=setpoint.step,
        native_unit_of_measurement=unit,
        device_class=device_class,
        entity_category=None if key in CONTROLS else EntityCategory.CONFIG,
        mode=NumberMode.BOX,
    )


def _temperature(key: str, module: Module) -> IQR23NumberEntityDescription:
    return _number(key, module, device_class=NumberDeviceClass.TEMPERATURE)


NUMBERS: tuple[IQR23NumberEntityDescription, ...] = (
    _temperature("tank_base", Module.TANK),
    _temperature("tank_upper_spring", Module.TANK),
    _temperature("tank_upper_summer", Module.TANK),
    _temperature("tank_upper_autumn", Module.TANK),
    _temperature("tank_upper_winter", Module.TANK),
    _temperature("tank_lower_spring", Module.TANK),
    _temperature("tank_lower_summer", Module.TANK),
    _temperature("tank_lower_autumn", Module.TANK),
    _temperature("tank_lower_winter", Module.TANK),
    _number("circuit_1_curve", Module.CIRCUIT_1, unit=None),
    _number("circuit_1_setback", Module.CIRCUIT_1, unit=PERCENTAGE),
    # Shifts and differences are temperature deltas, which must not be unit-converted.
    _number("circuit_1_shift", Module.CIRCUIT_1),
    _temperature("circuit_1_min", Module.CIRCUIT_1),
    _temperature("circuit_1_max", Module.CIRCUIT_1),
    _number("circuit_2_curve", Module.CIRCUIT_2, unit=None),
    _number("circuit_2_setback", Module.CIRCUIT_2, unit=PERCENTAGE),
    _number("circuit_2_shift", Module.CIRCUIT_2),
    _temperature("circuit_2_min", Module.CIRCUIT_2),
    _temperature("circuit_2_max", Module.CIRCUIT_2),
    _temperature("fireplace_start", Module.FIREPLACE),
    _number("fireplace_hysteresis", Module.FIREPLACE),
    _number("solar_difference", Module.SOLAR),
    _temperature("pool_on", Module.POOL),
    _temperature("pool_off", Module.POOL),
    _temperature("cooling_on", Module.COOLING),
    _temperature("cooling_off", Module.COOLING),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: IQR23ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        IQR23Number(coordinator, description)
        for description in async_module_descriptions(hass, entry, Platform.NUMBER, NUMBERS)
        if description.setpoint.value_key in coordinator.data
    )


class IQR23Number(IQR23Entity, NumberEntity):
    """Setpoint of the controller."""

    entity_description: IQR23NumberEntityDescription

    def __init__(
        self, coordinator: IQR23Coordinator, description: IQR23NumberEntityDescription
    ) -> None:
        super().__init__(coordinator, description, description.setpoint.value_key)

    @property
    def native_value(self) -> int | None:
        if (value := self.raw_value) is None:
            return None
        try:
            return int(value)
        except ValueError:
            return None

    async def async_set_native_value(self, value: float) -> None:
        try:
            await self.coordinator.client.async_set_setpoint(
                self.entity_description.key, int(value)
            )
        except IQR23Error as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="set_setpoint_failed",
                translation_placeholders={"error": str(err)},
            ) from err
        finally:
            await self.coordinator.async_request_refresh()
