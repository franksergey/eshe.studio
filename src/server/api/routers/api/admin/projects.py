from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Query
from pydantic import EmailStr

from server.api.dependencies import (
    ContainerDependency,
    CurrentSuperuserDependency,
)
from server.domain.selections.schemas import Selection, SelectionPure

router = APIRouter(prefix="/projects")


@router.get("/{project_id}/selections")
async def admin_read_selection(
    project_id: int,
    user: CurrentSuperuserDependency,
    container: ContainerDependency,
    user_email: Annotated[EmailStr | None, Query()] = None,
) -> Sequence[SelectionPure] | Selection | None:
    if user_email is None:
        return await container.selections.get_for_project(project_id)

    requested_user = await container.users.get_by_email(user_email)
    return await container.selections.get_by_user(project_id, requested_user)
