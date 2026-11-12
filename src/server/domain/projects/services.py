import bisect
import itertools
from dataclasses import dataclass
from typing import TYPE_CHECKING, overload

from server.api.errors import (
    GroupNotFoundError,
    ItemNotFoundError,
    ProjectNotFoundError,
)

from .schemas import CommentsBulkRead

if TYPE_CHECKING:
    from collections.abc import Generator, Mapping, Sequence

    from server.domain.files.schemas import ImageID, ImageRef
    from server.domain.users.schemas import UserRead

    from .admin_schemas import (
        AdminGroupPure,
        AdminProject,
        AdminProjectPure,
        GroupCreate,
        GroupPut,
        ProjectCreate,
        ProjectPut,
        ProjectUpdate,
    )
    from .ports import AbstractProjectsRepo
    from .schemas import (
        Comment,
        CommentCreate,
        GroupID,
        GroupOnlyItems,
        GroupPure,
        ItemID,
        Project,
        ProjectID,
        ProjectPure,
    )


@dataclass(eq=False, slots=True)
class ProjectsService:
    repo: AbstractProjectsRepo

    # Projects-related

    async def get(self, id: ProjectID) -> Project:
        obj = await self.repo.get(id)

        if obj is None:
            raise ProjectNotFoundError

        return obj

    async def get_pure(self, id: ProjectID) -> ProjectPure:
        obj = await self.repo.get_pure(id)

        if obj is None:
            raise ProjectNotFoundError

        return obj

    async def get_all(self) -> list[Project]:
        return await self.repo.get_all()

    async def get_all_pure(self) -> list[ProjectPure]:
        return await self.repo.get_all_pure()

    # Groups-related

    async def get_categories(
        self, project_id: ProjectID, group_id: GroupID
    ) -> GroupOnlyItems:
        group = await self.repo.get_category(project_id, group_id)

        if group is None:
            raise GroupNotFoundError

        return group

    async def get_categories_pure(
        self, project_id: ProjectID
    ) -> list[GroupPure]:
        return await self.repo.get_categories_pure(project_id)

    # Items-related

    async def get_item_comments(self, item_id: ItemID) -> list[Comment]:
        objs = await self.repo.get_item_comments(item_id)

        if objs is None:
            raise ItemNotFoundError

        return objs

    async def bulk_get_item_comments(
        self, item_ids: list[ItemID]
    ) -> CommentsBulkRead:
        items, items_not_found = await self.repo.bulk_get_item_comments(
            item_ids
        )
        return CommentsBulkRead(
            items=items, item_ids_not_found=items_not_found
        )

    async def add_comment(
        self, item_id: ItemID, user: UserRead, data: CommentCreate
    ) -> Comment:
        obj = await self.repo.add_comment(item_id, user.id, data)

        if obj is None:
            raise ItemNotFoundError

        return obj

    async def get_item_image(self, item_id: ItemID) -> ImageRef | None:
        return await self.repo.get_item_image(item_id)

    async def attach_image(
        self, item_id: ItemID, image_id: ImageID
    ) -> ImageID | None:
        return await self.repo.attach_image(item_id, image_id)

    async def detach_image(self, item_id: ItemID) -> ImageID:
        if (id := await self.repo.detach_image(item_id)) is None:
            raise ItemNotFoundError

        return id


ORDINAL_NO_STEP = 10_000
ORDINAL_NO_RANGE = range(-2_147_483_648, 2_147_483_648)


class SwitchToCompleteReorder(Exception):  # noqa: N818
    """Raised when couldn't reorder in an effective way.

    This is not an error and must be catched and handled. Leads to
    a complete reordering.
    """


