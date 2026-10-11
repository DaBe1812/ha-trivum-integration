"""DataUpdateCoordinator für trivum."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import TrivumApi, TrivumError
from .const import DOMAIN, LIST_PATHS, SCAN_INTERVAL_SECONDS

_LOGGER = logging.getLogger(__name__)

type TrivumConfigEntry = ConfigEntry[TrivumCoordinator]


class TrivumCoordinator(DataUpdateCoordinator[dict[int, dict[str, Any]]]):
    """Fragt alle Zonen zyklisch ab."""

    config_entry: TrivumConfigEntry

    def __init__(self, hass: HomeAssistant, entry: TrivumConfigEntry, api: TrivumApi) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL_SECONDS),
        )
        self.api = api
        # source name -> short name for set.xml (z.B. "Favorit: Radio" -> "f1")
        self.sources: dict[str, str] = {}

    async def _async_setup(self) -> None:
        """Einmalig: Quellenlisten laden."""
        for kind in LIST_PATHS:
            for name, short in await self.api.get_list(kind):
                key = f"{kind}: {name}"
                if key in self.sources:  # doppelte Namen unterscheidbar halten
                    key = f"{key} ({short})"
                self.sources[key] = short

    async def _async_update_data(self) -> dict[int, dict[str, Any]]:
        try:
            zones = await self.api.get_zones()
            details = await asyncio.gather(*(self.api.get_zone(z["id"]) for z in zones))
        except TrivumError as err:
            raise UpdateFailed(str(err)) from err
        result: dict[int, dict[str, Any]] = {}
        for zone, detail in zip(zones, details, strict=True):
            result[zone["id"]] = {**zone, **detail}
        return result
