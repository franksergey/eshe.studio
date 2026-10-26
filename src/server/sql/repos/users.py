from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from fastapi_users import exceptions
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlalchemy import delete, func, select, update

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
    from fastapi_users.models import OAuthAccountProtocol
    from fastapi_users_db_sqlalchemy import SQLAlchemyBaseOAuthAccountTable
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.sql.selectable import TypedReturnsRows

    from server.api.auth import UserManager


class UserDatabase(SQLAlchemyUserDatabase[UserRead, UserID]):
    # Both left uninitialized as these are not meant to be used
    user_table: type[UserRead]
    oauth_account_table: type[SQLAlchemyBaseOAuthAccountTable[UserID]] | None

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _to_domain_schema(user: UserDB) -> UserRead:
        return UserRead(
            id=user.id,
            hashed_password=user.hashed_password,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            is_verified=user.is_verified,
        )

    async def _get_unique[T](
        self, stmt: TypedReturnsRows[tuple[T]]
    ) -> T | None:
        results = await self.session.execute(stmt)
        return results.unique().scalar_one_or_none()

    @override
    async def get(self, id: UserID) -> UserRead | None:
        stmt = select(UserDB).where(UserDB.id == id)

        if (obj := await self._get_unique(stmt)) is None:
            return None

        return self._to_domain_schema(obj)

    @override
    async def get_by_email(self, email: str) -> UserRead | None:
        stmt = select(UserDB).where(
            func.lower(UserDB.email) == func.lower(email)
        )
        if (obj := await self._get_unique(stmt)) is None:
            return None

        return self._to_domain_schema(obj)

    @override
    async def get_by_oauth_account(
        self, oauth: str, account_id: str
    ) -> UserRead | None:
        raise NotImplementedError

    @override
    async def create(self, create_dict: dict[str, object]) -> UserRead:
        user = UserDB(**create_dict)
        self.session.add(user)

        await self.session.flush((user,))
        return self._to_domain_schema(user)

    @override
    async def update(
        self, user: UserRead, update_dict: dict[str, object]
    ) -> UserRead:
        stmt = (
            update(UserDB)
            .where(UserDB.id == user.id)
            .values(**update_dict)
            .returning(UserDB)
        )

        if (obj := await self._get_unique(stmt)) is None:
            msg = "Unreachable"
            raise RuntimeError(msg)

        return self._to_domain_schema(obj)

    @override
    async def delete(self, user: UserRead) -> None:
        stmt = delete(UserDB).where(UserDB.id == user.id)
        await self.session.execute(stmt)

    @override
    async def add_oauth_account(
        self, user: UserRead, create_dict: dict[str, object]
    ) -> UserRead:
        raise NotImplementedError

    @override
    async def update_oauth_account(
        self,
        user: UserRead,
        oauth_account: OAuthAccountProtocol[UserID],
        update_dict: dict[str, object],
    ) -> UserRead:
        raise NotImplementedError

    async def users_table_empty(self) -> bool:
        stmt = select(select(UserDB).exists())
        return not (await self.session.execute(stmt)).scalar_one()


@dataclass(eq=False, slots=True)
class UsersRepo(AbstractUsersRepo):
    users_db: UserDatabase
    user_manager: UserManager
    request: Request | None

    async def get(self, id: UserID) -> UserRead | None:
        return await self.users_db.get(id)

    async def get_by_email(self, user_email: str) -> UserRead | None:
        return await self.users_db.get_by_email(user_email)

    async def users_table_empty(self) -> bool:
        return await self.users_db.users_table_empty()

    async def create(
        self, data: UserCreate, *, safe: bool = False
    ) -> UserRead:
        try:
            return await self.user_manager.create(
                data, safe=safe, request=self.request
            )

        except exceptions.UserAlreadyExists as exc:
            raise UserAlreadyExistsError from exc

    async def update(
        self, user_email: str, data: UserUpdate, *, safe: bool = False
    ) -> UserRead | None:
        user = await self.users_db.get_by_email(user_email)

        if user is None:
            return None

        return await self.user_manager.update(
            data, user, safe=safe, request=self.request
        )

    async def delete(self, user_email: str) -> UserRead | None:
        user = await self.users_db.get_by_email(user_email)

        if user is None:
            return None

        await self.user_manager.delete(user, self.request)
        return user
