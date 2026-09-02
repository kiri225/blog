from __future__ import annotations

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class Chatter(SQLModel, table=True):
    """说说 / 微语。前台只展示 published；images 库内为 JSON 数组字符串。"""

    # 主键，自增
    id: Optional[int] = Field(default=None, primary_key=True)
    # Markdown 正文
    content: str
    # 图片 URL 列表，TEXT 存 JSON 数组字符串，如 '["https://a.png"]'；空为 '[]'
    images: str = Field(default="[]")
    # 心情，最长 20
    mood: str = Field(default="", max_length=20)
    # 点赞数
    likes: int = Field(default=0)
    # 评论数；发表评论 +1，删除评论 -1（最小 0）
    comments_count: int = Field(default=0)
    # 状态：draft / published；前台列表只返回 published
    status: str = Field(default="draft", max_length=20, index=True)
    # 创建时间
    created_at: datetime = Field(default_factory=datetime.now)
    # 更新时间
    updated_at: datetime = Field(default_factory=datetime.now)
