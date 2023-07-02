import logging

from .iqr23 import IQR23

import voluptuous as vol
from homeassistant import config_entries, exceptions, core
from homeassistant.helpers.device_registry import format_mac

#from skydance.network.discovery import discover_ips_by_mac
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema({vol.Required("host"): str})

# TODO stub of auto-discovery follows:
# async def _async_has_devices(hass) -> bool:
#     """Return if there are devices that can be discovered."""
#     local_ip = get_local_ip()
#     # simply assume /24 network
#     assumed_network_mask = "24"
#     network = ipaddress.IPv4Network(local_ip + "/" + assumed_network_mask, strict=False)
#     res = await discover_ips_by_mac(str(network.broadcast_address), broadcast=True)
#     return len(res) > 0
#
# config_entry_flow.register_discovery_flow(DOMAIN, MANUFACTURER, _async_has_devices, config_entries.CONN_CLASS_ASSUMED)


async def validate_input(hass: core.HomeAssistant, data: dict):
    """
    Validate the user input by executing a Skydance discovery protocol.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """
    if not data["host"]:
        raise InvalidHost()
    try:
        host = data['host']
        _LOGGER.info(f"Trying to discovery on {host}")
        discovery_result = await IQR23.discovery(host)
    except OSError as e:
        _LOGGER.exception(e)
        raise CannotConnect() from e

    if not discovery_result:
        _LOGGER.error(f"No discovery response from {host}")
        raise CannotConnect()

    return discovery_result


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_ASSUMED

    async def async_step_user(self, user_input=None):
        """Handle the initial step of config flow initiated by user manually."""
        errors = {}
        if user_input is not None:
            try:
                discovery_result = await validate_input(self.hass, user_input)
                host = user_input["host"]
                if not host.startswith('http://'):
                    host =  'http://'+host

                data = {
                    "host": host,
                    "version": discovery_result
                }
                _LOGGER.info("Adding IQ Topeni config entry with data=%s", data)
                await self.async_set_unique_id(host)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=host, data=data)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidHost:
                errors["host"] = "cannot_connect"
            except MultipleHosts:
                errors["host"] = "multiple_hosts"
            except Exception as e:  # NOQA
                _LOGGER.exception(e)
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidHost(exceptions.HomeAssistantError):
    """Error to indicate there is an invalid hostname."""


class MultipleHosts(exceptions.HomeAssistantError):
    """Error to indicate that we got multiple answers to the discovery request."""