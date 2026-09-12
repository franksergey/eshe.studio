"""Creation and the setup of application object of ASGI server."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from server.api.container import container_getter
from server.sql.database import Database

from . import __version__ as version
from .config import settings

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from server.api.container import ContainerGetter

logger = logging.getLogger(__name__)


def setup_app() -> FastAPI:
    """FastAPI application object factory.

    Args:
        debug: Should the server use debug mode for error responces?
            Defaults to False.

    Returns:
        A set up and ready to use application object.
    """
    logger.info("Setting up a FastAPI application object")
    app = FastAPI(debug=settings.DEBUG, version=version)

    setup_routers(app)
    setup_middlewares(app)

    return app


def setup_routers(app: FastAPI) -> None:
    """FastAPI routers configuration.

    Args:
        app: Application object.
    """
    static_directory = Path(settings.STATICFILES)
    app.mount(
        "/", StaticFiles(directory=static_directory, html=True), name="static"
    )
    logger.debug(
        "Using static files from directory %s as a root path", static_directory
    )


def setup_middlewares(app: FastAPI) -> None:
    """FastAPI middlewares configuration.

    Args:
        app: Application object
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.debug("Using Middleware CORSMiddleware")


class AppInitialState(TypedDict):
    get_container: ContainerGetter


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[AppInitialState]:
    async with Database(
        db_url=settings.db.database_url, echo=settings.db.ECHO
    ) as database:
        get_container = container_getter(database.get_session)

        logger.info("Сервер полностью настроен и готов к началу работы.")
        yield {"get_container": get_container}

        logger.info("Сервер останавливает свою работу...")
