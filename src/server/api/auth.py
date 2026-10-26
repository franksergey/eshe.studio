import logging
from datetime import timedelta
from typing import TYPE_CHECKING, override

from fastapi_users import BaseUserManager, UUIDIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    CookieTransport,
    JWTStrategy,
)

from server.config import settings
from server.domain.users.schemas import UserID, UserRead

if TYPE_CHECKING:
    from fastapi import Request

AUTH_TOKEN_DURATION = round(timedelta(days=14).total_seconds())

logger = logging.getLogger(__name__)
cookie_transport = CookieTransport(
    cookie_name="auth_token", cookie_max_age=AUTH_TOKEN_DURATION
)


def get_jwt_strategy() -> JWTStrategy[UserRead, UserID]:
    return JWTStrategy(
        secret=settings.secret, lifetime_seconds=AUTH_TOKEN_DURATION
    )


auth_backend = AuthenticationBackend(
    name="jwt", transport=cookie_transport, get_strategy=get_jwt_strategy
)


class UserManager(UUIDIDMixin, BaseUserManager[UserRead, UserID]):
    reset_password_token_secret = settings.secret
    verification_token_secret = settings.secret

    @override
    async def on_after_register(
        self, user: UserRead, request: Request | None = None
    ) -> None:
        logger.info(
            "User %r with email %r has been registered.", user.id, user.email
        )

    @override
    async def on_after_request_verify(
        self, user: UserRead, token: str, request: Request | None = None
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
        self, user: UserRead, token: str, request: Request | None = None
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
        self, user: UserRead, request: Request | None = None
    ) -> None:
        logger.info(
            "User %r with email %r has successfully reset their password.",
            user.id,
            user.email,
        )
