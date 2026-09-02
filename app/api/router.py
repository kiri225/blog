from fastapi import APIRouter

api_router = APIRouter()

from app.api.AuthRouter import router as auth_router
from app.api.GitHubAuthRouter import router as github_auth_router
from app.api.CategoriesRouter import router as categories_router
from app.api.TagsRouter import router as tags_router
from app.api.PostsApi import router as posts_router
from app.api.CommentRouter import router as comments_router
from app.api.MessagesRouter import router as messages_router
from app.api.ChatterRouter import router as chatters_router
from app.api.AlbumRouter import router as albums_router
from app.api.UploadRouter import router as upload_router
from app.api.ProjectRouter import router as projects_router
from app.api.FriendLinkRouter import router as friend_links_router

api_router.include_router(auth_router)
api_router.include_router(github_auth_router)
api_router.include_router(categories_router)
api_router.include_router(tags_router)
api_router.include_router(posts_router)
api_router.include_router(comments_router)
api_router.include_router(messages_router)
api_router.include_router(chatters_router)
api_router.include_router(albums_router)
api_router.include_router(upload_router)
api_router.include_router(projects_router)
api_router.include_router(friend_links_router)


