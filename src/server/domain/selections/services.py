from dataclasses import dataclass
from typing import TYPE_CHECKING

from server.api.errors import SelectionNotFoundError

if TYPE_CHECKING:
    from server.domain.projects.schemas import Project
    from server.domain.users.schemas import UserRead

    from .ports import AbstractSelectionsRepo
    from .schemas import Selection, SelectionCreate, SelectionPure


@dataclass(eq=False, slots=True)
class SelectionsService:
    repo: AbstractSelectionsRepo

    async def get(self, id: int) -> Selection:
        obj = await self.repo.get(id)

        if obj is None:
            raise SelectionNotFoundError

        return obj

    async def get_by_user(self, user: UserRead) -> list[SelectionPure]:
        return await self.repo.get_by_user(user.id)

    async def create(
        self, project: Project, data: SelectionCreate, user: UserRead
    ) -> None:
        await self.repo.create(project, data, user.id)
