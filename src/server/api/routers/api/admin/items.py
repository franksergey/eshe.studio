from fastapi import APIRouter, Request, UploadFile
from pydantic import HttpUrl

from server.api.dependencies import (
    ContainerDependency,
    CurrentSuperuserDependency,
)

router = APIRouter(prefix="/items")


ITEM_IMAGE_SIZE = (500, 600)
ITEM_IMAGE_QUALITY = 80


@router.post("/{item_id}/image")
async def admin_upload_image(
    item_id: int,
    image: UploadFile,
    user: CurrentSuperuserDependency,
    container: ContainerDependency,
    request: Request,
) -> HttpUrl:
    uploaded = await container.images.upload(
        image.file, ITEM_IMAGE_SIZE, ITEM_IMAGE_QUALITY, image.filename
    )
    previous = await container.projects.attach_image(item_id, uploaded.id)

    if previous is not None:
        await container.images.delete(previous)

    return HttpUrl(str(request.url_for("read_file", key=uploaded.object_id)))
