"""Dependency injection for kryten-api-gate routes."""

from fastapi import HTTPException, Request
from kryten import KrytenClient

from .config import Config
from .playback_cache import PlaybackCache


def get_client(request: Request) -> KrytenClient:
    """Get the shared KrytenClient instance."""
    try:
        return request.app.state.client
    except AttributeError as exc:
        raise HTTPException(status_code=503, detail=f"Service not ready: {exc}") from exc


def get_config(request: Request) -> Config:
    """Get the loaded configuration."""
    return request.app.state.config


def get_playback_cache(request: Request) -> PlaybackCache | None:
    """Get the in-memory playback position cache (None if not started)."""
    return getattr(request.app.state, "playback_cache", None)
