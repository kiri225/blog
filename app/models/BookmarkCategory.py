from __future__ import annotations

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class BookmarkCategory(SQLModel, table=True):
    """收藏夹分类。BookmarkSite.category_id 指向本表。"""

    # 类名 BookmarkCategory 小写是 bookmarkcategory，与库表 bookmark_category 不一致
    __tablename__ = "bookmark_category"  # pyright: ignore[reportAssignmentType]

    # 主键，自增
    id: Optional[int] = Field(default=None, primary_key=True)
    # 分类名称
    name: str = Field(max_length=50)
    # 短图标名，最长 50
    icon: str = Field(default="", max_length=50)
    # 分类描述
    description: str = Field(default="", max_length=200)
    # 排序，越小越靠前
    sort: int = Field(default=0)
    # 创建时间
    created_at: datetime = Field(default_factory=datetime.now)
    # 更新时间
    updated_at: datetime = Field(default_factory=datetime.now)
