from dataclasses import dataclass
from typing import TYPE_CHECKING, BinaryIO

if TYPE_CHECKING:
    from pathlib import Path

    from .ports import AbstractImagesRepo, AbstractObjectStorage
    from .schemas import ImageContentType, ImageRef, ObjectKey


@dataclass(eq=False, slots=True)
class FilesService:
    storage: AbstractObjectStorage

    def get(self, key: ObjectKey) -> Path:
        return self.storage.get(key)


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
