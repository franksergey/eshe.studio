from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from server.domain.projects.schemas import Project
    from server.domain.users.schemas import UserID

    from .schemas import Choice, ChoiceCreate, ChoicePure


class AbstractChoicesRepo(Protocol):
    async def get(self, id: int) -> Choice | None: ...
    async def get_by_user(self, user_id: UserID) -> list[ChoicePure]: ...
    async def create(
        self, project: Project, data: ChoiceCreate, user_id: UserID
    ) -> None: ...