@dataclass(eq=False, slots=True)
class AdminProjectService:
    repo: AbstractProjectsRepo

    # Projects-related methods

    async def create(self, data: ProjectCreate) -> AdminProjectPure:
        return await self.repo.create(data)

    async def update(
        self, id: ProjectID, data: ProjectUpdate
    ) -> AdminProjectPure:
        if (obj := await self.repo.update_project(id, data)) is None:
            raise ProjectNotFoundError

        return obj

    async def put(self, id: ProjectID, data: ProjectPut) -> ProjectPure:
        if (obj := await self.repo.put(id, data)) is None:
            raise ProjectNotFoundError

        return obj

    async def remove(self, id: ProjectID) -> AdminProject:
        if (obj := await self.repo.remove(id)) is None:
            raise ProjectNotFoundError

        return obj

    # Groups-related methods

    async def create_group(self, data: GroupCreate) -> AdminGroupPure:
        next_ordinal_no = self._get_next_ordinal(
            await self.repo.get_largest_group_ordinal(
                data.project_id, data.group_id
            )
        )

        return await self.repo.create_group(data, next_ordinal_no)

    async def put_group(self, id: GroupID, data: GroupPut) -> GroupPure:
        if (obj := await self.repo.put_group(id, data)) is None:
            return await self.create_group(data)

        return obj

    async def remove_group(self, id: GroupID) -> None:
        result = await self.repo.remove_group(id)

        if not result:
            raise GroupNotFoundError

    async def reorder_groups(
        self,
        project_id: ProjectID,
        parent_id: GroupID | None,
        new_groups_order: Sequence[GroupID],
    ) -> None:
        current_order = await self.repo.get_groups_order(project_id, parent_id)
        ordinals = dict(current_order)

        if not (
            set(new_groups_order) == ordinals.keys()
            and len(new_groups_order) == len(ordinals)
        ):
            msg = (
                "Provided list of group ids do not match "
                "the current groups in the project"
                if parent_id is None
                else "Provided list of group ids do not match "
                "the current subgroups in the group"
            )
            raise GroupNotFoundError(msg)

        new_ordinals = self._compute_new_ordinals(
            current_order, ordinals, new_groups_order
        )

        if not new_ordinals:
            return

        await self.repo.reorder_groups(new_ordinals)

    # Items/groups ordering

    @staticmethod
    def _get_next_ordinal(largest_ordinal: int | None) -> int:
        return (
            largest_ordinal + ORDINAL_NO_STEP
            if largest_ordinal is not None
            else 0
        )

    @staticmethod
    def _find_longest_increasing_subsequence(
        sequence: Sequence[int],
    ) -> list[int]:
        """Find the longest increasing subsequence.

        Args:
            sequence: The input sequence of integers.

        Returns:
            List of indices of the LIS in the input sequence.
        """
        if not sequence:
            return []

        parents: list[int | None] = [None] * len(sequence)
        tails: list[int] = []
        tails_vals: list[int] = []

        for i, x in enumerate(sequence):
            pos = bisect.bisect_left(tails_vals, x)

            if pos == len(tails):
                tails.append(i)
                tails_vals.append(x)
            else:
                tails[pos] = i
                tails_vals[pos] = x

            if pos > 0:
                parents[i] = tails[pos - 1]

        lis: list[int] = []
        current: int | None = tails[-1]

        while current is not None:
            lis.append(current)
            current = parents[current]

        return lis[::-1]

    @overload
    @staticmethod
    def _reorder_subsequence[ID](
        ids: Sequence[ID],
        left: int,
        right: int,
        *,
        left_ordinal_no: int,
        right_ordinal_no: int,
    ) -> Generator[tuple[ID, int]]: ...
    @overload
    @staticmethod
    def _reorder_subsequence[ID](
        ids: Sequence[ID], *, left: int, left_ordinal_no: int
    ) -> Generator[tuple[ID, int]]: ...
    @overload
    @staticmethod
    def _reorder_subsequence[ID](
        ids: Sequence[ID], *, right: int, right_ordinal_no: int
    ) -> Generator[tuple[ID, int]]: ...

    @staticmethod
    def _reorder_subsequence[ID](
        ids: Sequence[ID],
        left: int | None = None,
        right: int | None = None,
        left_ordinal_no: int | None = None,
        right_ordinal_no: int | None = None,
    ) -> Generator[tuple[ID, int]]:
        width = (
            min(right if right is not None else len(ids), len(ids))
            - max(left or 0, 0)
            + 1
        )

        if left_ordinal_no is None:
            if right_ordinal_no is None:
                msg = (
                    "Both left_ordinal_no and right_ordinal_no cannot be None"
                )
                raise TypeError(msg)

            step = ORDINAL_NO_STEP
            left_ordinal_no = right_ordinal_no - step * width
        elif right_ordinal_no is None:
            step = ORDINAL_NO_STEP
        else:
            step = (right_ordinal_no - left_ordinal_no) // width

            if step <= 0:
                raise SwitchToCompleteReorder

        ordinal_no = left_ordinal_no

        for group_id in itertools.islice(ids, left, right):
            ordinal_no += step

            if ordinal_no not in ORDINAL_NO_RANGE:
                raise SwitchToCompleteReorder

            yield (group_id, ordinal_no)

    @classmethod
    def _minimal_reorder[ID](
        cls, ids: Sequence[ID], ordinals: Sequence[int], lis: Sequence[int]
    ) -> Sequence[tuple[ID, int]]:
        new_ordinals: list[tuple[ID, int]] = [
            *cls._reorder_subsequence(
                ids, right=lis[0], right_ordinal_no=ordinals[lis[0]]
            )
        ]

        previous_index = lis[0]

        for index in itertools.islice(lis, 1, None):
            if previous_index + 1 != index:
                new_ordinals.extend(
                    cls._reorder_subsequence(
                        ids,
                        previous_index + 1,
                        index,
                        left_ordinal_no=ordinals[previous_index],
                        right_ordinal_no=ordinals[index],
                    )
                )

            previous_index = index

        new_ordinals.extend(
            cls._reorder_subsequence(
                ids, left=lis[-1] + 1, left_ordinal_no=ordinals[lis[-1]]
            )
        )
        return new_ordinals

    @staticmethod
    def _complete_reorder[ID](ids: Sequence[ID]) -> Sequence[tuple[ID, int]]:
        # NOTE: ORDINAL_NO_RANGE boundaries are not checked (intentional)
        # ordinal might go out of range after many consecutive reorders,
        # not after a complete reorder
        return [
            (group_id, i * ORDINAL_NO_STEP) for i, group_id in enumerate(ids)
        ]

    @classmethod
    def _compute_new_ordinals[ID](
        cls,
        current_order: Sequence[tuple[ID, int]],
        ordinals: Mapping[ID, int],
        new_order: Sequence[ID],
    ) -> Sequence[tuple[ID, int]] | None:
        current_indices = {
            id: index for index, [id, _] in enumerate(current_order)
        }
        new_to_current_order_map = [current_indices[id] for id in new_order]
        lis = cls._find_longest_increasing_subsequence(
            new_to_current_order_map
        )

        if not lis:
            return None

        try:
            return cls._minimal_reorder(
                new_order, [ordinals[id] for id in new_order], lis
            )
        except SwitchToCompleteReorder:
            return cls._complete_reorder(new_order)
