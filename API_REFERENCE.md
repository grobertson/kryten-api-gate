# kryten-api-gate API Reference

HTTP REST gateway for the Kryten ecosystem. All requests go through this service to a running **Kryten-Robot** instance via NATS.

Base path for all endpoints: `/api/v1`

---

## Authentication

All endpoints except `GET /api/v1/system/health` require a `Bearer` token.

```
Authorization: Bearer <api_key>
```

The key must match one of the values in `api_keys` in `config.json`. Missing or invalid tokens return `401 Unauthorized`.

```bash
# Set once and reuse across all examples below
export TOKEN="your-api-key"
export BASE="http://127.0.0.1:28288/api/v1"
```

---

## System

### `GET /system/health` — unauthenticated

Quick liveness check. Safe to call from a load-balancer probe; does not require a token.

```bash
curl $BASE/system/health
```

```json
{
  "status": "healthy",
  "service": "kryten-api-gate",
  "timestamp": "2026-05-04T12:00:00+00:00",
  "nats_connected": true
}
```

---

### `GET /system/version`

Returns the version reported by the connected Kryten-Robot instance.

```bash
curl -H "Authorization: Bearer $TOKEN" $BASE/system/version
```

```json
{ "version": "1.4.0" }
```

---

### `GET /system/ping`

Round-trip ping to verify the NATS connection and robot responsiveness.

```bash
curl -H "Authorization: Bearer $TOKEN" $BASE/system/ping
```

---

### `GET /system/stats`

Runtime stats from the bot (uptime, message counts, etc.).

```bash
curl -H "Authorization: Bearer $TOKEN" $BASE/system/stats
```

---

### `GET /system/services`

Lists active subsystems/services registered in the bot.

```bash
curl -H "Authorization: Bearer $TOKEN" $BASE/system/services
```

---

### `GET /system/config`

Returns the bot's current running configuration (read-only; does not expose the API key).

```bash
curl -H "Authorization: Bearer $TOKEN" $BASE/system/config
```

---

### `POST /system/reload`

Signals the bot to reload its configuration from disk.

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" $BASE/system/reload
```

---

## Chat

### `POST /chat/send`

Sends a message to the configured channel.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | string | yes | Text to post in chat |

```bash
curl -X POST $BASE/chat/send \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello from the API"}'
```

```json
{ "message_id": "abc123" }
```

---

### `POST /chat/pm`

Sends a private message to a specific user.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `username` | string | yes | CyTube username to message |
| `message` | string | yes | Text to send |

```bash
curl -X POST $BASE/chat/pm \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"username": "someuser", "message": "Hey there"}'
```

---

## Playlist

### `POST /playlist/add`

Adds a media item to the playlist.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `type` | string | yes | — | Media type: `yt`, `vi`, `dm`, `sc`, `fi`, `hl`, `tw`, `rt`, `gd`, `li`, `cm` |
| `id` | string | yes | — | Media ID for the given type (e.g. YouTube video ID). For `cm` (custom media), this must be the **full manifest URL** — see note below. |
| `position` | string | no | `"end"` | Where to insert: `"end"` or `"next"` |
| `temp` | bool | no | `true` | Whether the item is temporary (removed after playback) |

```bash
# Standard media type (YouTube)
curl -X POST $BASE/playlist/add \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type": "yt", "id": "dQw4w9WgXcQ", "position": "end", "temp": true}'

# Custom media (cm) — id must be the full manifest URL
curl -X POST $BASE/playlist/add \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type": "cm", "id": "https://example.com/media/manifest.json", "temp": false}'
```

```json
{ "success": true }
```

> **On failure** the bot returns `500` with `{"detail": "Failed to add video"}` if the socket.emit to CyTube did not succeed (e.g. bot not connected, insufficient rank).

> **Custom media (`cm`).** CyTube's custom media type expects a URL pointing to a JSON manifest file that describes the media sources, subtitles, and metadata. The `id` field must be the full manifest URL (e.g. `https://example.com/video.json`), not a short ID. CyTube fetches and validates the manifest server-side when the item is queued.

---

### `DELETE /playlist/{uid}`

Removes an item from the playlist by its unique ID.

