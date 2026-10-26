from dataclasses import dataclass
from typing import TYPE_CHECKING

from server.api.errors import UserNotFoundError

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from server.domain.users.schemas import UserID

    from .ports import AbstractUsersRepo
    from .schemas import UserCreate, UserRead, UserUpdate


@dataclass(eq=False, slots=True)
class UsersService:
    repo: AbstractUsersRepo

    async def get(self, id: UserID) -> UserRead:
        user = await self.repo.get(id)

        if user is None:
            raise UserNotFoundError

        return user

    async def get_by_email(self, user_email: str) -> UserRead:
        user = await self.repo.get_by_email(user_email)

        if user is None:
            raise UserNotFoundError

        return user

    async def bulk_get_users(
        self, user_ids: Iterable[UserID]
    ) -> Sequence[UserRead]:
        return await self.repo.bulk_get_users(user_ids)

    async def users_table_empty(self) -> bool:
        return await self.repo.users_table_empty()

    async def create(
        self, data: UserCreate, *, safe: bool = False
    ) -> UserRead:
        return await self.repo.create(data, safe=safe)

    async def update(
        self, user_email: str, data: UserUpdate, *, safe: bool = False
    ) -> UserRead:
        updated = await self.repo.update(user_email, data, safe=safe)

        if updated is None:
            raise UserNotFoundError

        return updated

    async def delete(self, user_email: str) -> UserRead:
        deleted = await self.repo.delete(user_email)

        if deleted is None:
            raise UserNotFoundError

        return deleted
