from dataclasses import dataclass
from typing import TYPE_CHECKING

from server.api.errors import SelectionNotFoundError

if TYPE_CHECKING:
    from collections.abc import Sequence

    from server.domain.projects.schemas import ProjectID, ProjectPure
    from server.domain.selections.schemas import SelectionPure
    from server.domain.users.schemas import UserID, UserRead

    from .ports import AbstractSelectionsRepo
    from .schemas import Selection, SelectionCreate


@dataclass(eq=False, slots=True)
class SelectionsService:
    repo: AbstractSelectionsRepo

    async def get(self, id: int) -> Selection:
        obj = await self.repo.get(id)

        if obj is None:
            raise SelectionNotFoundError

        return obj

    async def get_by_user(
        self, project_id: ProjectID, user: UserRead
    ) -> Selection | None:
        return await self.repo.get_by_user(project_id, user.id)

    async def get_users(self, project_id: ProjectID) -> Sequence[UserID]:
        return await self.repo.get_users(project_id)

    async def get_for_project(
        self, project_id: ProjectID
    ) -> Sequence[SelectionPure]:
        return await self.repo.get_for_project(project_id)

    async def create(
        self, project: ProjectPure, data: SelectionCreate, user: UserRead
    ) -> None:
        await self.repo.create(project, data, user.id)
