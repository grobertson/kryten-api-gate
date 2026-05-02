"""KV Store routes — CRUD for NATS JetStream KeyValue buckets."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from kryten import KrytenClient
from pydantic import BaseModel

from ..auth import verify_api_key
from ..config import Config
from ..deps import get_client, get_config

router = APIRouter(dependencies=[Depends(verify_api_key)])


class KvPutRequest(BaseModel):
    value: Any
    as_json: bool = False


def _check_write_allowed(config: Config) -> None:
    """Raise 403 if KV is configured as read-only."""
    if config.kv_read_only:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="KV store is configured as read-only",
        )


@router.get("/buckets/{bucket}/keys")
async def kv_keys(
    bucket: str,
    client: KrytenClient = Depends(get_client),
) -> dict:
    keys = await client.kv_keys(bucket)
    return {"bucket": bucket, "keys": keys}


@router.get("/buckets/{bucket}/keys/{key}")
async def kv_get(
    bucket: str,
    key: str,
    parse_json: bool = False,
    client: KrytenClient = Depends(get_client),
) -> dict:
    value = await client.kv_get(bucket, key, parse_json=parse_json)
    return {"bucket": bucket, "key": key, "value": value}


@router.get("/buckets/{bucket}")
async def kv_get_all(
    bucket: str,
    parse_json: bool = False,
    client: KrytenClient = Depends(get_client),
) -> dict:
    data = await client.kv_get_all(bucket, parse_json=parse_json)
    return {"bucket": bucket, "data": data}


@router.put("/buckets/{bucket}/keys/{key}")
async def kv_put(
    bucket: str,
    key: str,
    body: KvPutRequest,
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    _check_write_allowed(config)
    await client.kv_put(bucket, key, body.value, as_json=body.as_json)
    return {"bucket": bucket, "key": key, "status": "written"}


@router.delete("/buckets/{bucket}/keys/{key}")
async def kv_delete(
    bucket: str,
    key: str,
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    _check_write_allowed(config)
    await client.kv_delete(bucket, key)
    return {"bucket": bucket, "key": key, "status": "deleted"}
