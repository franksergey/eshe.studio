from typing import TYPE_CHECKING, override

from sqlalchemy import select
from sqlalchemy.orm import lazyload

from server.services.ports import AbstractSpecificationRepo
from server.services.schemas import (
    Category,
    Item,
    Room,
    Specification,
    SpecificationPure,
)
from server.sql.models import CategoryDB, ItemDB, RoomDB, SpecificationDB

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class SpecificationRepo(AbstractSpecificationRepo):
    session: AsyncSession

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @classmethod
    def _validate_item(cls, obj: ItemDB) -> Item:
        return Item(
            name=obj.name,
            count=obj.count,
            link=obj.link,
            tags=(tag.tag for tag in obj.tags),
            price=obj.price,
        )

    @classmethod
    def _validate_category(cls, obj: CategoryDB) -> Category:
        return Category(
            name=obj.name,
            items=(cls._validate_item(item) for item in obj.items),
        )

    @classmethod
    def _validate_room(cls, obj: RoomDB) -> Room:
        return Room(
            name=obj.name,
            categories=(
                cls._validate_category(category) for category in obj.categories
            ),
        )

    @classmethod
    def _to_domain_schema(cls, obj: SpecificationDB) -> Specification:
        return Specification(
            id=obj.id,
            name=obj.name,
            rooms=(cls._validate_room(room) for room in obj.rooms),
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
