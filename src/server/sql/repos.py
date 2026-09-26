from typing import TYPE_CHECKING, cast, override

from pydantic import HttpUrl
from sqlalchemy import select
from sqlalchemy.orm import lazyload

from server.api.errors import ItemNotFoundError
from server.services.ports import AbstractSpecificationRepo
from server.services.schemas import (
    Category,
    Comment,
    CommentCreate,
    CurrencyCode,
    Item,
    MoneyType,
    Room,
    Specification,
    SpecificationPure,
)
from server.sql.models import (
    CategoryDB,
    CommentDB,
    ItemDB,
    RoomDB,
    SpecificationDB,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class SpecificationRepo(AbstractSpecificationRepo):
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
            name=obj.name,
            count=obj.count,
            link=HttpUrl(obj.link) if obj.link is not None else None,
            tags=[tag.tag for tag in obj.tags],
            price=price,
            comments=[
                cls._validate_comment(comment) for comment in obj.comments
            ],
        )

    @classmethod
    def _validate_category(cls, obj: CategoryDB) -> Category:
        return Category(
            name=obj.name,
            items=[cls._validate_item(item) for item in obj.items],
        )

    @classmethod
    def _validate_room(cls, obj: RoomDB) -> Room:
        return Room(
            name=obj.name,
            categories=[
                cls._validate_category(category) for category in obj.categories
            ],
        )

    @classmethod
    def _to_domain_schema(cls, obj: SpecificationDB) -> Specification:
        return Specification(
            id=obj.id,
            name=obj.name,
            rooms=[cls._validate_room(room) for room in obj.rooms],
        )

    @staticmethod
    def _to_domain_schema_pure(obj: SpecificationDB) -> SpecificationPure:
        return SpecificationPure(id=obj.id, name=obj.name)

    @override
    async def get(self, id: int) -> Specification | None:
        stmt = select(SpecificationDB).where(SpecificationDB.id == id)
        obj = await self.session.scalar(stmt)

        if obj is None:
            return None

        return self._to_domain_schema(obj)

    GET_ALL_STMT = select(SpecificationDB)

    @override
    async def get_all(self) -> list[Specification]:
        objs = (await self.session.scalars(self.GET_ALL_STMT)).all()

        return [self._to_domain_schema(obj) for obj in objs]

    GET_ALL_PURE_STMT = select(SpecificationDB).options(
        lazyload(SpecificationDB.rooms)
    )

    @override
    async def get_all_pure(self) -> list[SpecificationPure]:
        objs = (await self.session.scalars(self.GET_ALL_PURE_STMT)).all()

        return [self._to_domain_schema_pure(obj) for obj in objs]

    @override
    async def get_item_comments(self, item_id: int) -> list[Comment]:
        stmt = select(CommentDB).where(CommentDB.item_id == item_id)
        objs = (await self.session.scalars(stmt)).all()

        return [self._validate_comment(comment) for comment in objs]

    # NOTE: Should it return new data of ItemDB?
    @override
    async def add_comment(self, item_id: int, data: CommentCreate) -> Comment:
        stmt = select(ItemDB).where(ItemDB.id == item_id)
        item = await self.session.scalar(stmt)

        if item is None:
            raise ItemNotFoundError

        obj = CommentDB(text=data.text)
        item.comments.append(obj)
        await self.session.flush((item,))

        return self._validate_comment(obj)
