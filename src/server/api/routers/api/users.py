from collections.abc import Sequence

from fastapi import APIRouter

from server.api.dependencies import (
    ContainerDependency,
    CurrentSuperuserDependency,
    fastapi_users,
)
from server.domain.users.schemas import UserID, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/")
async def list_user_ids(
    user: CurrentSuperuserDependency, container: ContainerDependency
) -> Sequence[UserID]:
    return await container.users.list_user_ids()


router.include_router(fastapi_users.get_users_router(UserRead, UserUpdate))
