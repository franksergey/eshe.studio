from dataclasses import dataclass
from typing import TYPE_CHECKING

from sqlalchemy import delete

from server.domain.files.ports import AbstractImagesRepo
from server.domain.files.schemas import ImageRef
from server.sql.models import ImageDB

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from server.domain.files.schemas import ObjectKey


@dataclass(eq=False, slots=True)
class ImagesRepo(AbstractImagesRepo):
    session: AsyncSession

    @staticmethod
    def _to_domain_schema(obj: ImageDB) -> ImageRef:
        return ImageRef(
            id=obj.id,
            object_id=obj.object_id,
            size=(obj.width, obj.height),
            quality=obj.quality,
        )

    async def create(
        self, object_id: ObjectKey, size: tuple[int, int], quality: int
    ) -> ImageRef:
        obj = ImageDB(
            object_id=object_id, width=size[0], height=size[1], quality=quality
        )

        self.session.add(obj)
        await self.session.flush((obj,))

        return self._to_domain_schema(obj)

    async def delete(self, id: int) -> ImageRef | None:
        stmt = delete(ImageDB).where(ImageDB.id == id).returning(ImageDB)

        if (obj := await self.session.scalar(stmt)) is None:
            return None

        return self._to_domain_schema(obj)
