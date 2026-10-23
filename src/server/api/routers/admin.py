from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from server.api.common import templates
from server.api.dependencies import CurrentSuperuserDependency

router = APIRouter(prefix="/admin", tags=["Admin Panel Router"])


@router.get("/")
async def read_admin_page(
    request: Request, user: CurrentSuperuserDependency
) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request, name="admin/index.html.jinja", context={"user": user}
    )
