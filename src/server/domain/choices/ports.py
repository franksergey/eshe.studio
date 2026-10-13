from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    import uuid

    from .schemas import Choice, ChoiceCreate


class AbstractChoicesRepo(Protocol):
    async def get(self, id: int) -> Choice | None: ...
    async def get_by_user(self, user_id: uuid.UUID) -> list[Choice]: ...
    async def create(self, data: ChoiceCreate, user_id: uuid.UUID) -> None: ...
