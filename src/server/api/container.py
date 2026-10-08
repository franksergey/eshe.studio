import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from server.domain.projects.service import ProjectsService
from server.sql.repos import ProjectsRepo

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
