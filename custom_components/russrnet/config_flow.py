"""Config flow for Russound RNET (CAM6.6)."""
from __future__ import annotations

import asyncio
import contextlib
from typing import Any

from aiorussound import RussoundTcpConnectionHandler
from aiorussound.exceptions import CommandError
from aiorussound.rnet.client import RussoundRNETClient
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
import homeassistant.helpers.config_validation as cv

from .const import CONF_SOURCES, CONF_ZONES, DEFAULT_NAME, DOMAIN, ZONES_PER_CONTROLLER

RNET_EXCEPTIONS = (
    CommandError,
    ConnectionRefusedError,
    TimeoutError,
    asyncio.IncompleteReadError,
    OSError,
)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_PORT): cv.port,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    }
)


async def _async_test_connection(host: str, port: int) -> None:
    """Raise on failure; used to validate user input."""
    client = RussoundRNETClient(RussoundTcpConnectionHandler(host, port))
    await client.connect()
    with contextlib.suppress(*RNET_EXCEPTIONS):
        await client.disconnect()


class RussoundRnetConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Russound RNET."""

    VERSION = 1

    def __init__(self) -> None:
        self._host: str | None = None
        self._port: int | None = None
        self._name: str = DEFAULT_NAME

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step: host/port/name."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self._host = user_input[CONF_HOST]
            self._port = user_input[CONF_PORT]
            self._name = user_input[CONF_NAME]

            self._async_abort_entries_match({CONF_HOST: self._host, CONF_PORT: self._port})

            try:
                await _async_test_connection(self._host, self._port)
            except RNET_EXCEPTIONS:
                errors["base"] = "cannot_connect"
            else:
                return await self.async_step_zones()

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors
        )

    async def async_step_zones(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Let the user name each of the 6 zones (blank = unused)."""
        errors: dict[str, str] = {}
        if user_input is not None:
            zones = {
                i: user_input[f"zone_{i}"]
                for i in range(1, ZONES_PER_CONTROLLER + 1)
                if user_input.get(f"zone_{i}")
            }
            if not zones:
                errors["base"] = "no_zones"
            else:
                self._zones = zones
                return await self.async_step_sources()

        schema = vol.Schema(
            {
                vol.Optional(f"zone_{i}", default=""): cv.string
                for i in range(1, ZONES_PER_CONTROLLER + 1)
            }
        )
        return self.async_show_form(step_id="zones", data_schema=schema, errors=errors)

    async def async_step_sources(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Let the user name each of the 6 sources (blank = unused)."""
        errors: dict[str, str] = {}
        if user_input is not None:
            sources = [
                user_input[f"source_{i}"]
                for i in range(1, ZONES_PER_CONTROLLER + 1)
                if user_input.get(f"source_{i}")
            ]
            if not sources:
                errors["base"] = "no_sources"
            else:
                return self.async_create_entry(
                    title=self._name,
                    data={
                        CONF_HOST: self._host,
                        CONF_PORT: self._port,
                        CONF_NAME: self._name,
                        CONF_ZONES: self._zones,
                        CONF_SOURCES: sources,
                    },
                )

        schema = vol.Schema(
            {
                vol.Optional(f"source_{i}", default=""): cv.string
                for i in range(1, ZONES_PER_CONTROLLER + 1)
            }
        )
        return self.async_show_form(step_id="sources", data_schema=schema, errors=errors)
