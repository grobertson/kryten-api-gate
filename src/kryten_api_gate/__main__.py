"""Entry point for kryten-api-gate service."""

import argparse
import asyncio
import logging
import signal
import sys
from importlib.metadata import version as pkg_version

import uvicorn
from kryten import KrytenClient

from .app import create_app
from .config import load_config
from .playback_cache import PlaybackCache

logger = logging.getLogger("kryten_api_gate")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Kryten API Gate — HTTP REST gateway")
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to config JSON file",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default=None,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log level override",
    )
    return parser.parse_args()


def setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


async def main_async() -> None:
    args = parse_args()
    config = load_config(args.config)

    log_level = args.log_level or config.log_level
    setup_logging(log_level)

    logger.info(f"Starting kryten-api-gate v{pkg_version('kryten-api-gate')}")
    logger.info(f"Channel: {config.channel} @ {config.domain}")
    logger.info(f"NATS: {config.nats_url}")
    logger.info(f"HTTP: {config.http_host}:{config.http_port}")

    # Create KrytenClient
    client_config = {
        "nats": {"servers": [config.nats_url]},
        "channels": [{"domain": config.domain, "channel": config.channel}],
        "service": {
            "name": config.service_name,
            "version": pkg_version("kryten-api-gate"),
            "enable_lifecycle": True,
            "enable_heartbeat": True,
            "enable_discovery": True,
        },
    }
    client = KrytenClient(client_config)

    # Connect to NATS
    await client.connect()
    logger.info("Connected to NATS")

    # Create FastAPI app and inject state
    app = create_app(config)
    app.state.client = client
    app.state.config = config

    # Start live playback position cache (subscribes to NATS mediaUpdate)
    playback_cache = PlaybackCache(client, config.channel)
    await playback_cache.start()
    app.state.playback_cache = playback_cache

    # Setup shutdown event
    shutdown_event = asyncio.Event()

    def _signal_handler() -> None:
        logger.info("Shutdown signal received")
        shutdown_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _signal_handler)
        except NotImplementedError:
            # Windows doesn't support add_signal_handler
            signal.signal(sig, lambda s, f: _signal_handler())

    # Run uvicorn
    uv_config = uvicorn.Config(
        app,
        host=config.http_host,
        port=config.http_port,
        log_level=log_level.lower(),
        access_log=log_level.upper() == "DEBUG",
    )
    server = uvicorn.Server(uv_config)

    # Run server with shutdown monitoring
    server_task = asyncio.create_task(server.serve())

    await shutdown_event.wait()

    # Graceful shutdown
    logger.info("Shutting down...")
    server.should_exit = True
    await server_task
    await playback_cache.stop()
    await client.disconnect("API gate shutting down")
    logger.info("Shutdown complete")


def main() -> None:
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        pass
    sys.exit(0)


if __name__ == "__main__":
    main()
