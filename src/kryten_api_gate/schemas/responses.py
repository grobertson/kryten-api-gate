"""Shared response models for kryten-api-gate."""

from pydantic import BaseModel


class CommandResponse(BaseModel):
    """Standard response for fire-and-forget commands."""

    message_id: str


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    service: str
    timestamp: str
    nats_connected: bool
