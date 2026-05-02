"""Emotes routes — update, remove, bulk import/export emotes."""

from fastapi import APIRouter, Depends
from kryten import KrytenClient
from pydantic import BaseModel

from ..auth import verify_api_key
from ..config import Config
from ..deps import get_client, get_config

router = APIRouter(dependencies=[Depends(verify_api_key)])


class UpdateEmoteRequest(BaseModel):
    image: str
    source: str = "imgur"


class EmoteImportItem(BaseModel):
    name: str
    image: str
    source: str = "imgur"


class BulkImportRequest(BaseModel):
    emotes: list[EmoteImportItem]


@router.get("/")
async def export_emotes(
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    emotes = await client.export_emotes(config.channel, domain=config.domain)
    return {"emotes": emotes}


@router.post("/import")
async def import_emotes(
    body: BulkImportRequest,
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    emote_dicts = [e.model_dump() for e in body.emotes]
    message_ids = await client.import_emotes(
        config.channel, emote_dicts, domain=config.domain
    )
    return {"message_ids": message_ids, "count": len(message_ids)}


@router.put("/{name}")
async def update_emote(
    name: str,
    body: UpdateEmoteRequest,
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    msg_id = await client.update_emote(
        config.channel, name, body.image, body.source, domain=config.domain
    )
    return {"message_id": msg_id}


@router.delete("/{name}")
async def remove_emote(
    name: str,
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    msg_id = await client.remove_emote(config.channel, name, domain=config.domain)
    return {"message_id": msg_id}
