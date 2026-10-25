"""Config entry migrations of the iQ R23 integration."""

from __future__ import annotations

import logging

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import (
    device_registry as dr,
)
from homeassistant.helpers import (
    entity_registry as er,
)
from homeassistant.helpers import (
    issue_registry as ir,
)

from .api import DIGITAL_OUTPUTS
from .const import (
    CONF_FIRMWARE_VERSION,
    CONF_MASTER_PASSWORD,
    DEFAULT_MASTER_PASSWORD,
    DOMAIN,
)
from .coordinator import IQR23ConfigEntry

_LOGGER = logging.getLogger(__name__)

# 1.x exposed the SOL output state as a standalone binary sensor.
V1_RENAMED_KEYS = {"solarCirculation": "SOL_running"}

# Entity keys of 1.x and 2.0 mapped to the snake_case keys introduced in 2.1.
V2_0_RENAMED_KEYS = {
    # Sensors
    "outdoorTemp": "outdoor_temperature",
    "outdoorTempMin": "outdoor_temperature_min",
    "outdoorTempMax": "outdoor_temperature_max",
    "outdoorTempMean": "outdoor_temperature_mean",
    "watertankUpper": "tank_upper",
    "watertankUpperRequest": "tank_upper_target",
    "watertankUpperHeatingTime": "tank_upper_heating_time",
    "watertankMiddle": "tank_middle",
    "watertankLower": "tank_lower",
    "watertankLowerRequest": "tank_lower_target",
    "watertankLowerHeatingTime": "tank_lower_heating_time",
    "lowerFloor": "circuit_1",
    "lowerFloorRequest": "circuit_1_target",
    "lowerFloorMixing": "circuit_1_mixing",
    "upperFloor": "circuit_2",
    "upperFloorRequest": "circuit_2_target",
    "upperFloorMixing": "circuit_2_mixing",
    "solarTemperature": "solar",
    "coolingTankTemperature": "cooling",
    "poolTemperatureFilter": "pool_filtration",
    "poolTemperatureExchanger": "pool_exchanger",
    "poolTemperatureMin": "pool_min",
    "poolTemperatureMax": "pool_max",
    # Binary sensors
    "watertankUpperHeating": "tank_upper_heating",
    "watertankLowerHeating": "tank_lower_heating",
    "watertankSafetySensor": "safety_thermostat",
    "watertankPressure": "system_pressure",
    "watertankUpperOvercurrent": "tank_upper_overcurrent",
    "watertankLowerOvercurrent": "tank_lower_overcurrent",
    "lowerFloorActive": "circuit_1_demand",
    "lowerFloorLimiting": "circuit_1_setback",
    "lowerFloorCirculation": "circuit_1_pump",
    "upperFloorActive": "circuit_2_demand",
    "upperFloorLimiting": "circuit_2_setback",
    "upperFloorCirculation": "circuit_2_pump",
    "fireplaceCirculation": "fireplace_pump",
    "waterCirculation": "hot_water_circulation",
    "lowTariff": "low_tariff",
    "UPS": "ups",
    "poolFiltrationCirculation": "pool_pump",
    "poolAzTemperatureReady": "pool_tank_ready",
    "poolSolarTemperatureReady": "pool_solar_ready",
    "poolError": "pool_error",
    # Digital inputs
    **{
        f"digitalInput{old}": f"digital_input_{new}"
        for old, new in (
            ("T95", "t95"),
            ("Pressure", "pressure"),
            ("LowTariff", "low_tariff"),
            ("NP1", "np1"),
            ("NP2", "np2"),
            ("TO1", "to1"),
            ("TO2", "to2"),
            ("DEF", "def"),
            ("UPS", "ups"),
            ("TC", "tc"),
            ("PRU", "pru"),
            ("TF1", "tf1"),
            ("TF2", "tf2"),
            ("TF3", "tf3"),
            ("PLo", "plo"),
            ("PHi", "phi"),
            ("TTo", "tto"),
            ("TCh", "tch"),
            ("AS1", "as1"),
        )
    },
    # Digital outputs
    **{
        f"{output.name}_{suffix}": key
        for output in DIGITAL_OUTPUTS.values()
        for suffix, key in (
            ("running", f"output_{output.key}"),
            ("mode", f"output_{output.key}_mode"),
        )
    },
}


async def async_migrate_entry(hass: HomeAssistant, entry: IQR23ConfigEntry) -> bool:
    """Migrate entries of older releases; entity IDs, names and history are kept."""
    if entry.version > 2:
        return False

    if entry.version == 1:
        await _async_migrate_v1(hass, entry)
        hass.config_entries.async_update_entry(
            entry,
            data={CONF_MASTER_PASSWORD: DEFAULT_MASTER_PASSWORD, **entry.data},
            version=2,
            minor_version=1,
        )

    if entry.minor_version < 2:
        await _async_rename_keys(hass, entry, V2_0_RENAMED_KEYS)
        data = dict(entry.data)
        # 2.0 stored the firmware version under the ambiguous "version" key.
        if (firmware_version := data.pop("version", None)) is not None:
            data[CONF_FIRMWARE_VERSION] = firmware_version
        hass.config_entries.async_update_entry(entry, data=data, minor_version=2)

    _LOGGER.info(
        "Migrated iQ R23 entry %s to version %s.%s",
        entry.entry_id,
        entry.version,
        entry.minor_version,
    )
    return True


async def _async_migrate_v1(hass: HomeAssistant, entry: IQR23ConfigEntry) -> None:
    """Scope unique IDs per entry and replace switches by selects."""
    entity_registry = er.async_get(hass)
    removed_switches: list[str] = []
    for entity in er.async_entries_for_config_entry(entity_registry, entry.entry_id):
        if entity.domain == Platform.SWITCH:
            removed_switches.append(entity.entity_id)
            entity_registry.async_remove(entity.entity_id)

    @callback
    def _migrate_unique_id(entity: er.RegistryEntry) -> dict[str, str] | None:
        if entity.unique_id.startswith(f"{entry.entry_id}_"):
            return None
        # Releases before 1.1.2 created binary sensors without the domain prefix.
        key = entity.unique_id.removeprefix(f"{DOMAIN}_")
        key = V1_RENAMED_KEYS.get(key, key)
        return {"new_unique_id": f"{entry.entry_id}_{key}"}

    await er.async_migrate_entries(hass, entry.entry_id, _migrate_unique_id)

    # 1.x identified the device by its host URL (or an empty string in old releases).
    device_registry = dr.async_get(hass)
    for device in dr.async_entries_for_config_entry(device_registry, entry.entry_id):
        if any(domain == DOMAIN for domain, _ in device.identifiers):
            device_registry.async_update_device(
                device.id, new_identifiers={(DOMAIN, entry.entry_id)}
            )

    if removed_switches:
        ir.async_create_issue(
            hass,
            DOMAIN,
            "switches_removed",
            is_fixable=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key="switches_removed",
            translation_placeholders={"entities": ", ".join(removed_switches)},
        )


async def _async_rename_keys(
    hass: HomeAssistant, entry: IQR23ConfigEntry, renamed_keys: dict[str, str]
) -> None:
    """Rename entity keys in unique IDs of the entry."""
    prefix = f"{entry.entry_id}_"

    @callback
    def _migrate_unique_id(entity: er.RegistryEntry) -> dict[str, str] | None:
        key = entity.unique_id.removeprefix(prefix)
        if (new_key := renamed_keys.get(key)) is None:
            return None
        return {"new_unique_id": f"{prefix}{new_key}"}

    await er.async_migrate_entries(hass, entry.entry_id, _migrate_unique_id)
