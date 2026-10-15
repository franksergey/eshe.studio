from typing import TYPE_CHECKING

from .api import api_router
from .auth import router as auth_router
from .root import router as root_router

if TYPE_CHECKING:
    from fastapi.routing import APIRouter

ALL_ROUTERS: list[APIRouter] = [api_router, auth_router, root_router]
