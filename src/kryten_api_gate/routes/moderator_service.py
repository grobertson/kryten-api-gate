"""Moderator service routes — proxies commands to kryten-moderator via NATS.

Exposes two routers:
  channels_router — channel-scoped moderation/pattern/user endpoints
                    (register at prefix /api/v1/channels)
  system_router   — moderator service status endpoints
                    (register at prefix /api/v1/moderator)
"""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from kryten import KrytenClient
from pydantic import BaseModel

from ..auth import verify_api_key
from ..deps import get_client

NATS_SUBJECT = "kryten.moderator.command"
NATS_TIMEOUT = 10.0

# ── auth dependency applied to both routers ────────────────────────────────────
_auth = [Depends(verify_api_key)]

channels_router = APIRouter(dependencies=_auth)
system_router = APIRouter(dependencies=_auth)


# ── helper ─────────────────────────────────────────────────────────────────────

async def _call(client: KrytenClient, payload: dict) -> dict:
    """Send a request to kryten-moderator and return the `data` dict.

    Raises:
        HTTPException 503 — moderator did not respond within the timeout.
        HTTPException 400 — request rejected due to missing/invalid fields.
        HTTPException 404 — requested resource was not found.
        HTTPException 500 — any other moderator-side error.
    """
    try:
        response = await client.nats_request(NATS_SUBJECT, payload, timeout=NATS_TIMEOUT)
    except TimeoutError as exc:
        raise HTTPException(
            status_code=503, detail="Moderator service unavailable (timeout)"
        ) from exc

    if not response.get("success"):
        error: str = response.get("error", "Unknown error")
        low = error.lower()
        if "required" in low or "must be" in low or "invalid" in low:
            raise HTTPException(status_code=400, detail=error)
        if "not found" in low or "not in" in low:
            raise HTTPException(status_code=404, detail=error)
        raise HTTPException(status_code=500, detail=error)

    return response.get("data", {})


# ── request bodies ─────────────────────────────────────────────────────────────

class EntryAddRequest(BaseModel):
    username: str
    action: Literal["ban", "smute", "mute"]
    domain: str | None = None
    reason: str | None = None
    moderator: str | None = None


class PatternAddRequest(BaseModel):
    pattern: str
    domain: str | None = None
    is_regex: bool = False
    action: Literal["ban", "smute", "mute"] = "ban"
    description: str | None = None
    added_by: str | None = None


# ── channel-scoped routes ──────────────────────────────────────────────────────

@channels_router.get("/{channel}/moderation", tags=["moderator"])
async def list_moderation_entries(
    channel: str,
    domain: Annotated[str | None, Query()] = None,
    action_filter: Annotated[
        Literal["ban", "smute", "mute"] | None, Query(alias="filter")
    ] = None,
    client: KrytenClient = Depends(get_client),
) -> dict:
    """List all moderation entries for a channel."""
    payload: dict = {"command": "entry.list", "channel": channel}
    if domain is not None:
        payload["domain"] = domain
    if action_filter is not None:
        payload["filter"] = action_filter
    return await _call(client, payload)


@channels_router.post("/{channel}/moderation", status_code=201, tags=["moderator"])
async def add_moderation_entry(
    channel: str,
    body: EntryAddRequest,
    client: KrytenClient = Depends(get_client),
) -> dict:
    """Add a user to the moderation list (or replace an existing entry)."""
    payload: dict = {
        "command": "entry.add",
        "channel": channel,
        "username": body.username,
        "action": body.action,
    }
    if body.domain is not None:
        payload["domain"] = body.domain
    if body.reason is not None:
        payload["reason"] = body.reason
    if body.moderator is not None:
        payload["moderator"] = body.moderator
    return await _call(client, payload)


@channels_router.get("/{channel}/moderation/{username}", tags=["moderator"])
async def get_moderation_entry(
    channel: str,
    username: str,
    domain: Annotated[str | None, Query()] = None,
    client: KrytenClient = Depends(get_client),
) -> dict:
    """Get the moderation entry for a specific user."""
    payload: dict = {"command": "entry.get", "channel": channel, "username": username}
    if domain is not None:
        payload["domain"] = domain
    return await _call(client, payload)


@channels_router.delete("/{channel}/moderation/{username}", tags=["moderator"])
async def remove_moderation_entry(
    channel: str,
    username: str,
    domain: Annotated[str | None, Query()] = None,
    client: KrytenClient = Depends(get_client),
) -> dict:
    """Remove a user from the moderation list."""
    payload: dict = {"command": "entry.remove", "channel": channel, "username": username}
    if domain is not None:
        payload["domain"] = domain
    return await _call(client, payload)


@channels_router.get("/{channel}/patterns", tags=["moderator"])
async def list_patterns(
    channel: str,
    domain: Annotated[str | None, Query()] = None,
    client: KrytenClient = Depends(get_client),
) -> dict:
    """List all banned username patterns for a channel."""
    payload: dict = {"command": "pattern.list", "channel": channel}
    if domain is not None:
        payload["domain"] = domain
    return await _call(client, payload)


@channels_router.post("/{channel}/patterns", status_code=201, tags=["moderator"])
async def add_pattern(
    channel: str,
    body: PatternAddRequest,
    client: KrytenClient = Depends(get_client),
) -> dict:
    """Register a banned username pattern."""
    payload: dict = {
        "command": "pattern.add",
        "channel": channel,
        "pattern": body.pattern,
        "is_regex": body.is_regex,
        "action": body.action,
    }
    if body.domain is not None:
        payload["domain"] = body.domain
    if body.description is not None:
        payload["description"] = body.description
    if body.added_by is not None:
        payload["added_by"] = body.added_by
    return await _call(client, payload)


@channels_router.delete("/{channel}/patterns/{pattern}", tags=["moderator"])
async def remove_pattern(
    channel: str,
    pattern: str,
    domain: Annotated[str | None, Query()] = None,
    client: KrytenClient = Depends(get_client),
) -> dict:
    """Remove a registered banned username pattern."""
    payload: dict = {"command": "pattern.remove", "channel": channel, "pattern": pattern}
    if domain is not None:
        payload["domain"] = domain
    return await _call(client, payload)


@channels_router.get("/{channel}/users/recent", tags=["moderator"])
async def list_recent_users(
    channel: str,
    domain: Annotated[str | None, Query()] = None,
    window_minutes: Annotated[float | None, Query(gt=0)] = None,
    client: KrytenClient = Depends(get_client),
) -> dict:
    """List users seen in a channel within a rolling time window."""
    payload: dict = {"command": "users.recent", "channel": channel}
    if domain is not None:
        payload["domain"] = domain
    if window_minutes is not None:
        payload["window_minutes"] = window_minutes
    return await _call(client, payload)


# ── moderator system routes ────────────────────────────────────────────────────

@system_router.get("/ping", tags=["moderator"])
async def moderator_ping(client: KrytenClient = Depends(get_client)) -> dict:
    """Liveness check for the kryten-moderator service."""
    return await _call(client, {"command": "system.ping"})


@system_router.get("/health", tags=["moderator"])
async def moderator_health(client: KrytenClient = Depends(get_client)) -> dict:
    """Health status of the kryten-moderator service."""
    return await _call(client, {"command": "system.health"})


@system_router.get("/stats", tags=["moderator"])
async def moderator_stats(client: KrytenClient = Depends(get_client)) -> dict:
    """Runtime statistics from the kryten-moderator service."""
    return await _call(client, {"command": "system.stats"})
