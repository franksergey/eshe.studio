from dataclasses import dataclass, field
from typing import TYPE_CHECKING, override

from pydantic import TypeAdapter
from sqlalchemy import delete, exists, inspect, select, update
from sqlalchemy.orm import lazyload, load_only, selectinload

from server.api.errors import (
    GroupNotFoundError,
    ItemNotFoundError,
    ProjectNotFoundError,
)
from server.domain.files.schemas import ImageRef
from server.domain.projects.admin_schemas import (
    AdminGroupPure,
    AdminProject,
    AdminProjectPure,
    GroupCreate,
    GroupPut,
)
from server.domain.projects.ports import AbstractProjectsRepo
from server.domain.projects.schemas import (
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
from server.sql.models import CommentDB, GroupDB, ItemDB, ProjectDB, UserDB

if TYPE_CHECKING:
    from collections.abc import Callable

    from pydantic import HttpUrl
    from sqlalchemy.ext.asyncio import AsyncSession

    from server.domain.files.schemas import ImageID
    from server.domain.projects.admin_schemas import (
        ProjectCreate,
        ProjectPut,
        ProjectUpdate,
    )
    from server.domain.users.schemas import UserID


@dataclass(eq=False, slots=True, frozen=True)
class ProjectsRepo(AbstractProjectsRepo):
    session: AsyncSession
    get_image_url: Callable[[ImageRef], HttpUrl]

    _validation_context: dict[str, object] = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "_validation_context", {"get_image_url": self.get_image_url}
        )

    # Validation/conversion

    @classmethod
    def _validate_comment(
        cls, obj: CommentDB, author: UserDB | None
    ) -> Comment:
        return Comment(
            id=obj.id,
            text=obj.text,
            created_at=obj.created_at,
            user_id=obj.user_id,
            author_name="Deleted User"
            if author is None
            else author.first_name
            if author.last_name is None
            else f"{author.first_name} {author.last_name}",
        )

    # Projects-related methods

    @override
    async def get(self, id: ProjectID) -> Project | None:
        stmt = select(ProjectDB).where(ProjectDB.id == id)
        obj = await self.session.scalar(stmt)

        if obj is None:
            return None

        return Project.model_validate(obj, context=self._validation_context)

    @override
    async def get_pure(self, id: ProjectID) -> ProjectPure | None:
        stmt = (
            select(ProjectDB)
            .where(ProjectDB.id == id)
            .options(lazyload(ProjectDB.categories))
        )
        obj = await self.session.scalar(stmt)

        if obj is None:
            return None

        return ProjectPure.model_validate(obj)

    GET_ALL_STMT = select(ProjectDB)
    ProjectList = TypeAdapter(list[Project])

    @override
    async def get_all(self) -> list[Project]:
        objs = (await self.session.scalars(self.GET_ALL_STMT)).all()

        return self.ProjectList.validate_python(
            objs, context=self._validation_context
        )

    GET_ALL_PURE_STMT = select(ProjectDB).options(
        lazyload(ProjectDB.categories)
    )

    @override
    async def get_all_pure(self) -> list[ProjectPure]:
        objs = (await self.session.scalars(self.GET_ALL_PURE_STMT)).all()

        return [ProjectPure.model_validate(obj) for obj in objs]

    async def exists(self, project_id: ProjectID) -> bool:
        stmt = select(exists(ProjectDB).where(ProjectDB.id == project_id))
        return (await self.session.execute(stmt)).scalar_one()

    @override
    async def create(self, data: ProjectCreate) -> AdminProjectPure:
        obj = ProjectDB(name=data.name, categories=[])
        self.session.add(obj)

        await self.session.flush()
        await self.session.refresh(obj, ("updated_at", "created_at"))

        return AdminProjectPure.model_validate(obj)

    @override
    async def update(
        self, id: ProjectID, data: ProjectUpdate
    ) -> AdminProjectPure | None:
        update_dict = data.model_dump(exclude_defaults=True)
        stmt = (
            update(ProjectDB)
            .where(ProjectDB.id == id)
            .values(*update_dict)
            .returning(ProjectDB)
        )

        if (obj := await self.session.scalar(stmt)) is None:
            return None

        return AdminProjectPure.model_validate(obj)

    @override
    async def put(
        self, id: ProjectID, data: ProjectPut
    ) -> AdminProjectPure | None:
        put_dict = data.model_dump()
        stmt = (
            update(ProjectDB)
            .where(ProjectDB.id == id)
            .values(**put_dict)
            .returning(ProjectDB)
        )

        if (obj := await self.session.scalar(stmt)) is None:
            return None

        return AdminProjectPure.model_validate(obj)

    @override
    async def remove(self, id: ProjectID) -> AdminProject | None:
        stmt = select(ProjectDB).where(ProjectDB.id == id).with_for_update()
        obj = await self.session.scalar(stmt)

        if obj is None:
            return None

        result = AdminProject.model_validate(
            obj, context=self._validation_context
        )

        await self.session.delete(obj)
        return result

    # Groups-related methods

    @override
    async def get_category(
        self, project_id: ProjectID, group_id: GroupID
    ) -> GroupOnlyItems | None:
        stmt = select(GroupDB).where(
            GroupDB.project_id == project_id, GroupDB.id == group_id
        )
        obj = await self.session.scalar(stmt)

        if obj is None:
            return obj

        return GroupOnlyItems.model_validate(
            obj, context=self._validation_context
        )

    @override
    async def get_categories_pure(
        self, project_id: ProjectID
    ) -> list[GroupPure]:
        stmt = (
            select(GroupDB)
            .where(
                GroupDB.project_id == project_id, GroupDB.group_id.is_(None)
            )
            .order_by(GroupDB.ordinal_no)
            .options(lazyload(GroupDB.items), lazyload(GroupDB.subgroups))
        )
        objs = await self.session.scalars(stmt)
        return [GroupPure.model_validate(group) for group in objs]

    async def group_exists(self, group_id: GroupID) -> bool:
        stmt = select(exists(GroupDB).where(GroupDB.id == group_id))
        return (await self.session.execute(stmt)).scalar_one()

    @override
    async def get_largest_group_ordinal_no(
        self, project_id: ProjectID, group_id: GroupID | None
    ) -> int | None:
        stmt = (
            select(GroupDB.ordinal_no)
            .where(
                GroupDB.project_id == project_id, GroupDB.group_id == group_id
            )
            .order_by(GroupDB.ordinal_no.desc())
            .limit(1)
        )
        return await self.session.scalar(stmt)

    async def _check_group_foreign_keys(self, data: GroupCreate) -> None:
        if not await self.exists(data.project_id):
            msg = f"Parent project with id {data.project_id} does not exist"
            raise ProjectNotFoundError(msg)

        if data.group_id is not None and not await self.group_exists(
            data.group_id
        ):
            msg = f"Parent group with id {data.group_id} does not exist"
            raise GroupNotFoundError(msg)

    @override
    async def create_group(
        self, data: GroupCreate, ordinal_no: int
    ) -> AdminGroupPure:
        await self._check_group_foreign_keys(data)

        obj = GroupDB(
            project_id=data.project_id,
            group_id=data.group_id,
            ordinal_no=ordinal_no,
            name=data.name,
            items=[],
            subgroups=[],
        )
        self.session.add(obj)

        await self.session.flush()
        await self.session.refresh(obj, ("updated_at", "created_at"))

        return AdminGroupPure.model_validate(obj)

    @override
    async def put_group(
        self, id: GroupID, data: GroupPut
    ) -> AdminGroupPure | None:
        await self._check_group_foreign_keys(data)

        put_dict = data.model_dump()
        stmt = (
            update(GroupDB)
            .where(GroupDB.id == id)
            .values(**put_dict)
            .returning(GroupDB)
        )

        if (obj := await self.session.scalar(stmt)) is None:
            return None

        return AdminGroupPure.model_validate(obj)

    @override
    async def remove_group(self, id: GroupID) -> bool:
        stmt = delete(GroupDB).where(GroupDB.id == id).returning(GroupDB.id)
        result = await self.session.scalar(stmt)
        return result is not None

    # Items-related methods

    @override
    async def check_item_exists(self, item_id: ItemID) -> bool:
        stmt = select(exists(ItemDB).where(ItemDB.id == item_id))
        return (await self.session.execute(stmt)).scalar_one()

    @override
    async def get_item(self, item_id: ItemID) -> Item | None:
        stmt = select(ItemDB).where(ItemDB.id == item_id)
        obj = await self.session.scalar(stmt)

        if obj is None:
            return None

        return Item.model_validate(obj, context=self._validation_context)

    @override
    async def get_item_comments(self, item_id: ItemID) -> list[Comment] | None:
        stmt = select(exists(ItemDB).where(ItemDB.id == item_id))

        if not (await self.session.execute(stmt)).scalar_one():
            return None

        stmt = (
            select(CommentDB)
            .options(selectinload(CommentDB.author))
            .where(CommentDB.item_id == item_id)
        )
        objs = (await self.session.scalars(stmt)).unique().all()

        return [
            self._validate_comment(comment, comment.author) for comment in objs
        ]

    @override
    async def bulk_get_item_comments(
        self, item_ids: list[ItemID]
    ) -> tuple[list[ItemOnlyComments], list[ItemID]]:
        ids = frozenset(item_ids)
        stmt = (
            select(ItemDB)
            .options(
                load_only(ItemDB.id),
                selectinload(ItemDB.comments).selectinload(CommentDB.author),
            )
            .where(ItemDB.id.in_(ids))
        )
        objs = (await self.session.scalars(stmt)).all()

        items = {
            obj.id: ItemOnlyComments(
                id=obj.id,
                comments=[
                    self._validate_comment(comment, comment.author)
                    for comment in obj.comments
                ],
            )
            for obj in objs
        }
        return (list(items.values()), list(ids - items.keys()))

    # NOTE: Should it return new data of ItemDB?
    @override
    async def add_comment(
        self, item_id: ItemID, user_id: UserID, data: CommentCreate
    ) -> Comment | None:
        stmt = (
            select(ItemDB)
            .where(ItemDB.id == item_id)
            .options(load_only(ItemDB.id))
            .with_for_update()
        )
        item = await self.session.scalar(stmt)

        if item is None:
            return None

        obj = CommentDB(item_id=item_id, user_id=user_id, text=data.text)
        state = inspect(item)

        if "comments" not in state.unloaded:
            item.comments.append(obj)
            await self.session.flush((item,))
        else:
            self.session.add(obj)
            await self.session.flush((obj,))

        await self.session.refresh(obj, ("author",))
        return self._validate_comment(obj, obj.author)

    @override
    async def get_item_image(self, item_id: ItemID) -> ImageRef | None:
        stmt = (
            select(ItemDB)
            .options(load_only(ItemDB.image))
            .where(ItemDB.id == item_id)
        )
        obj = await self.session.scalar(stmt)

        if obj is None:
            raise ItemNotFoundError

        image = obj.image

        if image is None:
            return None

        return ImageRef.model_validate(image)

    @override
    async def attach_image(
        self, item_id: ItemID, image_id: ImageID
    ) -> ImageID | None:
        stmt = (
            select(ItemDB)
            .options(load_only(ItemDB.image_id))
            .where(ItemDB.id == item_id)
            .with_for_update()
        )
        obj = await self.session.scalar(stmt)

        if obj is None:
            raise ItemNotFoundError

        old_image_id = obj.image_id
        obj.image_id = image_id
        await self.session.flush((obj,))

        return old_image_id

    @override
    async def detach_image(self, item_id: ItemID) -> ImageID | None:
        stmt = (
            select(ItemDB)
            .options(load_only(ItemDB.image_id))
            .where(ItemDB.id == item_id)
            .with_for_update()
        )
        obj = await self.session.scalar(stmt)

        if obj is None:
            return None

        old_image_id = obj.image_id
        obj.image_id = None
        await self.session.flush((obj,))

        return old_image_id
