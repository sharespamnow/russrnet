"""The Russound RNET (CAM6.6) integration."""
from __future__ import annotations

import asyncio
import contextlib
import logging

from aiorussound import RussoundTcpConnectionHandler
from aiorussound.exceptions import CommandError
from aiorussound.rnet.client import RussoundRNETClient

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.MEDIA_PLAYER]

RNET_EXCEPTIONS = (
    CommandError,
    ConnectionRefusedError,
    TimeoutError,
    asyncio.IncompleteReadError,
    OSError,
)


class RussoundRnetData:
    """Runtime data shared across entities for one config entry."""

    def __init__(self, client: RussoundRNETClient) -> None:
        self.client = client
        self.lock = asyncio.Lock()


type RussoundRnetConfigEntry = ConfigEntry[RussoundRnetData]


async def async_setup_entry(hass: HomeAssistant, entry: RussoundRnetConfigEntry) -> bool:
    """Set up Russound RNET from a config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]

    client = RussoundRNETClient(RussoundTcpConnectionHandler(host, port))

    try:
        await client.connect()
    except RNET_EXCEPTIONS as err:
        raise ConfigEntryNotReady(
            f"Could not connect to Russound RNET at {host}:{port}"
        ) from err

    entry.runtime_data = RussoundRnetData(client)

    async def _async_disconnect(*_: object) -> None:
        with contextlib.suppress(*RNET_EXCEPTIONS):
            await client.disconnect()

    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _async_disconnect)
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: RussoundRnetConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        data = entry.runtime_data
        with contextlib.suppress(*RNET_EXCEPTIONS):
            await data.client.disconnect()
    return unload_ok