```bash
curl -X DELETE -H "Authorization: Bearer $TOKEN" $BASE/playlist/42
```

---

### `PUT /playlist/{uid}/move`

Moves an item to a new position (0-indexed).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `position` | int | yes | Target 0-based position in the playlist |

```bash
curl -X PUT $BASE/playlist/42/move \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"position": 0}'
```

---

### `POST /playlist/{uid}/jump`

Jumps playback immediately to the specified item.

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" $BASE/playlist/42/jump
```

---

### `PUT /playlist/{uid}/temp`

Sets or clears the temporary flag on an existing playlist item.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `is_temp` | bool | no | `true` | `true` = item is removed after playback |

```bash
curl -X PUT $BASE/playlist/42/temp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_temp": false}'
```

---

### `POST /playlist/shuffle`

Randomly shuffles the playlist.

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" $BASE/playlist/shuffle
```

---

### `DELETE /playlist/`

Clears the entire playlist.

```bash
curl -X DELETE -H "Authorization: Bearer $TOKEN" "$BASE/playlist/"
```

> **Note:** The trailing slash is required to distinguish this from `DELETE /playlist/{uid}`.

---

## Playback

### `POST /playback/pause`

Pauses the currently playing item.

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" $BASE/playback/pause
```

---

### `POST /playback/play`

Resumes playback.

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" $BASE/playback/play
```

---

### `POST /playback/seek`

Seeks to an absolute timestamp in the current item.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `time_seconds` | float | yes | Position in seconds from the start |

```bash
curl -X POST $BASE/playback/seek \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"time_seconds": 90.5}'
```

---

### `POST /playback/voteskip`

Casts a voteskip on behalf of the bot.

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" $BASE/playback/voteskip
```

---

### `POST /playback/next`

Skips to the next item in the playlist.

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" $BASE/playback/next
```

---

## Moderator Service

