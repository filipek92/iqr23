"""Tests of setup, entities and migration."""

import re

import pytest

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_HOST, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import (
    device_registry as dr,
)
from homeassistant.helpers import (
    entity_registry as er,
)
from homeassistant.helpers import (
    issue_registry as ir,
)
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.iqr23.api import DATA_FILES
from custom_components.iqr23.const import (
    CONF_FIRMWARE_VERSION,
    CONF_MASTER_PASSWORD,
    CONF_MODULES,
    DOMAIN,
)

from .conftest import HOST, FIRMWARE_VERSION


async def _setup(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def test_setup_creates_entities(
    hass: HomeAssistant,
    mock_device,
    config_entry,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
) -> None:
    await _setup(hass, config_entry)
    assert config_entry.state is ConfigEntryState.LOADED

    assert hass.states.get("sensor.iq_r23_outdoor_temperature").state == "5.4"
    assert hass.states.get("sensor.iq_r23_sp2_heating_time").state == "4106.43"
    assert hass.states.get("sensor.iq_r23_circuit_to1_mixing_valve").state == "15"
    assert hass.states.get("binary_sensor.iq_r23_system_pressure").state == "off"
    assert hass.states.get("binary_sensor.iq_r23_krb_output").state == "on"
    assert hass.states.get("binary_sensor.iq_r23_sp1_overcurrent").state == "off"
    # NP2 input is disabled in the controller ('4'), which is not a fault.
    assert hass.states.get("binary_sensor.iq_r23_sp2_overcurrent").state == "off"

    sp1 = hass.states.get("select.iq_r23_sp1_mode")
    assert sp1.state == "off"
    assert sp1.attributes["options"] == ["auto", "auto_r", "on", "off"]
    assert hass.states.get("select.iq_r23_krb_mode").state == "auto"

    summer = hass.states.get("number.iq_r23_tank_lower_summer")
    assert summer.state == "10"
    assert (summer.attributes["min"], summer.attributes["max"]) == (10, 85)
    assert hass.states.get("number.iq_r23_circuit_to1_curve_shift").state == "-6"
    assert entity_registry.async_get("number.iq_r23_tank_base_temperature").entity_category is None
    assert (
        entity_registry.async_get("number.iq_r23_tank_lower_summer").entity_category
        is EntityCategory.CONFIG
    )

    # Modules not selected in options are not created at all.
    assert entity_registry.async_get("sensor.iq_r23_pool_filtration") is None
    np2 = entity_registry.async_get("binary_sensor.iq_r23_input_np2")
    assert np2.disabled_by is er.RegistryEntryDisabler.INTEGRATION

    device = device_registry.async_get_device(identifiers={(DOMAIN, config_entry.entry_id)})
    assert (device.manufacturer, device.model, device.name) == ("iQ vytápění", "iQ R23", "iQ R23")
    assert device.sw_version == FIRMWARE_VERSION

    # Unique IDs are built from stable snake_case keys.
    for entity in er.async_entries_for_config_entry(entity_registry, config_entry.entry_id):
        key = entity.unique_id.removeprefix(f"{config_entry.entry_id}_")
        assert re.fullmatch(r"[a-z0-9_]+", key), entity.unique_id

    assert await hass.config_entries.async_unload(config_entry.entry_id)
    assert config_entry.state is ConfigEntryState.NOT_LOADED


async def test_select_option_presses_mode_button(
    hass: HomeAssistant, mock_device, config_entry
) -> None:
    await _setup(hass, config_entry)
    mock_device.mock_calls.clear()

    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": "select.iq_r23_sp1_mode", "option": "auto"},
        blocking=True,
    )

    urls = [str(url) for _, url, _, _ in mock_device.mock_calls]
    assert f"{HOST}/t_but.cgi?but=300" in urls
    assert f"{HOST}/t_but.cgi?but=200" in urls


async def test_set_number_presses_buttons(hass: HomeAssistant, mock_device, config_entry) -> None:
    await _setup(hass, config_entry)
    mock_device.mock_calls.clear()

    # The recorded XML never changes, so the controller appears to ignore the presses.
    with pytest.raises(HomeAssistantError, match="stopped at 10 instead of 12"):
        await hass.services.async_call(
            "number",
            "set_value",
            {"entity_id": "number.iq_r23_tank_lower_summer", "value": 12},
            blocking=True,
        )

    urls = [str(url) for _, url, _, _ in mock_device.mock_calls]
    assert urls.count(f"{HOST}/t_but.cgi?but=113") == 4
    assert f"{HOST}/t_but.cgi?but=200" in urls


