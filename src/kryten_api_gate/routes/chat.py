"""Chat routes — send messages and PMs."""

from fastapi import APIRouter, Depends
from kryten import KrytenClient
from pydantic import BaseModel

from ..auth import verify_api_key
from ..config import Config
from ..deps import get_client, get_config

router = APIRouter(dependencies=[Depends(verify_api_key)])


class SendChatRequest(BaseModel):
    message: str


class SendPmRequest(BaseModel):
    username: str
    message: str


@router.post("/send")
async def send_chat(
    body: SendChatRequest,
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    msg_id = await client.send_chat(config.channel, body.message, domain=config.domain)
    return {"message_id": msg_id}


@router.post("/pm")
async def send_pm(
    body: SendPmRequest,
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    msg_id = await client.send_pm(
        config.channel, body.username, body.message, domain=config.domain
    )
    return {"message_id": msg_id}
