from fastapi import APIRouter

api_router = APIRouter()

from app.api.AuthRouter import router as auth_router

api_router.include_router(auth_router)