async def test_setup_retries_when_offline(hass: HomeAssistant, aioclient_mock, config_entry) -> None:
    aioclient_mock.get(f"{HOST}/data.xml", exc=TimeoutError)
    for file in DATA_FILES[1:]:
        aioclient_mock.get(f"{HOST}/{file}.xml", exc=TimeoutError)
    config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(config_entry.entry_id)

    assert config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_migrate_from_v1(
    hass: HomeAssistant,
    mock_device,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
    issue_registry: ir.IssueRegistry,
) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=1,
        unique_id=HOST,
        # 1.x stored the firmware version under "version".
        data={CONF_HOST: HOST, "version": FIRMWARE_VERSION},
    )
    entry.add_to_hass(hass)
    # Releases before 1.1.2 used an empty device identifier.
    device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id, identifiers={(DOMAIN, "")}
    )
    temp = entity_registry.async_get_or_create(
        "sensor", DOMAIN, "iqr23_outdoorTemp", config_entry=entry,
        suggested_object_id="iqr23_outdoortemp",
    )
    entity_registry.async_update_entity(temp.entity_id, name="Venkovní teplota garáž")
    # Releases before 1.1.2 created binary sensors without the domain prefix.
    tariff = entity_registry.async_get_or_create(
        "binary_sensor", DOMAIN, "lowTariff", config_entry=entry,
        suggested_object_id="iqr23_lowtariff",
    )
    solar = entity_registry.async_get_or_create(
        "binary_sensor", DOMAIN, "solarCirculation", config_entry=entry,
        suggested_object_id="iqr23_solarcirculation",
    )
    switch = entity_registry.async_get_or_create(
        "switch", DOMAIN, "iqr23_SP1", config_entry=entry, suggested_object_id="iqr23_sp1"
    )

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert (entry.version, entry.minor_version) == (2, 2)
    assert entry.data[CONF_MASTER_PASSWORD] == "Servis254"
    assert entry.data[CONF_FIRMWARE_VERSION] == FIRMWARE_VERSION

    migrated = entity_registry.async_get(temp.entity_id)
    assert migrated.unique_id == f"{entry.entry_id}_outdoor_temperature"
    assert migrated.name == "Venkovní teplota garáž"
    assert hass.states.get("sensor.iqr23_outdoortemp").state == "5.4"

    solar_entry = entity_registry.async_get(solar.entity_id)
    assert solar_entry.unique_id == f"{entry.entry_id}_output_sol"
    assert solar_entry.translation_key == "solar_pump"
    assert hass.states.get(tariff.entity_id).state == "on"
    # No duplicates were created next to the migrated entities.
    assert hass.states.get("binary_sensor.iq_r23_low_tariff") is None
    assert hass.states.get("binary_sensor.iq_r23_sol_output") is None
    # Modules are detected from connected sensors: no pool and cooling here.
    assert entry.options[CONF_MODULES] == [
        "tank", "circuit_1", "circuit_2", "fireplace", "solar"
    ]
    assert entity_registry.async_get(switch.entity_id) is None
    assert issue_registry.async_get_issue(DOMAIN, "switches_removed")

    assert device_registry.async_get(device.id).identifiers == {(DOMAIN, entry.entry_id)}
    assert len(dr.async_entries_for_config_entry(device_registry, entry.entry_id)) == 1
    assert entity_registry.async_get(temp.entity_id).device_id == device.id


async def test_migrate_from_v2_0(
    hass: HomeAssistant, mock_device, entity_registry: er.EntityRegistry
) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        version=2,
        minor_version=1,
        unique_id=HOST,
        data={CONF_HOST: HOST, CONF_MASTER_PASSWORD: "secret", "version": FIRMWARE_VERSION},
        options={CONF_MODULES: ["tank", "circuit_1"]},
    )
    entry.add_to_hass(hass)
    renamed = {
        ("sensor", "lowerFloorMixing"): "circuit_1_mixing",
        ("binary_sensor", "watertankPressure"): "system_pressure",
        ("binary_sensor", "digitalInputLowTariff"): "digital_input_low_tariff",
        ("binary_sensor", "T/C_running"): "output_tc",
        ("select", "SP1_mode"): "output_sp1_mode",
    }
    entity_ids = {
        new_key: entity_registry.async_get_or_create(
            platform, DOMAIN, f"{entry.entry_id}_{old_key}", config_entry=entry
        ).entity_id
        for (platform, old_key), new_key in renamed.items()
    }

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.minor_version == 2
    assert entry.data[CONF_FIRMWARE_VERSION] == FIRMWARE_VERSION
    assert "version" not in entry.data
    for new_key, entity_id in entity_ids.items():
        assert entity_registry.async_get(entity_id).unique_id == f"{entry.entry_id}_{new_key}"
    assert hass.states.get(entity_ids["output_sp1_mode"]).state == "off"
    # No duplicates were created next to the migrated entities.
    assert hass.states.get("select.iq_r23_sp1_mode") is None
    assert hass.states.get("binary_sensor.iq_r23_system_pressure") is None


async def test_diagnostics_redacts_password(hass: HomeAssistant, mock_device, config_entry) -> None:
    from custom_components.iqr23.diagnostics import async_get_config_entry_diagnostics

    await _setup(hass, config_entry)
    diag = await async_get_config_entry_diagnostics(hass, config_entry)

    assert diag["entry"][CONF_MASTER_PASSWORD] == "**REDACTED**"
    assert diag["data"]["txt113"].strip() == "5.4"


async def test_options_change_modules(
    hass: HomeAssistant, mock_device, config_entry, entity_registry: er.EntityRegistry
) -> None:
    await _setup(hass, config_entry)
    assert hass.states.get("sensor.iq_r23_fireplace")

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_MODULES: ["tank", "pool"]}
    )
    await hass.async_block_till_done()

    assert config_entry.options[CONF_MODULES] == ["tank", "pool"]
    assert entity_registry.async_get("sensor.iq_r23_fireplace") is None
    assert hass.states.get("sensor.iq_r23_pool_filtration").state == "unknown"
    assert hass.states.get("sensor.iq_r23_tank_upper").state == "64.0"


async def test_remove_stale_device(
    hass: HomeAssistant, mock_device, config_entry, device_registry: dr.DeviceRegistry
) -> None:
    from custom_components.iqr23 import async_remove_config_entry_device

    await _setup(hass, config_entry)
    active = device_registry.async_get_device(identifiers={(DOMAIN, config_entry.entry_id)})
    stale = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id, identifiers={(DOMAIN, "")}
    )

    assert not await async_remove_config_entry_device(hass, config_entry, active)
    assert await async_remove_config_entry_device(hass, config_entry, stale)
