from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from server.api.common import templates
from server.api.dependencies import ContainerDependency, OptionalUserDependency

router = APIRouter(prefix="", tags=["Root Router"])


@router.get("/project-{id}")
async def read_project(
    request: Request,
    id: int,
    user: OptionalUserDependency,
    container: ContainerDependency,
) -> HTMLResponse:
    project = await container.projects.get_pure(id)
    category = await container.projects.get_categories(id)
    categories = await container.projects.get_categories_pure(id)

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
    category = await container.projects.get_categories(id, index=index - 1)
    categories = await container.projects.get_categories_pure(id)

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
