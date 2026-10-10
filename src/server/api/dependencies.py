import uuid
from collections.abc import AsyncGenerator, Callable
from typing import Annotated, Any

from fastapi import Depends, Request
from fastapi_users import BaseUserManager

from server.sql.models import UserDB

from .container import ContainerGetter, ServiceContainer


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

    async with getter(request) as container:
        yield container


ContainerDependency = Annotated[ServiceContainer, Depends(get_container)]


@dependency
async def get_user_manager(
    container: ContainerDependency,
) -> AsyncGenerator[BaseUserManager[UserDB, uuid.UUID]]:
    yield container.user_manager
