from fastapi import Depends, Query
from fastapi.requests import Request
from fastapi.routing import APIRouter
from sqlmodel import Session

from app.Deps import get_current_user, get_github_user_optional, get_session
from app.common.Result import Result
from app.schemas.MessageSchemas import (
    CreateMessageRequest,
    MessageCountResponse,
    MessageResponse,
    UpdateMessageStatusRequest,
)
from app.service import MessageService as message_service


router = APIRouter(prefix="/api/messages", tags=["留言板"])


@router.get("/count", response_model=Result[MessageCountResponse])
def messages_count(session: Session = Depends(get_session)):
    """已审核顶层留言数量。

    公开接口。须写在 /{msg_id}/... 之前。

    Args:
        session: 数据库会话，由依赖注入提供。

    Returns:
        统一结果集。成功时 code=200，data 含 count。
    """
    return message_service.count_messages(session)


@router.get("/admin/count", response_model=Result[MessageCountResponse])
def admin_messages_count(
    status: str | None = None,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """管理端顶层留言数量。

    需管理员 JWT。可选按 status 筛选。须写在 /{msg_id}/... 之前。

    Args:
        status: 顶层状态筛选，可选 pending / approved / rejected。
        session: 数据库会话，由依赖注入提供。
        current_user: JWT payload，用来校验已登录；本接口不用里面的字段。

    Returns:
        统一结果集。成功时 code=200，data 含 count。
    """
    return message_service.count_messages_admin(session, status)


@router.get("/admin", response_model=Result[list[MessageResponse]])
def admin_list_messages(
    status: str | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """管理端留言列表。

    需管理员 JWT。只分页顶层留言，每条带 IP 与嵌套 replies。
    须写在 /{msg_id}/... 之前。

    Args:
        status: 顶层状态筛选，可选 pending / approved / rejected。
        page: 页码，从 1 开始。
        size: 每页顶层条数，最大 100。
        session: 数据库会话，由依赖注入提供。
        current_user: JWT payload，用来校验已登录；本接口不用里面的字段。

    Returns:
        统一结果集。成功时 code=200，data 为顶层留言列表（含 ip、replies）。
    """
    return message_service.list_messages_admin(session, status, page, size)


@router.get("", response_model=Result[list[MessageResponse]])
def list_messages(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
):
    """留言板列表。

    公开接口。只返回已审核顶层并分页，每条带嵌套 replies。

    Args:
        page: 页码，从 1 开始。
        size: 每页顶层条数，最大 100。
        session: 数据库会话，由依赖注入提供。

    Returns:
        统一结果集。成功时 code=200，data 为顶层留言列表。
    """
    return message_service.list_messages(session, page, size)


@router.post("", response_model=Result[MessageResponse])
def create_message(
    CreateMessageReq: CreateMessageRequest,
    request: Request,
    session: Session = Depends(get_session),
):
    """发表留言或回复。

    须 GitHub JWT。未登录 401；被回复的留言不存在 404。默认审核通过。

    Args:
        CreateMessageReq: 含 content、parent_id。
        request: 当前请求，用来读 Authorization 与客户端 IP。
        session: 数据库会话，由依赖注入提供。

    Returns:
        统一结果集。成功时 code=200，data 为新建留言（replies 为空）。
    """
    ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    if not ip:
        ip = request.headers.get("x-real-ip", "")
    if not ip:
        ip = request.client.host if request.client else ""
    return message_service.create_message(
        session, CreateMessageReq, get_github_user_optional(request, session), ip
    )


@router.post("/{msg_id}/like", response_model=Result[MessageResponse])
def like_message(msg_id: int, session: Session = Depends(get_session)):
    """点赞留言。

    公开接口。留言不存在则 404。likes +1。

    Args:
        msg_id: 留言 ID。
        session: 数据库会话，由依赖注入提供。

    Returns:
        统一结果集。成功时 code=200，data 为留言（含最新 likes）。
    """
    return message_service.toggle_message_like(session, msg_id, unlike=False)


@router.post("/{msg_id}/unlike", response_model=Result[MessageResponse])
def unlike_message(msg_id: int, session: Session = Depends(get_session)):
    """取消点赞留言。

    公开接口。留言不存在则 404。likes -1，最小为 0。

    Args:
        msg_id: 留言 ID。
        session: 数据库会话，由依赖注入提供。

    Returns:
        统一结果集。成功时 code=200，data 为留言（含最新 likes）。
    """
    return message_service.toggle_message_like(session, msg_id, unlike=True)


@router.put("/{msg_id}/status", response_model=Result[MessageResponse])
def update_message_status(
    msg_id: int,
    UpdateMessageStatusReq: UpdateMessageStatusRequest,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """修改留言审核状态。

    需管理员 JWT。status 仅允许 pending / approved / rejected。

    Args:
        msg_id: 留言 ID。
        UpdateMessageStatusReq: 含 status。
        session: 数据库会话，由依赖注入提供。
        current_user: JWT payload，用来校验已登录；本接口不用里面的字段。

    Returns:
        统一结果集。成功时 code=200，data 为留言（含 ip）。
    """
    return message_service.update_message_status(
        session, msg_id, UpdateMessageStatusReq
    )


@router.delete("/{msg_id}", response_model=Result)
def delete_message(
    msg_id: int,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """删除留言。

    需管理员 JWT。会先删子孙再删自身。留言不存在则 404。

    Args:
        msg_id: 留言 ID。
        session: 数据库会话，由依赖注入提供。
        current_user: JWT payload，用来校验已登录；本接口不用里面的字段。

    Returns:
        统一结果集。成功时 code=200，message 为「删除成功」。
    """
    return message_service.delete_message(session, msg_id)
