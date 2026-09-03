from __future__ import annotations

from datetime import datetime
from typing import Optional
from sqlalchemy import Index
from sqlmodel import SQLModel, Field


class Post(SQLModel, table=True):
    """文章。可选归属一个分类；标签走 PostTag，不在本表存。"""

    # 主键
    id: Optional[int] = Field(default=None, primary_key=True)
    # 标题
    title: str = Field(max_length=200)
    # URL 别名，前台按此访问，唯一（UNIQUE 自带索引，不再额外 index=True）
    slug: str = Field(max_length=200, unique=True)
    # 摘要
    description: str = Field(default="", max_length=500)
    # 正文
    content: str = Field(default="")
    # 封面图 URL
    cover: str = Field(default="", max_length=500)
    # 所属分类；分类删除时置空，不级联删文章
    category_id: Optional[int] = Field(default=None, foreign_key="category.id")
    # 状态：draft / published / archived
    status: str = Field(default="draft", max_length=20)
    # 是否置顶
    is_pinned: bool = Field(default=False)
    # 浏览量
    views: int = Field(default=0)
    # 点赞数
    likes: int = Field(default=0)
    # 字数
    word_count: int = Field(default=0)
    # 预计阅读分钟数
    reading_time: int = Field(default=0)
    # 首次发布为 published 时写入；草稿为 None
    published_at: Optional[datetime] = Field(default=None)
    # 创建时间
    created_at: datetime = Field(default_factory=datetime.now)
    # 更新时间
    updated_at: datetime = Field(default_factory=datetime.now)

    __table_args__ = (
        # 列表：WHERE status=? ORDER BY is_pinned DESC, created_at DESC
        Index("idx_post_list", "status", "is_pinned", "created_at"),
        # 按分类筛 / 重算 post_count
        Index("idx_post_category", "category_id"),
        # 仪表盘近 30 天：WHERE status=published AND published_at >= ?
        Index("idx_post_published", "status", "published_at"),
    )
