from fastapi import APIRouter
from pydantic import BaseModel

from server.api.dependencies import ContainerDependency
from server.api.errors import ProjectNotFoundError, error_handler
from server.domain.projects.schemas import (
    Comment,
    CommentCreate,
    CommentsBulkRead,
)

router = APIRouter(prefix="/items", tags=["Specification Items"])


class BulkReadCommentsRequest(BaseModel):
    item_ids: list[int]


@router.post("/bulk-comments")
async def bulk_read_comments(
    data: BulkReadCommentsRequest, container: ContainerDependency
) -> CommentsBulkRead:
    return await container.projects.bulk_get_item_comments(data.item_ids)


@router.get(
    "/{item_id}/comments",
    responses={
        404: error_handler.generate_swagger_response(ProjectNotFoundError)
    },
)
async def read_comment(
    item_id: int, container: ContainerDependency
) -> list[Comment]:
    """Получить список комментариев."""
    return await container.projects.get_item_comments(item_id)


@router.post(
    "/{item_id}/comments",
    responses={
        404: error_handler.generate_swagger_response(ProjectNotFoundError)
    },
    status_code=201,
)
async def create_comment(
    item_id: int, data: CommentCreate, container: ContainerDependency
) -> Comment:
    """Создать новый комментарий."""
    return await container.projects.add_comment(item_id, data)
