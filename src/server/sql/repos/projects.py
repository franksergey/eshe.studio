from dataclasses import dataclass
from typing import TYPE_CHECKING, cast, override

from pydantic import HttpUrl
from sqlalchemy import exists, inspect, select, update
from sqlalchemy.orm import lazyload, load_only, selectinload

from server.api.errors import ItemNotFoundError
from server.domain.files.schemas import ImageRef
from server.domain.projects.ports import AbstractProjectsRepo
from server.domain.projects.schemas import (
    Comment,
    CommentCreate,
    CurrencyCode,
    Group,
    GroupOnlyItems,
    GroupPure,
    Item,
    ItemOnlyComments,
    MoneyType,
    Project,
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
    from collections.abc import Callable, Iterable

    from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(eq=False, slots=True)
class ProjectsRepo(AbstractProjectsRepo):
    session: AsyncSession
    get_image_url: Callable[[ImageRef], HttpUrl]

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
            approved=obj.approved,
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

    @staticmethod
    def _to_domain_schema_pure(obj: ProjectDB) -> ProjectPure:
        return ProjectPure(id=obj.id, name=obj.name)

    @staticmethod
    def _image_to_domain_schema(image: ImageDB) -> ImageRef:
        return ImageRef(
            id=image.id,
            object_id=image.object_id,
            size=(image.width, image.height),
            quality=image.quality,
        )

    @override
    async def get(self, id: int) -> Project | None:
        stmt = select(ProjectDB).where(ProjectDB.id == id)
        obj = await self.session.scalar(stmt)

        if obj is None:
            return None

        return self._to_domain_schema(obj)

    @override
    async def get_pure(self, id: int) -> ProjectPure | None:
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

    @override
    async def get_category(
        self, project_id: int, group_id: int
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

    async def get_categories_pure(self, project_id: int) -> list[GroupPure]:
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

    @override
    async def check_item_exists(self, item_id: int) -> bool:
        stmt = select(exists(ItemDB).where(ItemDB.id == item_id))
        return (await self.session.execute(stmt)).scalar_one()

    @override
    async def get_item(self, item_id: int) -> Item | None:
        stmt = select(ItemDB).where(ItemDB.id == item_id)
        obj = await self.session.scalar(stmt)

        if obj is None:
            return None

        return self._validate_item(obj)

    @override
    async def get_item_comments(self, item_id: int) -> list[Comment] | None:
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
        self, item_ids: list[int]
    ) -> tuple[list[ItemOnlyComments], list[int]]:
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
        self, item_id: int, data: CommentCreate
    ) -> Comment | None:
        stmt = (
            select(ItemDB)
            .where(ItemDB.id == item_id)
            .options(load_only(ItemDB.id))
        )
        item = await self.session.scalar(stmt)

        if item is None:
            return None

        obj = CommentDB(
            item_id=item_id, text=data.text, author_name=data.author_name
        )
        state = inspect(item)

        if "comments" not in state.unloaded:
            item.comments.append(obj)
            await self.session.flush((item,))
        else:
            self.session.add(obj)
            await self.session.flush((obj,))

        await self.session.refresh(obj, ("author",))
        return self._validate_comment(obj, obj.author)

    async def get_item_image(self, item_id: int) -> ImageRef | None:
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

    async def attach_image(self, item_id: int, image_id: int) -> int | None:
        stmt = (
            select(ItemDB)
            .options(load_only(ItemDB.image_id))
            .where(ItemDB.id == item_id)
        )
        obj = await self.session.scalar(stmt)

        if obj is None:
            raise ItemNotFoundError

        old_image_id = obj.image_id
        obj.image_id = image_id
        await self.session.flush((obj,))

        return old_image_id

    async def detach_image(self, item_id: int) -> int | None:
        stmt = (
            select(ItemDB)
            .options(load_only(ItemDB.image_id))
            .where(ItemDB.id == item_id)
        )
        obj = await self.session.scalar(stmt)

        if obj is None:
            return None

        old_image_id = obj.image_id
        obj.image_id = None
        await self.session.flush((obj,))

        return old_image_id

    @override
    async def approve_item(
        self, item_id: int, *, approved: bool = True
    ) -> None:
        stmt = (
            update(ItemDB)
            .where(ItemDB.id == item_id)
            .values(approved=approved)
        )
        await self.session.execute(stmt)
