"""Config flow for the iQ R23 integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_HOST
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .api import IQR23Client, IQR23ConnectionError, normalize_host
from .const import (
    CONF_FIRMWARE_VERSION,
    CONF_MASTER_PASSWORD,
    CONF_MODULES,
    DEFAULT_MASTER_PASSWORD,
    DOMAIN,
)
from .modules import Module, detect_modules, enabled_modules

_LOGGER = logging.getLogger(__name__)


def _schema(host: str = "", master_password: str = DEFAULT_MASTER_PASSWORD) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_HOST, default=host): str,
            vol.Required(CONF_MASTER_PASSWORD, default=master_password): str,
        }
    )


MODULES_SELECTOR = SelectSelector(
    SelectSelectorConfig(
        options=[module.value for module in Module],
        multiple=True,
        mode=SelectSelectorMode.LIST,
        translation_key=CONF_MODULES,
    )
)


class IQR23ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for iQ R23."""

    VERSION = 2
    MINOR_VERSION = 2

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> IQR23OptionsFlow:
        return IQR23OptionsFlow()

    async def _async_validate(
        self, user_input: dict[str, Any], errors: dict[str, str]
    ) -> dict[str, Any] | None:
        """Return entry data when the controller answers, filling errors otherwise."""
        host = normalize_host(user_input[CONF_HOST])
        client = IQR23Client(
            async_get_clientsession(self.hass), host, user_input[CONF_MASTER_PASSWORD]
        )
        try:
            firmware_version = await client.async_get_firmware_version()
        except IQR23ConnectionError as err:
            _LOGGER.debug("Cannot connect to %s: %s", host, err)
            errors["base"] = "cannot_connect"
            return None
        except Exception:
            _LOGGER.exception("Unexpected error connecting to %s", host)
            errors["base"] = "unknown"
            return None
        return {
            CONF_HOST: host,
            CONF_MASTER_PASSWORD: user_input[CONF_MASTER_PASSWORD],
            CONF_FIRMWARE_VERSION: firmware_version,
        }

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            if data := await self._async_validate(user_input, errors):
                await self.async_set_unique_id(data[CONF_HOST])
                self._abort_if_unique_id_configured()
                client = IQR23Client(
                    async_get_clientsession(self.hass), data[CONF_HOST], data[CONF_MASTER_PASSWORD]
                )
                try:
                    values, _ = await client.async_fetch()
                    modules = detect_modules(values)
                except IQR23ConnectionError:
                    modules = [module.value for module in Module]
                return self.async_create_entry(
                    title=data[CONF_HOST], data=data, options={CONF_MODULES: modules}
                )

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(_schema(), user_input),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            if data := await self._async_validate(user_input, errors):
                await self.async_set_unique_id(data[CONF_HOST])
                self._abort_if_unique_id_mismatch(reason="wrong_device")
                return self.async_update_reload_and_abort(entry, data_updates=data)

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_schema(
                entry.data[CONF_HOST],
                entry.data.get(CONF_MASTER_PASSWORD, DEFAULT_MASTER_PASSWORD),
            ),
            errors=errors,
        )


class IQR23OptionsFlow(OptionsFlow):
    """Choose which modules of the controller are installed."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data={**self.config_entry.options, **user_input})

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_MODULES,
                        default=sorted(enabled_modules(self.config_entry)),
                    ): MODULES_SELECTOR
                }
            ),
        )
