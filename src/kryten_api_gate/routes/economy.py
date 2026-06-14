"""Economy proxy routes — forwards to kryten-economy via NATS."""

from fastapi import APIRouter, Depends, HTTPException, Query
from kryten import KrytenClient
from pydantic import BaseModel

from ..auth import verify_api_key
from ..config import Config
from ..deps import get_client, get_config

router = APIRouter(dependencies=[Depends(verify_api_key)])


def _unwrap(result: dict) -> dict:
    """Unwrap NATS economy response envelope, raising HTTP 502 on failure."""
    if not result.get("success"):
        raise HTTPException(status_code=502, detail=result.get("error", "economy error"))
    return result.get("data", {})


# ── Phase 1: Balance display ───────────────────────────────────

@router.get("/balance/{username}")
async def get_balance(
    username: str,
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    result = await client.economy_request(
        config.channel, "balance.get", {"username": username}
    )
    return _unwrap(result)


@router.get("/transactions/{username}")
async def get_transactions(
    username: str,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    result = await client.economy_request(
        config.channel,
        "transactions.list",
        {"username": username, "limit": limit, "offset": offset},
    )
    return _unwrap(result)


# ── Account summary & vanity items ─────────────────────────────

@router.get("/account/{username}")
async def get_account_summary(
    username: str,
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    """Full user-facing account snapshot: balance, rank progression, perks, vanity."""
    result = await client.economy_request(
        config.channel, "account.summary", {"username": username}
    )
    return _unwrap(result)


class VanityGreetingRequest(BaseModel):
    username: str
    value: str


@router.post("/vanity/greeting")
async def set_vanity_greeting(
    body: VanityGreetingRequest,
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    """Purchase/update the user's custom greeting."""
    result = await client.economy_request(
        config.channel, "vanity.set_greeting", body.model_dump()
    )
    return _unwrap(result)


class VanityColorRequest(BaseModel):
    username: str
    value: str


@router.post("/vanity/color")
async def set_vanity_color(
    body: VanityColorRequest,
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    """Purchase/update the user's custom chat color (6-digit hex)."""
    result = await client.economy_request(
        config.channel, "vanity.set_color", body.model_dump()
    )
    return _unwrap(result)


# ── Phase 2: Queue spending ────────────────────────────────────

class QueuePreviewRequest(BaseModel):
    username: str
    duration_sec: int
    tier: str = "queue"


@router.post("/queue-preview")
async def queue_preview(
    body: QueuePreviewRequest,
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    result = await client.economy_request(
        config.channel, "spending.queue_preview", body.model_dump()
    )
    return _unwrap(result)


class QueueSpendRequest(BaseModel):
    username: str
    duration_sec: int
    tier: str = "queue"
    request_id: str


@router.post("/queue-spend")
async def queue_spend(
    body: QueueSpendRequest,
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    result = await client.economy_request(
        config.channel, "spending.queue", body.model_dump()
    )
    return _unwrap(result)


class QueueRefundRequest(BaseModel):
    username: str
    request_id: str
    reason: str


@router.post("/queue-refund")
async def queue_refund(
    body: QueueRefundRequest,
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    result = await client.economy_request(
        config.channel, "spending.queue_refund", body.model_dump()
    )
    return _unwrap(result)