Persistent moderation tracking via [kryten-moderator](https://github.com/grobertson/kryten-moderator).
All requests are proxied over NATS to `kryten.moderator.command` with a 10 s timeout.
The `{channel}` path segment is the CyTube channel name; `domain` is an optional query parameter
(defaults to the first channel configured in the moderator service).

> **Error mapping**
> | Condition | HTTP status |
> |-----------|-------------|
> | Moderator did not respond (timeout) | `503 Service Unavailable` |
> | Moderator returned error containing "required" / "must be" / "invalid" | `400 Bad Request` |
> | Moderator returned error containing "not found" / "not in" | `404 Not Found` |
> | Any other moderator error | `500 Internal Server Error` |

---

### `GET /channels/{channel}/moderation`

List all moderation entries for a channel.

| Query param | Type | Default | Description |
|-------------|------|---------|-------------|
| `domain` | string | — | CyTube domain (omit to use moderator default) |
| `filter` | `ban`\|`smute`\|`mute` | — | Return only entries with this action |

```bash
curl -H "Authorization: Bearer $TOKEN" "$BASE/channels/lounge/moderation"
curl -H "Authorization: Bearer $TOKEN" "$BASE/channels/lounge/moderation?filter=ban"
```

```json
{
  "channel": "lounge",
  "domain": "cytu.be",
  "count": 1,
  "entries": [
    {
      "username": "baduser",
      "action": "ban",
      "reason": "spamming",
      "moderator": "admin",
      "timestamp": "2026-07-04T00:00:00",
      "ip_correlation_source": null,
      "pattern_match": null
    }
  ]
}
```

---

### `POST /channels/{channel}/moderation`

Add a user to the moderation list, or replace an existing entry.
Returns `201 Created` with the stored entry.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `username` | string | yes | Target username |
| `action` | `ban`\|`smute`\|`mute` | yes | Action to apply |
| `domain` | string | no | CyTube domain |
| `reason` | string | no | Human-readable reason |
| `moderator` | string | no | Who issued the action (defaults to `"cli"`) |

```bash
curl -X POST "$BASE/channels/lounge/moderation" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"username": "baduser", "action": "ban", "reason": "spamming", "moderator": "admin"}'
```

```json
{
  "username": "baduser",
  "action": "ban",
  "reason": "spamming",
  "moderator": "admin",
  "timestamp": "2026-07-04T00:00:00",
  "channel": "lounge",
  "domain": "cytu.be"
}
```

> If the user is currently online the action is applied immediately.

---

### `GET /channels/{channel}/moderation/{username}`

Get the moderation entry for a specific user.

```bash
curl -H "Authorization: Bearer $TOKEN" "$BASE/channels/lounge/moderation/baduser"
```

```json
{
  "username": "baduser",
  "channel": "lounge",
  "domain": "cytu.be",
  "moderated": true,
  "action": "ban",
  "reason": "spamming",
  "moderator": "admin",
  "timestamp": "2026-07-04T00:00:00",
  "ips": ["1.2.3.x"],
  "ip_correlation_source": null,
  "pattern_match": null
}
```

Returns `{ "moderated": false }` (with channel/domain) if the user is not moderated.

---

### `DELETE /channels/{channel}/moderation/{username}`

Remove a user from the moderation list. Returns `404` if the user is not listed.
If the user is online and was muted/smuted they are unmuted immediately.

```bash
curl -X DELETE -H "Authorization: Bearer $TOKEN" "$BASE/channels/lounge/moderation/baduser"
```

```json
{ "username": "baduser", "channel": "lounge", "domain": "cytu.be", "removed": true }
```

---

### `GET /channels/{channel}/patterns`

List all banned username patterns for a channel.

```bash
curl -H "Authorization: Bearer $TOKEN" "$BASE/channels/lounge/patterns"
```

```json
{
  "channel": "lounge",
  "domain": "cytu.be",
  "count": 1,
  "patterns": [
    {
      "pattern": "1488",
      "is_regex": false,
      "action": "ban",
      "added_by": "admin",
      "description": "Nazi hate symbol",
      "timestamp": "2026-07-04T00:00:00"
    }
  ]
}
```

---

### `POST /channels/{channel}/patterns`

Register a banned username pattern. Returns `201 Created`.
When a joining user's name matches the pattern the configured action is applied automatically.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `pattern` | string | yes | — | Pattern string or regular expression |
| `is_regex` | bool | no | `false` | Treat `pattern` as a regex; `false` = substring match |
| `action` | `ban`\|`smute`\|`mute` | no | `"ban"` | Action to apply on match |
| `domain` | string | no | — | CyTube domain |
| `description` | string | no | — | Human-readable label shown in logs |
| `added_by` | string | no | `"cli"` | Who added the pattern |

```bash
curl -X POST "$BASE/channels/lounge/patterns" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"pattern": "1488", "action": "ban", "description": "Nazi hate symbol", "added_by": "admin"}'
```

---

### `DELETE /channels/{channel}/patterns/{pattern}`

Remove a registered pattern by its exact string. Returns `404` if not found.

```bash
curl -X DELETE -H "Authorization: Bearer $TOKEN" \
  "$BASE/channels/lounge/patterns/1488"
```

```json
{ "pattern": "1488", "channel": "lounge", "domain": "cytu.be", "removed": true }
```

> **URL encoding:** URL-encode the pattern if it contains special characters, e.g. `%5Cspam%5Cd%2B` for a regex `\spam\d+`.

---

### `GET /channels/{channel}/users/recent`

List users seen in a channel within a rolling time window.
Designed to surface "driveby" accounts. Results are sorted by `last_seen` descending.

| Query param | Type | Default | Description |
|-------------|------|---------|-------------|
| `domain` | string | — | CyTube domain |
| `window_minutes` | float (>0) | `60` | How far back to look (capped at the moderator's `history_retention_hours × 60`) |

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "$BASE/channels/lounge/users/recent?window_minutes=30"
```

```json
{
  "channel": "lounge",
  "domain": "cytu.be",
  "window_minutes": 30.0,
  "generated_at": "2026-07-04T01:00:00+00:00",
  "count": 1,
  "users": [
    {
      "username": "driveby_user",
      "moderation_action": null,
      "session_count": 2,
      "total_messages": 1,
      "last_seen": "2026-07-04T00:59:00+00:00",
      "sessions": [
        {
          "joined_at": "2026-07-04T00:45:00+00:00",
          "left_at": "2026-07-04T00:45:12+00:00",
          "duration_seconds": 12.0,
          "ip": "1.2.3.x",
          "message_count": 0
        }
      ]
    }
  ]
}
```

`moderation_action` is the user's current moderation status (`"ban"`, `"smute"`, `"mute"`, or `null`).
`left_at` / `duration_seconds` are `null` for sessions where the user is still present.

---

### `GET /moderator/ping`

Liveness check for the kryten-moderator service. Returns version, uptime, and metrics endpoint URL.

```bash
curl -H "Authorization: Bearer $TOKEN" "$BASE/moderator/ping"
```

```json
{
  "pong": true,
  "service": "moderator",
  "version": "0.7.0",
  "uptime_seconds": 3600.0,
  "timestamp": "2026-07-04T00:00:00",
  "metrics_endpoint": "http://localhost:28284/metrics"
}
```

---

### `GET /moderator/health`

Health status of the kryten-moderator service.

```bash
curl -H "Authorization: Bearer $TOKEN" "$BASE/moderator/health"
```

```json
{ "service": "moderator", "status": "healthy", "version": "0.7.0", "uptime_seconds": 3600.0 }
```

---

### `GET /moderator/stats`

Full runtime statistics from the kryten-moderator service.

```bash
curl -H "Authorization: Bearer $TOKEN" "$BASE/moderator/stats"
```

```json
{
  "service": "moderator",
  "version": "0.7.0",
  "uptime_seconds": 3600.0,
  "events_processed": 1234,
  "commands_processed": 56,
  "messages_checked": 1200,
  "messages_flagged": 3,
  "users_tracked": 89,
  "moderation_entries": 12,
  "ip_mappings": 450,
  "patterns": 4,
  "bans_enforced": 3,
  "smutes_enforced": 5,
  "mutes_enforced": 2
}
```

---

## Admin

### `GET /admin/motd`

Returns the channel's current Message of the Day.

```bash
curl -H "Authorization: Bearer $TOKEN" $BASE/admin/motd
```

```json
{ "motd": "<p>Welcome to the channel!</p>" }
```

---

### `PUT /admin/motd`

Sets the channel MOTD. Accepts raw HTML.

```bash
curl -X PUT $BASE/admin/motd \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"motd": "<p>New MOTD set via API</p>"}'
```

---

### `GET /admin/css`

Returns the channel's custom CSS.

```bash
curl -H "Authorization: Bearer $TOKEN" $BASE/admin/css
```

```json
{ "css": "body { background: #1a1a1a; }" }
```

---

### `PUT /admin/css`

Sets the channel custom CSS.

```bash
curl -X PUT $BASE/admin/css \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"css": "body { background: #1a1a1a; color: #eee; }"}'
```

---

### `GET /admin/js`

Returns the channel's custom JavaScript.

```bash
curl -H "Authorization: Bearer $TOKEN" $BASE/admin/js
```

---

### `PUT /admin/js`

Sets the channel custom JavaScript.

```bash
curl -X PUT $BASE/admin/js \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"js": "console.log(\"channel loaded\");"}'
```

---

### `GET /admin/options`

Returns the current channel options object (e.g. title, chat settings).

```bash
curl -H "Authorization: Bearer $TOKEN" $BASE/admin/options
```

```json
{ "options": { "allow_voteskip": true, "voteskip_ratio": 0.5 } }
```

---

### `PUT /admin/options`

Sets channel options. Pass the full options object.

```bash
curl -X PUT $BASE/admin/options \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"options": {"allow_voteskip": true, "voteskip_ratio": 0.7}}'
```

---

### `GET /admin/permissions`

Returns the current channel permissions matrix.

```bash
curl -H "Authorization: Bearer $TOKEN" $BASE/admin/permissions
```

---

### `PUT /admin/permissions`

Sets the channel permissions matrix.

```bash
curl -X PUT $BASE/admin/permissions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"permissions": {"chat": 0, "addvideo": 1.5}}'
```

---

### `GET /admin/ranks`

Returns the list of users with elevated channel ranks. The gateway sends a request to the bot, which queries CyTube and awaits the `channelRanks` response event synchronously (up to 5 s timeout).

```bash
curl -H "Authorization: Bearer $TOKEN" $BASE/admin/ranks
```

```json
{
  "ranks": [
    { "name": "trusteduser", "rank": 2 },
    { "name": "admin", "rank": 3 }
  ]
}
```

> **Note:** Requires the bot to have rank 4+ (owner) on the channel. May return a timeout error if CyTube does not respond within 5 seconds.

---

### `PUT /admin/rank`

Sets the channel rank for a user.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `username` | string | yes | Target username |
| `rank` | int | yes | Rank value (e.g. `1` = regular, `2` = mod, `3` = admin) |

```bash
curl -X PUT $BASE/admin/rank \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"username": "trusteduser", "rank": 2}'
```

---

### `GET /admin/log`

Returns recent channel log entries. The gateway sends a request to the bot, which queries CyTube and awaits the `readChanLog` response event synchronously (up to 5 s timeout).

| Query param | Type | Default | Description |
|-------------|------|---------|-------------|
| `count` | int | `100` | Number of recent log entries to retrieve |

```bash
curl -H "Authorization: Bearer $TOKEN" "$BASE/admin/log?count=50"
```

```json
{
  "log": [
    { "time": 1714900000, "event": "Channel joined", "detail": "admin" },
    { "time": 1714900060, "event": "Video added", "detail": "yt:dQw4w9WgXcQ" }
  ]
}
```

> **Note:** Requires rank 3+ (admin). May return a timeout error if CyTube does not respond within 5 seconds.

---

## Emotes

### `GET /emotes/`

Exports all current channel emotes.

```bash
curl -H "Authorization: Bearer $TOKEN" "$BASE/emotes/"
```

```json
{
  "emotes": [
    { "name": "kappa", "image": "https://i.imgur.com/abc.png", "source": "imgur" }
  ]
}
```

---

### `POST /emotes/import`

Bulk-imports a list of emotes, replacing the current set.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `emotes` | array | yes | List of emote objects (see below) |

Each emote object:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | yes | — | Emote trigger word |
| `image` | string | yes | — | Image URL |
| `source` | string | no | `"imgur"` | Image source type |

```bash
curl -X POST "$BASE/emotes/import" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "emotes": [
      {"name": "kappa",  "image": "https://i.imgur.com/abc.png"},
      {"name": "poggers","image": "https://i.imgur.com/def.png"}
    ]
  }'
