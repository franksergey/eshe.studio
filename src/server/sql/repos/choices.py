from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, cast, override

from pydantic import HttpUrl
from sqlalchemy import select

from server.domain.choices.ports import AbstractChoicesRepo
from server.domain.choices.schemas import (
    Choice,
    ChoiceCreate,
    ChoicePure,
    GroupSnapshot,
    ItemChoice,
)
from server.domain.projects.schemas import (
    CurrencyCode,
    Group,
    Item,
    ItemType,
    MoneyType,
    Project,
)
from server.sql.models import ChoiceDB, GroupSnapshotDB, ItemChoiceDB

if TYPE_CHECKING:
    import uuid
    from collections.abc import Iterator, Mapping, Sequence

    from sqlalchemy.ext.asyncio import AsyncSession


STATIC_ORDINALS_START: int = 0


@dataclass(slots=True)
class ProjectSnapshotGroup:
    name: str
    items: list[Item | ProjectSnapshotGroup]

    has_subitems: bool

    item_type: Literal[ItemType.GROUP] = ItemType.GROUP


@dataclass(eq=False, slots=True)
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

    @classmethod
    def _validate_group(
        cls,
        obj: GroupSnapshotDB,
        groups_map: Mapping[int | None, Sequence[GroupSnapshotDB]],
    ) -> GroupSnapshot:
        items: list[GroupSnapshot | ItemChoice] = [
            *(cls._validate_item(item) for item in obj.items),
            *[
                cls._validate_group(subgroup, groups_map)
                for subgroup in groups_map[obj.id]
            ],
        ]
        return GroupSnapshot(name=obj.name, items=items)

    @classmethod
    def _to_domain_schema(cls, obj: ChoiceDB) -> Choice:
        groups_map: dict[int | None, list[GroupSnapshotDB]] = defaultdict(list)

        for group in obj.groups:
            groups_map[group.group_id].append(group)

        return Choice(
            id=obj.id,
            user_id=obj.user_id,
            created_at=obj.created_at,
            items=[
                cls._validate_group(group, groups_map)
                for group in groups_map[None]
            ],
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

        return self._to_domain_schema(obj)

    @override
    async def get_by_user(self, user_id: uuid.UUID) -> list[ChoicePure]:
        stmt = select(ChoiceDB).where(ChoiceDB.user_id == user_id)
        objs = (await self.session.scalars(stmt)).all()

        return [self._to_domain_schema_pure(obj) for obj in objs]

    @staticmethod
    def _item_to_snapshot(item: Item, ordinal_no: int) -> ItemChoiceDB:
        return ItemChoiceDB(
            name=item.name,
            count=item.count,
            approved=item.approved,
            link=str(item.link) if item.link is not None else None,
            price=item.price.amount if item.price is not None else None,
            price_currency=item.price.currency
            if item.price is not None
            else None,
            ordinal_no=ordinal_no,
            item_id=item.id,
            tags=item.tags,
        )

    @classmethod
    def _group_to_snapshot(
        cls, choice_id: int, group: ProjectSnapshotGroup, ordinal_no: int
    ) -> GroupSnapshotDB:
        root = GroupSnapshotDB(
            choice_id=choice_id, name=group.name, ordinal_no=ordinal_no
        )
        stack: list[
            tuple[
                GroupSnapshotDB,
                Iterator[tuple[int, Item | ProjectSnapshotGroup]],
            ]
        ] = [(root, enumerate(group.items, start=STATIC_ORDINALS_START))]

        while stack:
            obj, remaining = stack[-1]

            for i, item in remaining:
                if item.item_type == ItemType.ITEM:
                    obj.items.append(cls._item_to_snapshot(item, i))
                else:
                    child = GroupSnapshotDB(
                        choice_id=choice_id, name=item.name, ordinal_no=i
                    )
                    obj.subgroups.append(child)
                    stack.append(
                        (
                            child,
                            enumerate(item.items, start=STATIC_ORDINALS_START),
                        )
                    )
                    break
            else:
                stack.pop()

        return root

    @override
    async def create(
        self, project: Project, data: ChoiceCreate, user_id: uuid.UUID
    ) -> None:
        ids = set(data.item_ids)

        def process_group(group: Group) -> ProjectSnapshotGroup:
            root = ProjectSnapshotGroup(
                name=group.name, items=[], has_subitems=False
            )
            stack: list[
                tuple[ProjectSnapshotGroup, Iterator[Item | Group]]
            ] = [(root, iter(group.items))]

            while stack:
                snapshot, remaining = stack[-1]

                for item in remaining:
                    if item.item_type == ItemType.ITEM:
                        if item.id not in ids:
                            continue

                        ids.remove(item.id)
                        snapshot.items.append(item)
                        snapshot.has_subitems = True
                    else:
                        # Descend into the subgroup; resume this frame later
                        child = ProjectSnapshotGroup(
                            name=item.name, items=[], has_subitems=False
                        )
                        stack.append((child, iter(item.items)))
                        break
                else:
                    # This group is fully processed
                    stack.pop()

                    if stack and snapshot.has_subitems:
                        parent = stack[-1][0]
                        parent.items.append(snapshot)
                        parent.has_subitems = True

            return root

        tree: list[ProjectSnapshotGroup] = [
            process_group(group) for group in project.categories
        ]
        choice = ChoiceDB(user_id=user_id, groups=[])
        self.session.add(choice)
        await self.session.flush((choice,))

        for i, group in enumerate(tree, start=STATIC_ORDINALS_START):
            choice.groups.append(self._group_to_snapshot(choice.id, group, i))

        await self.session.flush()
