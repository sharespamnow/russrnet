"""Media player platform for Russound RNET (CAM6.6)."""
from __future__ import annotations

import contextlib
import logging
import math
from collections.abc import Callable, Coroutine
from typing import Any

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import RNET_EXCEPTIONS, RussoundRnetConfigEntry
from .const import CONF_SOURCES, CONF_ZONES, MAX_VOLUME

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: RussoundRnetConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Russound RNET media players from a config entry."""
    data = entry.runtime_data
    zones: dict[int, str] = entry.data[CONF_ZONES]
    sources: list[str] = entry.data[CONF_SOURCES]

    async_add_entities(
        [
            RussoundRnetZone(data.client, data.lock, sources, zone_id, name, entry.entry_id)
            for zone_id, name in zones.items()
        ],
        True,
    )


class RussoundRnetZone(MediaPlayerEntity):
    """Representation of a single RNET zone as a media player."""

    _attr_supported_features = (
        MediaPlayerEntityFeature.VOLUME_MUTE
        | MediaPlayerEntityFeature.VOLUME_SET
        | MediaPlayerEntityFeature.TURN_ON
        | MediaPlayerEntityFeature.TURN_OFF
        | MediaPlayerEntityFeature.SELECT_SOURCE
    )
    _attr_has_entity_name = False

    def __init__(self, client, lock, sources, zone_id, name, entry_id) -> None:
        self._attr_name = name
        self._attr_unique_id = f"{entry_id}_zone_{zone_id}"
        self._client = client
        self._lock = lock
        self._attr_source_list = sources
        self._controller_id = math.ceil(zone_id / 6)
        self._zone_id = (zone_id - 1) % 6 + 1

    async def _async_ensure_connected(self) -> None:
        if not self._client.is_connected:
            _LOGGER.debug("Reconnecting RNET client")
            await self._client.connect()

    async def _async_run_with_retry(
        self, command: Callable[[], Coroutine[Any, Any, Any]]
    ) -> None:
        async with self._lock:
            try:
                await self._async_ensure_connected()
                await command()
            except RNET_EXCEPTIONS:
                with contextlib.suppress(*RNET_EXCEPTIONS):
                    await self._client.disconnect()
                try:
                    await self._async_ensure_connected()
                    await command()
                except RNET_EXCEPTIONS:
                    _LOGGER.error(
                        "Command failed for zone %s on controller %s after retry",
                        self._zone_id,
                        self._controller_id,
                    )

    async def async_update(self) -> None:
        """Retrieve latest state via polling."""
        async with self._lock:
            try:
                await self._async_ensure_connected()
                info = await self._client.get_all_zone_info(
                    self._controller_id, self._zone_id
                )
            except RNET_EXCEPTIONS:
                with contextlib.suppress(*RNET_EXCEPTIONS):
                    await self._client.disconnect()
                try:
                    await self._async_ensure_connected()
                    info = await self._client.get_all_zone_info(
                        self._controller_id, self._zone_id
                    )
                except RNET_EXCEPTIONS:
                    _LOGGER.error(
                        "Could not update zone %s on controller %s",
                        self._zone_id,
                        self._controller_id,
                    )
                    self._attr_available = False
                    return

        self._attr_available = True
        self._attr_state = (
            MediaPlayerState.ON if info.power else MediaPlayerState.OFF
        )
        self._attr_volume_level = info.volume / MAX_VOLUME
        index = info.source - 1
        if self.source_list and 0 <= index < len(self.source_list):
            self._attr_source = self.source_list[index]

    async def async_set_volume_level(self, volume: float) -> None:
        device_volume = max(0, min(MAX_VOLUME, int(volume * MAX_VOLUME)))
        await self._async_run_with_retry(
            lambda: self._client.set_volume(
                self._controller_id, self._zone_id, device_volume
            )
        )

    async def async_turn_on(self) -> None:
        await self._async_run_with_retry(
            lambda: self._client.set_zone_power(
                self._controller_id, self._zone_id, True
            )
        )

    async def async_turn_off(self) -> None:
        await self._async_run_with_retry(
            lambda: self._client.set_zone_power(
                self._controller_id, self._zone_id, False
            )
        )

    async def async_mute_volume(self, mute: bool) -> None:
        async def _mute_if_needed() -> None:
            if self.is_volume_muted != mute:
                await self._client.toggle_mute(self._controller_id, self._zone_id)

        await self._async_run_with_retry(_mute_if_needed)

    async def async_select_source(self, source: str) -> None:
        if self.source_list and source in self.source_list:
            index = self.source_list.index(source) + 1
            await self._async_run_with_retry(
                lambda: self._client.select_source(
                    self._controller_id, self._zone_id, index
                )
            )
