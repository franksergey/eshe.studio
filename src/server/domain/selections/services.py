from dataclasses import dataclass
from typing import TYPE_CHECKING

from server.api.errors import ChoiceNotFoundError

if TYPE_CHECKING:
    from server.domain.projects.schemas import Project
    from server.domain.users.schemas import UserRead

    from .ports import AbstractSelectionsRepo
    from .schemas import Choice, ChoiceCreate, ChoicePure


@dataclass(eq=False, slots=True)
class SelectionsService:
    repo: AbstractSelectionsRepo

    async def get(self, id: int) -> Choice:
        obj = await self.repo.get(id)

        if obj is None:
            raise ChoiceNotFoundError

        return obj

    async def get_by_user(self, user: UserRead) -> list[ChoicePure]:
        return await self.repo.get_by_user(user.id)

    async def create(
        self, project: Project, data: ChoiceCreate, user: UserRead
    ) -> None:
        await self.repo.create(project, data, user.id)
