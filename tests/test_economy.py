"""Tests for economy proxy routes — Gap 8."""

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient


# ── GET /economy/balance/{username} ──────────────────────────────────────────

def test_get_balance_success(client: TestClient, mock_client: AsyncMock) -> None:
    """_unwrap extracts data; 200 response with balance fields."""
    mock_client.economy_request.return_value = {
        "success": True,
        "data": {"username": "alice", "balance": 500, "currency": "points"},
    }
    resp = client.get("/api/v1/economy/balance/alice")
    assert resp.status_code == 200
    data = resp.json()
    assert data["balance"] == 500
    assert data["username"] == "alice"


def test_get_balance_economy_error(client: TestClient, mock_client: AsyncMock) -> None:
    """Economy returns success: false → HTTP 502."""
    mock_client.economy_request.return_value = {
        "success": False,
        "error": "user not found",
    }
    resp = client.get("/api/v1/economy/balance/nobody")
    assert resp.status_code == 502
    assert "user not found" in resp.json()["detail"]


# ── GET /economy/transactions/{username} ─────────────────────────────────────

def test_get_transactions_pagination(client: TestClient, mock_client: AsyncMock) -> None:
    """limit and offset query params are forwarded in the economy request payload."""
    mock_client.economy_request.return_value = {
        "success": True,
        "data": {"transactions": [], "total": 0},
    }
    resp = client.get("/api/v1/economy/transactions/alice?limit=10&offset=5")
    assert resp.status_code == 200

    _channel, command, payload = mock_client.economy_request.call_args.args
    assert command == "transactions.list"
    assert payload["limit"] == 10
    assert payload["offset"] == 5
    assert payload["username"] == "alice"


# ── POST /economy/queue-preview ──────────────────────────────────────────────

def test_queue_preview_proxied(client: TestClient, mock_client: AsyncMock) -> None:
    """Request body forwarded flat (not nested under 'payload')."""
    mock_client.economy_request.return_value = {
        "success": True,
        "data": {"cost": 30, "affordable": True},
    }
    resp = client.post(
        "/api/v1/economy/queue-preview",
        json={"username": "alice", "duration_sec": 180, "tier": "queue"},
    )
    assert resp.status_code == 200
    _channel, command, payload = mock_client.economy_request.call_args.args
    assert command == "spending.queue_preview"
    assert payload["username"] == "alice"
    assert payload["duration_sec"] == 180


# ── POST /economy/queue-spend ─────────────────────────────────────────────────

def test_queue_spend_proxied(client: TestClient, mock_client: AsyncMock) -> None:
    """request_id is included in forwarded payload."""
    mock_client.economy_request.return_value = {
        "success": True,
        "data": {"transaction_id": "txn-99"},
    }
    resp = client.post(
        "/api/v1/economy/queue-spend",
        json={
            "username": "alice",
            "duration_sec": 120,
            "tier": "queue",
            "request_id": "req-abc",
        },
    )
    assert resp.status_code == 200
    _channel, command, payload = mock_client.economy_request.call_args.args
    assert command == "spending.queue"
    assert payload["request_id"] == "req-abc"


# ── POST /economy/queue-refund ────────────────────────────────────────────────

def test_queue_refund_proxied(client: TestClient, mock_client: AsyncMock) -> None:
    """reason is included in forwarded payload."""
    mock_client.economy_request.return_value = {
        "success": True,
        "data": {"refunded": 120},
    }
    resp = client.post(
        "/api/v1/economy/queue-refund",
        json={"username": "alice", "request_id": "req-abc", "reason": "user cancelled"},
    )
    assert resp.status_code == 200
    _channel, command, payload = mock_client.economy_request.call_args.args
    assert command == "spending.queue_refund"
    assert payload["reason"] == "user cancelled"


# ── POST /economy/vanity/shoutout ────────────────────────────────────────────

def test_vanity_shoutout_proxied(client: TestClient, mock_client: AsyncMock) -> None:
    """Shoutout body is forwarded flat to the vanity.shoutout command."""
    mock_client.economy_request.return_value = {
        "success": True,
        "data": {
            "username": "alice",
            "message": "go watch",
            "charged": 445,
            "new_balance": 9000,
        },
    }
    resp = client.post(
        "/api/v1/economy/vanity/shoutout",
        json={"username": "alice", "value": "go watch"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["message"] == "go watch"
    _channel, command, payload = mock_client.economy_request.call_args.args
    assert command == "vanity.shoutout"
    assert payload["username"] == "alice"
    assert payload["value"] == "go watch"


def test_vanity_shoutout_economy_error(client: TestClient, mock_client: AsyncMock) -> None:
    """Cooldown / funding errors from economy surface as HTTP 502."""
    mock_client.economy_request.return_value = {
        "success": False,
        "error": "Shoutout cooldown: 5 minute(s) remaining.",
    }
    resp = client.post(
        "/api/v1/economy/vanity/shoutout",
        json={"username": "alice", "value": "spammy"},
    )
    assert resp.status_code == 502
    assert "cooldown" in resp.json()["detail"].lower()

