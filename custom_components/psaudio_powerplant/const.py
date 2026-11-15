"""Constants for the PS Audio PowerPlant integration."""

from __future__ import annotations

from datetime import timedelta
from typing import Final

DOMAIN: Final = "psaudio_powerplant"
MANUFACTURER: Final = "PS Audio"

DEFAULT_NAME: Final = "P20"

CONF_SCAN_INTERVAL: Final = "scan_interval"
DEFAULT_SCAN_INTERVAL: Final = 60
MIN_SCAN_INTERVAL: Final = 30
MAX_SCAN_INTERVAL: Final = 3600

# The P20 network board is known to lock up under heavy use, so every
# request is short, serialized and spaced out.
REQUEST_TIMEOUT: Final = 8.0
MIN_REQUEST_GAP: Final = 1.0
# Give the unit a moment to act on a command before reading it back.
POST_COMMAND_DELAY: Final = 2.0


def scan_interval_from_seconds(seconds: int) -> timedelta:
    """Return a polling interval, never faster than the safe minimum."""
    return timedelta(seconds=max(MIN_SCAN_INTERVAL, seconds))
