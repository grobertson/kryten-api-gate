# kryten-api-gate

HTTP REST gateway for the Kryten ecosystem — exposes [`kryten-py`](https://github.com/grobertson/kryten-py) via FastAPI.

## Overview

`kryten-api-gate` sits between HTTP clients and the Kryten NATS message bus, translating REST calls into `KrytenClient` commands dispatched to [Kryten-Robot](https://github.com/grobertson/Kryten-Robot).

```
HTTP Client → kryten-api-gate → KrytenClient → NATS → Kryten-Robot → CyTube
```

## Installation

```bash
pip install kryten-api-gate
```

## Quick Start

1. Copy `config.example.json` to `config.json` and fill in your values:
   ```json
   {
     "nats_url": "nats://localhost:4222",
     "channel": "your-channel",
     "api_key": "your-secret-api-key",
     "host": "0.0.0.0",
     "port": 8080
   }
   ```

2. Run the server:
   ```bash
   kryten-api-gate
   # or
   python -m kryten_api_gate
   ```

3. Interactive API docs at `http://localhost:8080/docs`

## Authentication

All endpoints (except `/api/v1/system/health` and `/api/v1/system/version`) require a Bearer token:

```
Authorization: Bearer <api_key>
```

## API Routes

| Prefix | Description |
|--------|-------------|
| `GET /api/v1/system/health` | Health check (unauthenticated) |
| `GET /api/v1/system/version` | Version info (unauthenticated) |
| `POST /api/v1/chat/send` | Send a chat message |
| `GET/POST /api/v1/playlist/` | Playlist management |
| `POST /api/v1/playback/` | Playback control |
| `POST /api/v1/moderation/` | Moderation actions |
| `GET/POST /api/v1/admin/` | Admin channel settings |
| `GET/POST /api/v1/emotes/` | Emote management |
| `GET/POST /api/v1/filters/` | Chat filter management |
| `GET/POST /api/v1/polls/` | Poll management |
| `GET /api/v1/library/` | Media library search |
| `GET/PUT/DELETE /api/v1/kv/` | Key-value store |
| `GET /api/v1/state/` | Channel state queries |

## Configuration

| Key | Description | Default |
|-----|-------------|---------|
| `nats_url` | NATS server URL | `nats://localhost:4222` |
| `channel` | CyTube channel name | required |
| `api_key` | API authentication key | required |
| `host` | Listen address | `0.0.0.0` |
| `port` | Listen port | `8080` |
| `log_level` | Logging level | `info` |

## Systemd Service

A systemd unit file is provided at `systemd/kryten-api-gate.service`.

## Development

```bash
git clone https://github.com/grobertson/kryten-api-gate
cd kryten-api-gate
pip install -e ".[dev]"
uvicorn kryten_api_gate.app:create_app --factory --reload
```

## License

MIT
