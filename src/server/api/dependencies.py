import asyncio
import uuid
from collections.abc import AsyncGenerator, Callable
from typing import Annotated, Any

from fastapi import Depends, Request
from fastapi_users import BaseUserManager
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from server.sql.models import UserDB

from .auth import UserManager
from .container import ServiceContainer


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
async def get_container(session: AsyncSessionDependency) -> ServiceContainer:
    """Получить объект контейнера сервисов бизнес-логики.

    Returns:
        Объект, через который можно получить доступ к готовым объектам
            сервисов бизнес-логики для выполнения операций.
    """
    return ServiceContainer(session)


ContainerDependency = Annotated[ServiceContainer, Depends(get_container)]


@dependency
async def get_user_database(
    session: AsyncSessionDependency,
) -> SQLAlchemyUserDatabase[UserDB, uuid.UUID]:
    return SQLAlchemyUserDatabase(session, UserDB)


UserDatabaseDependency = Annotated[
    SQLAlchemyUserDatabase[UserDB, uuid.UUID], Depends(get_user_database)
]


@dependency
async def get_user_manager(
    user_database: UserDatabaseDependency,
) -> AsyncGenerator[BaseUserManager[UserDB, uuid.UUID]]:
    yield UserManager(user_database)
