from typing import TYPE_CHECKING, override

from sqlalchemy import select

from server.services.ports import AbstractSpecificationRepo
from server.services.schemas import Specification, SpecificationPure
from server.sql.models import SpecificationDB

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class SpecificationRepo(AbstractSpecificationRepo):
    session: AsyncSession

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _to_domain_schema(obj: SpecificationDB) -> Specification:
        return Specification(id=obj.id, name=obj.name, rooms=obj.rooms)

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

    GET_ALL_PURE_STMT = select(SpecificationDB)

    @override
    async def get_all_pure(self) -> list[SpecificationPure]:
        objs = (await self.session.scalars(self.GET_ALL_PURE_STMT)).all()

        return [self._to_domain_schema_pure(obj) for obj in objs]
