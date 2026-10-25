"""Tests of the standalone iQ R23 client."""

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from pytest_homeassistant_custom_component.test_util.aiohttp import (
    AiohttpClientMocker,
    AiohttpClientMockResponse,
)

from custom_components.iqr23.api import (
    DATA_FILES,
    DIGITAL_OUTPUTS,
    SETPOINTS,
    IQR23Client,
    IQR23ConnectionError,
    IQR23Error,
    OutputMode,
    Setpoint,
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


def test_setpoint_buttons_are_adjacent() -> None:
    buttons = [b for s in SETPOINTS.values() for b in (s.minus_button, s.plus_button)]
    assert len(buttons) == len(set(buttons))
    for setpoint in SETPOINTS.values():
        assert setpoint.plus_button == setpoint.minus_button + 1, setpoint.key
        assert setpoint.min_value < setpoint.max_value, setpoint.key


def _simulate_setpoint(
    aioclient_mock: AiohttpClientMocker, setpoint: Setpoint, value: int, drop: int = 0
) -> dict[str, int]:
    """Mock a controller that applies -/+ presses within limits, dropping the first `drop`."""
    state = {"value": value, "drop": drop}

    async def read(method, url, data):
        text = f"<response><{setpoint.value_key}>{state['value']:02}</{setpoint.value_key}></response>"
        return AiohttpClientMockResponse(method, url, text=text)

    async def press(method, url, data):
        if state["drop"]:
            state["drop"] -= 1
        elif (button := int(url.query["but"])) in (setpoint.minus_button, setpoint.plus_button):
            delta = setpoint.step if button == setpoint.plus_button else -setpoint.step
            state["value"] = min(max(state["value"] + delta, setpoint.min_value), setpoint.max_value)
        return AiohttpClientMockResponse(method, url, text="")

    aioclient_mock.get(f"{HOST}/{setpoint.file}.xml", side_effect=read)
    aioclient_mock.get(f"{HOST}/t_but.cgi", side_effect=press)
    aioclient_mock.post(f"{HOST}/login.html", text="")
    return state


async def test_set_setpoint_presses_buttons(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    setpoint = SETPOINTS["tank_lower_summer"]
    state = _simulate_setpoint(aioclient_mock, setpoint, 10)
    client = IQR23Client(async_get_clientsession(hass), HOST, "secret")

    await client.async_set_setpoint("tank_lower_summer", 13)

    assert state["value"] == 13
    calls = [(method, str(url), data) for method, url, data, _ in aioclient_mock.mock_calls]
    assert calls[0] == ("POST", f"{HOST}/login.html", {"pass": "secret"})
    assert calls.count(("GET", f"{HOST}/t_but.cgi?but=113", None)) == 3
    assert calls[-2:] == [
        ("GET", f"{HOST}/t_but.cgi?but=200", None),
        ("POST", f"{HOST}/login.html", {"pass": ""}),
    ]


async def test_set_setpoint_repeats_dropped_presses(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    state = _simulate_setpoint(aioclient_mock, SETPOINTS["tank_base"], 50, drop=2)
    client = IQR23Client(async_get_clientsession(hass), HOST, "secret")

    await client.async_set_setpoint("tank_base", 45)

    assert state["value"] == 45


async def test_set_setpoint_reports_ignored_presses(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    setpoint = SETPOINTS["tank_base"]
    _simulate_setpoint(aioclient_mock, setpoint, 50, drop=100)
    client = IQR23Client(async_get_clientsession(hass), HOST, "secret")

    with pytest.raises(IQR23Error, match="stopped at 50"):
        await client.async_set_setpoint("tank_base", 45)

    # The reached value is persisted and the session closed even on failure.
    urls = [str(url) for _, url, _, _ in aioclient_mock.mock_calls]
    assert f"{HOST}/t_but.cgi?but=200" in urls
    method, url, data, _ = aioclient_mock.mock_calls[-1]
    assert (method, data) == ("POST", {"pass": ""})


async def test_set_setpoint_rejects_out_of_range(hass: HomeAssistant) -> None:
    client = IQR23Client(async_get_clientsession(hass), HOST, "secret")
    setpoint = SETPOINTS["tank_base"]

    with pytest.raises(ValueError):
        await client.async_set_setpoint("tank_base", setpoint.max_value + 1)
