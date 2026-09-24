import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
from functools import cached_property
from typing import TYPE_CHECKING, Protocol

from server.services.specification import SpecificationService
from server.sql.repos import SpecificationRepo

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Callable
    from contextlib import AbstractAsyncContextManager

    from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(eq=False, slots=True)
class ServiceContainer:
    session: AsyncSession

    @cached_property
    def _specification_repo(self) -> SpecificationRepo:
        return SpecificationRepo(self.session)

    @cached_property
    def specifications(self) -> SpecificationService:
        return SpecificationService(self._specification_repo)


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
