"""Config flow for the Russound RNET (CAM6.6) integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from aiorussound import RussoundClient, RussoundTcpConnectionHandler

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT

from .const import DEFAULT_NAME, DEFAULT_PORT, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
    }
)


class RussrnetConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Russound RNET."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]

            await self.async_set_unique_id(f"{host}:{port}")
            self._abort_if_unique_id_configured()

            client = RussoundClient(RussoundTcpConnectionHandler(host, port))
            try:
                await client.connect()
                await client.disconnect()
            except Exception:
                _LOGGER.exception("Cannot connect to %s:%s", host, port)
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=DEFAULT_NAME, data=user_input
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
