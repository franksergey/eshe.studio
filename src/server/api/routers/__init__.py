from fastapi import APIRouter

from .auth import router as auth_router
from .items import router as items_router
from .projects import router as projects_router
from .users import router as users_router

__all__ = ["api_router", "auth_router"]

API_ROUTERS = [projects_router, items_router, users_router]

api_router = APIRouter(prefix="/api")

for router in API_ROUTERS:
    api_router.include_router(router)
