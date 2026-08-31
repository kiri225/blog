from __future__ import annotations

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class GitHubUser(SQLModel, table=True):
    """GitHub 访客账号。前台评论者，与管理员 User 分开。"""

    # 类名 GitHubUser 小写是 githubuser，与库表 github_user 不一致，必须显式指定
    __tablename__ = "github_user"  # pyright: ignore[reportAssignmentType]

    # 主键，自增；JWT 的 sub 用这个，不是 github_id
    id: Optional[int] = Field(default=None, primary_key=True)
    # GitHub 数字 id，唯一
    github_id: int = Field(unique=True, index=True)
    # GitHub 用户名
    login: str = Field(max_length=100)
    # 头像 URL
    avatar: str = Field(default="", max_length=500)
    # 简介
    bio: str = Field(default="", max_length=500)
    # 创建时间
    created_at: datetime = Field(default_factory=datetime.now)
