"""Diagnostics support for the iQ R23 integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from .const import CONF_MASTER_PASSWORD
from .coordinator import IQR23ConfigEntry

TO_REDACT = {CONF_MASTER_PASSWORD}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: IQR23ConfigEntry
) -> dict[str, Any]:
    coordinator = entry.runtime_data
    return {
        "entry": async_redact_data(dict(entry.data), TO_REDACT),
        "last_update_success": coordinator.last_update_success,
        "data": coordinator.data,
    }