```

```json
{ "message_ids": ["id1", "id2"], "count": 2 }
```

---

### `PUT /emotes/{name}`

Updates a single emote by name.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `image` | string | yes | — | New image URL |
| `source` | string | no | `"imgur"` | Image source type |

```bash
curl -X PUT $BASE/emotes/kappa \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"image": "https://i.imgur.com/newkappa.png"}'
```

---

### `DELETE /emotes/{name}`

Removes an emote by name.

```bash
curl -X DELETE -H "Authorization: Bearer $TOKEN" $BASE/emotes/kappa
```

---

## Filters

Chat filters are regex-based find-and-replace rules applied to all messages.

### `POST /filters/`

Adds a new chat filter.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | yes | — | Unique filter name |
| `source` | string | yes | — | Regex pattern to match |
| `flags` | string | no | `"gi"` | Regex flags (`g`, `i`, `m`) |
| `replace` | string | no | `""` | Replacement string |
| `filterlinks` | bool | no | `false` | Also apply to links |
| `active` | bool | no | `true` | Whether the filter is active |

```bash
curl -X POST "$BASE/filters/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "no-slurs", "source": "badword", "replace": "***"}'
```

---

### `PUT /filters/{name}`

Updates an existing filter by name. All fields are optional except `source`.

```bash
curl -X PUT $BASE/filters/no-slurs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"source": "badword|otherword", "replace": "[removed]", "active": true}'
```

---

### `DELETE /filters/{name}`

Removes a filter by name.

```bash
curl -X DELETE -H "Authorization: Bearer $TOKEN" $BASE/filters/no-slurs
```

---

## Polls

### `POST /polls/`

Creates a new poll.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `title` | string | yes | — | Poll question |
| `options` | array[string] | yes | — | List of answer options (min 2) |
| `obscured` | bool | no | `false` | Hide vote counts until poll closes |
| `timeout` | int | no | `0` | Auto-close after N seconds (0 = manual) |

```bash
curl -X POST "$BASE/polls/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Best programming language?",
    "options": ["Python", "Go", "Rust"],
    "timeout": 60
  }'
