import asyncio
import logging
from datetime import timedelta

import aiohttp
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN
from .iqr23 import IQR23, DIGITAL_OUTPUTS, HardwareDigitalOutput

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    api = hass.data[DOMAIN]["api"]

    new_entities = []

    for uid, output_info in DIGITAL_OUTPUTS.items():
        new_entities.append(IQR23Switch(api, uid, output_info))

    if new_entities:
        async_add_entities(new_entities, update_before_add=True)

class IQR23Switch(SwitchEntity):

    def __init__(self, api: IQR23, uid: str, info: HardwareDigitalOutput):
        super().__init__()
        self._api = api
        self._uid = uid
        self._info = info
        self._attr_available = False

    async def async_update(self) -> None:
        try:
            self._attr_is_on = await self._api.getDigitalOutputState(self._uid)
            #self._attr_extra_state_attributes = res["info"]
            self._attr_available = (await self._api.getDigitalOutputMode(self._uid)) in ["on", "off"]
        except (asyncio.TimeoutError, aiohttp.ClientError, KeyError):
            self._attr_available = False

    @property
    def name(self):
        return f"iqr23_{self._uid}"  # TODO translate?

    @property
    def unique_id(self):
        return f"iqr23_{self._uid}"

    @property
    def device_info(self):
        # https://developers.home-assistant.io/docs/device_registry_index/#device-properties
        return {
            "identifiers": {(DOMAIN, "")},
            "name": "iQ R23",
        }

    async def async_turn_on(self, **kwargs):
        """Instruct the light to turn on."""
        _LOGGER.warning(f"Tunrning on {self._uid}, {kwargs}")
        await self._api.setDigitalOutputMode(self._uid, "on")
        self._attr_is_on = True


    async def async_turn_off(self, **kwargs):
        """Instruct the light to turn off."""
        _LOGGER.warning(f"Tunrning off {self._uid}, {kwargs}")
        await self._api.setDigitalOutputMode(self._uid, "off")
        self._attr_is_on = False

    # @property
    # def device_class(self):
    #     return self._sensor_info.homeassistant_class

    # @property
    # def icon(self):
    #     return self._sensor_info.homeassistant_icon