from fastapi import APIRouter

from .auth import router as auth_router
from .items import router as items_router
from .specifications import router as specifications_router
from .users import router as users_router

__all__ = ["api_router", "auth_router"]

API_ROUTERS = [specifications_router, items_router, users_router]

api_router = APIRouter(prefix="/api")

for router in API_ROUTERS:
    api_router.include_router(router)
