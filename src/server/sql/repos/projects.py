from typing import TYPE_CHECKING, cast, override

from pydantic import HttpUrl
from sqlalchemy import exists, inspect, select, update
from sqlalchemy.orm import lazyload, load_only, selectinload

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
from server.sql.models import CommentDB, GroupDB, ItemDB, ProjectDB

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class ProjectsRepo(AbstractProjectsRepo):
    session: AsyncSession

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @classmethod
    def _validate_comment(cls, obj: CommentDB) -> Comment:
        return Comment(
            id=obj.id,
            text=obj.text,
            author_name=obj.author_name,
            created_at=obj.created_at,
        )

    @classmethod
    def _validate_item(cls, obj: ItemDB) -> Item:
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
        )

    @classmethod
    def _validate_group(cls, obj: GroupDB) -> Group:
        items: list[Group | Item] = [
            *(cls._validate_item(item) for item in obj.items),
            *[cls._validate_group(subgroup) for subgroup in obj.subgroups],
        ]
        return Group(id=obj.id, name=obj.name, items=items)

    @classmethod
    def _validate_group_pure(cls, obj: GroupDB) -> GroupPure:
        return GroupPure(id=obj.id, name=obj.name)

    @classmethod
    def _to_domain_schema(cls, obj: ProjectDB) -> Project:
        return Project(
            id=obj.id,
            name=obj.name,
            categories=[
                cls._validate_group(category) for category in obj.categories
            ],
        )

    @staticmethod
    def _to_domain_schema_pure(obj: ProjectDB) -> ProjectPure:
        return ProjectPure(id=obj.id, name=obj.name)

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
        self, project_id: int, index: int = 0
    ) -> GroupOnlyItems | None:
        stmt = (
            select(GroupDB)
            .where(
                GroupDB.project_id == project_id, GroupDB.group_id.is_(None)
            )
            .order_by(GroupDB.ordinal_no)
            .limit(1)
            .offset(index)
        )
        obj = await self.session.scalar(stmt)

        if obj is None:
            return obj

        items: list[Group | Item] = [
            *(self._validate_item(item) for item in obj.items),
            *[self._validate_group(subgroup) for subgroup in obj.subgroups],
        ]
        return GroupOnlyItems(id=obj.id, name=obj.name, items=items)

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
        stmt = (
            select(ItemDB)
            .options(load_only(ItemDB.id), selectinload(ItemDB.comments))
            .where(ItemDB.id == item_id)
        )
        obj = await self.session.scalar(stmt)

        if obj is None:
            return None

        return [self._validate_comment(comment) for comment in obj.comments]

    @override
    async def bulk_get_item_comments(
        self, item_ids: list[int]
    ) -> tuple[list[ItemOnlyComments], list[int]]:
        ids = frozenset(item_ids)
        stmt = (
            select(ItemDB)
            .options(load_only(ItemDB.id), selectinload(ItemDB.comments))
            .where(ItemDB.id.in_(ids))
        )
        objs = (await self.session.scalars(stmt)).all()

        items = {
            obj.id: ItemOnlyComments(
                id=obj.id,
                comments=[
                    self._validate_comment(comment) for comment in obj.comments
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

        return self._validate_comment(obj)

    @override
    async def approve_item(
        self, item_id: int, *, approved: bool = True
    ) -> None:
        stmt = (
            update(ItemDB)
            .where(ItemDB.id == item_id)
            # pyrefly: ignore [unexpected-keyword]
            .values(approved=approved)
        )
        await self.session.execute(stmt)
