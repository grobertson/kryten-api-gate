"""Polls routes — create, vote, close polls."""

from fastapi import APIRouter, Depends
from kryten import KrytenClient
from pydantic import BaseModel

from ..auth import verify_api_key
from ..config import Config
from ..deps import get_client, get_config

router = APIRouter(dependencies=[Depends(verify_api_key)])


class NewPollRequest(BaseModel):
    title: str
    options: list[str]
    obscured: bool = False
    timeout: int = 0


class VoteRequest(BaseModel):
    option: int


@router.post("/")
async def new_poll(
    body: NewPollRequest,
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    msg_id = await client.new_poll(
        config.channel,
        body.title,
        body.options,
        obscured=body.obscured,
        timeout=body.timeout,
        domain=config.domain,
    )
    return {"message_id": msg_id}


@router.post("/vote")
async def vote(
    body: VoteRequest,
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    msg_id = await client.vote(config.channel, body.option, domain=config.domain)
    return {"message_id": msg_id}


@router.post("/close")
async def close_poll(
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    msg_id = await client.close_poll(config.channel, domain=config.domain)
    return {"message_id": msg_id}
