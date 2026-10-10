import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable
from typing import Annotated, Any

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers

from server.api.auth import auth_backend
from server.domain.users.schemas import UserRead
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


fastapi_users = FastAPIUsers[UserDB, uuid.UUID](
    # BUG: Swapped type params # pyrefly: ignore [bad-argument-type]
    get_user_manager,
    [auth_backend],
)


def make_current_user_dependency(
    *,
    optional: bool = False,
    active: bool = False,
    verified: bool = False,
    superuser: bool = False,
) -> Callable[..., Awaitable[UserRead | None]]:
    dep = fastapi_users.current_user(
        optional=optional,
        active=active,
        verified=verified,
        superuser=superuser,
    )

    async def wrapper(
        obj: Annotated[UserDB | None, Depends(dep)],
    ) -> UserRead | None:
        if obj is None:
            return None

        return UserRead(
            id=obj.id,
            email=obj.email,
            is_active=obj.is_active,
            is_superuser=obj.is_superuser,
            is_verified=obj.is_verified,
        )

    return wrapper


CurrentUserDependency = Annotated[
    UserRead, Depends(make_current_user_dependency())
]
CurrentActiveUserDependency = Annotated[
    UserRead, Depends(make_current_user_dependency(active=True))
]
CurrentVerifiedUserDependency = Annotated[
    UserRead, Depends(make_current_user_dependency(active=True, verified=True))
]
CurrentSuperuserDependency = Annotated[
    UserRead,
    Depends(make_current_user_dependency(active=True, superuser=True)),
]
