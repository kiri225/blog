from fastapi import Depends, Query
from fastapi.requests import Request
from fastapi.routing import APIRouter
from sqlmodel import Session

from app.Deps import get_current_user, get_github_user_optional, get_session
from app.common.Result import Result
from app.schemas.ChatterSchemas import (
    ChatterCommentAdminResponse,
    ChatterCommentResponse,
    ChatterCountResponse,
    ChatterLikeResponse,
    ChatterResponse,
    CreateChatterCommentRequest,
    CreateChatterRequest,
    UpdateChatterCommentStatusRequest,
    UpdateChatterRequest,
)
from app.service import ChatterService as chatter_service


router = APIRouter(prefix="/api/chatters", tags=["说说模块"])


@router.get("", response_model=Result[list[ChatterResponse]])
def list_chatters(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    session: Session = Depends(get_session),
):
    """获取说说列表。

    公开接口。只返回 published，按 created_at 降序分页。

    Args:
        page: 页码，从 1 开始。
        size: 每页条数，最大 200。
        session: 数据库会话，由依赖注入提供。

    Returns:
        统一结果集。成功时 code=200，data 为说说列表。
    """
    return chatter_service.get_chatters(session, "published", page, size)


@router.get("/count", response_model=Result[ChatterCountResponse])
def get_chatter_count(
    status: str = "published",
    session: Session = Depends(get_session),
):
    """获取说说数量。

    公开接口。status 默认 published。须写在 /{chatter_id} 之前。

    Args:
        status: 说说状态，可选 draft / published；默认 published。
        session: 数据库会话，由依赖注入提供。

    Returns:
        统一结果集。成功时 code=200，data 含 count。
    """
    return chatter_service.get_chatter_count(session, status)


