"""Service configuration management.

All the settings are loaded from process environment variables and `.env`
file. Every setting uses a prefix `APP_` in its name when is loaded from
environment or `.env` file.
"""

from pathlib import Path
from typing import Literal

from pydantic import DirectoryPath
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """FastAPI server configuration.

    Attributes:
        HOST: `$APP_HOST`. FastAPI server host address.
            Defaults to "0.0.0.0".
        PORT: `$APP_PORT`. Port the server will listen to.
            Defaults to 8000.
        RELOAD: `$APP_RELOAD`. Watch for file updates and reload the
            server upon any changes. Defaults to true. Avoid in
            production environment.
        STATICFILES: `$APP_STATICFILES`. Use this directory as a source
            of static files used as the site's content.
        GRACEFULSHUTDOWNTIMEOUT: `$APP_GRACEFULSHUTDOWNTIMEOUT`. Timeout
            of `uvicorn`'s graceful shutdown. Defaults to 10.
        LOGGINGFORMAT: `$APP_LOGGINGFORMAT`. Format of logging.
            Determines which logging configuration will be used. Console
            is used by default.
        DEBUG: `$APP_DEBUG`. Debug mode. Defaults to False.
    """

    HOST: str = "0.0.0.0"  # noqa: S104
    PORT: int = 8000
    RELOAD: bool = False
    STATICFILES: DirectoryPath = Path("./static")
    GRACEFULSHUTDOWNTIMEOUT: int = 10
    LOGGINGFORMAT: Literal["rich", "console", "structured"] = "console"
    DEBUG: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="APP_",
        env_nested_delimiter="_",
        extra="ignore",
    )


settings: AppSettings = AppSettings()
