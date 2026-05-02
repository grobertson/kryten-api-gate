"""Filters routes — add, update, remove chat filters."""

from fastapi import APIRouter, Depends
from kryten import KrytenClient
from pydantic import BaseModel

from ..auth import verify_api_key
from ..config import Config
from ..deps import get_client, get_config

router = APIRouter(dependencies=[Depends(verify_api_key)])


class FilterRequest(BaseModel):
    name: str
    source: str
    flags: str = "gi"
    replace: str = ""
    filterlinks: bool = False
    active: bool = True


class UpdateFilterRequest(BaseModel):
    source: str
    flags: str = "gi"
    replace: str = ""
    filterlinks: bool = False
    active: bool = True


@router.post("/")
async def add_filter(
    body: FilterRequest,
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    msg_id = await client.add_filter(
        config.channel,
        body.name,
        body.source,
        body.flags,
        body.replace,
        filterlinks=body.filterlinks,
        active=body.active,
        domain=config.domain,
    )
    return {"message_id": msg_id}


@router.put("/{name}")
async def update_filter(
    name: str,
    body: UpdateFilterRequest,
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    msg_id = await client.update_filter(
        config.channel,
        name,
        body.source,
        body.flags,
        body.replace,
        filterlinks=body.filterlinks,
        active=body.active,
        domain=config.domain,
    )
    return {"message_id": msg_id}


@router.delete("/{name}")
async def remove_filter(
    name: str,
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    msg_id = await client.remove_filter(config.channel, name, domain=config.domain)
    return {"message_id": msg_id}
