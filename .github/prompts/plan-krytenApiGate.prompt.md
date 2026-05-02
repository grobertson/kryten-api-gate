# Plan: kryten-api-gate — HTTP REST Gateway for kryten-py

A FastAPI microservice that exposes the full `KrytenClient` API surface over HTTP REST. One instance per kryten-robot/NATS instance, single channel. API-key authenticated for service-to-service use. Upstream consumer web apps talk to one or more instances.

---

## Phase 0: Fix kryten-robot Routing Gap (Prerequisite, Blocking)

**Problem:** kryten-py's `__send_command()` publishes to `kryten.robot.command` (handled by `RobotCommandHandler`), but only basic commands (chat, playlist, playback, moderation) are in its dispatch table. Phase 2/3 admin commands (`setChannelCSS`, `setMotd`, `updateEmote`, filters, polls, ranks, banlist, chanlog, library) are silently dropped.

**Fix:** Add ~20 handler entries to `Kryten-Robot/kryten/robot_command_handler.py` routing them to `self.sender` (the `CytubeEventSender`), matching what `CommandSubscriber` already does.

**Commands to add:**
- `setMotd` / `set_motd`
- `setChannelCSS` / `set_channel_css`
- `setChannelJS` / `set_channel_js`
- `setOptions` / `set_options`
- `setPermissions` / `set_permissions`
- `updateEmote` / `update_emote`
- `removeEmote` / `remove_emote`
- `addFilter` / `add_filter`
- `updateFilter` / `update_filter`
- `removeFilter` / `remove_filter`
- `newPoll` / `new_poll`
- `vote`
- `closePoll` / `close_poll`
- `setChannelRank` / `set_channel_rank`
- `requestChannelRanks` / `request_channel_ranks`
- `requestBanlist` / `request_banlist`
- `unban`
- `readChanLog` / `read_chan_log`
- `searchLibrary` / `search_library`
- `deleteFromLibrary` / `delete_from_library`
- `playNext` / `play_next`

---

## Phase 1: Project Scaffold

```
kryten-api-gate/
├── pyproject.toml
├── config.example.json
├── systemd/kryten-api-gate.service
└── src/kryten_api_gate/
    ├── __init__.py
    ├── __main__.py        # Entry point
    ├── config.py          # Pydantic config model
    ├── app.py             # FastAPI app factory
    ├── deps.py            # DI (get_client, get_config)
    ├── auth.py            # API key dependency
    ├── routes/            # One file per domain
    │   ├── chat.py
    │   ├── playlist.py
    │   ├── playback.py
    │   ├── moderation.py
    │   ├── admin.py
    │   ├── emotes.py
    │   ├── filters.py
    │   ├── polls.py
    │   ├── library.py
    │   ├── kv.py
    │   ├── state.py
    │   └── system.py
    └── schemas/
        ├── __init__.py
        ├── requests.py    # Pydantic request models per route group
        └── responses.py   # Pydantic response models
```

**Dependencies:** `kryten-py>=0.10.5`, `fastapi>=0.115`, `uvicorn>=0.30`, `pydantic>=2.0`

---

## Phase 2: Core Infrastructure

### 2.1 Config (`config.py`)

Pydantic model loading JSON:

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `nats_url` | `str` | `nats://localhost:4222` | |
| `channel` | `str` | required | CyTube channel name |
| `domain` | `str` | `cytu.be` | |
| `http_host` | `str` | `127.0.0.1` | |
| `http_port` | `int` | `28288` | |
| `api_keys` | `list[str]` | required | Bearer tokens |
| `kv_read_only` | `bool` | `false` | When true, KV PUT/DELETE return 403 |
| `service_name` | `str` | `api-gate` | |
| `log_level` | `str` | `INFO` | |

### 2.2 Entry Point (`__main__.py`)

Standard kryten pattern:
1. Parse args (`--config`, `--log-level`)
2. Load config (json or yaml, check cwd, then `/etc/kryten/`, then `/opt/kryten/api-gate/` with precedence)
3. Create `KrytenClient` with config
4. `await client.connect()`
5. Create FastAPI app, inject client + config into `app.state`
6. Run uvicorn server
7. Signal handler for graceful shutdown → `client.disconnect()`

