"""Logging configuration functions."""

import http
import logging.config
from contextlib import contextmanager
from copy import copy
from importlib import resources
from logging.handlers import QueueHandler, QueueListener
from queue import Queue
from typing import TYPE_CHECKING, cast, override

import yaml
from pythonjsonlogger.json import JsonFormatter
from rich.logging import RichHandler

from .config import settings

if TYPE_CHECKING:
    from collections.abc import Callable, Generator
    from pathlib import Path

    from rich.console import ConsoleRenderable


@contextmanager
def setup_logging() -> Generator[None]:
    """Set up logging from the chosen logging configuration."""
    setup_logging_sync()

    with setup_asynchronous_logging(logging.getLogger()):
        yield


def setup_logging_sync() -> None:
    path = get_config_path()

    with path.open("rb") as fd:
        config = yaml.safe_load(fd)

    logging.config.dictConfig(config)


@contextmanager
def setup_asynchronous_logging(root_logger: logging.Logger) -> Generator[None]:
    queue: Queue[logging.LogRecord] = Queue(-1)

    handlers = root_logger.handlers.copy()
    listener = QueueListener(queue, *handlers, respect_handler_level=True)
    listener.start()

    for handler in handlers:
        root_logger.removeHandler(handler)

    handler = QueueHandler(queue)
    root_logger.addHandler(handler)

    yield

    listener.stop()
    root_logger.removeHandler(handler)

    for handler in handlers:
        root_logger.addHandler(handler)


def get_config_path() -> Path:
    """Get path to chosen logging configuration according to settings.

    Returns:
        Path to `.yaml` file written in `logging.dictConfig`-compatible way.
    """
    logging_configs_folder = resources.files("server") / "logging_configs"

    match settings.LOGGINGFORMAT:
        case "console":
            logging_config = logging_configs_folder / "console.yaml"
        case "rich":
            logging_config = logging_configs_folder / "rich.yaml"
        case "structured":
            logging_config = logging_configs_folder / "structured.yaml"

    with resources.as_file(logging_config) as path:
        return path


class JsonAccessFormatter(JsonFormatter):
    """Mirroring behavior of `uvicorn.logging.AccessFormatter` with JSON."""

    def _get_status_code(self, status_code: int) -> str:
        try:
            status_phrase = http.HTTPStatus(status_code).phrase
        except ValueError:
            return str(status_code)

        return f"{status_code} {status_phrase}"

    @override
    def format(self, record: logging.LogRecord) -> str:
        if not isinstance(record.args, tuple):
            return super().format(record)

        (client_addr, method, full_path, http_version, status_code) = (
            record.args
        )
        status_code = self._get_status_code(int(cast("str", status_code)))
        request_line = f"{method} {full_path} HTTP/{http_version}"

        recordcopy = copy(record)
        recordcopy.__dict__.update(
            {
                "client_addr": client_addr,
                "request_line": request_line,
                "status_code": status_code,
            }
        )

        return super().format(recordcopy)


class _WindowsLinkLogRender:
    def __init__(self, delegate: Callable[..., ConsoleRenderable]) -> None:
        self._delegate = delegate

    def __call__(self, *args: object, **kwargs: object) -> ConsoleRenderable:
        link_path = kwargs.get("link_path")

        if isinstance(link_path, str):
            kwargs["link_path"] = "/" + link_path.replace("\\", "/").lstrip(
                "/"
            )

        return self._delegate(*args, **kwargs)


class WindowsRichHandler(RichHandler):
    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)  # type: ignore [bad-argument-type]

        self._log_render = _WindowsLinkLogRender(self._log_render)  # type: ignore [bad-assignment]
