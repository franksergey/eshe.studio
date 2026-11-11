from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from server.domain.files.schemas import ImageID, ImageRef
    from server.domain.users.schemas import UserID

    from .schemas import (
        Comment,
        CommentCreate,
        GroupID,
        GroupOnlyItems,
        GroupPure,
        Item,
        ItemID,
        ItemOnlyComments,
        Project,
        ProjectID,
        ProjectPure,
    )


class AbstractProjectsRepo(Protocol):
    # Projects-related
    async def get(self, id: ProjectID) -> Project | None: ...
    async def get_pure(self, id: ProjectID) -> ProjectPure | None: ...
    async def get_all(self) -> list[Project]: ...
    async def get_all_pure(self) -> list[ProjectPure]: ...

    # Groups-related
    async def get_category(
        self, project_id: GroupID, group_id: GroupID
    ) -> GroupOnlyItems | None: ...
    async def get_categories_pure(
        self, project_id: ProjectID
    ) -> list[GroupPure]: ...

    # Items-related
    async def check_item_exists(self, item_id: ItemID) -> bool: ...
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
        self, item_id: ItemID, image_id: ImageID
    ) -> ImageID | None: ...
    async def detach_image(self, item_id: ItemID) -> ImageID | None: ...
