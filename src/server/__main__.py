"""Entry point for the application."""

import asyncio
import logging
import sys

import uvicorn

from . import __version__ as version
from .config import settings
from .logging import get_config_path, setup_logging

logger = logging.getLogger(__name__)


def create_asyncio_event_loop() -> asyncio.AbstractEventLoop:
    """Asynchronous loop factory.

    Returns:
        New event loop object.
    """
    if sys.platform == "win32":
        import winloop  # noqa: PLC0415

        logger.info("Using winloop.Loop as event loop class.")
        return winloop.new_event_loop()

    if sys.platform == "linux":
        import uvloop  # noqa: PLC0415

        logger.info("Using uvloop.Loop as event loop class.")
        return uvloop.new_event_loop()

    logger.info("Using default event loop from asyncio.")
    return asyncio.new_event_loop()


def launch_server() -> None:
    """Launch ASGI server."""
    logger.info("Launching main ASGI server runner.")
    uvicorn.run(
        "server.app:setup_app",
        factory=True,
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        reload_dirs=["src"],
        log_config=get_config_path(),
        log_level="debug",
        use_colors=True,
        loop="server.__main__:create_asyncio_event_loop",
        timeout_graceful_shutdown=settings.GRACEFULSHUTDOWNTIMEOUT,
    )
    logger.info("Main ASGI server runner has exited.")


def main() -> None:
    """Entry point of the whole FastAPI backend."""
    setup_logging()
    logger.info("Backend version: %s", version)
    launch_server()


if __name__ == "__main__":
    main()
