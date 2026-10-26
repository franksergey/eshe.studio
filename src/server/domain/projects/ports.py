from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from server.domain.files.schemas import ImageRef
    from server.domain.projects.schemas import ItemID
    from server.domain.users.schemas import UserID

    from .schemas import (
        Comment,
        CommentCreate,
        GroupOnlyItems,
        GroupPure,
        Item,
        ItemOnlyComments,
        Project,
        ProjectPure,
    )


class AbstractProjectsRepo(Protocol):
    async def get(self, id: int) -> Project | None: ...
    async def get_pure(self, id: int) -> ProjectPure | None: ...
    async def get_all(self) -> list[Project]: ...
    async def get_all_pure(self) -> list[ProjectPure]: ...
    async def get_category(
        self, project_id: int, group_id: int
    ) -> GroupOnlyItems | None: ...
    async def get_categories_pure(
        self, project_id: int
    ) -> list[GroupPure]: ...
    async def check_item_exists(self, item_id: int) -> bool: ...
    async def get_item(self, item_id: ItemID) -> Item | None: ...
    async def get_item_comments(
        self, item_id: ItemID
    ) -> list[Comment] | None: ...
    async def bulk_get_item_comments(
        self, item_ids: list[ItemID]
    ) -> tuple[list[ItemOnlyComments], list[ItemID]]:
        """Get lists of comments for multiple items.

        Args:
            item_ids: List of item ids.

        Returns:
            A list of items with comments and a list of item ids that
                weren't found.
        """
        ...

    async def add_comment(
        self, item_id: ItemID, user_id: UserID, data: CommentCreate
    ) -> Comment | None: ...
    async def get_item_image(self, item_id: ItemID) -> ImageRef | None: ...
    async def attach_image(
        self, item_id: ItemID, image_id: int
    ) -> int | None: ...
    async def detach_image(self, item_id: ItemID) -> int | None: ...
    async def approve_item(
        self, item_id: ItemID, *, approved: bool = True
    ) -> None: ...
