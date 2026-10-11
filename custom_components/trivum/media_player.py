"""media_player-Plattform: eine Entität pro trivum-Zone."""
from __future__ import annotations

from typing import Any

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import const as c
from .coordinator import TrivumConfigEntry, TrivumCoordinator

BUILTIN_SOURCES = {
    "Line-In": ("cmd", c.CMD_DEFAULT_LINEIN),
    "Tuner (UKW)": ("cmd", c.CMD_DEFAULT_TUNER),
    "Streaming": ("cmd", c.CMD_DEFAULT_STREAMING),
}

FEATURES = (
    MediaPlayerEntityFeature.TURN_ON
    | MediaPlayerEntityFeature.TURN_OFF
    | MediaPlayerEntityFeature.VOLUME_SET
    | MediaPlayerEntityFeature.VOLUME_STEP
    | MediaPlayerEntityFeature.VOLUME_MUTE
    | MediaPlayerEntityFeature.SELECT_SOURCE
    | MediaPlayerEntityFeature.NEXT_TRACK
    | MediaPlayerEntityFeature.PREVIOUS_TRACK
    | MediaPlayerEntityFeature.PLAY
    | MediaPlayerEntityFeature.PAUSE
    | MediaPlayerEntityFeature.STOP
)


async def async_setup_entry(
    hass: HomeAssistant, entry: TrivumConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        TrivumZone(coordinator, entry.entry_id, zone_id) for zone_id in coordinator.data
    )


class TrivumZone(CoordinatorEntity[TrivumCoordinator], MediaPlayerEntity):
    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_features = FEATURES
    _attr_media_content_type = MediaType.MUSIC

    def __init__(self, coordinator: TrivumCoordinator, entry_id: str, zone_id: int) -> None:
        super().__init__(coordinator)
        self._zone_id = zone_id
        self._attr_unique_id = f"{entry_id}_{zone_id}"
        self._muted: bool | None = None  # API liefert keinen Mute-Status -> optimistisch
        zone = coordinator.data[zone_id]
        self._attr_device_info = DeviceInfo(
            identifiers={(c.DOMAIN, self._attr_unique_id)},
            name=zone["name"],
            manufacturer="trivum technologies",
            model="Multiroom-Zone",
            configuration_url=coordinator.api.base_url,
        )

    # ---------- Zustand ----------
    @property
    def _data(self) -> dict[str, Any]:
        return self.coordinator.data.get(self._zone_id, {})

    @property
    def available(self) -> bool:
        return super().available and self._zone_id in self.coordinator.data

    @property
    def state(self) -> MediaPlayerState:
        d = self._data
        if not d.get("power"):
            return MediaPlayerState.OFF
        if d.get("stream_status") == 5:
            return MediaPlayerState.PLAYING
        return MediaPlayerState.ON

    @property
    def volume_level(self) -> float | None:
        vol = self._data.get("volume")
        return None if vol is None else vol / 100

    @property
    def is_volume_muted(self) -> bool | None:
        return self._muted

    @property
    def media_artist(self) -> str | None:
        return self._data.get("artist")

    @property
    def media_album_name(self) -> str | None:
        return self._data.get("album")

    @property
    def media_title(self) -> str | None:
        return self._data.get("track")

    @property
    def media_image_url(self) -> str | None:
        url = self._data.get("image_url")
        if url and url.startswith("/"):
            url = self.coordinator.api.base_url + url
        return url

    @property
    def media_duration(self) -> int | None:
        return self._data.get("stream_length") or None

    @property
    def media_position(self) -> int | None:
        return self._data.get("stream_position") if self._data.get("stream_length") else None

    @property
    def source_list(self) -> list[str]:
        return [*BUILTIN_SOURCES, *self.coordinator.sources]

    # ---------- Steuerung ----------
    async def _cmd(self, command: int) -> None:
        await self.coordinator.api.run_command(self._zone_id, command)
        await self.coordinator.async_request_refresh()

    async def async_turn_on(self) -> None:
        await self._cmd(c.CMD_POWER_ON)

    async def async_turn_off(self) -> None:
        await self._cmd(c.CMD_POWER_OFF)

    async def async_set_volume_level(self, volume: float) -> None:
        await self.coordinator.api.set_volume(self._zone_id, round(volume * 100))
        await self.coordinator.async_request_refresh()

    async def async_volume_up(self) -> None:
        await self._cmd(c.CMD_VOLUME_INC)

    async def async_volume_down(self) -> None:
        await self._cmd(c.CMD_VOLUME_DEC)

    async def async_mute_volume(self, mute: bool) -> None:
        self._muted = mute
        await self._cmd(c.CMD_MUTE_ON if mute else c.CMD_MUTE_OFF)

    async def async_media_next_track(self) -> None:
        await self._cmd(c.CMD_NEXT)

    async def async_media_previous_track(self) -> None:
        await self._cmd(c.CMD_PREV)

    async def async_media_play(self) -> None:
        await self._cmd(c.CMD_PLAY)

    async def async_media_pause(self) -> None:
        await self._cmd(c.CMD_PAUSE)

    async def async_media_stop(self) -> None:
        await self._cmd(c.CMD_STOP)

    async def async_select_source(self, source: str) -> None:
        if source in BUILTIN_SOURCES:
            await self._cmd(BUILTIN_SOURCES[source][1])
            return
        short = self.coordinator.sources.get(source)
        if short is None:
            return
        await self.coordinator.api.set_source(self._zone_id, short)
        await self.coordinator.async_request_refresh()
