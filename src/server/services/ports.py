from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from server.services.schemas import SpecificationPure

    from .schemas import Specification


class AbstractSpecificationRepo(Protocol):
    async def get(self, id: int) -> Specification | None: ...
    async def get_all(self) -> list[Specification]: ...
    async def get_all_pure(self) -> list[SpecificationPure]: ...