```

---

### `POST /polls/vote`

Casts a vote on the current poll on behalf of the bot.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `option` | int | yes | 0-based index of the chosen option |

```bash
curl -X POST $BASE/polls/vote \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"option": 1}'
```

---

### `POST /polls/close`

Closes the currently active poll.

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" $BASE/polls/close
```

---

## Library

### `GET /library/search`

Searches the channel's media library. The gateway sends a request to the bot, which queries CyTube and awaits the `searchResults` response event synchronously (up to 5 s timeout).

| Query param | Type | Required | Default | Description |
|-------------|------|----------|---------|-------------|
| `query` | string | yes | — | Search term |
| `source` | string | no | `"library"` | Source to search |

```bash
curl -H "Authorization: Bearer $TOKEN" "$BASE/library/search?query=rick+astley"
```

```json
{
  "results": [
    { "id": "dQw4w9WgXcQ", "title": "Rick Astley - Never Gonna Give You Up", "type": "yt", "seconds": 212 }
  ]
}
```

> **Note:** May return a timeout error if CyTube does not respond within 5 seconds.

---

### `DELETE /library/{media_id}`

Removes a media item from the library by its ID.

```bash
curl -X DELETE -H "Authorization: Bearer $TOKEN" $BASE/library/abc123
```

---

