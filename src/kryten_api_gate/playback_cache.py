"""In-memory playback position cache.

Subscribes to NATS mediaUpdate and changeMedia events published by Kryten-Robot
and keeps the latest currentTime / paused values in memory.

The NATS KV store only receives a 'current' entry when the video changes
(changeMedia).  CyTube's frequent mediaUpdate ticks (~every 5 s) are
published to NATS but never written back to KV, so polling KV alone always
returns stale playback position and pause state.

Usage:
    cache = PlaybackCache(client, channel)
    await cache.start()
    ...
    media = await client.get_state_current_media(channel)
    media = cache.overlay(media)   # currentTime / paused now fresh
    ...
    await cache.stop()
"""

import json
import logging
from typing import Any

from kryten import KrytenClient

logger = logging.getLogger("kryten_api_gate.playback_cache")


def _normalize(token: str) -> str:
    """Replicate Kryten-Robot's normalize_token for NATS subject construction."""
    token = token.lower()
    token = token.replace(".", "")
    token = token.replace(" ", "-")
    for ch in "*>!@#$%^&*()+=[]{|}\\:;\"'<>,?/":
        token = token.replace(ch, "")
    return token


class PlaybackCache:
    """Live playback position / pause state maintained via NATS subscriptions."""

    def __init__(self, client: KrytenClient, channel: str) -> None:
        self._client = client
        self._channel_norm = _normalize(channel)
        self._current_time: float | None = None
        self._paused: bool | None = None
        self._subs: list[Any] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def overlay(self, media: dict[str, Any]) -> dict[str, Any]:
        """Return a copy of *media* with fresh currentTime / paused values.

        If no mediaUpdate has been received yet (e.g. nothing is playing, or
        the cache was just reset by a changeMedia) the dict is returned
        unchanged.
        """
        if self._current_time is None:
            return media
        out = dict(media)
        out["currentTime"] = self._current_time
        if self._paused is not None:
            out["paused"] = self._paused
        return out

    async def start(self) -> None:
        """Subscribe to mediaUpdate and changeMedia for the configured channel."""
        prefix = f"kryten.events.cytube.{self._channel_norm}"

        async def on_media_update(msg: Any) -> None:
            try:
                data = json.loads(msg.data.decode())
                payload = data.get("payload", {})
                ct = payload.get("currentTime")
                if ct is not None:
                    self._current_time = float(ct)
                p = payload.get("paused")
                if p is not None:
                    self._paused = bool(p)
                logger.debug(
                    "mediaUpdate: currentTime=%.1f paused=%s",
                    self._current_time,
                    self._paused,
                )
            except Exception as exc:
                logger.warning("Failed to parse mediaUpdate message: %s", exc)

        async def on_change_media(msg: Any) -> None:
            # Reset cache — the KV store will have the new media's starting values.
            # Fresh mediaUpdate messages will refill the cache within a few seconds.
            self._current_time = None
            self._paused = None
            logger.debug("changeMedia received: playback cache reset")

        sub1 = await self._client.subscribe(f"{prefix}.mediaupdate", on_media_update)
        sub2 = await self._client.subscribe(f"{prefix}.changemedia", on_change_media)
        self._subs = [sub1, sub2]
        logger.info("PlaybackCache subscribed on %s.{mediaupdate,changemedia}", prefix)

    async def stop(self) -> None:
        """Unsubscribe from all NATS topics."""
        for sub in self._subs:
            try:
                await self._client.unsubscribe(sub)
            except Exception:
                pass
        self._subs.clear()
        logger.info("PlaybackCache stopped")
