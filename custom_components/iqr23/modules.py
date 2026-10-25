"""Optional modules of the universal iQ R23 controller."""

from __future__ import annotations

from enum import StrEnum

from homeassistant.config_entries import ConfigEntry

from .api import parse_temperature
from .const import CONF_MODULES


class Module(StrEnum):
    """Hydraulic module the controller may be configured with."""

    TANK = "tank"
    CIRCUIT_1 = "circuit_1"
    CIRCUIT_2 = "circuit_2"
    FIREPLACE = "fireplace"
    SOLAR = "solar"
    COOLING = "cooling"
    POOL = "pool"


# The controller lists every module it supports, so presence is judged by connected sensors.
MODULE_PROBES: dict[Module, tuple[str, ...]] = {
    Module.TANK: ("txt101", "txt102", "txt106"),
    Module.CIRCUIT_1: ("txt111",),
    Module.CIRCUIT_2: ("txt112",),
    Module.FIREPLACE: ("txt104",),
    Module.SOLAR: ("txt105",),
    Module.COOLING: ("txt109",),
    Module.POOL: ("txt107", "txt108"),
}


def detect_modules(data: dict[str, str]) -> list[str]:
    """Return modules having at least one connected temperature sensor."""
    return [
        module.value
        for module, keys in MODULE_PROBES.items()
        if any(data.get(key) and parse_temperature(data[key]) is not None for key in keys)
    ]


def enabled_modules(entry: ConfigEntry) -> set[Module]:
    return {Module(module) for module in entry.options.get(CONF_MODULES, list(Module))}
