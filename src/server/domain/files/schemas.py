import uuid
from enum import StrEnum
from typing import Annotated

from pydantic import AwareDatetime, BaseModel, Field, model_validator

type ObjectKey = uuid.UUID
type ImageID = int


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
    id: ImageID
    object_id: ObjectKey

    size: tuple[int, int]
    quality: int

    @model_validator(mode="before")
    @classmethod
    def _validate_size(cls, v: object) -> object:
        if isinstance(v, dict) and "width" in v and "height" in v:
            v["size"] = (v.pop("width"), v.pop("height"))

        elif hasattr(v, "width") and hasattr(v, "height"):
            # pyrefly: ignore[missing-attribute]
            v.size = (v.width, v.height)

        return v
