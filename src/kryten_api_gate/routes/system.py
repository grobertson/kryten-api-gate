"""System routes — health, version, stats, services, config, ping, reload, shutdown."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from kryten import KrytenClient

from ..auth import verify_api_key
from ..deps import get_client

# Public router (no auth required)
public_router = APIRouter()

# Protected router
router = APIRouter(dependencies=[Depends(verify_api_key)])


@public_router.get("/health")
async def health(client: KrytenClient = Depends(get_client)) -> dict:
    """Public health check endpoint."""
    return {
        "status": "healthy",
        "service": "kryten-api-gate",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "nats_connected": client.is_connected,
    }


@router.get("/version")
async def version(client: KrytenClient = Depends(get_client)) -> dict:
    result = await client.get_version()
    return {"version": result}


@router.get("/stats")
async def stats(client: KrytenClient = Depends(get_client)) -> dict:
    return await client.get_stats()


@router.get("/services")
async def services(client: KrytenClient = Depends(get_client)) -> dict:
    return await client.get_services()


@router.get("/config")
async def config(client: KrytenClient = Depends(get_client)) -> dict:
    return await client.get_config()


@router.get("/ping")
async def ping(client: KrytenClient = Depends(get_client)) -> dict:
    return await client.ping()


@router.post("/reload")
async def reload(client: KrytenClient = Depends(get_client)) -> dict:
    result = await client.reload_config()
    return {"result": result}


@router.post("/shutdown")
async def shutdown(client: KrytenClient = Depends(get_client)) -> dict:
    result = await client.shutdown()
    return {"result": result}
