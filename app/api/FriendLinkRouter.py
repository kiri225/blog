from fastapi import Depends
from fastapi.routing import APIRouter
from sqlmodel import Session

from app.Deps import get_current_user, get_session
from app.common.Result import Result
from app.schemas.FriendLinkSchemas import (
    CreateFriendLinkRequest,
    FriendLinkResponse,
    UpdateFriendLinkRequest,
)
from app.service import FriendLinkService as friend_link_service


router = APIRouter(prefix="/api/friend-links", tags=["友链"])


@router.get("/admin", response_model=Result[list[FriendLinkResponse]])
def admin_list_friend_links(
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """管理端友链列表。

    需管理员 JWT。返回全部（含未审核），按 sort 升序。
    须写在裸 GET 与如果以后加 /{id} GET 之前。

    Args:
        session: 数据库会话，由依赖注入提供。
        current_user: JWT payload，用来校验已登录；本接口不用里面的字段。

    Returns:
        统一结果集。成功时 code=200，data 为友链列表。
    """
    return friend_link_service.list_friend_links_admin(session)


@router.get("", response_model=Result[list[FriendLinkResponse]])
def list_friend_links(session: Session = Depends(get_session)):
    """获取已审核友链列表。

    公开接口。只返回 is_approved=true，按 sort 升序。

    Args:
        session: 数据库会话，由依赖注入提供。

    Returns:
        统一结果集。成功时 code=200，data 为友链列表。
    """
    return friend_link_service.list_friend_links(session)


@router.post("", response_model=Result[FriendLinkResponse])
def create_friend_link(
    CreateFriendLinkReq: CreateFriendLinkRequest,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """创建友链。

    需管理员 JWT。默认 is_approved=false，前台看不到，直到 PUT 审核。

    Args:
        CreateFriendLinkReq: 创建友链请求体。
        session: 数据库会话，由依赖注入提供。
        current_user: JWT payload，用来校验已登录；本接口不用里面的字段。

    Returns:
        统一结果集。成功时 code=200，data 为友链。
    """
    return friend_link_service.create_friend_link(session, CreateFriendLinkReq)


@router.put("/{link_id}", response_model=Result[FriendLinkResponse])
def update_friend_link(
    link_id: int,
    UpdateFriendLinkReq: UpdateFriendLinkRequest,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """更新友链。

    需管理员 JWT。全部字段可选，可改 is_approved。友链不存在则 404。

    Args:
        link_id: 友链 ID。
        UpdateFriendLinkReq: 更新友链请求体。
        session: 数据库会话，由依赖注入提供。
        current_user: JWT payload，用来校验已登录；本接口不用里面的字段。

    Returns:
        统一结果集。成功时 code=200，data 为友链。
    """
    return friend_link_service.update_friend_link(
        session, link_id, UpdateFriendLinkReq
    )


@router.delete("/{link_id}", response_model=Result)
def delete_friend_link(
    link_id: int,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """删除友链。

    需管理员 JWT。友链不存在则 404。

    Args:
        link_id: 友链 ID。
        session: 数据库会话，由依赖注入提供。
        current_user: JWT payload，用来校验已登录；本接口不用里面的字段。

    Returns:
        统一结果集。成功时 code=200，message 为「删除成功」。
    """
    return friend_link_service.delete_friend_link(session, link_id)
