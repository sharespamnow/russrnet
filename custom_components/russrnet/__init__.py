"""The Russound RNET (CAM6.6) integration."""

from __future__ import annotations

from aiorussound import RussoundClient, RussoundTcpConnectionHandler

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN

PLATFORMS: list[Platform] = [Platform.MEDIA_PLAYER]

type RussrnetConfigEntry = ConfigEntry[RussoundClient]


async def async_setup_entry(hass: HomeAssistant, entry: RussrnetConfigEntry) -> bool:
    """Set up Russound RNET from a config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]

    client = RussoundClient(RussoundTcpConnectionHandler(host, port))

    try:
        await client.connect()
    except Exception as err:
        raise ConfigEntryNotReady(f"Cannot connect to {host}:{port}") from err

    entry.runtime_data = client

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: RussrnetConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        await entry.runtime_data.disconnect()
    return unload_ok
