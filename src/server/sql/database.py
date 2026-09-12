import logging
from contextlib import AbstractAsyncContextManager
from textwrap import dedent
from typing import TYPE_CHECKING, Any, Self, override

from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext
from sqlalchemy import Connection, make_url
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

if TYPE_CHECKING:
    from types import TracebackType

    import sqlalchemy
    from sqlalchemy.engine.url import URL
    from sqlalchemy.ext.asyncio import AsyncEngine
    from sqlalchemy.orm import DeclarativeBase


logger = logging.getLogger(__name__)


class DatabaseSchemaMismatchError(Exception):
    def __init__(self, *args: object, db_url: URL | None = None) -> None:
        super().__init__(*args)

        if db_url is not None:
            self.add_note(f"NOTE: Database URL is:\n    {db_url}")


class Database(AbstractAsyncContextManager["Database"]):
    url: sqlalchemy.URL

    engine: AsyncEngine
    sessionmaker: async_sessionmaker[AsyncSession]

    def __init__(self, db_url: str | URL, *, echo: bool = False) -> None:
        url = make_url(db_url)
        self.url = url

        self.init_engine(echo=echo)
        self.sessionmaker = self.get_session = async_sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
            class_=AsyncSession,
        )

        logger.info("Создан и настроен новый объект базы данных")
        logger.debug("Используется URL базы данных: %s", self.url)

    def init_engine(self, *, echo: bool = False) -> None:
        return self._init_engine(echo=echo)

    def _init_engine(
        self, connect_args: dict[Any, Any] | None = None, *, echo: bool = False
    ) -> None:
        if hasattr(self, "engine"):
            msg = "Method `init_engine` must be called only once"
            raise RuntimeError(msg)

        self.engine = create_async_engine(
            self.url,
            echo=echo,  # Логирование SQL-запросов
            future=True,
            pool_pre_ping=True,  # Проверка соединения перед использованием
            connect_args=connect_args,
        )

    @override
    async def __aenter__(self) -> Self:
        return self

    @override
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        await self.engine.dispose()
        logger.info("Объект базы данных был закрыт")

    def get_session(self) -> AsyncSession:
        raise NotImplementedError


class DatabaseChecker:
    declarative_base: type[DeclarativeBase]
    database: Database

    def __init__(
        self, base: type[DeclarativeBase], database: Database
    ) -> None:
        self.declarative_base = base
        self.database = database

    def compare_metadata(self, connection: Connection) -> list[Any]:
        return self._compare_metadata(connection)

    def _compare_metadata(
        self, connection: Connection, opts: dict[Any, Any] | None = None
    ) -> list[Any]:
        opts_arg: dict[Any, Any] = {
            "compare_type": True,
            "compare_server_default": True,
        }

        if opts is not None:
            opts_arg.update(opts)

        context = MigrationContext.configure(connection, opts=opts_arg)
        return compare_metadata(context, self.declarative_base.metadata)

    async def check_schema(self) -> bool:
        async with self.database.engine.connect() as connection:
            diff = await connection.run_sync(self.compare_metadata)

        result = not diff

        if result:
            logger.info("Содержимое БД полностью соответствует схеме.")
        else:
            logger.warning("Содержимое БД и схема расходятся. Различия:")

            for d in diff:
                logger.debug("%r", d)

        return result

    async def raise_for_differences(self) -> None:
        if not await self.check_schema():
            msg = dedent("""\
            База данных не соответствует схеме.

            Это значит, что вы изменили содержимое модуля adapters.db.models
            без создания или применения необходимых миграций. Используйте
            команду alembic revision для генерации миграций. Используйте
            alembic upgrade для их применения.
            """)
            raise DatabaseSchemaMismatchError(msg, db_url=self.database.url)
