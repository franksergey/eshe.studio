from dataclasses import dataclass
from typing import TYPE_CHECKING

from server.api.errors import (
    GroupNotFoundError,
    ItemNotFoundError,
    ProjectNotFoundError,
)

from .schemas import CommentsBulkRead

if TYPE_CHECKING:
    from server.domain.files.schemas import ImageRef

    from .ports import AbstractProjectsRepo
    from .schemas import (
        Comment,
        CommentCreate,
        GroupOnlyItems,
        GroupPure,
        Project,
        ProjectPure,
    )


@dataclass(eq=False, slots=True)
class ProjectsService:
    repo: AbstractProjectsRepo

    async def get(self, id: int) -> Project:
        obj = await self.repo.get(id)

        if obj is None:
            raise ProjectNotFoundError

        return obj

    async def get_pure(self, id: int) -> ProjectPure:
        obj = await self.repo.get_pure(id)

        if obj is None:
            raise ProjectNotFoundError

        return obj

    async def get_all(self) -> list[Project]:
        return await self.repo.get_all()

    async def get_all_pure(self) -> list[ProjectPure]:
        return await self.repo.get_all_pure()

    async def get_categories(
        self, project_id: int, group_id: int
    ) -> GroupOnlyItems:
        group = await self.repo.get_category(project_id, group_id)

        if group is None:
            raise GroupNotFoundError

        return group

    async def get_categories_pure(self, project_id: int) -> list[GroupPure]:
        return await self.repo.get_categories_pure(project_id)

    async def get_item_comments(self, item_id: int) -> list[Comment]:
        objs = await self.repo.get_item_comments(item_id)

        if objs is None:
            raise ItemNotFoundError

        return objs

    async def bulk_get_item_comments(
        self, item_ids: list[int]
    ) -> CommentsBulkRead:
        items, items_not_found = await self.repo.bulk_get_item_comments(
            item_ids
        )
        return CommentsBulkRead(
            items=items, item_ids_not_found=items_not_found
        )

    async def add_comment(self, item_id: int, data: CommentCreate) -> Comment:
        obj = await self.repo.add_comment(item_id, data)

        if obj is None:
            raise ItemNotFoundError

        return obj

    async def get_item_image(self, item_id: int) -> ImageRef | None:
        return await self.repo.get_item_image(item_id)

    async def attach_image(self, item_id: int, image_id: int) -> int | None:
        return await self.repo.attach_image(item_id, image_id)

    async def detach_image(self, item_id: int) -> int:
        if (id := await self.repo.detach_image(item_id)) is None:
            raise ItemNotFoundError

        return id

    async def approve_item(
        self, item_id: int, *, approved: bool = True
    ) -> None:
        await self.repo.approve_item(item_id, approved=approved)
