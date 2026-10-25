"""Output mode selects of the iQ R23 integration."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import DIGITAL_OUTPUTS, DigitalOutput, IQR23Error, OutputMode, get_output_mode
from .const import DOMAIN
from .coordinator import IQR23ConfigEntry, IQR23Coordinator
from .entity import IQR23Entity

# The controller handles a single login at a time.
PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: IQR23ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        IQR23OutputModeSelect(coordinator, output)
        for output in DIGITAL_OUTPUTS.values()
        if output.state_key in coordinator.data
    )


class IQR23OutputModeSelect(IQR23Entity, SelectEntity):
    """Operating mode (Auto / AutoR / On / Off) of a digital output."""

    _attr_options = [mode.value for mode in OutputMode]

    def __init__(self, coordinator: IQR23Coordinator, output: DigitalOutput) -> None:
        description = SelectEntityDescription(
            key=f"output_{output.key}_mode",
            translation_key="output_mode",
            translation_placeholders={"output": output.name},
        )
        super().__init__(coordinator, description, output.state_key)
        self._output = output

    @property
    def current_option(self) -> str | None:
        mode = get_output_mode(self.coordinator.data, self._output)
        return mode.value if mode else None

    async def async_select_option(self, option: str) -> None:
        try:
            await self.coordinator.client.async_set_output_mode(
                self._output.key, OutputMode(option)
            )
        except IQR23Error as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="set_mode_failed",
                translation_placeholders={"output": self._output.name, "error": str(err)},
            ) from err
        await self.coordinator.async_request_refresh()
