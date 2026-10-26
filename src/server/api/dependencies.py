from collections.abc import AsyncGenerator, Callable
from typing import Annotated, Any

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers

from server.api.auth import auth_backend
from server.domain.users.schemas import UserID, UserRead

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
) -> AsyncGenerator[BaseUserManager[UserRead, UserID]]:
    yield container.user_manager


fastapi_users = FastAPIUsers[UserRead, UserID](
    # BUG: Swapped type params # pyrefly: ignore [bad-argument-type]
    get_user_manager,
    [auth_backend],
)


OptionalUserDependency = Annotated[
    UserRead | None, Depends(fastapi_users.current_user(optional=True))
]
CurrentUserDependency = Annotated[
    UserRead, Depends(fastapi_users.current_user())
]
CurrentActiveUserDependency = Annotated[
    UserRead, Depends(fastapi_users.current_user(active=True))
]
CurrentVerifiedUserDependency = Annotated[
    UserRead, Depends(fastapi_users.current_user(active=True, verified=True))
]
CurrentSuperuserDependency = Annotated[
    UserRead, Depends(fastapi_users.current_user(active=True, superuser=True))
]
