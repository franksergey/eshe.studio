from fastapi import APIRouter, status

from server.api.dependencies import (
    ContainerDependency,
    CurrentVerifiedUserDependency,
)
from server.api.errors import ProjectNotFoundError, error_handler
from server.domain.projects.schemas import Project, ProjectPure
from server.domain.selections.schemas import SelectionCreate

router = APIRouter(prefix="/projects", tags=["Arhitectural Projects"])


@router.get("/")
async def read_projects(container: ContainerDependency) -> list[ProjectPure]:
    """Получить список сразу всех комплектаций проектов."""
    return await container.projects.get_all_pure()


@router.get(
    "/{id}",
    responses={
        status.HTTP_404_NOT_FOUND: error_handler.generate_swagger_response(
            ProjectNotFoundError
        )
    },
)
async def read_project(id: int, container: ContainerDependency) -> ProjectPure:
    """Получить данные об архитектурном проекте."""
    return await container.projects.get_pure(id)


@router.get(
    "/{id}/spec",
    responses={
        status.HTTP_404_NOT_FOUND: error_handler.generate_swagger_response(
            ProjectNotFoundError
        )
    },
)
async def read_project_specification(
    id: int, container: ContainerDependency
) -> Project:
    """Получить таблицу комплектации архитектурного проекта."""
    return await container.projects.get(id)


@router.post(
    "/{id}/select",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_404_NOT_FOUND: error_handler.generate_swagger_response(
            ProjectNotFoundError
        )
    },
)
async def select_project_specification_items(
    id: int,
    data: SelectionCreate,
    user: CurrentVerifiedUserDependency,
    container: ContainerDependency,
) -> None:
    """Отправить выбор карточек таблицы спецификации."""
    project = await container.projects.get(id)

    await container.selections.create(project, data, user)
