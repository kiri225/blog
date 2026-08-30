from fastapi import APIRouter

api_router = APIRouter()

from app.api.AuthRouter import router as auth_router
from app.api.CategoriesRouter import router as categories_router
from app.api.TagsRouter import router as tags_router

api_router.include_router(auth_router)
api_router.include_router(categories_router)
api_router.include_router(tags_router)

