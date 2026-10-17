from dataclasses import dataclass
from typing import TYPE_CHECKING, BinaryIO

if TYPE_CHECKING:
    from pathlib import Path

    from server.domain.files.schemas import ObjectKey

    from .ports import AbstractImagesRepo, AbstractObjectStorage
    from .schemas import ImageContentType, ImageRef


@dataclass(eq=False, slots=True)
class StorageService:
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
