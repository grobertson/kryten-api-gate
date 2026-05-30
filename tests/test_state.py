"""Tests for GET /state/user/{username} — Gap 10."""

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient


def test_get_user_online(client: TestClient, mock_client: AsyncMock) -> None:
    """Returns full user dict when client.get_user() returns data."""
    mock_client.get_user.return_value = {
        "username": "alice",
        "rank": 2,
        "online": True,
        "meta": {},
    }
    resp = client.get("/api/v1/state/user/alice")
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "alice"
    assert data["rank"] == 2
    assert data["online"] is True


def test_get_user_offline(client: TestClient, mock_client: AsyncMock) -> None:
    """Returns offline sentinel when client.get_user() returns None."""
    mock_client.get_user.return_value = None
    resp = client.get("/api/v1/state/user/ghost")
    assert resp.status_code == 200
    data = resp.json()
    assert data == {"username": "ghost", "rank": 0, "online": False}
