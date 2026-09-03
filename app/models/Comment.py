from __future__ import annotations

from datetime import datetime
from typing import Optional
from sqlalchemy import Index
from sqlmodel import SQLModel, Field


class Comment(SQLModel, table=True):
    """文章评论。须 GitHub 登录发表；parent_id 自引用实现楼中楼。"""

    # 主键，自增
    id: Optional[int] = Field(default=None, primary_key=True)
    # 所属文章；文章删除时级联删评论
    post_id: int = Field(foreign_key="post.id")
    # 父评论，顶层为 None；回复时指向被回复那条
    parent_id: Optional[int] = Field(default=None, foreign_key="comment.id")
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
        # 前台：WHERE post_id=? AND status='approved'
        Index("idx_comment_post_status", "post_id", "status"),
        # 管理端顶层列表 / BFS 拉回复：WHERE parent_id ... AND status=? ORDER BY created_at
        Index("idx_comment_parent_status_created", "parent_id", "status", "created_at"),
        Index("idx_comment_github_user", "github_user_id"),
    )
