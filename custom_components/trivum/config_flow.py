"""Config Flow: IP/Hostname eingeben, Verbindung testen."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import TrivumApi, TrivumConnectionError, TrivumError
from .const import CONF_HOST, CONF_PORT, DEFAULT_PORT, DOMAIN


class TrivumConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            port = user_input[CONF_PORT]
            await self.async_set_unique_id(f"{host}:{port}")
            self._abort_if_unique_id_configured()

            api = TrivumApi(async_get_clientsession(self.hass), host, port)
            try:
                zones = await api.get_zones()
            except TrivumConnectionError:
                errors["base"] = "cannot_connect"
            except TrivumError:
                errors["base"] = "invalid_response"
            else:
                return self.async_create_entry(
                    title=f"trivum ({host}) – {len(zones)} Zonen",
                    data={CONF_HOST: host, CONF_PORT: port},
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=(user_input or {}).get(CONF_HOST, "")): str,
                vol.Required(CONF_PORT, default=(user_input or {}).get(CONF_PORT, DEFAULT_PORT)): int,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
