from fastapi import APIRouter

from server.api.dependencies import fastapi_users
from server.domain.users.schemas import UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])
router.include_router(fastapi_users.get_users_router(UserRead, UserUpdate))