## KV Store

Direct access to NATS JetStream KeyValue buckets used by the bot. Buckets must already exist in NATS; this API does not create them.

> If `kv_read_only: true` is set in `config.json`, all write operations return `403 Forbidden`.

### `GET /kv/buckets/{bucket}/keys`

Lists all keys in a bucket.

```bash
curl -H "Authorization: Bearer $TOKEN" $BASE/kv/buckets/kryten-state/keys
```

```json
{ "bucket": "kryten-state", "keys": ["channel.playlist", "channel.now-playing"] }
```

---

### `GET /kv/buckets/{bucket}/keys/{key}`

Gets the value for a specific key.

| Query param | Type | Default | Description |
|-------------|------|---------|-------------|
| `parse_json` | bool | `false` | Decode the stored bytes as JSON |

```bash
# Raw bytes as string
curl -H "Authorization: Bearer $TOKEN" \
  "$BASE/kv/buckets/kryten-state/keys/channel.now-playing"

# Decoded as JSON
curl -H "Authorization: Bearer $TOKEN" \
  "$BASE/kv/buckets/kryten-state/keys/channel.now-playing?parse_json=true"
```

```json
{ "bucket": "kryten-state", "key": "channel.now-playing", "value": { "title": "...", "seconds": 180 } }
```

---

### `GET /kv/buckets/{bucket}`

Gets all key/value pairs in a bucket at once.

| Query param | Type | Default | Description |
|-------------|------|---------|-------------|
| `parse_json` | bool | `false` | Decode all values as JSON |

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "$BASE/kv/buckets/kryten-config?parse_json=true"
```

---

### `PUT /kv/buckets/{bucket}/keys/{key}`

Writes a value to a key. Creates the key if it does not exist.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `value` | any | yes | — | Value to store (string, number, or object) |
| `as_json` | bool | no | `false` | JSON-encode `value` before storing |

```bash
# Store a plain string
curl -X PUT $BASE/kv/buckets/myapp/keys/greeting \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"value": "hello world"}'

# Store a JSON object (set as_json: true)
curl -X PUT $BASE/kv/buckets/myapp/keys/config \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"value": {"theme": "dark", "volume": 80}, "as_json": true}'
```

```json
{ "bucket": "myapp", "key": "greeting", "status": "written" }
```

---

### `DELETE /kv/buckets/{bucket}/keys/{key}`

Deletes a key from a bucket.

```bash
curl -X DELETE -H "Authorization: Bearer $TOKEN" \
  $BASE/kv/buckets/myapp/keys/greeting
