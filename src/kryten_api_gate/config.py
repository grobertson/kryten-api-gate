"""Configuration model for kryten-api-gate."""

import json
import logging
from pathlib import Path

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Config search paths in priority order
CONFIG_SEARCH_PATHS = [
    Path("./config.json"),
    Path("/etc/kryten/api-gate/config.json"),
    Path("/opt/kryten/api-gate/config.json"),
]


class Config(BaseModel):
    """API gate configuration."""

    nats_url: str = Field(default="nats://localhost:4222")
    channel: str = Field(description="CyTube channel name")
    domain: str = Field(default="cytu.be")
    http_host: str = Field(default="127.0.0.1")
    http_port: int = Field(default=28288)
    api_keys: list[str] = Field(description="Authorized bearer tokens")
    kv_read_only: bool = Field(default=False)
    service_name: str = Field(default="api-gate")
    log_level: str = Field(default="INFO")
    disabled_routes: list[str] = Field(
        default_factory=list,
        description="List of route operation IDs to disable (e.g. 'playback_pause', 'playback_seek')",
    )


def load_config(config_path: str | None = None) -> Config:
    """Load configuration from JSON file.

    Search order:
    1. Explicit path (if provided)
    2. ./config.json (cwd)
    3. /etc/kryten/api-gate/config.json
    4. /opt/kryten/api-gate/config.json
    """
    if config_path:
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        logger.info(f"Loading config from: {path}")
        data = json.loads(path.read_text())
        return Config(**data)

    for path in CONFIG_SEARCH_PATHS:
        if path.exists():
            logger.info(f"Loading config from: {path}")
            data = json.loads(path.read_text())
            return Config(**data)

    raise FileNotFoundError(
        f"No config file found. Searched: {[str(p) for p in CONFIG_SEARCH_PATHS]}"
    )
