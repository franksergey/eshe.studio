from typing import TYPE_CHECKING, BinaryIO, Protocol

if TYPE_CHECKING:
    from pathlib import Path

    from .schemas import (
        ContentType,
        ImageContentType,
        ImageRef,
        ObjectInfo,
        ObjectKey,
    )


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
    def get(self, key: ObjectKey) -> Path: ...
    async def head(self, key: ObjectKey) -> ObjectInfo | None: ...
    async def delete(self, key: ObjectKey) -> None: ...


class AbstractImagesRepo(Protocol):
    async def create(
        self,
        content: BinaryIO,
        filename: str | None = None,
        content_type: ImageContentType | None = None,
    ) -> ImageRef: ...
    async def put(
        self,
        id: int,
        content: BinaryIO,
        filename: str | None = None,
        content_type: ImageContentType | None = None,
    ) -> ImageRef | None: ...
