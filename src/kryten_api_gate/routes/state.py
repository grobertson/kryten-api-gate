"""State routes — query channel state (users, playlist, now-playing, channels)."""

from fastapi import APIRouter, Depends
from kryten import KrytenClient

from ..auth import verify_api_key
from ..config import Config
from ..deps import get_client, get_config, get_playback_cache
from ..playback_cache import PlaybackCache

router = APIRouter(dependencies=[Depends(verify_api_key)])


@router.get("/user/{username}")
async def get_user(
    username: str,
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    result = await client.get_user(config.channel, username, domain=config.domain)
    return result


@router.get("/channels")
async def get_channels(
    client: KrytenClient = Depends(get_client),
) -> dict:
    channels = await client.get_channels()
    return {"channels": channels}


@router.get("/playlist")
async def get_playlist(
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
) -> dict:
    items = await client.get_state_playlist_items(config.channel)
    return {"items": items}


@router.get("/now-playing")
async def get_now_playing(
    client: KrytenClient = Depends(get_client),
    config: Config = Depends(get_config),
    cache: PlaybackCache | None = Depends(get_playback_cache),
) -> dict:
    media = await client.get_state_current_media(config.channel)
    if not media:
        return {}
    if cache is not None:
        media = cache.overlay(media)
    return media
