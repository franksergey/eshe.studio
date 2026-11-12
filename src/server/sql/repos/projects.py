from dataclasses import dataclass
from typing import TYPE_CHECKING, cast, override

from pydantic import HttpUrl
from sqlalchemy import bindparam, delete, exists, inspect, select, update
from sqlalchemy.orm import lazyload, load_only, selectinload

from server.api.errors import (
    GroupNotFoundError,
    ItemNotFoundError,
    ProjectNotFoundError,
)
from server.domain.files.schemas import ImageID, ImageRef
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
    CurrencyCode,
    Group,
    GroupID,
    GroupOnlyItems,
    GroupPure,
    Item,
    ItemID,
    ItemOnlyComments,
    MoneyType,
    Project,
    ProjectID,
    ProjectPure,
)
from server.sql.models import (
    CommentDB,
    GroupDB,
    ImageDB,
    ItemDB,
    ProjectDB,
    UserDB,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Sequence

    from sqlalchemy.ext.asyncio import AsyncSession

    from server.domain.projects.admin_schemas import (
        ProjectCreate,
        ProjectPut,
        ProjectUpdate,
    )
    from server.domain.users.schemas import UserID


@dataclass(eq=False, slots=True)
class ProjectsRepo(AbstractProjectsRepo):
    session: AsyncSession
    get_image_url: Callable[[ImageRef], HttpUrl]

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

    def _validate_item(self, obj: ItemDB) -> Item:
        if obj.price is None:
            price = None
        else:
            price = MoneyType(
                amount=obj.price,
                currency=cast("CurrencyCode", obj.price_currency),
            )

        return Item(
            id=obj.id,
            name=obj.name,
            count=obj.count,
            status=obj.status,
            link=HttpUrl(obj.link) if obj.link is not None else None,
            tags=[tag.tag for tag in obj.tags],
            price=price,
            image=self.get_image_url(self._image_to_domain_schema(obj.image))
            if obj.image is not None
            else None,
        )

    def _validate_group_items(
        self, items: Iterable[ItemDB], subgroups: Iterable[GroupDB]
    ) -> list[Item] | list[Group]:
        if items and subgroups:
            msg = "Group in database cannot contain both subgroups and items"
            raise ValueError(msg)

        if items:
            return [self._validate_item(item) for item in items]

        if subgroups:
            return [self._validate_group(subgroup) for subgroup in subgroups]

        return []

    def _validate_group(self, obj: GroupDB) -> Group:
        if obj.items and obj.subgroups:
            msg = "Group in database cannot contain both subgroups and items"
            raise ValueError(msg)

        return Group(
            id=obj.id,
            name=obj.name,
            items=self._validate_group_items(obj.items, obj.subgroups),
        )

    def _validate_group_pure_admin(self, obj: GroupDB) -> AdminGroupPure:
        return AdminGroupPure(
            id=obj.id,
            name=obj.name,
            updated_at=obj.updated_at,
            created_at=obj.created_at,
        )

    @classmethod
    def _validate_group_pure(cls, obj: GroupDB) -> GroupPure:
        return GroupPure(id=obj.id, name=obj.name)

    def _to_domain_schema(self, obj: ProjectDB) -> Project:
        return Project(
            id=obj.id,
            name=obj.name,
            categories=[
                self._validate_group(category) for category in obj.categories
            ],
        )

    def _to_domain_schema_admin(self, obj: ProjectDB) -> AdminProject:
        return AdminProject(
            id=obj.id,
            name=obj.name,
            updated_at=obj.updated_at,
            created_at=obj.created_at,
            categories=[
                self._validate_group(category) for category in obj.categories
            ],
        )

    @staticmethod
    def _to_domain_schema_pure(obj: ProjectDB) -> ProjectPure:
        return ProjectPure(id=obj.id, name=obj.name)

    @staticmethod
    def _to_domain_schema_pure_admin(obj: ProjectDB) -> AdminProjectPure:
        return AdminProjectPure(
            id=obj.id,
            name=obj.name,
            updated_at=obj.updated_at,
            created_at=obj.created_at,
        )

    @staticmethod
    def _image_to_domain_schema(image: ImageDB) -> ImageRef:
        return ImageRef(
            id=image.id,
            object_id=image.object_id,
            size=(image.width, image.height),
            quality=image.quality,
        )

    # Projects-related methods

    @override
    async def get(self, id: ProjectID) -> Project | None:
        stmt = select(ProjectDB).where(ProjectDB.id == id)
        obj = await self.session.scalar(stmt)

        if obj is None:
            return None

        return self._to_domain_schema(obj)

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

        return self._to_domain_schema_pure(obj)

    GET_ALL_STMT = select(ProjectDB)

    @override
    async def get_all(self) -> list[Project]:
        objs = (await self.session.scalars(self.GET_ALL_STMT)).all()

        return [self._to_domain_schema(obj) for obj in objs]

    GET_ALL_PURE_STMT = select(ProjectDB).options(
        lazyload(ProjectDB.categories)
    )

    @override
    async def get_all_pure(self) -> list[ProjectPure]:
        objs = (await self.session.scalars(self.GET_ALL_PURE_STMT)).all()

        return [self._to_domain_schema_pure(obj) for obj in objs]

    async def exists(self, project_id: ProjectID) -> bool:
        stmt = select(exists(ProjectDB).where(ProjectDB.id == project_id))
        return (await self.session.execute(stmt)).scalar_one()

    @override
    async def create(self, data: ProjectCreate) -> AdminProjectPure:
        obj = ProjectDB(name=data.name, categories=[])
        self.session.add(obj)

        await self.session.flush()
        await self.session.refresh(obj, ("updated_at", "created_at"))

        return self._to_domain_schema_pure_admin(obj)

    @override
    async def update_project(
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

        return self._to_domain_schema_pure_admin(obj)

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

        return self._to_domain_schema_pure_admin(obj)

    @override
    async def remove(self, id: ProjectID) -> AdminProject | None:
        stmt = select(ProjectDB).where(ProjectDB.id == id).with_for_update()
        obj = await self.session.scalar(stmt)

        if obj is None:
            return None

        result = self._to_domain_schema_admin(obj)

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

        return GroupOnlyItems(
            id=obj.id,
            name=obj.name,
            items=self._validate_group_items(obj.items, obj.subgroups),
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
        return [self._validate_group_pure(group) for group in objs]

    async def group_exists(self, group_id: GroupID) -> bool:
        stmt = select(exists(GroupDB).where(GroupDB.id == group_id))
        return (await self.session.execute(stmt)).scalar_one()

    @override
    async def get_largest_group_ordinal(
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

    @override
    async def create_group(
        self, data: GroupCreate, ordinal_no: int
    ) -> AdminGroupPure:
        if not await self.exists(data.project_id):
            msg = f"Parent project with id {data.project_id} does not exist"
            raise ProjectNotFoundError(msg)

        if data.group_id is not None and not await self.group_exists(
            data.group_id
        ):
            msg = f"Parent group with id {data.group_id} does not exist"
            raise GroupNotFoundError(msg)

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

        return self._validate_group_pure_admin(obj)

    @override
    async def put_group(
        self, id: GroupID, data: GroupPut
    ) -> AdminGroupPure | None:
        put_dict = data.model_dump()
        stmt = (
            update(GroupDB)
            .where(GroupDB.id == id)
            .values(**put_dict)
            .returning(GroupDB)
        )

        if (obj := await self.session.scalar(stmt)) is None:
            return None

        return self._validate_group_pure_admin(obj)

    @override
    async def remove_group(self, id: GroupID) -> bool:
        stmt = delete(GroupDB).where(GroupDB.id == id).returning(GroupDB.id)
        result = await self.session.scalar(stmt)
        return result is not None

    @override
    async def get_groups_order(
        self, project_id: ProjectID, group_id: GroupID | None
    ) -> Sequence[tuple[GroupID, int]]:
        stmt = (
            select(GroupDB.id, GroupDB.ordinal_no)
            .where(
                GroupDB.project_id == project_id, GroupDB.group_id == group_id
            )
            .order_by(GroupDB.ordinal_no)
        )
        return (await self.session.execute(stmt)).tuples().all()

    REORDER_GROUPS_STMT = (
        update(GroupDB)
        .where(GroupDB.id == bindparam("b_id"))
        .values(ordinal_no=bindparam("b_ordinal_no"))
    )

    @override
    async def reorder_groups(
        self, new_ordinals: Sequence[tuple[GroupID, int]]
    ) -> None:
        if not new_ordinals:
            return

        await self.session.execute(
            self.REORDER_GROUPS_STMT,
            [
                {"b_id": id, "b_ordinal_no": ordinal}
                for id, ordinal in new_ordinals
            ],
        )

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

        return self._validate_item(obj)

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

        return self._image_to_domain_schema(image)

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
