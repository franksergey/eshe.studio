"""Creation and the setup of application object of ASGI server."""

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from . import __version__ as version
from .config import settings

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
