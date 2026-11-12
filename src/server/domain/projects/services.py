from dataclasses import dataclass
from typing import TYPE_CHECKING

from server.api.errors import (
    GroupNotFoundError,
    ItemNotFoundError,
    ProjectNotFoundError,
)

from .schemas import CommentsBulkRead

if TYPE_CHECKING:
    from server.domain.files.schemas import ImageID, ImageRef
    from server.domain.projects.admin_schemas import (
        AdminItemPure,
        ItemCreate,
        ItemPut,
    )
    from server.domain.users.schemas import UserRead

    from .admin_schemas import (
        AdminGroupPure,
        AdminProject,
        AdminProjectPure,
        GroupCreate,
        GroupPut,
        ProjectCreate,
        ProjectPut,
        ProjectUpdate,
    )
    from .ports import AbstractProjectsRepo
    from .schemas import (
        Comment,
        CommentCreate,
        GroupID,
        GroupOnlyItems,
        GroupPure,
        ItemID,
        Project,
        ProjectID,
        ProjectPure,
    )


@dataclass(eq=False, slots=True)
class ProjectsService:
    repo: AbstractProjectsRepo

    # Projects-related

    async def get(self, id: ProjectID) -> Project:
        obj = await self.repo.get(id)

        if obj is None:
            raise ProjectNotFoundError

        return obj

    async def get_pure(self, id: ProjectID) -> ProjectPure:
        obj = await self.repo.get_pure(id)

        if obj is None:
            raise ProjectNotFoundError

        return obj

    async def get_all(self) -> list[Project]:
        return await self.repo.get_all()

    async def get_all_pure(self) -> list[ProjectPure]:
        return await self.repo.get_all_pure()

    # Groups-related

    async def get_categories(
        self, project_id: ProjectID, group_id: GroupID
    ) -> GroupOnlyItems:
        group = await self.repo.get_category(project_id, group_id)

        if group is None:
            raise GroupNotFoundError

        return group

    async def get_categories_pure(
        self, project_id: ProjectID
    ) -> list[GroupPure]:
        return await self.repo.get_categories_pure(project_id)

    # Items-related

    async def get_item_comments(self, item_id: ItemID) -> list[Comment]:
        objs = await self.repo.get_item_comments(item_id)

        if objs is None:
            raise ItemNotFoundError

        return objs

    async def bulk_get_item_comments(
        self, item_ids: list[ItemID]
    ) -> CommentsBulkRead:
        items, items_not_found = await self.repo.bulk_get_item_comments(
            item_ids
        )
        return CommentsBulkRead(
            items=items, item_ids_not_found=items_not_found
        )

    async def add_comment(
        self, item_id: ItemID, user: UserRead, data: CommentCreate
    ) -> Comment:
        obj = await self.repo.add_comment(item_id, user.id, data)

        if obj is None:
            raise ItemNotFoundError

        return obj

    async def get_item_image(self, item_id: ItemID) -> ImageRef | None:
        return await self.repo.get_item_image(item_id)

    async def attach_image(
        self, item_id: ItemID, image_id: ImageID
    ) -> ImageID | None:
        return await self.repo.attach_image(item_id, image_id)

    async def detach_image(self, item_id: ItemID) -> ImageID:
        if (id := await self.repo.detach_image(item_id)) is None:
            raise ItemNotFoundError

        return id


ORDINAL_NO_STEP = 10_000


@dataclass(eq=False, slots=True)
class AdminProjectService:
    repo: AbstractProjectsRepo

    # Projects-related methods

    async def create(self, data: ProjectCreate) -> AdminProjectPure:
        return await self.repo.create(data)

    async def update(
        self, id: ProjectID, data: ProjectUpdate
    ) -> AdminProjectPure:
        if (obj := await self.repo.update(id, data)) is None:
            raise ProjectNotFoundError

        return obj

    async def put(self, id: ProjectID, data: ProjectPut) -> ProjectPure:
        if (obj := await self.repo.put(id, data)) is None:
            raise ProjectNotFoundError

        return obj

    async def remove(self, id: ProjectID) -> AdminProject:
        if (obj := await self.repo.remove(id)) is None:
            raise ProjectNotFoundError

        return obj

    # Groups-related methods

    @staticmethod
    def _get_next_ordinal_no(largest_ordinal_no: int | None) -> int:
        return (
            largest_ordinal_no + ORDINAL_NO_STEP
            if largest_ordinal_no is not None
            else 0
        )

    async def create_group(self, data: GroupCreate) -> AdminGroupPure:
        next_ordinal_no = self._get_next_ordinal_no(
            await self.repo.get_largest_group_ordinal(
                data.project_id, data.group_id
            )
        )

        return await self.repo.create_group(data, next_ordinal_no)

    async def put_group(self, id: GroupID, data: GroupPut) -> AdminGroupPure:
        if (obj := await self.repo.put_group(id, data)) is None:
            return await self.create_group(data)

        return obj

    async def remove_group(self, id: GroupID) -> None:
        result = await self.repo.remove_group(id)

        if not result:
            raise GroupNotFoundError

    # Items-related methods

    async def create_item(self, data: ItemCreate) -> AdminItemPure:
        next_ordinal_no = self._get_next_ordinal_no(
            await self.repo.get_largest_item_ordinal(data.group_id)
        )

        return await self.repo.create_item(data, next_ordinal_no)

    async def put_item(self, id: ItemID, data: ItemPut) -> AdminItemPure:
        if (obj := await self.repo.put_item(id, data)) is None:
            return await self.create_item(data)

        return obj

    async def remove_item(self, id: ItemID) -> None:
        result = await self.repo.remove_item(id)

        if not result:
            raise ItemNotFoundError
