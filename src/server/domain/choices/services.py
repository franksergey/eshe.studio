from dataclasses import dataclass
from typing import TYPE_CHECKING

from server.api.errors import ChoiceNotFoundError

if TYPE_CHECKING:
    from server.domain.users.schemas import UserRead

    from .ports import AbstractChoicesRepo
    from .schemas import Choice, ChoiceCreate


@dataclass(eq=False, slots=True)
class ChoicesService:
    repo: AbstractChoicesRepo

    async def get(self, id: int) -> Choice:
        obj = await self.repo.get(id)

        if obj is None:
            raise ChoiceNotFoundError

        return obj

    async def get_by_user(self, user: UserRead) -> list[Choice]:
        return await self.repo.get_by_user(user.id)

    async def create(self, data: ChoiceCreate, user: UserRead) -> None:
        await self.repo.create(data, user.id)
