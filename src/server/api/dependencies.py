import asyncio
from collections.abc import AsyncGenerator, Callable
from typing import Annotated, Any

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from server.api.container import ServiceContainer


def dependency[FuncT: Callable[..., Any]](function: FuncT) -> FuncT:
    return function


@dependency
async def get_session(request: Request) -> AsyncGenerator[AsyncSession]:
    """Получить объект асинхронной сессии базы данных.

    Returns:
        Управляемый генератором объект сессии. Метод `AsyncSession.commit`
            и похожие методы не должны быть вызваны за пределами генератора.
    """
    get_session: Callable[[], AsyncSession] = request.state.get_session

    async with get_session() as session:
        try:
            yield session
        except:
            await asyncio.shield(session.rollback())
            raise
        else:
            await asyncio.shield(session.commit())


AsyncSessionDependency = Annotated[AsyncSession, Depends(get_session)]


@dependency
async def get_container(
    session: AsyncSessionDependency,
) -> AsyncGenerator[ServiceContainer]:
    """Получить объект контейнера сервисов бизнес-логики.

    Returns:
        Объект, через который можно получить доступ к готовым объектам
            сервисов бизнес-логики для выполнения операций.
    """
    yield ServiceContainer(session)


ContainerDependency = Annotated[ServiceContainer, Depends(get_container)]
