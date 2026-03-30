import math
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
import xmltodict

from custom_components.iqr23.iqr23 import AccessLevel, IQR23, parseTemperature, sptime
import custom_components.iqr23.iqr23 as iqr23_mod


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "iqr23_10_6_2_20"


def _load_fixture_dict(filename: str) -> dict:
    return xmltodict.parse((FIXTURES_DIR / filename).read_text())["response"]


def test_sptime_parses_hours_and_minutes() -> None:
    assert sptime("x 01:30") == 1.5


def test_parse_temperature_handles_placeholders() -> None:
    assert math.isnan(parseTemperature("--.-"))
    assert parseTemperature(" 12.5 ") == 12.5


@pytest.mark.asyncio
async def test_discovery_normalizes_host_and_returns_version(monkeypatch) -> None:
    async def fake_get_xml(url: str):
        assert url == "http://192.168.1.5/data.xml"
        return {"_accvers": "1.2.3"}

    monkeypatch.setattr(iqr23_mod, "getXml", fake_get_xml)

    version = await IQR23.discovery("192.168.1.5")

    assert version == "1.2.3"


@pytest.mark.asyncio
async def test_discovery_returns_none_on_error(monkeypatch) -> None:
    async def fake_get_xml(_: str):
        raise RuntimeError("boom")

    monkeypatch.setattr(iqr23_mod, "getXml", fake_get_xml)

    version = await IQR23.discovery("192.168.1.5")

    assert version is None


@pytest.mark.asyncio
async def test_load_if_required_loads_when_cache_is_stale(monkeypatch) -> None:
    api = IQR23("device.local")
    api.load = AsyncMock()
    api.loadtime = 0

    monkeypatch.setattr(iqr23_mod, "time", lambda: 10)

    await api.loadIfRequired()

    api.load.assert_awaited_once()
    assert api.loadtime == 10


@pytest.mark.asyncio
async def test_load_if_required_skips_when_cache_is_fresh(monkeypatch) -> None:
    api = IQR23("device.local")
    api.load = AsyncMock()
    api.loadtime = 8

    monkeypatch.setattr(iqr23_mod, "time", lambda: 10)

    await api.loadIfRequired()

    api.load.assert_not_called()
    assert api.loadtime == 8


@pytest.mark.asyncio
async def test_load_if_required_uses_cached_state_when_refresh_fails(monkeypatch) -> None:
    api = IQR23("device.local")
    api.load = AsyncMock(side_effect=RuntimeError("boom"))
    api.loadtime = 0
    api.state = {"txt113": "11.0"}

    monkeypatch.setattr(iqr23_mod, "time", lambda: 10)

    await api.loadIfRequired()

    assert api.loadtime == 0
    assert api.state["txt113"] == "11.0"


@pytest.mark.asyncio
async def test_get_digital_output_mode() -> None:
    api = IQR23("device.local")
    api.loadIfRequired = AsyncMock()
    api.state = {"col402": "1"}

    mode = await api.getDigitalOutputMode("SP1")

    assert mode == "auto_r"


@pytest.mark.asyncio
async def test_get_sensor_parses_value() -> None:
    api = IQR23("device.local")
    api.loadIfRequired = AsyncMock()
    api.state = {"txt113": "10.0"}

    value = await api.getSensor("outdoorTemp")

    assert value == 10.0


@pytest.mark.asyncio
async def test_get_sensor_raises_when_missing_value() -> None:
    api = IQR23("device.local")
    api.loadIfRequired = AsyncMock()
    api.state = {}

    with pytest.raises(KeyError, match="Value not found"):
        await api.getSensor("outdoorTemp")


@pytest.mark.asyncio
async def test_set_digital_output_mode_calls_login_press_logout_and_load() -> None:
    api = IQR23("device.local")
    api.login = AsyncMock(return_value=True)
    api._pressBtn = AsyncMock(return_value=True)
    api.logout = AsyncMock(return_value=True)
    api.load = AsyncMock(return_value=True)

    await api.setDigitalOutputMode("SP1", "on")

    api.login.assert_awaited_once_with(AccessLevel.MASTER)
    api._pressBtn.assert_awaited_once_with(302)
    api.logout.assert_awaited_once_with()
    api.load.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_discovery_reads_real_device_version_from_fixture(monkeypatch) -> None:
    fixture = _load_fixture_dict("data.xml")

    async def fake_get_xml(_: str):
        return fixture

    monkeypatch.setattr(iqr23_mod, "getXml", fake_get_xml)

    version = await IQR23.discovery("10.6.2.20")

    assert "iQR23" in version


@pytest.mark.asyncio
async def test_load_merges_real_fixture_payloads(monkeypatch) -> None:
    api = IQR23("10.6.2.20")
    fixtures = {
        "data": _load_fixture_dict("data.xml"),
        "data_i_all": _load_fixture_dict("data_i_all.xml"),
        "data_t_zas": _load_fixture_dict("data_t_zas.xml"),
        "data_n_txo": _load_fixture_dict("data_n_txo.xml"),
    }

    async def fake_load_file(file: str):
        return fixtures[file]

    monkeypatch.setattr(api, "loadFile", fake_load_file)

    await api.load()

    assert api.state["txt113"].strip() == "5.4"
    assert api.state["txt101"].strip() == "64.0"
    assert api.state["col402"] in {"0", "1"}


@pytest.mark.asyncio
async def test_load_keeps_previous_values_when_one_file_fails(monkeypatch) -> None:
    api = IQR23("10.6.2.20")
    api.state = {"txt113": "9.9"}

    async def fake_load_file(file: str):
        if file == "data_i_all":
            raise RuntimeError("temporary error")
        return {"txt113": "10.1", "txt101": "61.0"}

    monkeypatch.setattr(api, "loadFile", fake_load_file)

    await api.load()

    assert api.state["txt113"] == "10.1"
    assert api.state["txt101"] == "61.0"


@pytest.mark.asyncio
async def test_sensor_and_output_mode_from_real_fixtures(monkeypatch) -> None:
    api = IQR23("10.6.2.20")
    api.state = {
        **_load_fixture_dict("data_i_all.xml"),
        **_load_fixture_dict("data_n_txo.xml"),
    }
    api.loadIfRequired = AsyncMock()

    outdoor = await api.getSensor("outdoorTemp")
    mode = await api.getDigitalOutputMode("SP1")

    assert isinstance(outdoor, float)
    assert mode in {"auto", "auto_r", "on", "off"}
