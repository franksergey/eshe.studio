import uuid
from enum import StrEnum
from typing import Annotated

from pydantic import AwareDatetime, BaseModel, Field

type ObjectKey = uuid.UUID


class ImageContentType(StrEnum):
    IMAGE_JPEG = "image/jpeg"
    IMAGE_PNG = "image/png"
    IMAGE_WEBP = "image/webp"
    IMAGE_GIF = "image/gif"
    IMAGE_SVG = "image/svg+xml"


class ContentType(StrEnum):
    IMAGE_JPEG = "image/jpeg"
    IMAGE_PNG = "image/png"
    IMAGE_WEBP = "image/webp"
    IMAGE_GIF = "image/gif"
    IMAGE_SVG = "image/svg+xml"


class ObjectInfo(BaseModel):
    id: ObjectKey

    size: int
    sha256: str
    etag: str

    original_filename: Annotated[str, Field(max_length=1024)] | None
    content_type: ContentType | None

    created_at: AwareDatetime
    updated_at: AwareDatetime


class ImageRef(BaseModel):
    id: int
    object_id: ObjectKey

    size: tuple[int, int]
    quality: int
