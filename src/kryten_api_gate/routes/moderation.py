"""Moderation routes — kick, ban, mute, shadow-mute, unmute, assign-leader, banlist, unban."""

from fastapi import APIRouter, Depends
from kryten import KrytenClient
from pydantic import BaseModel

from ..auth import verify_api_key
from ..config import Config
from ..deps import get_client, get_config

router = APIRouter(dependencies=[Depends(verify_api_key)])


class KickRequest(BaseModel):
    username: str
    reason: str = ""


class BanRequest(BaseModel):
    username: str
    reason: str = ""


class UserRequest(BaseModel):
    username: str


@router.post("/kick")
async def kick_user(
    body: KickRequest,
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    msg_id = await client.kick_user(
        config.channel, body.username, body.reason, domain=config.domain
    )
    return {"message_id": msg_id}


@router.post("/ban")
async def ban_user(
    body: BanRequest,
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    msg_id = await client.ban_user(
        config.channel, body.username, body.reason, domain=config.domain
    )
    return {"message_id": msg_id}


@router.post("/mute")
async def mute_user(
    body: UserRequest,
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    msg_id = await client.mute_user(config.channel, body.username, domain=config.domain)
    return {"message_id": msg_id}


@router.post("/shadow-mute")
async def shadow_mute_user(
    body: UserRequest,
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    msg_id = await client.shadow_mute_user(config.channel, body.username, domain=config.domain)
    return {"message_id": msg_id}


@router.post("/unmute")
async def unmute_user(
    body: UserRequest,
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    msg_id = await client.unmute_user(config.channel, body.username, domain=config.domain)
    return {"message_id": msg_id}


@router.post("/assign-leader")
async def assign_leader(
    body: UserRequest,
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    msg_id = await client.assign_leader(config.channel, body.username, domain=config.domain)
    return {"message_id": msg_id}


@router.get("/banlist")
async def request_banlist(
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    msg_id = await client.request_banlist(config.channel, domain=config.domain)
    return {"message_id": msg_id}


@router.delete("/ban/{ban_id}")
async def unban(
    ban_id: int,
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    msg_id = await client.unban(config.channel, ban_id, domain=config.domain)
    return {"message_id": msg_id}