### 2.3 Auth (`auth.py`)

- FastAPI dependency extracting `Authorization: Bearer <key>`
- Validates against `config.api_keys`
- Returns 401 on mismatch
- Health endpoint exempted (public for monitoring)

### 2.4 Dependencies (`deps.py`)

```python
def get_client(request: Request) -> KrytenClient:
    return request.app.state.client

def get_config(request: Request) -> Config:
    return request.app.state.config
```

---

## Phase 3: Route Implementation

All routes under `/api/v1/`. Channel is fixed from config (not passed per-request).

### Chat (`/api/v1/chat`)

| Method | Endpoint | KrytenClient method |
|--------|----------|---------------------|
| POST | `/send` | `send_chat(channel, message)` |
| POST | `/pm` | `send_pm(channel, username, message)` |

### Playlist (`/api/v1/playlist`)

| Method | Endpoint | KrytenClient method |
|--------|----------|---------------------|
| POST | `/add` | `add_media(channel, type, id, position, temp)` |
| DELETE | `/{uid}` | `delete_media(channel, uid)` |
| PUT | `/{uid}/move` | `move_media(channel, uid, position)` |
| POST | `/{uid}/jump` | `jump_to(channel, uid)` |
| DELETE | `/` | `clear_playlist(channel)` |
| POST | `/shuffle` | `shuffle_playlist(channel)` |
| PUT | `/{uid}/temp` | `set_temp(channel, uid, is_temp)` |

### Playback (`/api/v1/playback`)

| Method | Endpoint | KrytenClient method |
|--------|----------|---------------------|
| POST | `/pause` | `pause(channel)` | (disableable by config)
| POST | `/play` | `play(channel)` |
| POST | `/seek` | `seek(channel, time_seconds)` | (disableable by config)
| POST | `/voteskip` | `voteskip(channel)` | (disableable by config)
| POST | `/next` | `play_next(channel)` |

### Moderation (`/api/v1/moderation`)

| Method | Endpoint | KrytenClient method |
|--------|----------|---------------------|
| POST | `/kick` | `kick_user(channel, username, reason)` |
| POST | `/ban` | `ban_user(channel, username, reason)` |
| POST | `/mute` | `mute_user(channel, username)` |
| POST | `/shadow-mute` | `shadow_mute_user(channel, username)` |
| POST | `/unmute` | `unmute_user(channel, username)` |
| POST | `/assign-leader` | `assign_leader(channel, username)` |
| GET | `/banlist` | `request_banlist(channel)` |
| DELETE | `/ban/{ban_id}` | `unban(channel, ban_id)` |

### Admin (`/api/v1/admin`)

| Method | Endpoint | KrytenClient method |
|--------|----------|---------------------|
| PUT | `/motd` | `set_motd(channel, motd)` |
| GET | `/motd` | `request_motd(channel)` |
| PUT | `/css` | `set_channel_css(channel, css)` |
| GET | `/css` | `request_channel_css(channel)` |
| PUT | `/js` | `set_channel_js(channel, js)` |
| GET | `/js` | `request_channel_js(channel)` |
| PUT | `/options` | `set_options(channel, options)` |
| GET | `/options` | `request_options(channel)` |
| PUT | `/permissions` | `set_permissions(channel, permissions)` |
| GET | `/permissions` | `request_permissions(channel)` |
| GET | `/ranks` | `request_channel_ranks(channel)` |
| PUT | `/rank` | `set_channel_rank(channel, username, rank)` |
| GET | `/log` | `read_chan_log(channel, count)` |

### Emotes (`/api/v1/emotes`)
## (Note: There is a way in the cytube UI to bulk import emotes via JSON, and to bulk export the JSON as well. No corresponding kryten-py methods exist, so we NEED to add `export_emotes(channel)` and `import_emotes(channel, emotes_json)` methods to KrytenClient, and route them here as POST `/import` and GET `/export`. The single-emote CRUD routes below are still needed for fine-grained updates.)
| Method | Endpoint | KrytenClient method |
|--------|----------|---------------------|
| PUT | `/{name}` | `update_emote(channel, name, image, source)` |
| DELETE | `/{name}` | `remove_emote(channel, name)` |

