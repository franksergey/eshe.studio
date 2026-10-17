from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from server.api.common import templates
from server.api.dependencies import ContainerDependency, OptionalUserDependency
from server.api.errors import GroupNotFoundError

router = APIRouter(prefix="", tags=["Root Router"])


@router.get("/project-{id}")
async def read_project(
    request: Request,
    id: int,
    user: OptionalUserDependency,
    container: ContainerDependency,
) -> HTMLResponse:
    project = await container.projects.get_pure(id)
    categories = await container.projects.get_categories_pure(id)

    if not categories:
        raise GroupNotFoundError

    category = await container.projects.get_categories(id, categories[0].id)

    return templates.TemplateResponse(
        request=request,
        name="project_spec.html.jinja",
        context={
            "project": project,
            "user": user,
            "category": category,
            "categories": categories,
        },
    )


@router.get("/project-{id}/{index}")
async def read_project_category(
    request: Request,
    id: int,
    index: int,
    user: OptionalUserDependency,
    container: ContainerDependency,
) -> HTMLResponse:
    project = await container.projects.get_pure(id)
    categories = await container.projects.get_categories_pure(id)

    if index < 1 or len(categories) < index:
        raise GroupNotFoundError

    category = await container.projects.get_categories(
        id, group_id=categories[index - 1].id
    )

    return templates.TemplateResponse(
        request=request,
        name="project_spec.html.jinja",
        context={
            "project": project,
            "user": user,
            "category": category,
            "categories": categories,
        },
    )
