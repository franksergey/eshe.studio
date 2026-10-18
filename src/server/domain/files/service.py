from dataclasses import dataclass
from typing import TYPE_CHECKING, BinaryIO

from server.api.errors import ObjectNotFoundError

if TYPE_CHECKING:
    from pathlib import Path

    from .ports import AbstractImagesRepo, AbstractObjectStorage
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
    repo: AbstractImagesRepo

    async def create(
        self,
        content: BinaryIO,
        filename: str | None = None,
        content_type: ImageContentType | None = None,
    ) -> ImageRef:
        return await self.repo.create(content, filename, content_type)
