from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
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
    ) -> dict[int, list[Comment]]:
        """Get lists of comments for multiple items.

        Args:
            item_ids: List of item ids.

        Returns:
            A mapping from ids to lists of comments. When item is not
                found, no error is thrown. Keys of resulting dictionary
                are formed only by existng items.
        """
        ...

    async def add_comment(
        self, item_id: int, data: CommentCreate
    ) -> Comment | None: ...
    async def approve_item(
        self, item_id: int, *, approved: bool = True
    ) -> None: ...
