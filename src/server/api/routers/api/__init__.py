from fastapi import APIRouter

from server.api.routers.api.items import router as items_router
from server.api.routers.api.projects import router as projects_router
from server.api.routers.api.users import router as users_router

__all__ = ["api_router"]

API_ROUTERS = [projects_router, items_router, users_router]
api_router = APIRouter(prefix="/api")

for router in API_ROUTERS:
    api_router.include_router(router)
