"""Playlist routes — add, delete, move, jump, clear, shuffle, set_temp."""

from fastapi import APIRouter, Depends
from kryten import KrytenClient
from pydantic import BaseModel

from ..auth import verify_api_key
from ..config import Config
from ..deps import get_client, get_config

router = APIRouter(dependencies=[Depends(verify_api_key)])


class AddMediaRequest(BaseModel):
    type: str
    id: str
    position: str = "end"
    temp: bool = True


class MoveMediaRequest(BaseModel):
    position: int


class SetTempRequest(BaseModel):
    is_temp: bool = True


@router.post("/add")
async def add_media(
    body: AddMediaRequest,
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    msg_id = await client.add_media(
        config.channel,
        body.type,
        body.id,
        position=body.position,
        temp=body.temp,
        domain=config.domain,
    )
    return {"message_id": msg_id}


@router.delete("/{uid}")
async def delete_media(
    uid: int,
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    msg_id = await client.delete_media(config.channel, uid, domain=config.domain)
    return {"message_id": msg_id}


@router.put("/{uid}/move")
async def move_media(
    uid: int,
    body: MoveMediaRequest,
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    msg_id = await client.move_media(
        config.channel, uid, body.position, domain=config.domain
    )
    return {"message_id": msg_id}


@router.post("/{uid}/jump")
async def jump_to(
    uid: int,
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    msg_id = await client.jump_to(config.channel, uid, domain=config.domain)
    return {"message_id": msg_id}


@router.delete("/")
async def clear_playlist(
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    msg_id = await client.clear_playlist(config.channel, domain=config.domain)
    return {"message_id": msg_id}


@router.post("/shuffle")
async def shuffle_playlist(
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    msg_id = await client.shuffle_playlist(config.channel, domain=config.domain)
    return {"message_id": msg_id}


@router.put("/{uid}/temp")
async def set_temp(
    uid: int,
    body: SetTempRequest,
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    msg_id = await client.set_temp(config.channel, uid, body.is_temp, domain=config.domain)
    return {"message_id": msg_id}
