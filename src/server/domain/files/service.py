from dataclasses import dataclass
from typing import TYPE_CHECKING, BinaryIO

from server.api.errors import ImageNotFoundError, ObjectNotFoundError

from .schemas import ContentType

if TYPE_CHECKING:
    from pathlib import Path

    from .ports import (
        AbstractImagesProcessor,
        AbstractImagesRepo,
        AbstractObjectStorage,
    )
    from .schemas import ImageContentType, ImageRef, ObjectKey


@dataclass(eq=False, slots=True)
class FilesService:
    storage: AbstractObjectStorage

    async def get(self, key: ObjectKey) -> Path:
        if (obj := await self.storage.get(key)) is None:
            raise ObjectNotFoundError

        return obj


@dataclass(eq=False, slots=True)
class ImagesService:
    images_repo: AbstractImagesRepo
    objects_repo: AbstractObjectStorage
    processor: AbstractImagesProcessor

    async def upload(
        self,
        content: BinaryIO,
        size: tuple[int, int],
        quality: int,
        filename: str | None = None,
        content_type: ImageContentType | None = None,
    ) -> ImageRef:
        compressed = await self.processor.compress(content, size, quality)

        obj = await self.objects_repo.create(
            compressed, filename, ContentType(content_type)
        )

        return await self.images_repo.create(obj.id, size, quality)

    async def delete(self, id: int) -> None:
        if (deleted := await self.images_repo.delete(id)) is None:
            raise ImageNotFoundError

        await self.objects_repo.delete(deleted.object_id)
