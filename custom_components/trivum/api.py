"""Kleiner async-Client für die trivum HTTP/XML-Schnittstelle."""
from __future__ import annotations

import asyncio
import logging
import re
import xml.etree.ElementTree as ET
from typing import Any
from urllib.parse import unquote

import aiohttp
from yarl import URL

from .const import LIST_PATHS

_LOGGER = logging.getLogger(__name__)

NAME_TAGS = ("info1", "name", "title", "text", "description")


class TrivumError(Exception):
    """Allgemeiner Fehler."""


class TrivumConnectionError(TrivumError):
    """Server nicht erreichbar."""


def _int(value: str | None, default: int | None = None) -> int | None:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


class TrivumApi:
    """Zugriff auf einen trivum-Server."""

    def __init__(self, session: aiohttp.ClientSession, host: str, port: int = 80) -> None:
        self._session = session
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"

    async def _get(self, path: str) -> str:
        # encoded=True: '@' und flag-artige Parameter (&now) unverändert senden
        url = URL(self.base_url + path, encoded=True)
        try:
            async with asyncio.timeout(10):
                async with self._session.get(url) as resp:
                    resp.raise_for_status()
                    return await resp.text()
        except (aiohttp.ClientError, TimeoutError) as err:
            raise TrivumConnectionError(f"Verbindung zu {self.host} fehlgeschlagen: {err}") from err

    async def _get_xml(self, path: str) -> ET.Element:
        text = await self._get(path)
        try:
            return ET.fromstring(text)
        except ET.ParseError as err:
            raise TrivumError(f"Ungültige XML-Antwort von {path}") from err

    # ---------- Zonen ----------
    async def get_zones(self) -> list[dict[str, Any]]:
        """/xml/zone/getAll.xml"""
        root = await self._get_xml("/xml/zone/getAll.xml")
        zones: list[dict[str, Any]] = []
        for z in root.iter("zone"):
            zid = _int(z.findtext("id"))
            if zid is None:
                continue
            zones.append(
                {
                    "id": zid,
                    "name": (z.findtext("description") or f"Zone {zid + 1}").strip(),
                    "power": (z.findtext("status") or "off").strip().lower() == "on",
                    "volume": _int(z.findtext("volume"), 0),
                    "groupmaster": _int(z.findtext("groupmaster")),
                }
            )
        if not zones:
            raise TrivumError("Keine Zonen in getAll.xml gefunden")
        return zones

    async def get_zone(self, zone_id: int) -> dict[str, Any]:
        """/xml/zone/get.xml mit Quelleninfos."""
        root = await self._get_xml(
            f"/xml/zone/get.xml?zone=@{zone_id}&addSourceBasicData&addSourceStatusData"
        )
        rt = root.find(".//runtime")
        if rt is None:
            rt = root
        src = rt.find("source/status")
        data: dict[str, Any] = {
            "power": (rt.findtext("status") or "off").strip().lower() == "on",
            "volume": _int(rt.findtext("volume"), 0),
        }
        if src is not None:
            data.update(
                {
                    "artist": src.findtext("artist") or None,
                    "album": src.findtext("album") or None,
                    "track": src.findtext("track") or None,
                    "service": src.findtext("service") or None,
                    "image_url": src.findtext("imageURL") or None,
                    "stream_status": _int(src.findtext("streamStatus")),
                    "stream_length": _int(src.findtext("streamLength")),
                    "stream_position": _int(src.findtext("streamPosition")),
                }
            )
        return data

    # ---------- Steuerung ----------
    async def run_command(self, zone_id: int, command: int) -> None:
        await self._get(f"/xml/zone/runCommand.xml?zone=@{zone_id}&command={command}")

    async def set_volume(self, zone_id: int, volume: int) -> None:
        volume = max(0, min(100, volume))
        await self._get(f"/xml/zone/set.xml?zone=@{zone_id}&volume={volume}")

    async def set_source(self, zone_id: int, short_name: str) -> None:
        """short_name z.B. 'f2', 'y1', 'i5', 'a1', 'p3'."""
        await self._get(f"/xml/zone/set.xml?zone=@{zone_id}&source=@{short_name}")

    # ---------- Quellenlisten ----------
    async def get_list(self, kind: str) -> list[tuple[str, str]]:
        """Favoriten/Playlists/TuneIn -> Liste aus (Anzeigename, Kurzname für set.xml)."""
        path, prefix = LIST_PATHS[kind]
        try:
            root = await self._get_xml(path)
        except TrivumError as err:
            _LOGGER.debug("Liste %s nicht abrufbar: %s", kind, err)
            return []
        items: list[tuple[str, str]] = []
        for row in root.iter("row"):
            name = next((row.findtext(t) for t in NAME_TAGS if row.findtext(t)), None)
            name = unquote((name or "").strip()).strip()
            # Kurzname bevorzugt aus der action-URL (z.B. ".../set.xml?source=@f1")
            match = re.search(r"source=@(\w+)", row.findtext("action") or "")
            number = _int(row.findtext("number"), len(items))
            short = match.group(1) if match else f"{prefix}{number + 1}"
            items.append((name or f"{kind} {len(items) + 1}", short))
        return items
