"""Base entity for the iQ R23 integration."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_FIRMWARE_VERSION, DOMAIN, MANUFACTURER, MODEL
from .coordinator import IQR23ConfigEntry, IQR23Coordinator
from .modules import enabled_modules


@callback
def async_module_descriptions[DescriptionT: Any](
    hass: HomeAssistant,
    entry: IQR23ConfigEntry,
    platform: Platform,
    descriptions: Iterable[DescriptionT],
) -> list[DescriptionT]:
    """Return descriptions of enabled modules, removing entities of disabled ones."""
    modules = enabled_modules(entry)
    entity_registry = er.async_get(hass)
    enabled = []
    for description in descriptions:
        if description.module is None or description.module in modules:
            enabled.append(description)
        elif entity_id := entity_registry.async_get_entity_id(
            platform, DOMAIN, f"{entry.entry_id}_{description.key}"
        ):
            entity_registry.async_remove(entity_id)
    return enabled


class IQR23Entity(CoordinatorEntity[IQR23Coordinator]):
    """Entity backed by a single raw value of the controller data."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: IQR23Coordinator,
        description: EntityDescription,
        raw_key: str,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._raw_key = raw_key
        entry = coordinator.config_entry
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=MODEL,
            manufacturer=MANUFACTURER,
            model=MODEL,
            sw_version=entry.data.get(CONF_FIRMWARE_VERSION),
            configuration_url=coordinator.client.host,
        )

    @property
    def raw_value(self) -> str | None:
        """Raw string value from the controller."""
        return self.coordinator.data.get(self._raw_key)

    @property
    def available(self) -> bool:
        return super().available and self.raw_value is not None
