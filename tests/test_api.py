"""Tests of the standalone iQ R23 client."""

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.iqr23.api import (
    DATA_FILES,
    DIGITAL_OUTPUTS,
    IQR23Client,
    IQR23ConnectionError,
    OutputMode,
    get_output_mode,
    normalize_host,
    parse_counter_hours,
    parse_percent,
    parse_temperature,
)

from .conftest import HOST, FIRMWARE_VERSION


def test_parsers() -> None:
    assert parse_temperature(" 12.5 ") == 12.5
    assert parse_temperature("--.-") is None
    assert parse_counter_hours("SP1:  007500:50") == pytest.approx(7500.83)
    assert parse_percent("015%") == 15


def test_normalize_host() -> None:
    assert normalize_host("10.6.2.20") == HOST
    assert normalize_host("http://10.6.2.20/") == HOST


def test_output_definitions_match_controller_layout() -> None:
    sp1, sto = DIGITAL_OUTPUTS["sp1"], DIGITAL_OUTPUTS["sto"]
    assert sp1.state_key == "col400"
    assert sp1.mode_keys == {
        "col401": OutputMode.AUTO,
        "col402": OutputMode.AUTO_R,
        "col403": OutputMode.ON,
        "col404": OutputMode.OFF,
    }
    assert sp1.mode_buttons[OutputMode.ON] == 302
    assert sto.state_key == "col455"
    assert sto.mode_buttons[OutputMode.OFF] == 347


def test_get_output_mode() -> None:
    sp1 = DIGITAL_OUTPUTS["sp1"]
    assert get_output_mode({"col402": "1"}, sp1) is OutputMode.AUTO_R
    assert get_output_mode({"col402": "0"}, sp1) is None


async def test_fetch_merges_all_files(hass: HomeAssistant, mock_device) -> None:
    client = IQR23Client(async_get_clientsession(hass), HOST, "secret")

    data, failed = await client.async_fetch()

    assert failed == []
    assert data["txt113"].strip() == "5.4"
    assert data["col404"] == "1"
    assert await client.async_get_firmware_version() == FIRMWARE_VERSION


async def test_fetch_tolerates_partial_failure(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    aioclient_mock.get(f"{HOST}/data.xml", text="<response><txt113>1.0</txt113></response>")
    for file in DATA_FILES[1:]:
        aioclient_mock.get(f"{HOST}/{file}.xml", status=500)
    client = IQR23Client(async_get_clientsession(hass), HOST, "secret")

    data, failed = await client.async_fetch()

    assert data == {"txt113": "1.0"}
    assert failed == list(DATA_FILES[1:])


async def test_fetch_raises_when_everything_fails(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    aioclient_mock.get(f"{HOST}/data.xml", exc=TimeoutError)
    for file in DATA_FILES[1:]:
        aioclient_mock.get(f"{HOST}/{file}.xml", status=500)
    client = IQR23Client(async_get_clientsession(hass), HOST, "secret")

    with pytest.raises(IQR23ConnectionError):
        await client.async_fetch()


async def test_set_output_mode_sequence(hass: HomeAssistant, mock_device) -> None:
    client = IQR23Client(async_get_clientsession(hass), HOST, "secret")

    await client.async_set_output_mode("krb", OutputMode.AUTO)

    calls = [(method, str(url), data) for method, url, data, _ in mock_device.mock_calls]
    assert calls == [
        ("POST", f"{HOST}/login.html", {"pass": "secret"}),
        ("GET", f"{HOST}/t_but.cgi?but=312", None),
        ("GET", f"{HOST}/t_but.cgi?but=200", None),
        ("POST", f"{HOST}/login.html", {"pass": ""}),
    ]


async def test_set_output_mode_logs_out_after_failure(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    aioclient_mock.post(f"{HOST}/login.html", text="")
    aioclient_mock.get(f"{HOST}/t_but.cgi", status=500)
    client = IQR23Client(async_get_clientsession(hass), HOST, "secret")

    with pytest.raises(IQR23ConnectionError):
        await client.async_set_output_mode("sp1", OutputMode.ON)

    method, url, data, _ = aioclient_mock.mock_calls[-1]
    assert (method, data) == ("POST", {"pass": ""})
