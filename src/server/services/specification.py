from dataclasses import dataclass
from typing import TYPE_CHECKING

from server.api.errors import SpecificationNotFoundError

if TYPE_CHECKING:
    from server.services.ports import AbstractSpecificationRepo
    from server.services.schemas import Specification, SpecificationPure


@dataclass(eq=False, slots=True)
class SpecificationService:
    repo: AbstractSpecificationRepo

    async def get(self, id: int) -> Specification:
        obj = await self.repo.get(id)

        if obj is None:
            raise SpecificationNotFoundError

        return obj

    async def get_all(self) -> list[Specification]:
        return await self.repo.get_all()

    async def get_all_pure(self) -> list[SpecificationPure]:
        return await self.repo.get_all_pure()
