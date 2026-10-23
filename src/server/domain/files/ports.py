from typing import TYPE_CHECKING, BinaryIO, Protocol

if TYPE_CHECKING:
    from pathlib import Path

    from .schemas import ContentType, ImageRef, ObjectInfo, ObjectKey


class AbstractObjectStorage(Protocol):
    async def create(
        self,
        content: BinaryIO,
        filename: str | None = None,
        content_type: ContentType | None = None,
    ) -> ObjectInfo: ...
    async def put(
        self,
        key: ObjectKey,
        content: BinaryIO,
        filename: str | None = None,
        content_type: ContentType | None = None,
        expected: ObjectInfo | None = None,
    ) -> ObjectInfo | None: ...
    async def get(self, key: ObjectKey) -> Path | None: ...
    async def head(self, key: ObjectKey) -> ObjectInfo | None: ...
    async def delete(self, key: ObjectKey) -> None: ...


class AbstractImagesRepo(Protocol):
    async def create(
        self, object_id: ObjectKey, size: tuple[int, int], quality: int
    ) -> ImageRef: ...
    async def delete(self, id: int) -> ImageRef | None: ...


class AbstractImagesProcessor(Protocol):
    async def compress(
        self, image: BinaryIO, size: tuple[int, int], quality: int
    ) -> BinaryIO: ...
