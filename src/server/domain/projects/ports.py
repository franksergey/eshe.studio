from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from server.domain.projects.schemas import ItemOnlyComments

    from .schemas import Comment, CommentCreate, Item, Project, ProjectPure


class AbstractProjectsRepo(Protocol):
    async def get(self, id: int) -> Project | None: ...
    async def get_pure(self, id: int) -> ProjectPure | None: ...
    async def get_all(self) -> list[Project]: ...
    async def get_all_pure(self) -> list[ProjectPure]: ...
    async def check_item_exists(self, item_id: int) -> bool: ...
    async def get_item(self, item_id: int) -> Item | None: ...
    async def get_item_comments(
        self, item_id: int
    ) -> list[Comment] | None: ...
    async def bulk_get_item_comments(
        self, item_ids: list[int]
    ) -> tuple[list[ItemOnlyComments], list[int]]:
        """Get lists of comments for multiple items.

        Args:
            item_ids: List of item ids.

        Returns:
            A list of items with comments and a list of item ids that
                weren't found.
        """
        ...

    async def add_comment(
        self, item_id: int, data: CommentCreate
    ) -> Comment | None: ...
    async def approve_item(
        self, item_id: int, *, approved: bool = True
    ) -> None: ...
