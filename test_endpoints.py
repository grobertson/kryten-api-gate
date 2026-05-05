#!/usr/bin/env python3
"""
kryten-api-gate endpoint tester.

Tests every API endpoint. Results are colour-coded: green = pass, yellow = expected
error (auth/validation), red = unexpected failure.

Usage:
    python test_endpoints.py [--base-url URL] [--api-key KEY] [--timeout SECONDS]

    Reads defaults from config.json in the current directory if present.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

try:
    import httpx
except ImportError:
    print("ERROR: httpx is required — pip install httpx", file=sys.stderr)
    sys.exit(1)

# ---------------------------------------------------------------------------
# Colour helpers (no deps)
# ---------------------------------------------------------------------------

GREEN  = "\033[32m"
YELLOW = "\033[33m"
RED    = "\033[31m"
CYAN   = "\033[36m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def _c(colour: str, text: str) -> str:
    if sys.stdout.isatty():
        return f"{colour}{text}{RESET}"
    return text

# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------

class Result:
    def __init__(self, label: str, method: str, path: str):
        self.label  = label
        self.method = method
        self.path   = path
        self.status: int | None = None
        self.ok     = False
        self.note   = ""
        self.ms: float = 0.0


results: list[Result] = []


def run(
    client: httpx.Client,
    label: str,
    method: str,
    path: str,
    *,
    json_body: dict | None = None,
    params: dict | None = None,
    expected_ok: tuple[int, ...] = (200, 201, 202),
    expected_err: tuple[int, ...] = (),
    note: str = "",
) -> Result:
    r = Result(label, method, path)
    for attempt in range(2):
        try:
            t0 = time.perf_counter()
            resp = client.request(method, path, json=json_body, params=params)
            r.ms = (time.perf_counter() - t0) * 1000
            r.status = resp.status_code
            if resp.status_code in expected_ok:
                r.ok   = True
                r.note = note or "OK"
            elif resp.status_code in expected_err:
                r.ok   = True
                r.note = f"expected {resp.status_code}"
            else:
                r.ok   = False
                try:
                    body = resp.json()
                    r.note = body.get("detail", str(body))[:100]
                except Exception:
                    r.note = resp.text[:100]
            break  # response received — no retry needed
        except httpx.ConnectError:
            r.ok   = False
            r.note = "CONNECTION REFUSED — is the server running?"
            break  # no point retrying a refused connection
        except (httpx.RemoteProtocolError, ConnectionResetError) as exc:
            if attempt == 0:
                continue  # server closed keep-alive after a 500 — retry once
            r.ok   = False
            r.note = f"Connection reset (server closed connection): {exc}"
        except Exception as exc:
            r.ok   = False
            r.note = f"EXCEPTION: {exc}"
            break
    results.append(r)
    _print_result(r)
    return r


def _print_result(r: Result) -> None:
    if r.status is None:
        icon = _c(RED, "✗ ERR ")
    elif r.ok:
        icon = _c(GREEN, "✓ pass")
    else:
        icon = _c(RED, "✗ FAIL")
    status_str = f"{r.status}" if r.status else "   "
    print(
        f"    {icon}  {_c(CYAN, f'{r.method:<7}')} {r.label:<35} {r.path:<48}"
        f"  {status_str}  {r.ms:5.0f}ms  {r.note}"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Test every kryten-api-gate endpoint")
    parser.add_argument("--base-url", default="", help="Base URL, e.g. http://localhost:28288")
    parser.add_argument("--api-key",  default="", help="API key / Bearer token")
    parser.add_argument("--timeout",  type=float, default=10.0, help="Per-request timeout (s)")
    args = parser.parse_args()

    # --- resolve config ---------------------------------------------------------
    base_url = args.base_url
    api_key  = args.api_key

    if not base_url or not api_key:
        for cfg_path in ("config.json", "config.example.json"):
            p = Path(cfg_path)
            if p.exists():
                try:
                    cfg = json.loads(p.read_text())
                    if not base_url:
                        host = cfg.get("http_host", "127.0.0.1")
                        port = cfg.get("http_port", 28288)
                        base_url = f"http://{host}:{port}"
                    if not api_key:
                        keys = cfg.get("api_keys", [])
                        if keys:
                            api_key = keys[0]
                    print(f"  Config loaded from {cfg_path}")
                except Exception:
                    pass
                break

    if not base_url:
        base_url = "http://127.0.0.1:28288"
    if not api_key:
        api_key = os.environ.get("KRYTEN_API_KEY", "")

    base = base_url.rstrip("/") + "/api/v1"

    print()
    print(_c(BOLD, "kryten-api-gate endpoint tester"))
    print(f"  Base URL : {base_url}")
    print(f"  API key  : {api_key[:8]}{'***' if len(api_key) > 8 else '(not set)'}")
    print(f"  {'METHOD':<7}  {'LABEL':<35} {'PATH':<48}  {'STS':>3}  {'TIME':>7}  NOTE")
    print(f"  {'-'*7}  {'-'*35} {'-'*48}  {'-'*3}  {'-'*7}  {'-'*20}")

    auth_headers = {"Authorization": f"Bearer {api_key}"}
    bad_headers  = {"Authorization": "Bearer wrong-key"}

    with httpx.Client(
        base_url=base,
        headers=auth_headers,
        timeout=args.timeout,
        follow_redirects=True,
    ) as client:

        # ==============================================================
        # SYSTEM — public
        # ==============================================================
        print(_c(BOLD, "  System (public)"))
        run(client, "health (no auth)",
            "GET", "/system/health",
            note="public endpoint")

        # ==============================================================
        # SYSTEM — auth required
        # ==============================================================
        print(_c(BOLD, "  System"))
        run(client, "version",          "GET",  "/system/version")
        run(client, "stats",            "GET",  "/system/stats")
        run(client, "services",         "GET",  "/system/services")
        run(client, "config",           "GET",  "/system/config")
        run(client, "ping",             "GET",  "/system/ping")
        run(client, "reload",           "POST", "/system/reload")
        # shutdown intentionally skipped — it would kill the service

        # --- auth rejection smoke-test ---
        print(_c(BOLD, "  Auth rejection"))
        with httpx.Client(base_url=base, headers=bad_headers,
                          timeout=args.timeout) as bad_client:
            run(bad_client, "version (bad key)",
                "GET", "/system/version",
                expected_ok=(), expected_err=(401, 403),
                note="should reject bad key")

        # ==============================================================
        # CHAT
        # ==============================================================
        print(_c(BOLD, "  Chat"))
        run(client, "send chat",
            "POST", "/chat/send",
            json_body={"message": "[test] kryten-api-gate endpoint test"})
        run(client, "send PM",
            "POST", "/chat/pm",
            json_body={"username": "testuser", "message": "test PM"})

        # ==============================================================
        # PLAYLIST
        # ==============================================================
        print(_c(BOLD, "  Playlist"))
        run(client, "add media",
            "POST", "/playlist/add",
            json_body={"type": "yt", "id": "dQw4w9WgXcQ", "position": "end", "temp": True})
        run(client, "shuffle",   "POST", "/playlist/shuffle")
        run(client, "clear",     "DELETE", "/playlist/")
        # uid-based routes tested with a placeholder uid; expect 2xx or a bot-side error
        run(client, "jump to uid=1",
            "POST", "/playlist/1/jump",
            expected_ok=(200,), expected_err=(400, 404, 422))
        run(client, "move uid=1",
            "PUT", "/playlist/1/move",
            json_body={"position": 0},
            expected_ok=(200,), expected_err=(400, 404, 422))
        run(client, "set temp uid=1",
            "PUT", "/playlist/1/temp",
            json_body={"is_temp": True},
            expected_ok=(200,), expected_err=(400, 404, 422))
        run(client, "delete uid=1",
            "DELETE", "/playlist/1",
            expected_ok=(200,), expected_err=(400, 404, 422))

        # ==============================================================
        # PLAYBACK
        # ==============================================================
        print(_c(BOLD, "  Playback"))
        run(client, "pause",    "POST", "/playback/pause")
        run(client, "play",     "POST", "/playback/play")
        run(client, "seek",     "POST", "/playback/seek",
            json_body={"time_seconds": 0.0})
        run(client, "voteskip", "POST", "/playback/voteskip")
        run(client, "next",     "POST", "/playback/next")

        # ==============================================================
        # MODERATION
        # ==============================================================
        print(_c(BOLD, "  Moderation"))
        run(client, "kick",
            "POST", "/moderation/kick",
            json_body={"username": "testuser", "reason": "test"},
            expected_ok=(200,), expected_err=(400, 404, 422))
        run(client, "ban",
            "POST", "/moderation/ban",
            json_body={"username": "testuser", "reason": "test"},
            expected_ok=(200,), expected_err=(400, 404, 422))
        run(client, "mute",
            "POST", "/moderation/mute",
            json_body={"username": "testuser"},
            expected_ok=(200,), expected_err=(400, 404, 422))
        run(client, "shadow-mute",
            "POST", "/moderation/shadow-mute",
            json_body={"username": "testuser"},
            expected_ok=(200,), expected_err=(400, 404, 422))
        run(client, "unmute",
            "POST", "/moderation/unmute",
            json_body={"username": "testuser"},
            expected_ok=(200,), expected_err=(400, 404, 422))
        run(client, "assign leader",
            "POST", "/moderation/assign-leader",
            json_body={"username": "testuser"},
            expected_ok=(200,), expected_err=(400, 404, 422))
        run(client, "banlist",
            "GET", "/moderation/banlist",
            expected_ok=(200,), expected_err=(400, 404, 422))
        run(client, "unban id=1",
            "DELETE", "/moderation/ban/1",
            expected_ok=(200,), expected_err=(400, 404, 422))

        # ==============================================================
        # ADMIN
        # ==============================================================
        print(_c(BOLD, "  Admin"))
        run(client, "get motd",        "GET",  "/admin/motd")
        run(client, "set motd",        "PUT",  "/admin/motd",
            json_body={"motd": "Test MOTD from endpoint tester"})
        run(client, "get css",         "GET",  "/admin/css")
        run(client, "set css",         "PUT",  "/admin/css",
            json_body={"css": "/* test */"})
        run(client, "get js",          "GET",  "/admin/js")
        run(client, "set js",          "PUT",  "/admin/js",
            json_body={"js": "// test"})
        run(client, "get options",     "GET",  "/admin/options")
        run(client, "set options",     "PUT",  "/admin/options",
            json_body={"options": {}},
            expected_ok=(200,), expected_err=(400, 422))
        run(client, "get permissions", "GET",  "/admin/permissions")
        run(client, "set permissions", "PUT",  "/admin/permissions",
            json_body={"permissions": {}},
            expected_ok=(200,), expected_err=(400, 422))
        run(client, "request ranks",   "GET",  "/admin/ranks")
        run(client, "set rank",        "PUT",  "/admin/rank",
            json_body={"username": "testuser", "rank": 1},
            expected_ok=(200,), expected_err=(400, 404, 422))
        run(client, "channel log",     "GET",  "/admin/log", params={"count": 10})

        # ==============================================================
        # EMOTES
        # ==============================================================
        print(_c(BOLD, "  Emotes"))
        run(client, "export emotes",   "GET",  "/emotes/")
        run(client, "import emotes",   "POST", "/emotes/import",
            json_body={"emotes": [
                {"name": "testemote", "image": "https://i.imgur.com/test.png", "source": "imgur"}
            ]},
            expected_ok=(200,), expected_err=(400, 422))
        run(client, "update emote",    "PUT",  "/emotes/testemote",
            json_body={"image": "https://i.imgur.com/test2.png", "source": "imgur"},
            expected_ok=(200,), expected_err=(400, 404, 422))
        run(client, "remove emote",    "DELETE", "/emotes/testemote",
            expected_ok=(200,), expected_err=(400, 404, 422))

        # ==============================================================
        # FILTERS
        # ==============================================================
        print(_c(BOLD, "  Filters"))
        run(client, "add filter",
            "POST", "/filters/",
            json_body={"name": "testfilter", "source": "badword", "replace": "***"},
            expected_ok=(200,), expected_err=(400, 422))
        run(client, "update filter",
            "PUT", "/filters/testfilter",
            json_body={"source": "badword2", "replace": "***"},
            expected_ok=(200,), expected_err=(400, 404, 422))
        run(client, "remove filter",
            "DELETE", "/filters/testfilter",
            expected_ok=(200,), expected_err=(400, 404, 422))

        # ==============================================================
        # POLLS
        # ==============================================================
        print(_c(BOLD, "  Polls"))
        run(client, "new poll",
            "POST", "/polls/",
            json_body={"title": "Test poll", "options": ["Option A", "Option B"]},
            expected_ok=(200,), expected_err=(400, 422))
        run(client, "vote option 0",
            "POST", "/polls/vote",
            json_body={"option": 0},
            expected_ok=(200,), expected_err=(400, 422))
        run(client, "close poll",
            "POST", "/polls/close",
            expected_ok=(200,), expected_err=(400, 422))

        # ==============================================================
        # LIBRARY
        # ==============================================================
        print(_c(BOLD, "  Library"))
        run(client, "search library",
            "GET", "/library/search",
            params={"query": "test", "source": "library"},
            expected_ok=(200,), expected_err=(400, 422))
        run(client, "delete from library",
            "DELETE", "/library/testmediaid",
            expected_ok=(200,), expected_err=(400, 404, 422))

        # ==============================================================
        # KV STORE
        # ==============================================================
        print(_c(BOLD, "  KV Store"))
        TEST_BUCKET = "kryten-test"
        TEST_KEY    = "endpoint-test-key"
        run(client, "kv put",
            "PUT", f"/kv/buckets/{TEST_BUCKET}/keys/{TEST_KEY}",
            json_body={"value": "hello from endpoint tester", "as_json": False},
            expected_ok=(200,), expected_err=(403, 404, 422))
        run(client, "kv get",
            "GET", f"/kv/buckets/{TEST_BUCKET}/keys/{TEST_KEY}",
            expected_ok=(200,), expected_err=(404, 422))
        run(client, "kv keys",
            "GET", f"/kv/buckets/{TEST_BUCKET}/keys",
            expected_ok=(200,), expected_err=(404, 422))
        run(client, "kv get all",
            "GET", f"/kv/buckets/{TEST_BUCKET}",
            expected_ok=(200,), expected_err=(404, 422))
        run(client, "kv delete",
            "DELETE", f"/kv/buckets/{TEST_BUCKET}/keys/{TEST_KEY}",
            expected_ok=(200,), expected_err=(403, 404, 422))

        # ==============================================================
        # STATE
        # ==============================================================
        print(_c(BOLD, "  State"))
        run(client, "get channels",    "GET", "/state/channels")
        run(client, "get playlist",    "GET", "/state/playlist")
        run(client, "now playing",     "GET", "/state/now-playing")
        run(client, "get user",
            "GET", "/state/user/testuser",
            expected_ok=(200,), expected_err=(400, 404, 422))

    # ---------------------------------------------------------------------------
    # Summary
    # ---------------------------------------------------------------------------
    print()
    total         = len(results)
    passed        = sum(1 for r in results if r.ok)
    failed        = total - passed
    conn_failures = sum(1 for r in results if r.status is None)

    colour = GREEN if failed == 0 else RED
    print(_c(colour, _c(BOLD, f"  {passed}/{total} passed")) + (f", {_c(RED, str(failed) + ' failed')}" if failed else ""))
    if conn_failures:
        print(_c(RED, f"  ({conn_failures} could not connect — is the server running?)"))
    print()

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
