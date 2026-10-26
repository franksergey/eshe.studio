from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Sequence

    from server.domain.projects.schemas import ProjectPure
    from server.domain.selections.schemas import SelectionPure
    from server.domain.users.schemas import UserID

    from .schemas import Selection, SelectionCreate


class AbstractSelectionsRepo(Protocol):
    async def get(self, id: int) -> Selection | None: ...
    async def get_by_user(
        self, project_id: int, user_id: UserID
    ) -> Selection | None: ...
    async def get_users(self, project_id: int) -> Sequence[UserID]: ...
    async def get_for_project(
        self, project_id: int
    ) -> Sequence[SelectionPure]: ...
    async def create(
        self, project: ProjectPure, data: SelectionCreate, user_id: UserID
    ) -> None: ...
