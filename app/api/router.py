from fastapi import APIRouter

api_router = APIRouter()

from app.api.AuthRouter import router as auth_router
from app.api.GitHubAuthRouter import router as github_auth_router
from app.api.CategoriesRouter import router as categories_router
from app.api.TagsRouter import router as tags_router
from app.api.PostsApi import router as posts_router
from app.api.CommentRouter import router as comments_router

api_router.include_router(auth_router)
api_router.include_router(github_auth_router)
api_router.include_router(categories_router)
api_router.include_router(tags_router)
api_router.include_router(posts_router)
api_router.include_router(comments_router)


