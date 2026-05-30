"""Tests for playlist routes — Gaps 3 and 7."""

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient


# ── Gap 3: POST /playlist/add returns uid ─────────────────────────────────────

def test_add_media_returns_uid(client: TestClient, mock_client: AsyncMock) -> None:
    """add_media response includes success and uid."""
    mock_client.add_media.return_value = {"success": True, "uid": 4242}
    resp = client.post(
        "/api/v1/playlist/add",
        json={"type": "yt", "id": "dQw4w9WgXcQ", "position": "end", "temp": True},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data == {"success": True, "uid": 4242}


def test_add_media_uid_null_when_timeout(client: TestClient, mock_client: AsyncMock) -> None:
    """uid is null when robot timed out waiting for CyTube confirmation."""
    mock_client.add_media.return_value = {"success": True, "uid": None}
    resp = client.post(
        "/api/v1/playlist/add",
        json={"type": "yt", "id": "abc123"},
    )
    assert resp.status_code == 200
    assert resp.json()["uid"] is None


def test_add_media_failure_raises_500(client: TestClient, mock_client: AsyncMock) -> None:
    """HTTP 500 raised when success is False."""
    mock_client.add_media.return_value = {"success": False, "error": "queue rejected"}
    resp = client.post(
        "/api/v1/playlist/add",
        json={"type": "yt", "id": "bad"},
    )
    assert resp.status_code == 500
    assert "queue rejected" in resp.json()["detail"]


# ── Gap 7: PUT /playlist/{uid}/move accepts string position ──────────────────

def test_move_with_int_position(client: TestClient, mock_client: AsyncMock) -> None:
    """Integer position accepted by MoveMediaRequest."""
    mock_client.move_media.return_value = "msg-001"
    resp = client.put("/api/v1/playlist/10/move", json={"position": 42})
    assert resp.status_code == 200


def test_move_with_string_prepend(client: TestClient, mock_client: AsyncMock) -> None:
    """String 'prepend' accepted — not rejected by Pydantic validation."""
    mock_client.move_media.return_value = "msg-002"
    resp = client.put("/api/v1/playlist/10/move", json={"position": "prepend"})
    assert resp.status_code == 200


def test_move_with_string_append(client: TestClient, mock_client: AsyncMock) -> None:
    """String 'append' accepted — not rejected by Pydantic validation."""
    mock_client.move_media.return_value = "msg-003"
    resp = client.put("/api/v1/playlist/10/move", json={"position": "append"})
    assert resp.status_code == 200
