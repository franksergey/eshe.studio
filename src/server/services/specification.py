from dataclasses import dataclass
from typing import TYPE_CHECKING

from server.api.errors import SpecificationNotFoundError

if TYPE_CHECKING:
    from server.services.ports import AbstractSpecificationRepo
    from server.services.schemas import Specification, SpecificationPure


@dataclass(eq=False, slots=True)
class SpecificationService:
    repo: AbstractSpecificationRepo

    def get(self, id: int) -> Specification:
        obj = self.repo.get(id)

        if obj is None:
            raise SpecificationNotFoundError

        return obj

    def get_all(self) -> list[Specification]:
        return self.repo.get_all()

    def get_all_pure(self) -> list[SpecificationPure]:
        return self.repo.get_all_pure()
