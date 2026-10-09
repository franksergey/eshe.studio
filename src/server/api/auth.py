import uuid

from fastapi_users import BaseUserManager, UUIDIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)

from server.config import settings
from server.sql.models import UserDB

bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")


def get_jwt_strategy() -> JWTStrategy[UserDB, uuid.UUID]:
    return JWTStrategy(secret=settings.secret, lifetime_seconds=3600)


auth_backend = AuthenticationBackend(
    name="jwt", transport=bearer_transport, get_strategy=get_jwt_strategy
)


class UserManager(UUIDIDMixin, BaseUserManager[UserDB, uuid.UUID]):
    reset_password_token_secret = settings.secret
    verification_token_secret = settings.secret
