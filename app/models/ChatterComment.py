from __future__ import annotations

from datetime import datetime
from typing import Optional
from sqlalchemy import Index
from sqlmodel import SQLModel, Field


class ChatterComment(SQLModel, table=True):
    """说说评论。须 GitHub 登录发表；parent_id 自引用实现楼中楼。"""

    # 类名 ChatterComment 小写是 chattercomment，与库表 chatter_comment 不一致，必须显式指定
    __tablename__ = "chatter_comment"  # pyright: ignore[reportAssignmentType]

    # 主键，自增
    id: Optional[int] = Field(default=None, primary_key=True)
    # 所属说说；说说删除时级联删评论
    chatter_id: int = Field(foreign_key="chatter.id")
    # 父评论，顶层为 None；回复时指向被回复那条
    parent_id: Optional[int] = Field(default=None, foreign_key="chatter_comment.id")
    # 评论者，对应 github_user.id；用户删了可置空
    github_user_id: Optional[int] = Field(
        default=None, foreign_key="github_user.id"
    )
    # 评论正文
    content: str
    # 点赞数
    likes: int = Field(default=0)
    # 评论者 IP，IPv6 最长 45
    ip: str = Field(default="", max_length=45)
    # 审核状态：pending / approved / rejected；前台只展示 approved
    status: str = Field(default="approved", max_length=20)
    # 创建时间
    created_at: datetime = Field(default_factory=datetime.now)

    __table_args__ = (
        # 前台：WHERE chatter_id=? AND status='approved'
        Index("idx_chatter_comment_chatter_status", "chatter_id", "status"),
        # 管理端顶层列表 / BFS 拉回复
        Index(
            "idx_chatter_comment_parent_status_created",
            "parent_id",
            "status",
            "created_at",
        ),
        Index("idx_chatter_comment_github_user", "github_user_id"),
    )
