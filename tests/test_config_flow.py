"""Tests of the iQ R23 config flow."""

from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.iqr23.const import (
    CONF_FIRMWARE_VERSION,
    CONF_MASTER_PASSWORD,
    CONF_MODULES,
    DOMAIN,
)

from .conftest import HOST, FIRMWARE_VERSION

USER_INPUT = {CONF_HOST: "10.6.2.20", CONF_MASTER_PASSWORD: "secret"}


async def test_user_flow_creates_entry(hass: HomeAssistant, mock_device) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == HOST
    assert result["data"] == {
        CONF_HOST: HOST,
        CONF_MASTER_PASSWORD: "secret",
        CONF_FIRMWARE_VERSION: FIRMWARE_VERSION,
    }
    assert result["result"].unique_id == HOST
    assert result["options"] == {
        CONF_MODULES: ["tank", "circuit_1", "circuit_2", "fireplace", "solar"]
    }


async def test_user_flow_cannot_connect(hass: HomeAssistant, aioclient_mock) -> None:
    aioclient_mock.get(f"{HOST}/data.xml", exc=TimeoutError)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=USER_INPUT
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_user_flow_rejects_foreign_device(hass: HomeAssistant, aioclient_mock) -> None:
    aioclient_mock.get(f"{HOST}/data.xml", text="<html>router</html>")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=USER_INPUT
    )

    assert result["errors"] == {"base": "cannot_connect"}


async def test_user_flow_aborts_when_configured(
    hass: HomeAssistant, mock_device, config_entry
) -> None:
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=USER_INPUT
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_reconfigure_updates_password(
    hass: HomeAssistant, mock_device, config_entry
) -> None:
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: HOST, CONF_MASTER_PASSWORD: "new"}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert config_entry.data[CONF_MASTER_PASSWORD] == "new"
