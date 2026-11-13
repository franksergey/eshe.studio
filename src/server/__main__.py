"""Entry point for the application."""

import argparse
import asyncio
import logging
import sys
from typing import Never
from urllib.parse import urlparse

import uvicorn
from alembic.config import Config
from fastapi import FastAPI, Request

from server.api.app import get_temp_dir, setup_app
from server.api.container import ServiceContainer
from server.domain.users.schemas import UserCreate
from server.sql.database import Database, DatabaseChecker
from server.sql.models import Base

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
        "server.api.app:setup_app",
        factory=True,
        host=settings.api.HOST,
        port=settings.api.PORT,
        reload=settings.api.RELOAD,
        reload_dirs=["src"],
        log_config=get_config_path(),
        log_level="debug",
        use_colors=True,
        loop="server.__main__:create_asyncio_event_loop",
        timeout_graceful_shutdown=settings.api.GRACEFULSHUTDOWNTIMEOUT,
    )
    logger.info("Main ASGI server runner has exited.")


async def perform_checks() -> None:
    logger.info("Performing an initial health check")

    async with (
        Database(
            db_url=settings.db.database_url, echo=settings.db.ECHO
        ) as database,
        ServiceContainer(
            database.get_session, settings.STORAGEDIR
        ) as container,
    ):
        if settings.db.CHECKSCHEMA:
            alembic_config = Config(toml_file=settings.PYPROJECT)

            checker = DatabaseChecker(Base, database, alembic_config)
            await checker.raise_for_differences(
                upgrade_if_empty=settings.db.UPGRADEIFEMPTY
            )

        if (
            settings.users.CREATEDEFAULTUSER
            and await container.users.users_table_empty()
        ):
            user_create = UserCreate(
                email="admin@example.com",
                password="admin",  # noqa: S106
                first_name="Admin",
                last_name=None,
                is_active=True,
                is_superuser=True,
                is_verified=True,
            )
            await container.users.create(user_create, safe=False)

    logger.info("Initial health check has been finished")


def get_dummy_request(
    app: FastAPI, base_url: str = "https://example.com", root_path: str = ""
) -> Request:
    parsed = urlparse(base_url)
    scheme = parsed.scheme or "http"
    host = parsed.hostname or "localhost"
    port = parsed.port or (443 if scheme == "https" else 80)

    scope: dict[str, object] = {
        "type": "http",
        "app": app,
        "scheme": scheme,
        "server": (host, port),
        "root_path": root_path,
        "headers": [],
    }
    return Request(scope)


async def interactive_debug_mode() -> Never:
    app = setup_app()
    request = get_dummy_request(app)
    asyncio.new_event_loop = create_asyncio_event_loop

    async with (
        Database(
            db_url=settings.db.database_url, echo=settings.db.ECHO
        ) as database,
        get_temp_dir() as temp_dir,
    ):
        while True:
            async with ServiceContainer(
                database.get_session, settings.STORAGEDIR, temp_dir, request
            ) as container:
                _ = container
                breakpoint()  # noqa: T100


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--interactive-debug", action="store_true")

    return parser.parse_args()


def main() -> None:
    """Entry point of the whole FastAPI backend."""
    setup_logging()
    logger.info("Backend version: %s", version)

    args = parse_args()

    with asyncio.Runner(loop_factory=create_asyncio_event_loop) as runner:
        if args.interactive_debug:
            runner.run(interactive_debug_mode())
            return

        runner.run(perform_checks())

    launch_server()


if __name__ == "__main__":
    main()
