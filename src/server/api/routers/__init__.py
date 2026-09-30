from .items import router as items_router
from .specifications import router as specifications_router

ROUTERS = [specifications_router, items_router]
