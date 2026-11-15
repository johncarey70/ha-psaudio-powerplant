"""Parse PowerPlant status replies.

Pure Python with no Home Assistant imports, so it can be unit tested alone.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Final

_OUTLET_KEY = re.compile(r"^z(\d+)pwr$")


class PowerPlantParseError(ValueError):
    """Raised when a reply does not look like a PowerPlant status dump."""


@dataclass(frozen=True, slots=True)
class Outlet:
    """One outlet as reported by the unit (switched as part of its zone)."""

    number: int
    name: str
    is_on: bool
    delay_mode: str | None = None


@dataclass(frozen=True, slots=True)
class Zone:
    """A group of outlets that the unit switches together.

    The P20 reports each outlet separately, but switching any outlet in a
    zone switches the whole zone. Commands go to the zone's first outlet.
    """

    letter: str
    outlets: tuple[int, ...]
    high_current: bool = False

    @property
    def command_outlet(self) -> int:
        """Outlet number that ``ZP=<n>,ON|OFF`` is sent to for this zone."""
        return self.outlets[0]


# US P20 zone map, confirmed on John's unit on Nov 15, 2026 by cycling each
# zone from the front panel and watching which outlets changed together.
P20_ZONES: Final[tuple[Zone, ...]] = (
    Zone("a", (1, 2, 3, 4)),
    Zone("b", (5, 6, 7, 8)),
    Zone("c", (9, 10, 11, 12)),
    Zone("d", (13, 14), high_current=True),
    Zone("e", (15, 16), high_current=True),
)


def zone_for_outlet(number: int) -> Zone | None:
    """Return the P20 zone that outlet ``number`` belongs to."""
    return next((zone for zone in P20_ZONES if number in zone.outlets), None)


@dataclass(frozen=True, slots=True)
class PowerPlantStatus:
    """Typed view of the ``RA`` status dump."""

    unit_type: str
    is_on: bool
    mac: str | None = None
    hostname: str | None = None
    firmware: str | None = None
    web_firmware: str | None = None
    mov_ok: bool | None = None
    locked: bool | None = None
    input_voltage: float | None = None
    output_voltage: float | None = None
    input_thd: float | None = None
    output_thd: float | None = None
    output_current: float | None = None
    # Output volts x amps. The unit's own ``watts`` field is unreliable on the
    # P20 (it read 823 W while volts x amps and an Emporia meter read ~115 W).
    output_power: float | None = None
    reported_watts: float | None = None
    frequency: float | None = None
    dc_offset: float | None = None
    temperature_1: float | None = None
    temperature_2: float | None = None
    voltage_setting: float | None = None
    multiwave_strength: int | None = None
    regulation_mode: str | None = None
    waveform: str | None = None
    outlets: dict[int, Outlet] = field(default_factory=dict)
    raw: dict[str, str] = field(default_factory=dict, repr=False)

    def zone_outlets(self, zone: Zone) -> list[Outlet]:
        """Outlets of ``zone`` that the unit reported, in order."""
        return [self.outlets[n] for n in zone.outlets if n in self.outlets]

    def zone_is_on(self, zone: Zone) -> bool | None:
        """True if any outlet in the zone is on; None if none were reported."""
        outlets = self.zone_outlets(zone)
        if not outlets:
            return None
        return any(outlet.is_on for outlet in outlets)


def split_pairs(text: str) -> dict[str, str]:
    """Split ``&key=value&key=value`` into a dict.

    Values are not URL-encoded and may contain spaces, so each pair is split
    on its first ``=`` only. Empty fragments and pairs without ``=`` are
    skipped.
    """
    pairs: dict[str, str] = {}
    for fragment in text.strip().split("&"):
        key, sep, value = fragment.partition("=")
        key = key.strip()
        if not sep or not key:
            continue
        pairs[key] = value.strip()
    return pairs


def _float(raw: dict[str, str], key: str) -> float | None:
    value = raw.get(key)
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _int(raw: dict[str, str], key: str) -> int | None:
    value = _float(raw, key)
    return None if value is None else int(value)


def _flag(raw: dict[str, str], key: str) -> bool | None:
    value = raw.get(key)
    if value == "1":
        return True
    if value == "0":
        return False
    return None


def _text(raw: dict[str, str], key: str) -> str | None:
    value = raw.get(key)
    return value if value else None


def _product(a: float | None, b: float | None) -> float | None:
    if a is None or b is None:
        return None
    return round(a * b, 1)


def _format_mac(value: str | None) -> str | None:
    """Turn ``001122334455`` into ``00:11:22:33:44:55``."""
    if not value:
        return None
    digits = re.sub(r"[^0-9a-fA-F]", "", value).lower()
    if len(digits) != 12:
        return None
    return ":".join(digits[i : i + 2] for i in range(0, 12, 2))


def _parse_outlets(raw: dict[str, str]) -> dict[int, Outlet]:
    outlets: dict[int, Outlet] = {}
    for key, value in raw.items():
        match = _OUTLET_KEY.match(key)
        if match is None or value not in ("0", "1"):
            continue
        number = int(match.group(1))
        outlets[number] = Outlet(
            number=number,
            name=raw.get(f"z{number}name") or f"Outlet {number}",
            is_on=value == "1",
            delay_mode=_text(raw, f"z{number}dlymode"),
        )
    return dict(sorted(outlets.items()))


def parse_status(text: str) -> PowerPlantStatus:
    """Parse the reply to ``commands.cgi?command=RA``.

    Raises PowerPlantParseError if the reply lacks the unit type or the unit
    power flag, which every PowerPlant status dump carries.
    """
    raw = split_pairs(text)
    unit_type = raw.get("utype")
    is_on = _flag(raw, "upwr")
    if not unit_type or is_on is None:
        raise PowerPlantParseError("Reply is not a PowerPlant status dump")

    output_voltage = _float(raw, "voltsout")
    output_current = _float(raw, "amps")
    return PowerPlantStatus(
        unit_type=unit_type,
        is_on=is_on,
        mac=_format_mac(raw.get("mac")),
        hostname=_text(raw, "hostname"),
        firmware=_text(raw, "fwvproc"),
        web_firmware=_text(raw, "fwvweb"),
        mov_ok=_flag(raw, "umov"),
        locked=_flag(raw, "ulock"),
        input_voltage=_float(raw, "voltsin"),
        output_voltage=output_voltage,
        input_thd=_float(raw, "thdin"),
        output_thd=_float(raw, "thdout"),
        output_current=output_current,
        output_power=_product(output_voltage, output_current),
        reported_watts=_float(raw, "watts"),
        frequency=_float(raw, "freq"),
        dc_offset=_float(raw, "dc"),
        temperature_1=_float(raw, "temp1"),
        temperature_2=_float(raw, "temp2"),
        voltage_setting=_float(raw, "voltssetting"),
        multiwave_strength=_int(raw, "mwstrength"),
        regulation_mode=_text(raw, "regmode"),
        waveform=_text(raw, "waveform"),
        outlets=_parse_outlets(raw),
        raw=raw,
    )