### Filters (`/api/v1/filters`)

| Method | Endpoint | KrytenClient method |
|--------|----------|---------------------|
| POST | `/` | `add_filter(channel, name, source, flags, replace, ...)` |
| PUT | `/{name}` | `update_filter(channel, ...)` |
| DELETE | `/{name}` | `remove_filter(channel, name)` |

### Polls (`/api/v1/polls`)

| Method | Endpoint | KrytenClient method |
|--------|----------|---------------------|
| POST | `/` | `new_poll(channel, title, options, obscured, timeout)` |
| POST | `/vote` | `vote(channel, option)` |
| POST | `/close` | `close_poll(channel)` |

### Library (`/api/v1/library`)

| Method | Endpoint | KrytenClient method |
|--------|----------|---------------------|
| GET | `/search` | `search_library(channel, query, source)` |
| DELETE | `/{media_id}` | `delete_from_library(channel, media_id)` |

### KV Store (`/api/v1/kv`)

| Method | Endpoint | KrytenClient method | Notes |
|--------|----------|---------------------|-------|
| GET | `/buckets/{bucket}/keys` | `kv_keys(bucket)` | |
| GET | `/buckets/{bucket}/keys/{key}` | `kv_get(bucket, key)` | |
| GET | `/buckets/{bucket}` | `kv_get_all(bucket)` | |
| PUT | `/buckets/{bucket}/keys/{key}` | `kv_put(bucket, key, value)` | Gated by `kv_read_only` |
| DELETE | `/buckets/{bucket}/keys/{key}` | `kv_delete(bucket, key)` | Gated by `kv_read_only` | (Delete whole bucket supported via `kv_delete(bucket, '*')`)

### State (`/api/v1/state`)

| Method | Endpoint | KrytenClient method |
|--------|----------|---------------------|
| GET | `/user/{username}` | `get_user(channel, username)` |
| GET | `/channels` | `get_channels()` |
| GET | `/playlist` | `get_state_playlist_items(channel)` |
| GET | `/now-playing` | `get_state_current_media(channel)` |

### System (`/api/v1/system`)

| Method | Endpoint | KrytenClient method | Auth |
|--------|----------|---------------------|------|
| GET | `/health` | local health check | **Public** |
| GET | `/version` | `get_version()` | Required |
| GET | `/stats` | `get_stats()` | Required |
| GET | `/services` | `get_services()` | Required |
| GET | `/config` | `get_config()` | Required |
| GET | `/ping` | `ping()` | Required |
| POST | `/reload` | `reload_config()` | Required |
| POST | `/shutdown` | `shutdown()` | Required |

---

## Phase 4: Packaging & Deployment

- `pyproject.toml` with console script `kryten-api-gate = kryten_api_gate.__main__:main`
- `config.example.json` with documented defaults
- `systemd/kryten-api-gate.service` — standard kryten pattern (port 28288, user `kryten`, `/opt/kryten/api-gate/`)

---

## Verification

1. Start NATS + kryten-robot → start kryten-api-gate
2. `GET /api/v1/system/ping` with API key → success response
3. `POST /api/v1/chat/send` → message appears on CyTube
4. `GET /api/v1/system/health` without auth → 200 (public)
5. Any protected route without auth → 401
6. KV PUT with `kv_read_only: true` → 403

---

## Key Decisions

- **Channel from config, not per-request** — matches single-channel-per-instance model across all kryten services
- **API keys only** — machine-to-machine; user auth lives in upstream consumer app
- **No event streaming** — REST only; upstream app can poll state endpoints
- **Health is unauthenticated** — standard for monitoring/load balancers
- **KV write gating via config** — allows deployment in read-only mode
- **Phase 0 is blocking** — API gate depends on robot dispatching all commands properly

---

## Excluded from Scope

- WebSocket/SSE streaming
- OTP/session user auth
- Frontend/UI
- Multi-channel or multi-NATS routing
- Docker
- Bulk emote import (consumer can loop PUT calls)
