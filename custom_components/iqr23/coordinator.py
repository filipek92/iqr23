"""Data update coordinator for the iQ R23 integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import IQR23Client, IQR23Error
from .const import DOMAIN, MAX_CONSECUTIVE_FAILURES, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

type IQR23ConfigEntry = ConfigEntry[IQR23Coordinator]


class IQR23Coordinator(DataUpdateCoordinator[dict[str, str]]):
    """Polls all XML data files of the controller."""

    config_entry: IQR23ConfigEntry

    def __init__(
        self, hass: HomeAssistant, entry: IQR23ConfigEntry, client: IQR23Client
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.client = client
        self._failures = 0

    async def _async_update_data(self) -> dict[str, str]:
        try:
            data, failed = await self.client.async_fetch()
        except IQR23Error as err:
            self._failures += 1
            # The controller occasionally drops requests; bridge short outages with
            # the last known state instead of flapping every entity to unavailable.
            if self.data and self._failures < MAX_CONSECUTIVE_FAILURES:
                _LOGGER.debug("Refresh failed (%s), keeping cached state: %s", self._failures, err)
                return self.data
            raise UpdateFailed(str(err)) from err

        self._failures = 0
        if failed:
            _LOGGER.debug("Partial refresh, failed files: %s", ", ".join(failed))
        # Keep values from files that failed this round.
        return {**(self.data or {}), **data}
