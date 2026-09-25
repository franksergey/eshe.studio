"""Service configuration management.

All the settings are loaded from process environment variables and `.env`
file. Every setting uses a prefix `APP_` in its name when is loaded from
environment or `.env` file.
"""

from functools import cached_property
from pathlib import Path
from typing import Literal, Self

from pydantic import BaseModel, DirectoryPath, FilePath, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL, make_url

DATA_FOLDER_SENTIEL = ":DATA_FOLDER:"


class DatabaseConfig(BaseModel):
    """Конфигурация подключения к базе данных.

    Attributes:
        DIALECT: `$APP_DB_DIALECT`. SQL-диалект. По умолчанию `sqlite`.
        DRIVER: `$APP_DB_DRIVER`. Драйвер для подключения к БД. Должен
            поддерживать асинхронную работу с SQLAlchemy.
        USERNAME: `$APP_DB_USERNAME`. Имя пользователя базы данных.
        PASSWORD: `$APP_DB_PASSWORD`. Пароль для подключения к БД.
        PASSWORDFILE: `$APP_DB_PASSWORDFILE`. Файл с паролем для
            подключения к базе данных.
        HOST: `$APP_DB_HOST`. Адрес хоста базы данных.
        PORT: `$APP_DB_PORT`. Порт для подключения к базе данных.
        DATABASE: `$APP_DB_DATABASE`. Имя базы данных.
        DATAFOLDER: `$APP_DB_DATAFOLDER`. Путь к папке с SQLite базой
            данных. По умолчанию `./data`.
        ECHO: `$APP_DB_ECHO`. Если True, SQLAlchemy будет логировать все
            SQL-запросы. Полезно для отладки. По умолчанию False.
        CHECKSCHEMA: `$APP_DB_CHECKSCHEMA`. Проверять схему базы данных
            на расхождения с базой данных? По умолчанию True.
        UPGRADEIFEMPTY: `$APP_DB_UPGRADEIFEMPTY`. Выполнять ли миграции,
            если база данных пуста? По умолчанию да.
    """

    DIALECT: str = "sqlite"
    DRIVER: str = "aiosqlite"
    USERNAME: str | None = None
    PASSWORD: SecretStr | None = None
    PASSWORDFILE: FilePath | None = None
    HOST: str | None = None
    PORT: int | None = None
    DATABASE: str | None = DATA_FOLDER_SENTIEL
    DATAFOLDER: Path | None = None

    ECHO: bool = False
    CHECKSCHEMA: bool = True
    UPGRADEIFEMPTY: bool = True

    @cached_property
    def database_url(self) -> URL:
        """DSN (URL) адрес для подключения к БД.

        Автоматически собирает URL-объект из отдельных атрибутов этого
        класса.

        Returns:
            URL адрес для инициализации движка базы данных.
        """
        if not self.DIALECT or not self.DRIVER:
            msg = "$APP_DB_DIALECT and $APP_DB_DRIVER must be set"
            raise ValueError(msg)

        if self.PASSWORD:
            password = self.PASSWORD.get_secret_value()
        elif self.PASSWORDFILE is not None:
            password = self.PASSWORDFILE.read_text()
        else:
            password = None

        return URL.create(
            drivername=f"{self.DIALECT}+{self.DRIVER}",
            username=self.USERNAME,
            password=password,
            host=self.HOST,
            port=self.PORT,
            database=self.get_database(),
        )

    def get_database(self) -> str | None:
        if self.DATABASE != DATA_FOLDER_SENTIEL:
            return self.DATABASE

        folder = self.DATAFOLDER

        if folder is None:
            folder = Path.cwd() / "data"

        folder.mkdir(parents=True, exist_ok=True)
        gitignore = folder / ".gitignore"

        if not gitignore.is_file():
            gitignore.write_text("*\n")

        path = folder / "db.sqlite"
        return str(path.absolute())

    @classmethod
    def from_url(
        cls, url: URL | str, *, echo: bool = False, checkschema: bool = True
    ) -> Self:
        url = make_url(url)
        dialect, driver = url.drivername.split("+")

        return cls(
            DIALECT=dialect,
            DRIVER=driver,
            USERNAME=url.username,
            PASSWORD=SecretStr(url.password)
            if url.password is not None
            else url.password,
            HOST=url.host,
            PORT=url.port,
            DATABASE=url.database,
            ECHO=echo,
            CHECKSCHEMA=checkschema,
        )


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
        PYPROJECT: `$APP_PYPROJECT`. Path to `pyproject.toml`.
    """

    HOST: str = "0.0.0.0"  # noqa: S104
    PORT: int = 8000
    RELOAD: bool = False
    STATICFILES: DirectoryPath = Path("./static")
    GRACEFULSHUTDOWNTIMEOUT: int = 10
    LOGGINGFORMAT: Literal["rich", "console", "structured"] = "console"
    DEBUG: bool = False
    PYPROJECT: FilePath = Path.cwd() / "pyproject.toml"

    db: DatabaseConfig = DatabaseConfig()

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="APP_",
        env_nested_delimiter="_",
        extra="ignore",
    )


settings: AppSettings = AppSettings()