```

```json
{ "bucket": "myapp", "key": "greeting", "status": "deleted" }
```

---

## State

Read-only views into the bot's current channel state. These query the bot's in-memory state directly — they do not make a round-trip to CyTube.

### `GET /state/channels`

Returns the list of channels the bot is currently connected to.

```bash
curl -H "Authorization: Bearer $TOKEN" $BASE/state/channels
```

```json
{ "channels": ["mychannel"] }
```

---

### `GET /state/playlist`

Returns the current playlist items.

```bash
curl -H "Authorization: Bearer $TOKEN" $BASE/state/playlist
```

```json
{
  "items": [
    { "uid": 42, "title": "Never Gonna Give You Up", "type": "yt", "id": "dQw4w9WgXcQ", "temp": true }
  ]
}
```

---

### `GET /state/now-playing`

Returns the currently playing media item and its playback position.

```bash
curl -H "Authorization: Bearer $TOKEN" $BASE/state/now-playing
```

```json
{ "title": "Never Gonna Give You Up", "type": "yt", "id": "dQw4w9WgXcQ", "uid": 42, "seconds": 47, "paused": false }
```

> `uid` is the playlist UID of the now-playing item (added by kryten-robot ≥ 1.9.0). It may be absent on older bot versions or before the first `setCurrent` event after connect.

---

### `GET /state/user/{username}`

Returns current state for a specific user (rank, mute status, etc.).

```bash
curl -H "Authorization: Bearer $TOKEN" $BASE/state/user/someuser
```

```json
{ "name": "someuser", "rank": 1, "meta": { "muted": false, "smuted": false } }
```

---

## Economy

Proxies to the kryten-economy service (Z-Coin). All economy commands are scoped
to the gateway's configured `channel`.

### `GET /economy/balance/{username}`

Current balance, lifetime earned, and rank name for a user.

```bash
curl -H "Authorization: Bearer $TOKEN" $BASE/economy/balance/someuser
```

```json
{ "found": true, "username": "someuser", "balance": 5011144, "lifetime_earned": 29960293, "rank_name": "Hollywood Mogul" }
```

---

### `GET /economy/transactions/{username}`

Paginated transaction history (most recent first).

Query params: `limit` (1–100, default 20), `offset` (default 0).

```bash
curl -H "Authorization: Bearer $TOKEN" "$BASE/economy/transactions/someuser?limit=20&offset=0"
```

```json
{
  "username": "someuser",
  "limit": 20,
  "offset": 0,
  "transactions": [
    { "id": 9912, "amount": -7500, "type": "spend", "reason": "Vanity: chat_color", "trigger_id": "spend.vanity.chat_color", "created_at": "2026-06-14T00:39:02Z" }
  ]
}
```

---

### `GET /economy/account/{username}`

Full user-facing account snapshot: balance, lifetime earned, current rank
(name/level/tier count), next-rank progress, active perks, spend discount, and
editable vanity items with their costs. Designed to render a complete
progression panel in a single request.

```bash
curl -H "Authorization: Bearer $TOKEN" $BASE/economy/account/someuser
```

```json
{
  "found": true,
  "username": "someuser",
  "balance": 5011144,
  "lifetime_earned": 29960293,
  "lifetime_spent": 1200000,
  "currency_name": "Z-Coin",
  "currency_symbol": "Z",
  "rank": { "name": "Hollywood Mogul", "index": 8, "level": 9, "tier_count": 10, "min_lifetime_earned": 25000000 },
  "next_rank": { "name": "Hollywood Legend", "min_lifetime_earned": 50000000, "remaining": 20039707, "progress_percent": 59.9 },
  "perks": ["10% discount", "priority queue position"],
  "spend_discount_percent": 11.0,
  "vanity": { "custom_greeting": "Welcome back, legend!", "custom_color": "#DC143C" },
  "vanity_costs": { "custom_greeting": 5000, "custom_color": 7500 },
  "vanity_enabled": { "custom_greeting": true, "custom_color": true }
}
```

Returns `{ "found": false }` when the user has no economy account yet.

---

### `GET /economy/race`

Live race snapshot for the web spectator view (read-only, safe to poll).
Proxies the economy `race.state` command, scoped to the gate's channel.

```bash
curl -H "Authorization: Bearer $TOKEN" $BASE/economy/race
```

```json
{
  "active": true,
  "frame": {
    "race_id": "a1b2c3d4e5f6",
    "channel": "Channel-Z",
    "phase": "racing",
    "tick": 7,
    "finish_distance": 20.0,
    "leader": "Blue",
    "betting_closes_in": 0,
    "min_bet": 10,
    "symbol": "Z",
    "racers": [
      { "color": "Blue", "emoji": "🔵", "progress": 12.4, "pct": 62.0, "position": 1, "odds": "2.5x", "trait": "⚡ Fast start" }
    ],
    "pool": 1500,
    "bettor_count": 4,
    "bets_by_color": { "Blue": { "amount": 900, "bettors": 2 } },
    "winner": null,
    "payouts": []
  }
}
```

`phase` is one of `betting`, `racing`, or `finished`. During `betting`,
`betting_closes_in` counts down the wager window. When `finished`, `winner` is
`{ "color", "emoji" }` and `payouts` lists `{ "username", "net" }` (top winners).
Returns `{ "active": false, "frame": null }` when no race is running. Economy
failures surface as `502`.

---

### `POST /economy/vanity/greeting`

Purchase or update the user's custom greeting. Charges the configured cost
(after any rank discount) and persists the value.

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"username": "someuser", "value": "Welcome back, legend!"}' \
  $BASE/economy/vanity/greeting
```

