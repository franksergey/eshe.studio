from fastapi import APIRouter

from server.api.dependencies import ContainerDependency
from server.api.errors import ProjectNotFoundError, error_handler
from server.domain.projects.schemas import Project, ProjectPure

router = APIRouter(prefix="/projects", tags=["Arhitectural Projects"])


@router.get("/")
async def read_projects(container: ContainerDependency) -> list[ProjectPure]:
    """Получить список сразу всех комплектаций проектов."""
    return await container.projects.get_all_pure()


@router.get(
    "/{id}",
    responses={
        404: error_handler.generate_swagger_response(ProjectNotFoundError)
    },
)
async def read_project(id: int, container: ContainerDependency) -> ProjectPure:
    """Получить данные об архитектурном проекте."""
    return await container.projects.get_pure(id)


@router.get(
    "/{id}/spec",
    responses={
        404: error_handler.generate_swagger_response(ProjectNotFoundError)
    },
)
async def read_project_specification(
    id: int, container: ContainerDependency
) -> Project:
    """Получить таблицу комплектации архитектурного проекта."""
    return await container.projects.get(id)
