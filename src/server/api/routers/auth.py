from server.api.auth import auth_backend
from server.api.dependencies import fastapi_users

router = fastapi_users.get_auth_router(auth_backend)
