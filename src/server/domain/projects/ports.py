from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from .schemas import (
        Comment,
        CommentCreate,
        Specification,
        SpecificationPure,
    )


class AbstractSpecificationRepo(Protocol):
    async def get(self, id: int) -> Specification | None: ...
    async def get_all(self) -> list[Specification]: ...
    async def get_all_pure(self) -> list[SpecificationPure]: ...
    async def check_item_exists(self, item_id: int) -> bool: ...
    async def get_item_comments(
        self, item_id: int
    ) -> list[Comment] | None: ...
    async def add_comment(
        self, item_id: int, data: CommentCreate
    ) -> Comment | None: ...
