from collections.abc import AsyncGenerator, Callable
from typing import TYPE_CHECKING, Annotated, Any

from fastapi import Depends

from server.api.container import ServiceContainer

if TYPE_CHECKING:
    from fastapi import Request

    from server.api.container import ContainerGetter


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
