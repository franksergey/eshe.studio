from fastapi import APIRouter

from server.api.dependencies import ContainerDependency
from server.api.errors import SpecificationNotFoundError, error_handler
from server.services.schemas import Comment, CommentCreate

router = APIRouter(prefix="/items", tags=["Specification Items"])


@router.get(
    "/{item_id}/comments",
    responses={
        404: error_handler.generate_swagger_response(
            SpecificationNotFoundError
        )
    },
)
async def read_comment(
    item_id: int, container: ContainerDependency
) -> list[Comment]:
    """Получить список комментариев."""
    return await container.specifications.get_item_comments(item_id)


@router.post(
    "/{item_id}/comments",
    responses={
        404: error_handler.generate_swagger_response(
            SpecificationNotFoundError
        )
    },
    status_code=201,
)
async def create_comment(
    item_id: int, data: CommentCreate, container: ContainerDependency
) -> Comment:
    """Создать новый комментарий."""
    return await container.specifications.add_comment(item_id, data)
