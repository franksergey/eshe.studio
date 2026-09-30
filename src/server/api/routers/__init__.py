from fastapi import APIRouter

from .items import router as items_router
from .specifications import router as specifications_router

API_ROUTERS = [specifications_router, items_router]

api_router = APIRouter(prefix="/api")

for router in API_ROUTERS:
    api_router.include_router(router)
