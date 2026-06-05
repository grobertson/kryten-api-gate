# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2026-06-04

### Fixed

- **`/playlist/add` response unwrapping** — Robot wraps handler results in an outer `{service, command, success, data}` envelope; the route was checking the outer `success` (correct) but returning `result.get("uid")` (always `None`) instead of `result["data"]["uid"]`. Also added inner `data.success` check so a CyTube-level failure (e.g. not connected) is surfaced as HTTP 500 rather than silently returning `uid: null`
- **`TimeoutError` handling on `/playlist/add`** — If the Robot NATS subject times out, the unhandled `TimeoutError` now becomes HTTP 504 instead of an unhandled exception
- **502 vs 500 status codes** — When the Robot sends back `{success: false}` (exception in handler — e.g. sender not initialised), the route now returns HTTP 502 Bad Gateway instead of 500, distinguishing a downstream failure from an internal server error

[0.4.0]: https://github.com/grobertson/kryten-api-gate/releases/tag/v0.4.0

## [0.3.9] - 2026-06-02

### Fixed

- **anyio threadpool crash** — Dependency injection functions were synchronous (`def`) while the app ran under `anyio`. Converted `get_config` and `get_client` to `async def` to avoid the broken `anyio._backends` threadpool path

[0.3.9]: https://github.com/grobertson/kryten-api-gate/releases/tag/v0.3.9

## [0.3.8] - 2026-06-02

### Fixed

- **`get_client` AttributeError → HTTP 503** — `AttributeError` raised when building the NATS client (e.g. missing config field) is now caught and converted to a `503 Service Unavailable` response for easier diagnostics

[0.3.8]: https://github.com/grobertson/kryten-api-gate/releases/tag/v0.3.8

## [0.3.7] - 2026-06-02

### Fixed

- **NATS KV errors in state routes** — `/state/playlist` and `/state/now-playing` routes now catch NATS KV `NotFoundError` and other exceptions and return empty/default responses instead of raising HTTP 500

[0.3.7]: https://github.com/grobertson/kryten-api-gate/releases/tag/v0.3.7

## [0.3.6] - 2026-05-30

### Added

- **Economy proxy routes** — `/economy/*` endpoints proxied through to kryten-economy via NATS; includes `queue-preview`, `queue-spend`, `queue-refund`, and balance/history queries
- **`add_media` UID passthrough** — `uid` field now forwarded in add-media requests
- **`move_media` type flexibility** — Accepts both `int` and `str` for media position arguments

### Fixed

- **`get_user` offline guard** — Returns a safe default response when the NATS user-lookup subject is unreachable, rather than raising an unhandled exception

[0.3.6]: https://github.com/grobertson/kryten-api-gate/releases/tag/v0.3.6

## [0.3.5] - 2026-05-10

### Changed

- **Version from package metadata** — `importlib.metadata.version("kryten-api-gate")` replaces hardcoded `"0.1.0"` string in the `/version` route

[0.3.5]: https://github.com/grobertson/kryten-api-gate/releases/tag/v0.3.5

## [0.3.4] - 2026-05-08

### Changed

- **kryten-py ≥0.16.0 required** — Uses KV-based reads for MOTD, CSS, and JS (replaces older subject-based reads)

[0.3.4]: https://github.com/grobertson/kryten-api-gate/releases/tag/v0.3.4

## [0.3.3] - 2026-05-07

### Added

- **Live `currentTime`/`paused` via NATS subscription cache** — Background NATS subscription keeps a real-time cache of player state; `/state/now-playing` reads from the cache instead of issuing a blocking NATS request on every poll

[0.3.3]: https://github.com/grobertson/kryten-api-gate/releases/tag/v0.3.3

## [0.3.2] - 2026-05-05

### Added

- **CORS middleware** — Cross-origin requests permitted for browser clients
- **cytube.js queue button script** — Client-side script injected via the `/cytube.js` route to add a "Queue" button to CyTube media entries

### Fixed

- **`add_media` response** — Returns structured `{success, error}` instead of raw NATS reply; requires kryten-py ≥0.15.1

[0.3.2]: https://github.com/grobertson/kryten-api-gate/releases/tag/v0.3.2

## [0.3.1] - 2026-05-05

### Changed

- **API reference docs** — `API_REFERENCE.md` updated to document all synchronous endpoints and response shapes

[0.3.1]: https://github.com/grobertson/kryten-api-gate/releases/tag/v0.3.1

## [0.3.0] - 2026-05-05

### Changed

- **Real data from read endpoints** — `/banlist`, `/ranks`, `/log`, and `/catalog/search` now return actual data from NATS rather than stub responses

[0.3.0]: https://github.com/grobertson/kryten-api-gate/releases/tag/v0.3.0

## [0.2.0] - 2026-05-01

### Added

- Initial public release: FastAPI app with NATS-backed proxy routes for Kryten-Robot, hatchling build, README

[0.2.0]: https://github.com/grobertson/kryten-api-gate/releases/tag/v0.2.0
