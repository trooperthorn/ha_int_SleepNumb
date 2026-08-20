"""Local hub transport for Sleep Number Local-First.

Talks to the on-hub bridge daemon (bridge/sleepnumber_bridge.py) over the LAN.
This is the *preferred* transport once the hub is rooted: sub-second, no cloud.
Until a bridge is reachable the integration uses the cloud transport, and this
module simply reports itself unavailable.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

import aiohttp

_LOGGER = logging.getLogger(__name__)

DEFAULT_PORT = 8765
DEFAULT_TIMEOUT = 4


@dataclass
class LocalStatus:
    """Snapshot returned by the bridge /status endpoint."""

    sleep_number_left: int | None = None
    sleep_number_right: int | None = None
    in_bed_left: bool | None = None
    in_bed_right: bool | None = None


def _as_int(raw: str | None) -> int | None:
    if raw is None:
        return None
    digits = "".join(ch for ch in str(raw) if ch.isdigit())
    return int(digits) if digits else None


def _as_bool(raw: str | None) -> bool | None:
    if raw is None:
        return None
    text = str(raw).strip().lower()
    if text in ("1", "true", "yes", "in", "inbed", "occupied"):
        return True
    if text in ("0", "false", "no", "out", "empty"):
        return False
    return None


def parse_status(payload: dict) -> LocalStatus:
    """Translate the bridge's raw JSON into a typed snapshot."""
    return LocalStatus(
        sleep_number_left=_as_int(payload.get("sleep_number_left")),
        sleep_number_right=_as_int(payload.get("sleep_number_right")),
        in_bed_left=_as_bool(payload.get("in_bed_left")),
        in_bed_right=_as_bool(payload.get("in_bed_right")),
    )


class LocalBridgeClient:
    """Minimal async client for the on-hub bridge."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        port: int = DEFAULT_PORT,
        token: str | None = None,
    ) -> None:
        self._session = session
        self._base = f"http://{host}:{port}"
        self._headers = {"X-SNB-Token": token} if token else {}

    async def _get(self, path: str) -> dict:
        async with self._session.get(
            f"{self._base}{path}",
            headers=self._headers,
            timeout=aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT),
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def available(self) -> bool:
        """Return True if the bridge answers /health."""
        try:
            data = await self._get("/health")
            return bool(data.get("ok"))
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return False

    async def status(self) -> LocalStatus:
        """Fetch and parse the live status snapshot."""
        return parse_status(await self._get("/status"))
