"""Creation and the setup of application object of ASGI server."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_problem.handler import (
    add_exception_handler,
    new_exception_handler,
)
from starlette.staticfiles import StaticFiles
from starlette_problem.cors import CorsConfiguration

from server import __version__ as version
from server.api.container import container_getter
from server.config import settings
from server.sql.database import Database

from .errors import logger as errors_logger

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from server.api.container import ContainerGetter

logger = logging.getLogger(__name__)

cors_configuration = CorsConfiguration(
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    setup_exception_handlers(app)

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
        app: Application object.
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_configuration.allow_origins,
        allow_credentials=cors_configuration.allow_credentials,
        allow_methods=cors_configuration.allow_methods,
        allow_headers=cors_configuration.allow_headers,
    )
    logger.debug("Using Middleware CORSMiddleware")


def setup_exception_handlers(app: FastAPI) -> None:
    """FastAPI exception handlers configuration

    Args:
        app: Application object.
    """
    eh = new_exception_handler(logger=errors_logger, cors=cors_configuration)
    add_exception_handler(app, eh)
    logger.debug("Using fastapi-problem as errors handler")


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
