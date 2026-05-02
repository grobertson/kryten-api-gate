"""Library routes — search and delete from media library."""

from fastapi import APIRouter, Depends
from kryten import KrytenClient

from ..auth import verify_api_key
from ..config import Config
from ..deps import get_client, get_config

router = APIRouter(dependencies=[Depends(verify_api_key)])


@router.get("/search")
async def search_library(
    query: str,
    source: str = "library",
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    msg_id = await client.search_library(
        config.channel, query, source, domain=config.domain
    )
    return {"message_id": msg_id}


@router.delete("/{media_id}")
async def delete_from_library(
    media_id: str,
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    msg_id = await client.delete_from_library(config.channel, media_id, domain=config.domain)
    return {"message_id": msg_id}
