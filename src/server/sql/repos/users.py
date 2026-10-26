from dataclasses import dataclass
from typing import TYPE_CHECKING

from fastapi_users import exceptions
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy import select

from server.api.errors import UserAlreadyExistsError
from server.domain.users.ports import AbstractUsersRepo
from server.domain.users.schemas import (
    UserCreate,
    UserID,
    UserRead,
    UserUpdate,
)
from server.sql.models import UserDB

if TYPE_CHECKING:
    from fastapi import Request

    from server.api.auth import UserManager


class UserDatabase(SQLAlchemyUserDatabase[UserDB, UserID]):
    async def users_table_empty(self) -> bool:
        stmt = select(select(self.user_table).exists())
        return not (await self.session.execute(stmt)).scalar_one()


@dataclass(eq=False, slots=True)
class UsersRepo(AbstractUsersRepo):
    users_db: UserDatabase
    user_manager: UserManager
    request: Request | None

    @staticmethod
    def _to_domain_schema(user: UserDB) -> UserRead:
        return UserRead(
            id=user.id,
            email=user.email,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            is_verified=user.is_verified,
        )

    async def get(self, id: UserID) -> UserRead | None:
        user = await self.users_db.get(id)

        if user is None:
            return None

        return self._to_domain_schema(user)

    async def get_by_email(self, user_email: str) -> UserRead | None:
        user = await self.users_db.get_by_email(user_email)

        if user is None:
            return None

        return self._to_domain_schema(user)

    async def users_table_empty(self) -> bool:
        return await self.users_db.users_table_empty()

    async def create(
        self, data: UserCreate, *, safe: bool = False
    ) -> UserRead:
        try:
            return self._to_domain_schema(
                await self.user_manager.create(
                    data, safe=safe, request=self.request
                )
            )
        except exceptions.UserAlreadyExists as exc:
            raise UserAlreadyExistsError from exc

    async def update(
        self, user_email: str, data: UserUpdate, *, safe: bool = False
    ) -> UserRead | None:
        user = await self.users_db.get_by_email(user_email)

        if user is None:
            return None

        return self._to_domain_schema(
            await self.user_manager.update(
                data, user, safe=safe, request=self.request
            )
        )

    async def delete(self, user_email: str) -> UserRead | None:
        user = await self.users_db.get_by_email(user_email)

        if user is None:
            return None

        await self.user_manager.delete(user, self.request)
        return self._to_domain_schema(user)
