from collections.abc import AsyncGenerator, Callable
from typing import Annotated, Any

from fastapi import Depends, Request

from server.api.container import ContainerGetter, ServiceContainer


def dependency[FuncT: Callable[..., Any]](function: FuncT) -> FuncT:
    return function


@dependency
async def get_container(request: Request) -> AsyncGenerator[ServiceContainer]:
    """Получить объект контейнера сервисов бизнес-логики.

    Returns:
        Объект, через который можно получить доступ к готовым объектам
            сервисов бизнес-логики для выполнения операций.
    """
    getter: ContainerGetter = request.state.get_container

    async with getter() as container:
        yield container


ContainerDependency = Annotated[ServiceContainer, Depends(get_container)]
