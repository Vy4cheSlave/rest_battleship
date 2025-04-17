from fastapi import APIRouter
from .auth import auth_router
from .routes import routes
from .websockets import websoket_router



api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(routes)
api_router.include_router(websoket_router)