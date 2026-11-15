"""Config and options flow for the PowerPlant."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import format_mac

from .api import PowerPlantClient, PowerPlantConnectionError, PowerPlantResponseError
from .const import (
    CONF_SCAN_INTERVAL,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)
from .coordinator import PowerPlantConfigEntry

_LOGGER = logging.getLogger(__name__)

USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
    }
)


class PowerPlantConfigFlow(ConfigFlow, domain=DOMAIN):
    """Add a PowerPlant by host, checked with one status read."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            client = PowerPlantClient(async_get_clientsession(self.hass), host)
            try:
                status = await client.async_get_status()
            except PowerPlantConnectionError:
                errors["base"] = "cannot_connect"
            except PowerPlantResponseError:
                errors["base"] = "not_powerplant"
            except Exception:
                _LOGGER.exception("Unexpected error while checking %s", host)
                errors["base"] = "unknown"
            else:
                if status.mac is None:
                    errors["base"] = "no_mac"
                else:
                    await self.async_set_unique_id(format_mac(status.mac))
                    self._abort_if_unique_id_configured(updates={CONF_HOST: host})
                    return self.async_create_entry(
                        title=user_input[CONF_NAME].strip() or DEFAULT_NAME,
                        data={CONF_HOST: host},
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(USER_SCHEMA, user_input),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: PowerPlantConfigEntry) -> OptionsFlow:
        return PowerPlantOptionsFlow()


class PowerPlantOptionsFlow(OptionsFlow):
    """Change how often the unit is polled."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        current = self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        schema = vol.Schema(
            {
                vol.Required(CONF_SCAN_INTERVAL, default=current): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL),
                )
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
