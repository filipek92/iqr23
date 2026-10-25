"""Shared fixtures for iQ R23 tests."""

from pathlib import Path

import pytest
from homeassistant.const import CONF_HOST
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.iqr23.api import DATA_FILES
from custom_components.iqr23.const import CONF_FIRMWARE_VERSION, CONF_MASTER_PASSWORD, DOMAIN

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "iqr23_10_6_2_20"
HOST = "http://10.6.2.20"
FIRMWARE_VERSION = "iQR23L08b:2018/03/06  BD: Apr 14 2018 08:51:08"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading of the custom integration in all tests."""
    return


def fixture_xml(file: str) -> str:
    return (FIXTURES_DIR / f"{file}.xml").read_text()


@pytest.fixture
def mock_device(aioclient_mock: AiohttpClientMocker) -> AiohttpClientMocker:
    """Serve the recorded XML files of a real controller."""
    for file in DATA_FILES:
        aioclient_mock.get(f"{HOST}/{file}.xml", text=fixture_xml(file))
    aioclient_mock.post(f"{HOST}/login.html", text="")
    aioclient_mock.get(f"{HOST}/t_but.cgi", text="")
    return aioclient_mock


@pytest.fixture
def config_entry() -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        version=2,
        minor_version=2,
        unique_id=HOST,
        title=HOST,
        data={CONF_HOST: HOST, CONF_MASTER_PASSWORD: "secret", CONF_FIRMWARE_VERSION: FIRMWARE_VERSION},
    )
