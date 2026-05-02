"""Playback routes — pause, play, seek, voteskip, next."""

from fastapi import APIRouter, Depends
from kryten import KrytenClient
from pydantic import BaseModel

from ..auth import verify_api_key
from ..config import Config
from ..deps import get_client, get_config

router = APIRouter(dependencies=[Depends(verify_api_key)])


class SeekRequest(BaseModel):
    time_seconds: float


@router.post("/pause")
async def pause(
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    msg_id = await client.pause(config.channel, domain=config.domain)
    return {"message_id": msg_id}


@router.post("/play")
async def play(
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    msg_id = await client.play(config.channel, domain=config.domain)
    return {"message_id": msg_id}


@router.post("/seek")
async def seek(
    body: SeekRequest,
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    msg_id = await client.seek(config.channel, body.time_seconds, domain=config.domain)
    return {"message_id": msg_id}


@router.post("/voteskip")
async def voteskip(
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    msg_id = await client.voteskip(config.channel, domain=config.domain)
    return {"message_id": msg_id}


@router.post("/next")
async def play_next(
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    msg_id = await client.play_next(config.channel, domain=config.domain)
    return {"message_id": msg_id}
