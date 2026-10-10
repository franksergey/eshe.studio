import asyncio
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from fastapi_users.db import SQLAlchemyUserDatabase

from server.domain.projects.service import ProjectsService
from server.sql.models import UserDB
from server.sql.repos import ProjectsRepo

from .auth import UserManager

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Callable
    from contextlib import AbstractAsyncContextManager

    from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(eq=False, slots=True)
class ServiceContainer:
    session: AsyncSession
    _specification_service: ProjectsService | None = None

    @property
    def specifications(self) -> ProjectsService:
        if self._specification_service is None:
            repo = ProjectsRepo(self.session)
            self._specification_service = ProjectsService(repo)

        return self._specification_service

    _user_manager: UserManager | None = None

    @property
    def user_manager(self) -> UserManager:
        if self._user_manager is None:
            user_db = SQLAlchemyUserDatabase[UserDB, uuid.UUID](
                self.session, UserDB
            )
            self._user_manager = UserManager(user_db)

        return self._user_manager


class ContainerGetter(Protocol):
    def __call__(self) -> AbstractAsyncContextManager[ServiceContainer]:
        raise NotImplementedError


def container_getter(
    sessionmaker: Callable[[], AsyncSession],
) -> ContainerGetter:
    @asynccontextmanager
    async def get_container() -> AsyncGenerator[ServiceContainer]:
        async with sessionmaker() as session:
            try:
                yield ServiceContainer(session)
            except:
                await asyncio.shield(session.rollback())
                raise
            else:
                await asyncio.shield(session.commit())

    return get_container
