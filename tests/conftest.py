"""Fixtures for the PowerPlant tests."""

from collections.abc import Generator
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Let Home Assistant load custom_components in every test."""


@pytest.fixture(autouse=True)
def no_delays() -> Generator[None]:
    """Skip the request spacing and post-command wait."""
    with (
        patch("custom_components.psaudio_powerplant.api.MIN_REQUEST_GAP", 0),
        patch("custom_components.psaudio_powerplant.switch.POST_COMMAND_DELAY", 0),
    ):
        yield
