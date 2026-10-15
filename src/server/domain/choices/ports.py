from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    import uuid

    from server.domain.projects.schemas import Project

    from .schemas import Choice, ChoiceCreate, ChoicePure


class AbstractChoicesRepo(Protocol):
    async def get(self, id: int) -> Choice | None: ...
    async def get_by_user(self, user_id: uuid.UUID) -> list[ChoicePure]: ...
    async def create(
        self, project: Project, data: ChoiceCreate, user_id: uuid.UUID
    ) -> None: ...
