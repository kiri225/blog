from __future__ import annotations

from datetime import datetime
from typing import Optional
from sqlalchemy import Index
from sqlmodel import SQLModel, Field


class FriendLink(SQLModel, table=True):
    """友链。前台只展示 is_approved=true；新建默认未审核。"""

    # 类名 FriendLink 小写是 friendlink，与库表 friend_link 不一致，必须显式指定
    __tablename__ = "friend_link"  # pyright: ignore[reportAssignmentType]

    # 主键，自增
    id: Optional[int] = Field(default=None, primary_key=True)
    # 站点名称
    name: str = Field(max_length=100)
    # 站点 URL
    url: str = Field(max_length=500)
    # 头像 / 站点图标 URL
    avatar: str = Field(default="")
    # 描述
    description: str = Field(default="", max_length=500)
    # 排序，越小越靠前
    sort: int = Field(default=0)
    # 是否已审核；前台列表只返回 True
    is_approved: bool = Field(default=False)
    # 创建时间
    created_at: datetime = Field(default_factory=datetime.now)
    # 更新时间
    updated_at: datetime = Field(default_factory=datetime.now)

    __table_args__ = (
        # 前台：WHERE is_approved=true ORDER BY sort
        Index("idx_friend_link_approved_sort", "is_approved", "sort"),
    )
