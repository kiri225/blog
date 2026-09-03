from __future__ import annotations

from datetime import datetime
from typing import Optional
from sqlalchemy import Index
from sqlmodel import SQLModel, Field


class Message(SQLModel, table=True):
    """全站留言板。须 GitHub 登录发表；parent_id 自引用实现楼中楼，不挂文章。"""

    # 主键，自增
    id: Optional[int] = Field(default=None, primary_key=True)
    # 留言者，对应 github_user.id；用户删了可置空
    github_user_id: Optional[int] = Field(
        default=None, foreign_key="github_user.id"
    )
    # 父留言，顶层为 None；回复时指向被回复那条
    parent_id: Optional[int] = Field(
        default=None, foreign_key="message.id"
    )
    # 留言正文
    content: str
    # 留言者 IP，IPv6 最长 45
    ip: str = Field(default="", max_length=45)
    # 审核状态：pending / approved / rejected；前台只展示 approved
    status: str = Field(default="approved", max_length=20)
    # 点赞数
    likes: int = Field(default=0)
    # 创建时间
    created_at: datetime = Field(default_factory=datetime.now)

    __table_args__ = (
        # 前台/后台顶层列表与 BFS：WHERE parent_id ... AND status=? ORDER BY created_at DESC
        Index("idx_message_parent_status_created", "parent_id", "status", "created_at"),
        Index("idx_message_github_user", "github_user_id"),
    )
