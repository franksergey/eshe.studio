from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from server.api.common import templates
from server.api.dependencies import ContainerDependency

router = APIRouter(prefix="", tags=["Root Router"])


@router.get("/project-{id}")
async def read_project(
    request: Request, id: int, container: ContainerDependency
) -> HTMLResponse:
    project = await container.projects.get_pure(id)

    return templates.TemplateResponse(
        request=request,
        name="project_spec.html.jinja",
        context={"name": project.name, "id": project.id},
    )
