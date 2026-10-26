from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Literal, override

from sqlalchemy import delete, select

from server.domain.projects.schemas import Item, ItemType, ProjectPure
from server.domain.selections.ports import AbstractSelectionsRepo
from server.domain.selections.schemas import Selection, SelectionCreate
from server.sql.models import GroupDB, ItemDB, ItemSelectionDB, SelectionDB

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sqlalchemy.ext.asyncio import AsyncSession

    from server.domain.users.schemas import UserID


STATIC_ORDINALS_START: int = 0


@dataclass(slots=True)
class ProjectSnapshotGroup:
    name: str
    items: list[Item | ProjectSnapshotGroup]

    has_subitems: bool

    item_type: Literal[ItemType.GROUP] = ItemType.GROUP


@dataclass(eq=False, slots=True)
class SelectionsRepo(AbstractSelectionsRepo):
    session: AsyncSession

    @staticmethod
    def _to_domain_schema(obj: SelectionDB) -> Selection:
        return Selection(
            id=obj.id,
            user_id=obj.user_id,
            items=[item_ref.item_id for item_ref in obj.items],
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )

    @override
    async def get(self, id: int) -> Selection | None:
        stmt = select(SelectionDB).where(SelectionDB.id == id)
        obj = await self.session.scalar(stmt)

        if obj is None:
            return None

        return self._to_domain_schema(obj)

    @override
    async def get_by_user(
        self, project_id: int, user_id: UserID
    ) -> Selection | None:
        stmt = select(SelectionDB).where(
            SelectionDB.project_id == project_id,
            SelectionDB.user_id == user_id,
        )

        if (obj := await self.session.scalar(stmt)) is None:
            return None

        return self._to_domain_schema(obj)

    @override
    async def get_users(self, project_id: int) -> Sequence[UserID]:
        stmt = select(SelectionDB.user_id).where(
            SelectionDB.project_id == project_id
        )
        return (await self.session.scalars(stmt)).all()

    @override
    async def create(
        self, project: ProjectPure, data: SelectionCreate, user_id: UserID
    ) -> None:
        stmt = select(SelectionDB).where(
            SelectionDB.project_id == project.id,
            SelectionDB.user_id == user_id,
        )
        selection = await self.session.scalar(stmt)

        stmt = (
            select(ItemDB.id)
            .join(GroupDB, ItemDB.group_id == GroupDB.id)
            .where(GroupDB.project_id == project.id)
            .where(ItemDB.id.in_(data.item_ids))
        )
        item_ids = set((await self.session.scalars(stmt)).all())

        if selection is None:
            selection = SelectionDB(
                project_id=project.id,
                user_id=user_id,
                items=[
                    ItemSelectionDB(item_id=item_id) for item_id in item_ids
                ],
            )
            self.session.add(selection)
            self.session.add_all(selection.items)
        else:
            selected_ids = {item.item_id for item in selection.items}
            to_delete = selected_ids - item_ids

            stmt = delete(ItemSelectionDB).where(
                ItemSelectionDB.selection_id == selection.id,
                ItemSelectionDB.item_id.in_(to_delete),
            )
            await self.session.execute(stmt)

            to_create = item_ids - selected_ids

            for id in to_create:
                item = ItemSelectionDB(selection_id=selection.id, item_id=id)
                selection.items.append(item)
                self.session.add(item)

            selection.updated_at = datetime.now(tz=UTC)

        await self.session.flush()
