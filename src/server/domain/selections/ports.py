from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    import uuid

    from server.domain.projects.schemas import Project

    from .schemas import Selection, SelectionCreate, SelectionPure


class AbstractSelectionsRepo(Protocol):
    async def get(self, id: int) -> Selection | None: ...
    async def get_by_user(self, user_id: uuid.UUID) -> list[SelectionPure]: ...
    async def create(
        self, project: Project, data: SelectionCreate, user_id: uuid.UUID
    ) -> None: ...
