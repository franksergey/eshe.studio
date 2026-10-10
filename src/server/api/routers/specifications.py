from fastapi import APIRouter

from server.api.dependencies import ContainerDependency
from server.api.errors import ProjectNotFoundError, error_handler
from server.domain.projects.schemas import Project, ProjectPure

router = APIRouter(prefix="/specifications", tags=["Rooms Specifications"])


@router.get("/")
async def read_specifications(
    container: ContainerDependency,
) -> list[ProjectPure]:
    """Получить список сразу всех комплектаций проектов."""
    return await container.specifications.get_all_pure()


@router.get(
    "/{id}",
    responses={
        404: error_handler.generate_swagger_response(ProjectNotFoundError)
    },
)
async def read_specification(
    id: int, container: ContainerDependency
) -> Project:
    """Получить список сразу всех комплектаций проектов."""
    return await container.specifications.get(id)
