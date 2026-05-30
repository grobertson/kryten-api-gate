"""Shared fixtures for kryten-api-gate tests."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from kryten_api_gate.app import create_app
from kryten_api_gate.config import Config
from kryten_api_gate.deps import get_client, get_config

TEST_API_KEY = "test-key-abc123"

TEST_CONFIG = Config(
    channel="testchannel",
    domain="cytu.be",
    api_keys=[TEST_API_KEY],
    nats_url="nats://localhost:4222",
)


@pytest.fixture()
def mock_client() -> AsyncMock:
    """Return a mock KrytenClient."""
    return AsyncMock()


@pytest.fixture()
def app(mock_client: AsyncMock):
    """Return a configured FastAPI app with dependency overrides."""
    _app = create_app(TEST_CONFIG)
    _app.state.client = mock_client
    _app.state.config = TEST_CONFIG
    _app.dependency_overrides[get_client] = lambda: mock_client
    _app.dependency_overrides[get_config] = lambda: TEST_CONFIG
    return _app


@pytest.fixture()
def client(app) -> TestClient:
    """Return an httpx TestClient with the auth header pre-set."""
    return TestClient(app, headers={"Authorization": f"Bearer {TEST_API_KEY}"})
