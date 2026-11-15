"""Parser tests that need no Home Assistant."""

import importlib.util
from pathlib import Path
import sys

import pytest

from .sample import RA, RS

_PATH = Path(__file__).parents[1] / "custom_components/psaudio_powerplant/parser.py"
_spec = importlib.util.spec_from_file_location("p20_parser", _PATH)
parser = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = parser  # dataclasses need the module registered
_spec.loader.exec_module(parser)


def test_parse_full_dump() -> None:
    s = parser.parse_status(RA)
    assert s.unit_type == "p20"
    assert s.is_on is False
    assert s.mac == "00:11:22:33:44:55"
    assert s.hostname == "POWERPLANT"
    assert s.firmware == "0.01.25"
    assert s.web_firmware == "1.22.00"
    assert s.mov_ok is True
    assert s.locked is False
    assert s.input_voltage == 120.1
    assert s.output_voltage == 119.6
    assert s.input_thd == 4.5
    assert s.output_thd == 0.2
    assert s.output_current == 0.01
    # Output power is volts x amps, not the unit's watts field.
    assert s.output_power == 1.2
    assert s.reported_watts == 5
    assert s.frequency == 60.0
    assert s.dc_offset == 15
    assert (s.temperature_1, s.temperature_2) == (23, 27)
    assert s.voltage_setting == 120
    assert s.multiwave_strength == 4
    assert s.regulation_mode == "reg"
    assert s.waveform == "sine"


def test_outlets_keep_spaces_and_order() -> None:
    s = parser.parse_status(RA)
    assert list(s.outlets) == list(range(1, 17))
    assert s.outlets[1].name == "OUTLET 1"
    assert s.outlets[16].name == "OUTLET 16"
    assert s.outlets[3].delay_mode == "SW"
    assert not any(o.is_on for o in s.outlets.values())


def test_power_on_and_outlet_on() -> None:
    s = parser.parse_status(RA.replace("&upwr=0", "&upwr=1").replace("&z5pwr=0", "&z5pwr=1"))
    assert s.is_on is True
    assert s.outlets[5].is_on is True
    assert s.outlets[4].is_on is False


def test_split_first_equals_only() -> None:
    assert parser.split_pairs("&a=b=c&name=Big Amp&&noequals&=x\r\n") == {
        "a": "b=c",
        "name": "Big Amp",
    }


def test_short_reply_has_no_outlets_or_mac() -> None:
    # RS lacks utype, so it is rejected; with utype added it parses sparsely.
    with pytest.raises(parser.PowerPlantParseError):
        parser.parse_status(RS)
    s = parser.parse_status(RS + "&utype=p20")
    assert s.outlets == {}
    assert s.mac is None
    assert s.frequency is None


def test_bad_numbers_become_none() -> None:
    s = parser.parse_status(
        RA.replace("&watts=5", "&watts=--").replace("&mwstrength=4", "&mwstrength=")
    )
    assert s.reported_watts is None
    assert s.multiwave_strength is None
    assert parser.parse_status(RA.replace("&amps=0.01", "&amps=")).output_power is None


@pytest.mark.parametrize("text", ["", "<html>Not found</html>", "&upwr=0", "&utype=p20&upwr=x"])
def test_rejects_non_powerplant(text: str) -> None:
    with pytest.raises(parser.PowerPlantParseError):
        parser.parse_status(text)


def test_output_power_ignores_bad_watts_field() -> None:
    # The unit's watts field can disagree with volts x amps.
    s = parser.parse_status(
        RA.replace("&amps=0.01", "&amps=0.94").replace("&watts=5", "&watts=823")
    )
    assert s.output_power == 112.4
    assert s.reported_watts == 823


def test_zone_map_covers_every_outlet_once() -> None:
    outlets = [n for zone in parser.P20_ZONES for n in zone.outlets]
    assert outlets == list(range(1, 17))
    assert [z.letter for z in parser.P20_ZONES] == ["a", "b", "c", "d", "e"]
    assert [z.command_outlet for z in parser.P20_ZONES] == [1, 5, 9, 13, 15]
    assert [z.high_current for z in parser.P20_ZONES] == [False, False, False, True, True]


def test_zone_is_on_if_any_outlet_is_on() -> None:
    zone_b = parser.P20_ZONES[1]
    s = parser.parse_status(RA)
    assert s.zone_is_on(zone_b) is False
    s = parser.parse_status(RA.replace("&z7pwr=0", "&z7pwr=1"))
    assert s.zone_is_on(zone_b) is True
    assert s.zone_is_on(parser.P20_ZONES[0]) is False
    assert [o.number for o in s.zone_outlets(zone_b)] == [5, 6, 7, 8]


def test_zone_unknown_without_outlets() -> None:
    s = parser.parse_status(RS + "&utype=p20")
    assert s.zone_outlets(parser.P20_ZONES[0]) == []
    assert s.zone_is_on(parser.P20_ZONES[0]) is None


def test_zone_for_outlet() -> None:
    assert parser.zone_for_outlet(1).letter == "a"
    assert parser.zone_for_outlet(8).letter == "b"
    assert parser.zone_for_outlet(14).letter == "d"
    assert parser.zone_for_outlet(16).letter == "e"
    assert parser.zone_for_outlet(17) is None
