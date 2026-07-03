"""Media player platform for Russound RNET (CAM6.6)."""

from __future__ import annotations

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import RussrnetConfigEntry
from .const import DOMAIN

SUPPORT_RUSSRNET = (
    MediaPlayerEntityFeature.VOLUME_SET
    | MediaPlayerEntityFeature.VOLUME_MUTE
    | MediaPlayerEntityFeature.TURN_ON
    | MediaPlayerEntityFeature.TURN_OFF
    | MediaPlayerEntityFeature.SELECT_SOURCE
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: RussrnetConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Russound zones from a config entry."""
    client = entry.runtime_data

    entities: list[RussrnetZone] = []
    for controller in client.controllers.values():
        for zone_id, zone in controller.zones.items():
            entities.append(RussrnetZone(client, controller, zone_id, zone))

    async_add_entities(entities)


class RussrnetZone(MediaPlayerEntity):
    """Representation of a single Russound zone."""

    _attr_has_entity_name = True
    _attr_supported_features = SUPPORT_RUSSRNET

    def __init__(self, client, controller, zone_id, zone) -> None:
        """Initialize the zone."""
        self._client = client
        self._controller = controller
        self._zone_id = zone_id
        self._zone = zone
        self._attr_unique_id = f"{controller.mac_address}-zone-{zone_id}"
        self._attr_name = zone.name or f"Zone {zone_id}"

    @property
    def state(self) -> MediaPlayerState:
        """Return the state of the zone."""
        if self._zone.is_on:
            return MediaPlayerState.ON
        return MediaPlayerState.OFF

    @property
    def volume_level(self) -> float | None:
        """Volume level of the zone (0..1)."""
        # Russound volume is 0..50; scale to 0..1
        return self._zone.volume / 50

    @property
    def is_volume_muted(self) -> bool | None:
        """Return whether the zone is muted."""
        return getattr(self._zone, "is_mute", None)

    @property
    def source(self) -> str | None:
        """Return the currently selected source."""
        source = self._zone.current_source
        if source is not None:
            return source.name
        return None

    @property
    def source_list(self) -> list[str]:
        """List of available sources."""
        return [src.name for src in self._client.sources.values()]

    async def async_turn_on(self) -> None:
        """Turn the zone on."""
        await self._zone.zone_on()

    async def async_turn_off(self) -> None:
        """Turn the zone off."""
        await self._zone.zone_off()

    async def async_set_volume_level(self, volume: float) -> None:
        """Set the volume (0..1 -> 0..50)."""
        await self._zone.set_volume(int(volume * 50))

    async def async_mute_volume(self, mute: bool) -> None:
        """Mute or unmute the zone."""
        await self._zone.set_mute(mute)

    async def async_select_source(self, source: str) -> None:
        """Select a source by name."""
        for source_id, src in self._client.sources.items():
            if src.name == source:
                await self._zone.select_source(source_id)
                return
