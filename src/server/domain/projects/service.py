from dataclasses import dataclass
from typing import TYPE_CHECKING

from server.api.errors import ItemNotFoundError, ProjectNotFoundError

if TYPE_CHECKING:
    from .ports import AbstractProjectsRepo
    from .schemas import Comment, CommentCreate, Project, ProjectPure


@dataclass(eq=False, slots=True)
class ProjectsService:
    repo: AbstractProjectsRepo

    async def get(self, id: int) -> Project:
        obj = await self.repo.get(id)

        if obj is None:
            raise ProjectNotFoundError

        return obj

    async def get_all(self) -> list[Project]:
        return await self.repo.get_all()

    async def get_all_pure(self) -> list[ProjectPure]:
        return await self.repo.get_all_pure()

    async def get_item_comments(self, item_id: int) -> list[Comment]:
        objs = await self.repo.get_item_comments(item_id)

        if objs is None:
            raise ItemNotFoundError

        return objs

    async def add_comment(self, item_id: int, data: CommentCreate) -> Comment:
        obj = await self.repo.add_comment(item_id, data)

        if obj is None:
            raise ItemNotFoundError

        return obj
