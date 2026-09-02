from __future__ import annotations

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class Message(SQLModel, table=True):
    """全站留言板。须 GitHub 登录发表；parent_id 自引用实现楼中楼，不挂文章。"""

    # 主键，自增
    id: Optional[int] = Field(default=None, primary_key=True)
    # 留言者，对应 github_user.id；用户删了可置空
    github_user_id: Optional[int] = Field(
        default=None, foreign_key="github_user.id", index=True
    )
    # 父留言，顶层为 None；回复时指向被回复那条
    parent_id: Optional[int] = Field(
        default=None, foreign_key="message.id", index=True
    )
    # 留言正文
    content: str
    # 留言者 IP，IPv6 最长 45
    ip: str = Field(default="", max_length=45)
    # 审核状态：pending / approved / rejected；前台只展示 approved
    status: str = Field(default="approved", max_length=20, index=True)
    # 点赞数
    likes: int = Field(default=0)
    # 创建时间
    created_at: datetime = Field(default_factory=datetime.now)
