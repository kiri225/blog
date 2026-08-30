from __future__ import annotations

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class Category(SQLModel, table=True):
    """文章分类。Post.category_id 指向本表。"""

    # 主键
    id: Optional[int] = Field(default=None, primary_key=True)
    # 分类名称，唯一
    name: str = Field(max_length=50, unique=True)
    # URL 别名，前台路径用，唯一
    slug: str = Field(max_length=50, unique=True)
    # 分类描述
    description: str = Field(default="", max_length=200)
    # 排序，越小越靠前
    sort: int = Field(default=0)
    # 该分类下文章数量（冗余计数，由文章增删改时维护）
    post_count: int = Field(default=0)
    # 创建时间
    created_at: datetime = Field(default_factory=datetime.now)
    # 更新时间
    updated_at: datetime = Field(default_factory=datetime.now)
