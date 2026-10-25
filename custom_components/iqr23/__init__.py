"""Home Assistant integration for the iQ R23 heating controller."""

from __future__ import annotations

import logging

from homeassistant.const import CONF_HOST, Platform
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
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import IQR23Client
from .const import (
    CONF_MASTER_PASSWORD,
    CONF_MODULES,
    DEFAULT_MASTER_PASSWORD,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import IQR23ConfigEntry, IQR23Coordinator
from .modules import detect_modules

_LOGGER = logging.getLogger(__name__)

# 1.x exposed the SOL output state as a standalone binary sensor.
LEGACY_RENAMED_KEYS = {"solarCirculation": "SOL_running"}


async def async_setup_entry(hass: HomeAssistant, entry: IQR23ConfigEntry) -> bool:
    client = IQR23Client(
        async_get_clientsession(hass),
        entry.data[CONF_HOST],
        entry.data[CONF_MASTER_PASSWORD],
    )
    coordinator = IQR23Coordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    if CONF_MODULES not in entry.options:
        # Entries migrated from 1.x: pick modules by connected sensors.
        hass.config_entries.async_update_entry(
            entry,
            options={**entry.options, CONF_MODULES: detect_modules(coordinator.data)},
        )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(hass: HomeAssistant, entry: IQR23ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: IQR23ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_migrate_entry(hass: HomeAssistant, entry: IQR23ConfigEntry) -> bool:
    """Migrate 1.x entries: scope unique IDs per entry and replace switches by selects."""
    if entry.version > 2:
        return False

    if entry.version == 1:
        entity_registry = er.async_get(hass)
        removed_switches: list[str] = []
        for entity in er.async_entries_for_config_entry(entity_registry, entry.entry_id):
            if entity.domain == Platform.SWITCH:
                removed_switches.append(entity.entity_id)
                entity_registry.async_remove(entity.entity_id)

        @callback
        def _migrate_unique_id(entity: er.RegistryEntry) -> dict[str, str] | None:
            if not entity.unique_id.startswith(f"{DOMAIN}_"):
                return None
            key = entity.unique_id.removeprefix(f"{DOMAIN}_")
            key = LEGACY_RENAMED_KEYS.get(key, key)
            return {"new_unique_id": f"{entry.entry_id}_{key}"}

        await er.async_migrate_entries(hass, entry.entry_id, _migrate_unique_id)

        # 1.x identified the device by its host URL.
        device_registry = dr.async_get(hass)
        if device := device_registry.async_get_device(
            identifiers={(DOMAIN, entry.data[CONF_HOST])}
        ):
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

        hass.config_entries.async_update_entry(
            entry,
            data={CONF_MASTER_PASSWORD: DEFAULT_MASTER_PASSWORD, **entry.data},
            version=2,
        )
        _LOGGER.info("Migrated iQ R23 entry %s to version 2", entry.entry_id)

    return True
