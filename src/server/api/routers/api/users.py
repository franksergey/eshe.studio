from collections.abc import Sequence

from fastapi import APIRouter, status
from rfc9457 import UnauthorisedProblem

from server.api.dependencies import (
    ContainerDependency,
    CurrentSuperuserDependency,
    fastapi_users,
)
from server.api.errors import error_handler
from server.domain.users.schemas import (
    UserCreate,
    UserID,
    UserRead,
    UserUpdate,
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/",
    responses={
        status.HTTP_401_UNAUTHORIZED: error_handler.generate_swagger_response(
            UnauthorisedProblem
        )
    },
)
async def list_user_ids(
    user: CurrentSuperuserDependency, container: ContainerDependency
) -> Sequence[UserID]:
    return await container.users.list_user_ids()


@router.post(
    "/",
    responses={
        status.HTTP_401_UNAUTHORIZED: error_handler.generate_swagger_response(
            UnauthorisedProblem
        )
    },
)
async def create_user(
    data: UserCreate,
    user: CurrentSuperuserDependency,
    container: ContainerDependency,
) -> UserRead:
    return await container.users.create(data)


router.include_router(fastapi_users.get_users_router(UserRead, UserUpdate))
