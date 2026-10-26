from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    import uuid
    from collections.abc import Sequence

    from server.domain.projects.schemas import ProjectPure

    from .schemas import Selection, SelectionCreate


class AbstractSelectionsRepo(Protocol):
    async def get(self, id: int) -> Selection | None: ...
    async def get_by_user(
        self, project_id: int, user_id: uuid.UUID
    ) -> Selection | None: ...
    async def get_users(self, project_id: int) -> Sequence[uuid.UUID]: ...
    async def create(
        self, project: ProjectPure, data: SelectionCreate, user_id: uuid.UUID
    ) -> None: ...
