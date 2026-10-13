from typing import TYPE_CHECKING, cast, override

from pydantic import HttpUrl
from sqlalchemy import select

from server.domain.choices.ports import AbstractChoicesRepo
from server.domain.choices.schemas import (
    Choice,
    ChoicePure,
    GroupSnapshot,
    ItemChoice,
)
from server.domain.projects.schemas import CurrencyCode, MoneyType
from server.sql.models import ChoiceDB, GroupSnapshotDB, ItemChoiceDB

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession


class ChoicesRepo(AbstractChoicesRepo):
    session: AsyncSession

    @staticmethod
    def _validate_item(obj: ItemChoiceDB) -> ItemChoice:
        if obj.price is None:
            price = None
        else:
            price = MoneyType(
                amount=obj.price,
                currency=cast("CurrencyCode", obj.price_currency),
            )

        return ItemChoice(
            item_id=obj.item_id,
            name=obj.name,
            count=obj.count,
            approved=obj.approved,
            link=HttpUrl(obj.link) if obj.link is not None else None,
            tags=obj.tags,
            price=price,
        )

    async def _validate_group(self, obj: GroupSnapshotDB) -> GroupSnapshot:
        if "subgroups" not in obj.__dict__:
            await self.session.refresh(obj, ("subgroups",))

        items: list[GroupSnapshot | ItemChoice] = [
            *(self._validate_item(item) for item in obj.items),
            *[
                await self._validate_group(subgroup)
                for subgroup in obj.subgroups
            ],
        ]
        return GroupSnapshot(name=obj.name, items=items)

    async def _to_domain_schema(self, obj: ChoiceDB) -> Choice:
        return Choice(
            id=obj.id,
            user_id=obj.user_id,
            created_at=obj.created_at,
            items=[await self._validate_group(group) for group in obj.groups],
        )

    @staticmethod
    def _to_domain_schema_pure(obj: ChoiceDB) -> ChoicePure:
        return ChoicePure(
            id=obj.id, user_id=obj.user_id, created_at=obj.created_at
        )

    @override
    async def get(self, id: int) -> Choice | None:
        stmt = select(ChoiceDB).where(ChoiceDB.id == id)
        obj = await self.session.scalar(stmt)

        if obj is None:
            return None

        return await self._to_domain_schema(obj)

    @override
    async def get_by_user(self, user_id: uuid.UUID) -> list[ChoicePure]:
        stmt = select(ChoiceDB).where(ChoiceDB.user_id == user_id)
        objs = (await self.session.scalars(stmt)).all()

        return [self._to_domain_schema_pure(obj) for obj in objs]