```json
{ "username": "someuser", "item_type": "custom_greeting", "value": "Welcome back, legend!", "charged": 4450, "discount": 0.11, "new_balance": 5006694 }
```

Validation: greeting must be 1–200 characters. Insufficient funds or invalid
input return `502` with the economy error message.

---

### `POST /economy/vanity/color`

Purchase or update the user's custom chat color. Accepts any 6-digit hex
(`#RRGGBB` or `RRGGBB`), normalized to upper-case `#RRGGBB`.

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"username": "someuser", "value": "#DC143C"}' \
  $BASE/economy/vanity/color
```

```json
{ "username": "someuser", "item_type": "chat_color", "value": "#DC143C", "charged": 6675, "discount": 0.11, "new_balance": 5000019 }
```

Validation: an invalid color returns `502` with `Invalid color. Provide a 6-digit hex like #1A2B3C.`

When applied, the purchased color is also written into the channel's CyTube CSS
by kryten-economy (a per-user `.chat-msg-<user>` rule in an auto-managed block);
bot/manually-styled users on the economy's protected list are skipped.

---

### `POST /economy/vanity/shoutout`

Purchase a shoutout — the bot immediately posts the user's message to public
chat as `📢 <username>: <message>`. Charges the configured cost (after any rank
discount) and enforces a per-user cooldown.

```bash
curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"username": "someuser", "value": "Go watch the main event!"}' \
  $BASE/economy/vanity/shoutout
```

```json
{ "username": "someuser", "message": "Go watch the main event!", "charged": 445, "discount": 0.11, "new_balance": 5006249 }
```

Validation: message must be 1–`max_length` characters (default 200). A shoutout
during the cooldown window, insufficient funds, or an over-length message
return `502` with the economy error message.

---

## Error Responses

All errors follow FastAPI's standard envelope:

```json
{ "detail": "Human-readable error message" }
```

| Status | Meaning |
|--------|---------|
| `401` | Missing or invalid `Authorization` header |
| `403` | Action not permitted (e.g. KV write when `kv_read_only` is set) |
| `404` | Resource not found |
| `422` | Request body failed validation (field missing or wrong type) |
| `500` | Unhandled error in the gateway or bot |
| `503` | Downstream service (kryten-moderator) did not respond within the timeout |

---

## Interactive Docs

When the server is running, Swagger UI is available at:

```
http://<host>:<port>/docs
```

ReDoc is at `/redoc`. Both are generated automatically from the route definitions and require no authentication to view.
