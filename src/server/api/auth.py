import logging
import uuid
from typing import TYPE_CHECKING, override

from fastapi_users import BaseUserManager, UUIDIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)

from server.config import settings
from server.sql.models import UserDB

if TYPE_CHECKING:
    from fastapi import Request

logger = logging.getLogger(__name__)
bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")


def get_jwt_strategy() -> JWTStrategy[UserDB, uuid.UUID]:
    return JWTStrategy(secret=settings.secret, lifetime_seconds=3600)


auth_backend = AuthenticationBackend(
    name="jwt", transport=bearer_transport, get_strategy=get_jwt_strategy
)


class UserManager(UUIDIDMixin, BaseUserManager[UserDB, uuid.UUID]):
    reset_password_token_secret = settings.secret
    verification_token_secret = settings.secret

    @override
    async def on_after_register(
        self, user: UserDB, request: Request | None = None
    ) -> None:
        logger.info(
            "User %r with email %r has been registered.", user.id, user.email
        )

    @override
    async def on_after_request_verify(
        self, user: UserDB, token: str, request: Request | None = None
    ) -> None:
        logger.info(
            "Verification request for user %r with email %r."
            "Verification token: %r",
            user.id,
            user.email,
            token,
        )

    @override
    async def on_after_forgot_password(
        self, user: UserDB, token: str, request: Request | None = None
    ) -> None:
        logger.info(
            "User %r with email %r has forgotten their password. "
            "Reset token: %r",
            user.id,
            user.email,
            token,
        )

    @override
    async def on_after_reset_password(
        self, user: UserDB, request: Request | None = None
    ) -> None:
        logger.info(
            "User %r with email %r has successfully reset their password.",
            user.id,
            user.email,
        )
