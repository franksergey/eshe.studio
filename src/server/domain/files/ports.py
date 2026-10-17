from typing import TYPE_CHECKING, BinaryIO, Protocol

if TYPE_CHECKING:
    from .schemas import ObjectInfo, ObjectKey


class ObjectStorage(Protocol):
    async def create(
        self, key: ObjectKey, content: BinaryIO
    ) -> ObjectInfo: ...
    async def put(
        self,
        key: ObjectKey,
        content: BinaryIO,
        expected: ObjectInfo | None = None,
    ) -> ObjectInfo: ...
    async def get(self, key: ObjectKey) -> BinaryIO: ...
    async def head(self, key: ObjectKey) -> ObjectInfo: ...
    async def delete(self, key: ObjectKey) -> None: ...
