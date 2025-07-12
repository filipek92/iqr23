import asyncio
import logging
from datetime import timedelta

import aiohttp
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN
from .iqr23 import IQR23, SENSORS, Sensor

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    api = hass.data[DOMAIN]["api"]

    new_entities = []
    for uid, sensor_info in SENSORS.items():
        if sensor_info.type == bool:
            continue
        new_entities.append(IQR23Sensor(api, uid, sensor_info))

    if new_entities:
        async_add_entities(new_entities, update_before_add=True)

class IQR23Sensor(SensorEntity):

    def __init__(self, api: IQR23, uid: str, sensor_info: Sensor):
        super().__init__()
        self._api = api
        self._uid = uid
        self._sensor_info = sensor_info
        self._attr_available = False

    async def async_update(self) -> None:
        try:
            self._attr_native_value = await self._api.getSensor(self._uid)
            #self._attr_extra_state_attributes = res["info"]
            self._attr_available = True
        except (asyncio.TimeoutError, aiohttp.ClientError, KeyError):
            self._attr_available = False

    @property
    def name(self):
        return f"iqr23_{self._uid}"

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

    @property
    def friendly_name(self):
        return self._sensor_info.friendly_name

    @property
    def device_class(self):
        return self._sensor_info.homeassistant_class
    
    @property
    def state_class(self):
        return self._sensor_info.homeassistant_sclass

    @property
    def icon(self):
        return self._sensor_info.homeassistant_icon

    @property
    def native_unit_of_measurement(self):
        return self._sensor_info.unit