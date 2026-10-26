from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from server.api.common import templates
from server.api.dependencies import ContainerDependency, OptionalUserDependency
from server.api.errors import GroupNotFoundError

router = APIRouter(prefix="", tags=["Root Router"])


@router.get("/")
async def read_root_page(
    request: Request,
    user: OptionalUserDependency,
    container: ContainerDependency,
) -> HTMLResponse:
    projects = await container.projects.get_all_pure()

    return templates.TemplateResponse(
        request=request,
        name="index.html.jinja",
        context={"projects": projects, "user": user},
    )


@router.get("/project-{id}")
async def read_project_page(
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
    users_selected = await container.selections.get_users(id)

    return templates.TemplateResponse(
        request=request,
        name="project_spec.html.jinja",
        context={
            "project": project,
            "user": user,
            "category": category,
            "categories": categories,
            "project_users_selected": users_selected,
        },
    )


@router.get("/project-{id}/{index}")
async def read_project_category_page(
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
    users_selected = await container.users.bulk_get_users(
        await container.selections.get_users(id)
    )

    return templates.TemplateResponse(
        request=request,
        name="project_spec.html.jinja",
        context={
            "project": project,
            "user": user,
            "category": category,
            "categories": categories,
            "project_users_selected": users_selected,
        },
    )


@router.get("/login")
async def read_login_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request, name="login.html.jinja", context={}
    )
