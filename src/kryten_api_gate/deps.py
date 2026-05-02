"""Dependency injection for kryten-api-gate routes."""

from fastapi import Request
from kryten import KrytenClient

from .config import Config


def get_client(request: Request) -> KrytenClient:
    """Get the shared KrytenClient instance."""
    return request.app.state.client


def get_config(request: Request) -> Config:
    """Get the loaded configuration."""
    return request.app.state.config
