from fastapi import Depends, Query
from fastapi.requests import Request
from fastapi.routing import APIRouter
from sqlmodel import Session

from app.Deps import get_current_user, get_github_user_optional, get_session
from app.common.Result import Result
from app.schemas.CommentSchemas import (
    CommentAdminResponse,
    CommentResponse,
    CreateCommentRequest,
    UpdateCommentStatusRequest,
)
from app.service import CommentService as comment_service


router = APIRouter(prefix="/api/comments", tags=["评论"])


@router.get("/post/{post_id}", response_model=Result[list[CommentResponse]])
def post_comments(post_id: int, session: Session = Depends(get_session)):
    """按文章获取已审核评论树。

    公开接口。只返回 status=approved；顶层按时间降序，回复升序嵌套在 replies。

    Args:
        post_id: 文章 ID。
        session: 数据库会话，由依赖注入提供。

    Returns:
        统一结果集。成功时 code=200，data 为顶层评论列表（含 github_user、replies）。
    """
    return comment_service.get_comments_by_post(session, post_id)


@router.get("/admin", response_model=Result[list[CommentAdminResponse]])
def admin_list_comments(
    status: str | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """管理端评论列表。

    需管理员 JWT。只分页顶层评论，每条带 IP 与嵌套 replies。
    须写在 /{comment_id}/... 之前。

    Args:
        status: 顶层状态筛选，可选 pending / approved / rejected。
        page: 页码，从 1 开始。
        size: 每页顶层条数，最大 100。
        session: 数据库会话，由依赖注入提供。
        current_user: JWT payload，用来校验已登录；本接口不用里面的字段。

    Returns:
        统一结果集。成功时 code=200，data 为顶层评论列表（含 ip、replies）。
    """
    return comment_service.list_comments_admin(session, status, page, size)


@router.post("", response_model=Result[CommentResponse])
def create_comment(
    CreateCommentReq: CreateCommentRequest,
    request: Request,
    session: Session = Depends(get_session),
):
    """发表评论或回复。

    须 GitHub JWT。未登录 401；文章不存在或被回复的评论不存在 404。
    默认审核通过。路由只解析 IP 与访客，业务在 service。

    Args:
        CreateCommentReq: 发表请求体，含 post_id、parent_id、content。
        request: 当前请求，用来读 Authorization 与客户端 IP。
        session: 数据库会话，由依赖注入提供。

    Returns:
        统一结果集。成功时 code=200，data 为新建评论（replies 为空）。
    """
    # 获取客户端 IP
    ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    # 如果获取不到，则获取 X-Real-IP
    if not ip:
        ip = request.headers.get("x-real-ip", "")
    # 如果获取不到，则获取客户端主机名
    if not ip:
        ip = request.client.host if request.client else ""
    # 创建评论
    return comment_service.create_comment(
        session, CreateCommentReq, get_github_user_optional(request, session), ip
    )


@router.post("/{comment_id}/like", response_model=Result[CommentResponse])
def like_comment(comment_id: int, session: Session = Depends(get_session)):
    """点赞评论。

    公开接口。评论不存在则 404。likes +1。

    Args:
        comment_id: 评论 ID。
        session: 数据库会话，由依赖注入提供。

    Returns:
        统一结果集。成功时 code=200，data 为评论（含最新 likes）。
    """
    return comment_service.toggle_comment_like(session, comment_id, unlike=False)


@router.post("/{comment_id}/unlike", response_model=Result[CommentResponse])
def unlike_comment(comment_id: int, session: Session = Depends(get_session)):
    """取消点赞评论。

    公开接口。评论不存在则 404。likes -1，最小为 0。

    Args:
        comment_id: 评论 ID。
        session: 数据库会话，由依赖注入提供。

    Returns:
        统一结果集。成功时 code=200，data 为评论（含最新 likes）。
    """
    return comment_service.toggle_comment_like(session, comment_id, unlike=True)


@router.put("/{comment_id}/status", response_model=Result[CommentAdminResponse])
def update_comment_status(
    comment_id: int,
    UpdateCommentStatusReq: UpdateCommentStatusRequest,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """修改评论审核状态。

    需管理员 JWT。status 仅允许 pending / approved / rejected。

    Args:
        comment_id: 评论 ID。
        UpdateCommentStatusReq: 含 status。
        session: 数据库会话，由依赖注入提供。
        current_user: JWT payload，用来校验已登录；本接口不用里面的字段。

    Returns:
        统一结果集。成功时 code=200，data 为评论（含 ip）。
    """
    return comment_service.update_comment_status(
        session, comment_id, UpdateCommentStatusReq
    )


@router.delete("/{comment_id}", response_model=Result)
def delete_comment(
    comment_id: int,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """删除评论。

    需管理员 JWT。会先删子孙再删自身。评论不存在则 404。

    Args:
        comment_id: 评论 ID。
        session: 数据库会话，由依赖注入提供。
        current_user: JWT payload，用来校验已登录；本接口不用里面的字段。

    Returns:
        统一结果集。成功时 code=200，message 为「删除成功」。
    """
    return comment_service.delete_comment(session, comment_id)
