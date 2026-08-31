from fastapi import Depends, Query
from fastapi.routing import APIRouter
from sqlmodel import Session

from app.Deps import get_current_user, get_session
from app.common.Result import Result
from app.schemas.PostSchemas import (
    CreatePostRequest,
    PostCountResponse,
    PostDetailResponse,
    PostLikeResponse,
    PostResponse,
    UpdatePostRequest,
)
from app.service import PostService as post_service


router = APIRouter(prefix="/api/posts", tags=["文章模块"])


@router.get("", response_model=Result[list[PostResponse]])
def list_posts(
    status: str | None = None,
    category: str | None = None,
    tag: str | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=200),
    session: Session = Depends(get_session),
):
    """获取文章列表。

    可按状态、分类 slug、标签 slug 筛选，分页返回。公开接口。不含正文。

    Args:
        status: 文章状态，可选 draft / published / archived。
        category: 分类 slug，可选。
        tag: 标签 slug，可选。
        page: 页码，从 1 开始。
        size: 每页条数，最大 200。
        session: 数据库会话，由依赖注入提供。

    Returns:
        统一结果集。成功时 code=200，data 为文章列表。
    """
    return post_service.list_posts(session, status, category, tag, page, size)


@router.get("/count", response_model=Result[PostCountResponse])
def posts_count(
    status: str | None = None, session: Session = Depends(get_session)
):
    """获取文章数量。

    可按状态筛选。公开接口。须注册在 /{slug} 之前。

    Args:
        status: 文章状态，可选 draft / published / archived。
        session: 数据库会话，由依赖注入提供。

    Returns:
        统一结果集。成功时 code=200，data 含 count。
    """
    return post_service.count_posts(session, status)


@router.get("/detail/{post_id}", response_model=Result[PostDetailResponse])
def post_detail_by_id(post_id: int, session: Session = Depends(get_session)):
    """按 ID 获取文章详情。

    含正文，不增加浏览量。给后台编辑页用。公开接口。
    文章不存在则 404。须注册在 /{slug} 之前。

    Args:
        post_id: 文章 ID。
        session: 数据库会话，由依赖注入提供。

    Returns:
        统一结果集。成功时 code=200，data 为文章详情（含正文）。
    """
    return post_service.get_post_by_id(session, post_id)


@router.get("/{slug}", response_model=Result[PostDetailResponse])
def post_detail_by_slug(slug: str, session: Session = Depends(get_session)):
    """按 slug 获取文章详情。

    含正文，每次访问浏览量 +1。给前台展示页用。公开接口。
    文章不存在则 404。须写在 /count、/detail/{id} 之后。

    Args:
        slug: 文章 URL 别名。
        session: 数据库会话，由依赖注入提供。

    Returns:
        统一结果集。成功时 code=200，data 为文章详情（含正文）。
    """
    return post_service.get_post_by_slug(session, slug)


@router.post("", response_model=Result[PostResponse])
def create_post(
    CreatePostReq: CreatePostRequest,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """创建文章。

    需管理员 JWT。slug 全站唯一，冲突则 400。
    tags 为标签名称，没有则创建。已发布且无 published_at 时写入当前时间。

    Args:
        CreatePostReq: 创建文章请求体。
        session: 数据库会话，由依赖注入提供。
        current_user: JWT payload，用来校验已登录；本接口不用里面的字段。

    Returns:
        统一结果集。成功时 code=200，data 为文章（不含正文）。
    """
    return post_service.create_post(session, CreatePostReq)



@router.put("/{post_id}", response_model=Result[PostResponse])
def update_post(
    post_id: int,
    UpdatePostReq: UpdatePostRequest,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """更新文章。

    需管理员 JWT。全部字段可选。文章不存在则 404。
    slug 全站唯一（排除自身），冲突则 400。
    tags 不传则不改标签；传 [] 表示清空。

    Args:
        post_id: 文章 ID。
        UpdatePostReq: 更新文章请求体。
        session: 数据库会话，由依赖注入提供。
        current_user: JWT payload，用来校验已登录；本接口不用里面的字段。

    Returns:
        统一结果集。成功时 code=200，data 为文章（不含正文）。
    """
    return post_service.update_post(session, post_id, UpdatePostReq)


@router.post("/{post_id}/like", response_model=Result[PostLikeResponse])
def like_post(post_id: int, session: Session = Depends(get_session)):
    """给文章点赞。

    公开接口。文章不存在则 404。likes +1。

    Args:
        post_id: 文章 ID。
        session: 数据库会话，由依赖注入提供。

    Returns:
        统一结果集。成功时 code=200，data 含 likes。
    """
    return post_service.like_post(session, post_id,unliked=False)


@router.post("/{post_id}/unlike", response_model=Result[PostLikeResponse])
def unlike_post(post_id: int, session: Session = Depends(get_session)):
    """取消文章点赞。

    Args:
        post_id: 文章 ID。
        session: 数据库会话，由依赖注入提供。

    Returns:
        统一结果集。成功时 code=200，data 含 likes。
    """
    return post_service.like_post(session, post_id,unliked=True)


@router.delete("/{post_id}", response_model=Result)
def delete_post(
    post_id: int,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """删除文章。

    需管理员 JWT。文章不存在则 404。
    删除后重算所属分类和全部标签的文章数。

    Args:
        post_id: 文章 ID。
        session: 数据库会话，由依赖注入提供。
        current_user: JWT payload，用来校验已登录；本接口不用里面的字段。

    Returns:
        统一结果集。成功时 code=200，message 为「删除成功」。
    """
    return post_service.delete_post(session, post_id)

