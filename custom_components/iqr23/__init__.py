"""Home Assistant integration for the iQ R23 heating controller."""

from __future__ import annotations

from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import IQR23Client
from .const import CONF_MASTER_PASSWORD, CONF_MODULES, DOMAIN, PLATFORMS
from .coordinator import IQR23ConfigEntry, IQR23Coordinator
from .migration import async_migrate_entry
from .modules import detect_modules

__all__ = ["async_migrate_entry"]


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


async def async_remove_config_entry_device(
    hass: HomeAssistant, entry: IQR23ConfigEntry, device: dr.DeviceEntry
) -> bool:
    """Allow removing devices that no longer belong to the controller."""
    return (DOMAIN, entry.entry_id) not in device.identifiers
