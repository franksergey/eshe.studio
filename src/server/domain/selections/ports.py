from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Sequence

    from server.domain.projects.schemas import ProjectID, ProjectPure
    from server.domain.users.schemas import UserID

    from .schemas import Selection, SelectionCreate, SelectionPure


class AbstractSelectionsRepo(Protocol):
    async def get(self, id: int) -> Selection | None: ...
    async def get_by_user(
        self, project_id: ProjectID, user_id: UserID
    ) -> Selection | None: ...
    async def get_users(self, project_id: ProjectID) -> Sequence[UserID]: ...
    async def get_for_project(
        self, project_id: ProjectID
    ) -> Sequence[SelectionPure]: ...
    async def create(
        self, project: ProjectPure, data: SelectionCreate, user_id: UserID
    ) -> None: ...
