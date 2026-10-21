from fastapi import APIRouter

from .items import router as items_admin_router

__all__ = ["admin_router"]

ADMIN_ROUTERS = [items_admin_router]
admin_router = APIRouter(prefix="/admin", tags=["API Admin-panel"])

for router in ADMIN_ROUTERS:
    admin_router.include_router(router)
