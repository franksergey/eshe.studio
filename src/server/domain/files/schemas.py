import uuid
from enum import StrEnum

from pydantic import AwareDatetime, BaseModel

type ObjectKey = uuid.UUID


class ContentType(StrEnum):
    IMAGE_JPEG = "image/jpeg"
    IMAGE_PNG = "image/png"
    IMAGE_WEBP = "image/webp"
    IMAGE_GIF = "image/gif"
    IMAGE_SVG = "image/svg+xml"


class ObjectInfo(BaseModel):
    id: uuid.UUID

    original_filename: str | None
    content_type: ContentType

    created_at: AwareDatetime
    updated_at: AwareDatetime
