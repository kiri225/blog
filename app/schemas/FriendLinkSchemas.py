from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class CreateFriendLinkRequest(BaseModel):
    """创建友链请求体。不含 is_approved，新建默认未审核。"""

    # 站点名称
    name: str
    # 站点 URL
    url: str
    # 头像 / 站点图标 URL
    avatar: str = ""
    # 描述
    description: str = ""
    # 排序，越小越靠前
    sort: int = 0


class UpdateFriendLinkRequest(BaseModel):
    """更新友链请求体。全部可选。"""

    # 站点名称；不传则不改
    name: str | None = None
    # 站点 URL；不传则不改
    url: str | None = None
    # 头像 / 站点图标 URL；不传则不改，传 "" 表示清空
    avatar: str | None = None
    # 描述；不传则不改
    description: str | None = None
    # 排序，越小越靠前；不传则不改
    sort: int | None = None
    # 是否已审核；不传则不改
    is_approved: bool | None = None


class FriendLinkResponse(BaseModel):
    """友链响应体。"""

    # 主键
    id: int
    # 站点名称
    name: str
    # 站点 URL
    url: str
    # 头像 / 站点图标 URL，空则 ""
    avatar: str = ""
    # 描述，空则 ""
    description: str = ""
    # 排序
    sort: int = 0
    # 是否已审核；前台列表恒为 true
    is_approved: bool
    # 创建时间
    created_at: datetime
    # 更新时间
    updated_at: datetime
