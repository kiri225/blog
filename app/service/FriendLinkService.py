from datetime import datetime

from fastapi import HTTPException
from sqlmodel import Session, select

from app.common.Result import Result
from app.models.FriendLink import FriendLink
from app.schemas.FriendLinkSchemas import (
    CreateFriendLinkRequest,
    UpdateFriendLinkRequest,
)


def list_friend_links(session: Session) -> Result:
    """前台友链列表：仅已审核，按 sort 升序。

    Args:
        session: 数据库会话，由路由传入。

    Returns:
        统一结果集。成功时 code=200，data 为友链列表。
    """
    # 1.只取已审核，按 sort 升序
    friend_links_data = list(
        session.exec(
            select(FriendLink)
            .where(FriendLink.is_approved.is_(True))
            .order_by(FriendLink.sort)
        ).all()
    )

    # 2.统一结果集返回
    return Result.success(friend_links_data)


def list_friend_links_admin(session: Session) -> Result:
    """管理端友链列表：全部，按 sort 升序。

    Args:
        session: 数据库会话，由路由传入。

    Returns:
        统一结果集。成功时 code=200，data 为友链列表。
    """
    # 1.按 sort 升序查询全部
    friend_links_admin_data = list(session.exec(select(FriendLink).order_by(FriendLink.sort)).all())

    # 2.统一结果集返回
    return Result.success(friend_links_admin_data)


def create_friend_link(
    session: Session, CreateFriendLinkReq: CreateFriendLinkRequest
) -> Result:
    """管理员创建友链。默认未审核。

    Args:
        session: 数据库会话，由路由传入。
        CreateFriendLinkReq: 创建友链请求体。

    Returns:
        统一结果集。成功时 code=200，data 为友链。
    """
    # 1.落库（is_approved 固定 False，Create 不含该字段）
    link = FriendLink(
        name=CreateFriendLinkReq.name,
        url=CreateFriendLinkReq.url,
        avatar=CreateFriendLinkReq.avatar or "",
        description=CreateFriendLinkReq.description or "",
        sort=CreateFriendLinkReq.sort,
        is_approved=False,
    )
    session.add(link)
    session.commit()
    session.refresh(link)

    # 2.统一结果集返回
    return Result.success(link)


def update_friend_link(
    session: Session,
    link_id: int,
    UpdateFriendLinkReq: UpdateFriendLinkRequest,
) -> Result:
    """管理员更新友链。只改传入字段，可改 is_approved。

    Args:
        session: 数据库会话，由路由传入。
        link_id: 友链 ID。
        UpdateFriendLinkReq: 更新友链请求体。

    Returns:
        统一结果集。成功时 code=200，data 为友链。
    """
    # 1.友链必须存在
    link = session.get(FriendLink, link_id)
    if not link:
        raise HTTPException(status_code=404, detail="友链不存在")

    # 2.按传入字段更新
    if UpdateFriendLinkReq.name is not None:
        link.name = UpdateFriendLinkReq.name
    if UpdateFriendLinkReq.url is not None:
        link.url = UpdateFriendLinkReq.url
    if UpdateFriendLinkReq.avatar is not None:
        link.avatar = UpdateFriendLinkReq.avatar
    if UpdateFriendLinkReq.description is not None:
        link.description = UpdateFriendLinkReq.description
    if UpdateFriendLinkReq.sort is not None:
        link.sort = UpdateFriendLinkReq.sort
    if UpdateFriendLinkReq.is_approved is not None:
        link.is_approved = UpdateFriendLinkReq.is_approved
    link.updated_at = datetime.now()

    # 3.落库
    session.add(link)
    session.commit()
    session.refresh(link)

    # 4.统一结果集返回
    return Result.success(link)


def delete_friend_link(session: Session, link_id: int) -> Result:
    """管理员删除友链。

    Args:
        session: 数据库会话，由路由传入。
        link_id: 友链 ID。

    Returns:
        统一结果集。成功时 code=200，message 为「删除成功」。
    """
    # 1.友链必须存在
    link = session.get(FriendLink, link_id)
    if not link:
        raise HTTPException(status_code=404, detail="友链不存在")

    # 2.删除并落库
    session.delete(link)
    session.commit()

    # 3.统一结果集返回
    return Result.success(message="删除成功")
