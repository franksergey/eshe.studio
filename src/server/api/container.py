import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from server.domain.projects.service import ProjectsService
from server.domain.users.service import UsersService
from server.sql.models import UserDB
from server.sql.repos import ProjectsRepo, UserDatabase, UsersRepo

from .auth import UserManager

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Callable
    from contextlib import AbstractAsyncContextManager

    from fastapi import Request
    from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(eq=False, slots=True)
class ServiceContainer:
    session: AsyncSession
    request: Request | None

    _specification_service: ProjectsService | None = None

    @property
    def specifications(self) -> ProjectsService:
        if self._specification_service is None:
            repo = ProjectsRepo(self.session)
            self._specification_service = ProjectsService(repo)

        return self._specification_service

    _users_service: UsersService | None = None

    @property
    def users(self) -> UsersService:
        if self._users_service is None:
            repo = UsersRepo(self.user_db, self.user_manager, self.request)
            self._users_service = UsersService(repo)

        return self._users_service

    _user_db: UserDatabase | None = None

    @property
    def user_db(self) -> UserDatabase:
        if self._user_db is None:
            self._user_db = UserDatabase(self.session, UserDB)

        return self._user_db

    _user_manager: UserManager | None = None

    @property
    def user_manager(self) -> UserManager:
        if self._user_manager is None:
            self._user_manager = UserManager(self.user_db)

        return self._user_manager


class ContainerGetter(Protocol):
    def __call__(
        self, request: Request | None = None
    ) -> AbstractAsyncContextManager[ServiceContainer]:
        raise NotImplementedError


def container_getter(
    sessionmaker: Callable[[], AsyncSession],
) -> ContainerGetter:
    @asynccontextmanager
    async def get_container(
        request: Request | None = None,
    ) -> AsyncGenerator[ServiceContainer]:
        async with sessionmaker() as session:
            try:
                yield ServiceContainer(session, request)
            except:
                await asyncio.shield(session.rollback())
                raise
            else:
                await asyncio.shield(session.commit())

    return get_container
