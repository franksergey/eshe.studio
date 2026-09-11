"""Logging configuration functions."""

import http
import logging.config
from copy import copy
from importlib import resources
from typing import TYPE_CHECKING, cast, override

import yaml
from pythonjsonlogger.json import JsonFormatter

from .config import settings

if TYPE_CHECKING:
    from pathlib import Path


def setup_logging() -> None:
    """Set up logging from the chosen logging configuration."""
    path = get_config_path()

    with path.open("rb") as fd:
        config = yaml.safe_load(fd)

    logging.config.dictConfig(config)


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
