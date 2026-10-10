import uuid

from fastapi_users import FastAPIUsers

from server.api.auth import auth_backend
from server.api.dependencies import get_user_manager
from server.sql.models import UserDB

fastapi_users = FastAPIUsers[UserDB, uuid.UUID](
    # BUG: Swapped type params # pyrefly: ignore [bad-argument-type]
    get_user_manager,
    [auth_backend],
)

router = fastapi_users.get_auth_router(auth_backend)