@router.get("/admin", response_model=Result[list[ChatterResponse]])
def admin_list_chatters(
    status: str | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """管理端说说列表。

    需管理员 JWT。可按 status 筛选（含草稿），分页返回。
    须写在裸 /{chatter_id} 之前。

    Args:
        status: 说说状态，可选 draft / published；不传则全部。
        page: 页码，从 1 开始。
        size: 每页条数，最大 200。
        session: 数据库会话，由依赖注入提供。
        current_user: JWT payload，用来校验已登录；本接口不用里面的字段。

    Returns:
        统一结果集。成功时 code=200，data 为说说列表。
    """
    return chatter_service.get_chatters(session, status, page, size)


@router.post("", response_model=Result[ChatterResponse])
def create_chatter(
    CreateChatterReq: CreateChatterRequest,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """管理员发表说说。

    需管理员 JWT。status 仅允许 draft / published，默认 draft。

    Args:
        CreateChatterReq: 创建说说请求体。
        session: 数据库会话，由依赖注入提供。
        current_user: JWT payload，用来校验已登录；本接口不用里面的字段。

    Returns:
        统一结果集。成功时 code=200，data 为说说。
    """
    return chatter_service.create_chatter(session, CreateChatterReq)


@router.get(
    "/comments/admin",
    response_model=Result[list[ChatterCommentAdminResponse]],
)
def admin_list_chatter_comments(
    status: str | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """管理端说说评论列表。

    需管理员 JWT。只分页顶层评论，每条带 IP 与嵌套 replies。
    须写在裸 /{chatter_id} 与 /comments/{comment_id}/... 之前。

    Args:
        status: 顶层状态筛选，可选 pending / approved / rejected。
        page: 页码，从 1 开始。
        size: 每页顶层条数，最大 100。
        session: 数据库会话，由依赖注入提供。
        current_user: JWT payload，用来校验已登录；本接口不用里面的字段。

    Returns:
        统一结果集。成功时 code=200，data 为顶层评论列表（含 ip、replies）。
    """
    return chatter_service.list_chatter_comments_admin(session, status, page, size)


@router.put(
    "/comments/{comment_id}/status",
    response_model=Result[ChatterCommentAdminResponse],
)
def update_chatter_comment_status(
    comment_id: int,
    UpdateChatterCommentStatusReq: UpdateChatterCommentStatusRequest,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """修改说说评论审核状态。

    需管理员 JWT。status 仅允许 pending / approved / rejected。

    Args:
        comment_id: 说说评论 ID。
        UpdateChatterCommentStatusReq: 含 status。
        session: 数据库会话，由依赖注入提供。
        current_user: JWT payload，用来校验已登录；本接口不用里面的字段。

    Returns:
        统一结果集。成功时 code=200，data 为评论（含 ip）。
    """
    return chatter_service.update_chatter_comment_status(
        session, comment_id, UpdateChatterCommentStatusReq
    )


@router.delete("/comments/{comment_id}", response_model=Result)
def delete_chatter_comment(
    comment_id: int,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """删除说说评论。

    需管理员 JWT。会先删子孙再删自身，并回减说说 comments_count。
    评论不存在则 404。

    Args:
        comment_id: 说说评论 ID。
        session: 数据库会话，由依赖注入提供。
        current_user: JWT payload，用来校验已登录；本接口不用里面的字段。

    Returns:
        统一结果集。成功时 code=200，message 为「删除成功」。
    """
    return chatter_service.delete_chatter_comment(session, comment_id)


@router.post("/comments", response_model=Result[ChatterCommentResponse])
def create_chatter_comment(
    CreateChatterCommentReq: CreateChatterCommentRequest,
    request: Request,
    session: Session = Depends(get_session),
):
    """发表说说评论或回复。

    须 GitHub JWT。未登录 401；说说不存在或被回复的评论不存在 404。
    默认审核通过。路由只解析 IP 与访客，业务在 service。
    须写在裸 /{chatter_id} 之前。

    Args:
        CreateChatterCommentReq: 发表请求体，含 chatter_id、parent_id、content。
        request: 当前请求，用来读 Authorization 与客户端 IP。
        session: 数据库会话，由依赖注入提供。

    Returns:
        统一结果集。成功时 code=200，data 为新建评论（replies 为空）。
    """
    ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    if not ip:
        ip = request.headers.get("x-real-ip", "")
    if not ip:
        ip = request.client.host if request.client else ""
    return chatter_service.create_chatter_comment(
        session,
        CreateChatterCommentReq,
        get_github_user_optional(request, session),
        ip,
    )


@router.post(
    "/comments/{comment_id}/like",
    response_model=Result[ChatterCommentResponse],
)
def like_chatter_comment(comment_id: int, session: Session = Depends(get_session)):
    """点赞说说评论。

    公开接口。评论不存在则 404。likes +1。须写在裸 /{chatter_id} 之前。

    Args:
        comment_id: 说说评论 ID。
        session: 数据库会话，由依赖注入提供。

    Returns:
        统一结果集。成功时 code=200，data 为评论（含最新 likes）。
    """
    return chatter_service.toggle_chatter_comment_like(
        session, comment_id, unlike=False
    )


@router.post(
    "/comments/{comment_id}/unlike",
    response_model=Result[ChatterCommentResponse],
)
def unlike_chatter_comment(
    comment_id: int, session: Session = Depends(get_session)
):
    """取消点赞说说评论。

    公开接口。评论不存在则 404。likes -1，最小为 0。须写在裸 /{chatter_id} 之前。

    Args:
        comment_id: 说说评论 ID。
        session: 数据库会话，由依赖注入提供。

    Returns:
        统一结果集。成功时 code=200，data 为评论（含最新 likes）。
    """
    return chatter_service.toggle_chatter_comment_like(
        session, comment_id, unlike=True
    )


@router.get(
    "/{chatter_id}/comments",
    response_model=Result[list[ChatterCommentResponse]],
)
def get_chatter_comments(
    chatter_id: int, session: Session = Depends(get_session)
):
    """按说说获取已审核评论树。

    公开接口。只返回 status=approved；顶层按时间降序，回复升序嵌套在 replies。
    说说不存在或无已审核评论时 data 为 []。须写在裸 /{chatter_id} 之前。

    Args:
        chatter_id: 说说 ID。
        session: 数据库会话，由依赖注入提供。

    Returns:
        统一结果集。成功时 code=200，data 为顶层评论列表（含 github_user、replies）。
    """
    return chatter_service.get_chatter_comments(session, chatter_id)


@router.get("/{chatter_id}", response_model=Result[ChatterResponse])
def get_chatter(chatter_id: int, session: Session = Depends(get_session)):
    """按 ID 获取说说详情。

    公开接口。不存在则 404。含草稿。须写在 /admin、/comments 相关静态路径之后。

    Args:
        chatter_id: 说说 ID。
        session: 数据库会话，由依赖注入提供。

    Returns:
        统一结果集。成功时 code=200，data 为说说。
    """
    return chatter_service.get_chatter_by_id(session, chatter_id)


@router.post("/{chatter_id}/like", response_model=Result[ChatterLikeResponse])
def like_chatter(chatter_id: int, session: Session = Depends(get_session)):
    """点赞说说。

    公开接口。说说不存在则 404。likes +1。

    Args:
        chatter_id: 说说 ID。
        session: 数据库会话，由依赖注入提供。

    Returns:
        统一结果集。成功时 code=200，data 含 likes。
    """
    return chatter_service.toggle_chatter_like(session, chatter_id, unlike=False)


@router.post("/{chatter_id}/unlike", response_model=Result[ChatterLikeResponse])
def unlike_chatter(chatter_id: int, session: Session = Depends(get_session)):
    """取消点赞说说。

    公开接口。说说不存在则 404。likes -1，最小为 0。

    Args:
        chatter_id: 说说 ID。
        session: 数据库会话，由依赖注入提供。

    Returns:
        统一结果集。成功时 code=200，data 含 likes。
    """
    return chatter_service.toggle_chatter_like(session, chatter_id, unlike=True)


@router.put("/{chatter_id}", response_model=Result[ChatterResponse])
def update_chatter(
    chatter_id: int,
    UpdateChatterReq: UpdateChatterRequest,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """更新说说。

    需管理员 JWT。全部字段可选。说说不存在则 404。
    status 仅允许 draft / published。

    Args:
        chatter_id: 说说 ID。
        UpdateChatterReq: 更新说说请求体。
        session: 数据库会话，由依赖注入提供。
        current_user: JWT payload，用来校验已登录；本接口不用里面的字段。

    Returns:
        统一结果集。成功时 code=200，data 为说说。
    """
    return chatter_service.update_chatter(session, chatter_id, UpdateChatterReq)


@router.delete("/{chatter_id}", response_model=Result)
def delete_chatter(
    chatter_id: int,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """删除说说。

    需管理员 JWT。会先删该说说下全部评论再删自身。说说不存在则 404。

    Args:
        chatter_id: 说说 ID。
        session: 数据库会话，由依赖注入提供。
        current_user: JWT payload，用来校验已登录；本接口不用里面的字段。

    Returns:
        统一结果集。成功时 code=200，message 为「删除成功」。
    """
    return chatter_service.delete_chatter(session, chatter_id)
