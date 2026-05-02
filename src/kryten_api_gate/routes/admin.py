"""Admin routes — MOTD, CSS, JS, options, permissions, ranks, channel log."""

from fastapi import APIRouter, Depends
from kryten import KrytenClient
from pydantic import BaseModel

from ..auth import verify_api_key
from ..config import Config
from ..deps import get_client, get_config

router = APIRouter(dependencies=[Depends(verify_api_key)])


class MotdRequest(BaseModel):
    motd: str


class CssRequest(BaseModel):
    css: str


class JsRequest(BaseModel):
    js: str


class OptionsRequest(BaseModel):
    options: dict


class PermissionsRequest(BaseModel):
    permissions: dict


class SetRankRequest(BaseModel):
    username: str
    rank: int


# --- MOTD ---


@router.get("/motd")
async def get_motd(
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    motd = await client.get_state_motd(config.channel, domain=config.domain)
    return {"motd": motd}


@router.put("/motd")
async def set_motd(
    body: MotdRequest,
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    msg_id = await client.set_motd(config.channel, body.motd, domain=config.domain)
    return {"message_id": msg_id}


# --- CSS ---


@router.get("/css")
async def get_channel_css(
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    css = await client.get_state_channel_css(config.channel, domain=config.domain)
    return {"css": css}


@router.put("/css")
async def set_channel_css(
    body: CssRequest,
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    msg_id = await client.set_channel_css(config.channel, body.css, domain=config.domain)
    return {"message_id": msg_id}


# --- JS ---


@router.get("/js")
async def get_channel_js(
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    js = await client.get_state_channel_js(config.channel, domain=config.domain)
    return {"js": js}


@router.put("/js")
async def set_channel_js(
    body: JsRequest,
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    msg_id = await client.set_channel_js(config.channel, body.js, domain=config.domain)
    return {"message_id": msg_id}


# --- Options ---


@router.get("/options")
async def get_options(
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    options = await client.get_state_channel_options(config.channel, domain=config.domain)
    return {"options": options}


@router.put("/options")
async def set_options(
    body: OptionsRequest,
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    msg_id = await client.set_options(config.channel, body.options, domain=config.domain)
    return {"message_id": msg_id}


# --- Permissions ---


@router.get("/permissions")
async def get_permissions(
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    permissions = await client.get_state_channel_permissions(
        config.channel, domain=config.domain
    )
    return {"permissions": permissions}


@router.put("/permissions")
async def set_permissions(
    body: PermissionsRequest,
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    msg_id = await client.set_permissions(
        config.channel, body.permissions, domain=config.domain
    )
    return {"message_id": msg_id}


# --- Ranks ---


@router.get("/ranks")
async def request_channel_ranks(
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    msg_id = await client.request_channel_ranks(config.channel, domain=config.domain)
    return {"message_id": msg_id}


@router.put("/rank")
async def set_channel_rank(
    body: SetRankRequest,
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    msg_id = await client.set_channel_rank(
        config.channel, body.username, body.rank, domain=config.domain
    )
    return {"message_id": msg_id}


# --- Channel Log ---


@router.get("/log")
async def read_chan_log(
    count: int = 100,
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    msg_id = await client.read_chan_log(config.channel, count, domain=config.domain)
    return {"message_id": msg_id}
