"""FastAPI application factory for kryten-api-gate."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import __version__
from .config import Config
from .routes import (
    admin,
    chat,
    emotes,
    filters,
    kv,
    library,
    moderation,
    playback,
    playlist,
    polls,
    state,
    system,
)


def create_app(config: Config | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="kryten-api-gate",
        version=__version__,
        description="HTTP REST gateway for the Kryten ecosystem",
    )

    if config and config.allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=config.allowed_origins,
            allow_methods=["GET", "POST", "PUT", "DELETE"],
            allow_headers=["Authorization", "Content-Type"],
        )

    # Public routes (no auth)
    app.include_router(system.public_router, prefix="/api/v1/system", tags=["system"])

    # Protected routes (require API key)
    app.include_router(system.router, prefix="/api/v1/system", tags=["system"])
    app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
    app.include_router(playlist.router, prefix="/api/v1/playlist", tags=["playlist"])
    app.include_router(playback.router, prefix="/api/v1/playback", tags=["playback"])
    app.include_router(moderation.router, prefix="/api/v1/moderation", tags=["moderation"])
    app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
    app.include_router(emotes.router, prefix="/api/v1/emotes", tags=["emotes"])
    app.include_router(filters.router, prefix="/api/v1/filters", tags=["filters"])
    app.include_router(polls.router, prefix="/api/v1/polls", tags=["polls"])
    app.include_router(library.router, prefix="/api/v1/library", tags=["library"])
    app.include_router(kv.router, prefix="/api/v1/kv", tags=["kv"])
    app.include_router(state.router, prefix="/api/v1/state", tags=["state"])

    return app
