"""Config flow and entity tests with mocked HTTP."""

from datetime import timedelta

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_fire_time_changed
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.psaudio_powerplant.const import CONF_SCAN_INTERVAL, DOMAIN
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, STATE_OFF, STATE_ON, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType, InvalidData
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util

from .sample import HOST, MAC, RA

BASE = f"http://{HOST}/commands.cgi?command="


def mock_ra(aioclient_mock: AiohttpClientMocker, text: str = RA) -> None:
    aioclient_mock.get(BASE + "RA", text=text)


def sent_commands(aioclient_mock: AiohttpClientMocker) -> list[str]:
    return [str(call[1]).removeprefix(BASE) for call in aioclient_mock.mock_calls]


async def setup_entry(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN, title="P20 Front Right", unique_id=MAC, data={CONF_HOST: HOST}
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_flow_creates_entry(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    mock_ra(aioclient_mock)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: f" {HOST} ", CONF_NAME: "P20 Front Right"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "P20 Front Right"
    assert result["data"] == {CONF_HOST: HOST}
    assert result["result"].unique_id == MAC
    # The flow only ever reads status.
    assert set(sent_commands(aioclient_mock)) == {"RA"}


@pytest.mark.parametrize(
    ("mock_kwargs", "error"),
    [
        ({"exc": TimeoutError()}, "cannot_connect"),
        ({"status": 500}, "not_powerplant"),
        ({"text": "<html>hello</html>"}, "not_powerplant"),
        ({"text": RA.replace("&mac=001122334455", "")}, "no_mac"),
    ],
)
async def test_flow_errors(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, mock_kwargs: dict, error: str
) -> None:
    aioclient_mock.get(BASE + "RA", **mock_kwargs)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: HOST, CONF_NAME: "P20"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": error}


async def test_flow_already_configured(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    MockConfigEntry(domain=DOMAIN, unique_id=MAC, data={CONF_HOST: "10.0.0.9"}).add_to_hass(hass)
    mock_ra(aioclient_mock)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: HOST, CONF_NAME: "P20"}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_entities(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    mock_ra(aioclient_mock)
    await setup_entry(hass)
    reg = er.async_get(hass)

    assert hass.states.get("switch.p20_front_right_power").state == STATE_OFF
    assert hass.states.get("sensor.p20_front_right_input_voltage").state == "120.1"
    # 119.6 V x 0.01 A, not the unit's watts field (5).
    assert hass.states.get("sensor.p20_front_right_output_power").state == "1.2"
    assert reg.async_get("sensor.p20_front_right_reported_watts").disabled_by is not None
    assert hass.states.get("sensor.p20_front_right_temperature_2").state == "27.0"
    assert hass.states.get("sensor.p20_front_right_regulation_mode").state == "reg"
    assert hass.states.get("binary_sensor.p20_front_right_unit_lockout").state == STATE_OFF

    entries = er.async_entries_for_config_entry(
        reg, hass.config_entries.async_entries(DOMAIN)[0].entry_id
    )
    # No outlet switches any more (outlets are read-only binary sensors).
    assert not [e for e in entries if e.domain == "switch" and "_outlet_" in e.unique_id]
    zones = sorted(e.entity_id for e in entries if "_zone_" in e.unique_id)
    assert zones == [f"switch.p20_front_right_zone_{letter}" for letter in "abcde"]
    assert reg.async_get("switch.p20_front_right_zone_d").unique_id == f"{MAC}_zone_d"
    assert all(reg.async_get(z).disabled_by is None for z in zones)
    assert hass.states.get("switch.p20_front_right_zone_a").state == STATE_OFF
    assert hass.states.get("switch.p20_front_right_zone_d").name == "P20 Front Right Zone D (HC)"
    assert reg.async_get("binary_sensor.p20_front_right_mov_status").disabled_by is not None

    # One request per poll, and only status reads so far.
    assert sent_commands(aioclient_mock) == ["RA"]


async def test_power_switch_sends_command(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    mock_ra(aioclient_mock)
    aioclient_mock.get(BASE + "UP=ON", text="OK")
    await setup_entry(hass)

    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": "switch.p20_front_right_power"}, blocking=True
    )
    await hass.async_block_till_done()
    calls = sent_commands(aioclient_mock)
    assert calls[:2] == ["RA", "UP=ON"]
    # The command URL is sent literally, not as UP%3DON.
    assert any(str(c[1]).endswith("command=UP=ON") for c in aioclient_mock.mock_calls)
    assert calls[-1] == "RA"


async def test_command_failure_raises(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    from homeassistant.exceptions import HomeAssistantError

    mock_ra(aioclient_mock)
    aioclient_mock.get(BASE + "UP=OFF", exc=TimeoutError())
    await setup_entry(hass)
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            "switch", "turn_off", {"entity_id": "switch.p20_front_right_power"}, blocking=True
        )


async def test_unavailable_on_failed_poll(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    mock_ra(aioclient_mock)
    await setup_entry(hass)
    aioclient_mock.clear_requests()
    aioclient_mock.get(BASE + "RA", exc=TimeoutError())
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=61))
    await hass.async_block_till_done()
    assert hass.states.get("switch.p20_front_right_power").state == STATE_UNAVAILABLE
    assert hass.states.get("sensor.p20_front_right_input_voltage").state == STATE_UNAVAILABLE


async def test_options_flow(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    mock_ra(aioclient_mock)
    entry = await setup_entry(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM

    with pytest.raises(InvalidData):
        await hass.config_entries.options.async_configure(
            result["flow_id"], {CONF_SCAN_INTERVAL: 5}
        )

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_SCAN_INTERVAL: 120}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert entry.options == {CONF_SCAN_INTERVAL: 120}
    assert entry.runtime_data.coordinator.update_interval == timedelta(seconds=120)


async def test_unload(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    mock_ra(aioclient_mock)
    entry = await setup_entry(hass)
    assert await hass.config_entries.async_unload(entry.entry_id)
    assert entry.state is config_entries.ConfigEntryState.NOT_LOADED


async def test_zone_state_and_attributes(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    # Only outlet 14 of zone D reports on: the zone counts as on.
    mock_ra(aioclient_mock, RA.replace("&z14pwr=0", "&z14pwr=1"))
    await setup_entry(hass)
    state = hass.states.get("switch.p20_front_right_zone_d")
    assert state.state == STATE_ON
    assert state.attributes["outlets"] == [13, 14]
    assert state.attributes["outlet_states"] == {"13": "off", "14": "on"}
    assert state.attributes["high_current"] is True
    assert state.attributes["delay_mode"] == "SW"
    assert hass.states.get("switch.p20_front_right_zone_e").state == STATE_OFF
    assert hass.states.get("switch.p20_front_right_zone_a").name == "P20 Front Right Zone A"


@pytest.mark.parametrize(
    ("entity_id", "service", "command"),
    [
        ("switch.p20_front_right_zone_a", "turn_on", "ZP=1,ON"),
        ("switch.p20_front_right_zone_c", "turn_off", "ZP=9,OFF"),
        ("switch.p20_front_right_zone_d", "turn_off", "ZP=13,OFF"),
        ("switch.p20_front_right_zone_e", "turn_on", "ZP=15,ON"),
    ],
)
async def test_zone_switch_sends_first_outlet(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    entity_id: str,
    service: str,
    command: str,
) -> None:
    mock_ra(aioclient_mock)
    aioclient_mock.get(BASE + command, text="OK")
    await setup_entry(hass)
    await hass.services.async_call("switch", service, {"entity_id": entity_id}, blocking=True)
    await hass.async_block_till_done()
    assert sent_commands(aioclient_mock) == ["RA", command, "RA"]


async def test_outlet_status_sensors(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    mock_ra(aioclient_mock, RA.replace("&z14pwr=0", "&z14pwr=1"))
    await setup_entry(hass)
    reg = er.async_get(hass)
    entries = er.async_entries_for_config_entry(
        reg, hass.config_entries.async_entries(DOMAIN)[0].entry_id
    )
    statuses = [e for e in entries if e.translation_key == "outlet"]
    assert len(statuses) == 16
    assert all(e.disabled_by is None for e in statuses)
    # New unique ids, not the 0.1.0 outlet switch ids.
    assert reg.async_get("binary_sensor.p20_front_right_outlet_1").unique_id == (
        f"{MAC}_outlet_1_status"
    )
    assert not reg.async_get_entity_id("switch", DOMAIN, f"{MAC}_outlet_1")

    state = hass.states.get("binary_sensor.p20_front_right_outlet_14")
    assert state.state == STATE_ON
    assert state.name == "P20 Front Right Outlet 14"
    assert state.attributes["device_class"] == "power"
    assert state.attributes["zone"] == "D"
    assert hass.states.get("binary_sensor.p20_front_right_outlet_13").state == STATE_OFF
    assert hass.states.get("binary_sensor.p20_front_right_outlet_5").attributes["zone"] == "B"
    # Read-only: still only one status read.
    assert sent_commands(aioclient_mock) == ["RA"]
