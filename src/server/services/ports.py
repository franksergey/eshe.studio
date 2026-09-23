from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from server.services.schemas import SpecificationPure

    from .schemas import Specification


class AbstractSpecificationRepo(Protocol):
    def get(self, id: int) -> Specification | None: ...
    def get_all(self) -> list[Specification]: ...
    def get_all_pure(self) -> list[SpecificationPure]: ...
