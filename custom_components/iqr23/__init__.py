"""A Home Assistant integration for communication with IQ R23 heating controller."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS, MANUFACTURER, MODEL

from .iqr23 import IQR23

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass, config):
    hass.data.setdefault(DOMAIN, {})
    # we don't support YAML configuration, therefore just return True
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    hass.data.setdefault(DOMAIN, {})

    _LOGGER.info(f"Setup of IQR23 platform {entry.data}")

    api = IQR23(entry.data["host"])

    # Store version info for device_info
    device_info = {
        "identifiers": {(DOMAIN, entry.data["host"])},
        "name": "iQ R23",
        "manufacturer": MANUFACTURER,
        "model": MODEL,
        "sw_version": entry.data.get("version", "unknown"),
    }

    hass.data[DOMAIN] = {
        "api": api,
        "device_info": device_info,
    }
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _LOGGER.info(f"Setup of IQR23 platform {entry.data} done")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data.pop(DOMAIN)
    return unload_ok
