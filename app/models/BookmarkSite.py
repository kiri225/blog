from __future__ import annotations

from datetime import datetime
from typing import Optional
from sqlalchemy import Index
from sqlmodel import SQLModel, Field


class BookmarkSite(SQLModel, table=True):
    """收藏站点。platforms 库内为 JSON 数组字符串。"""

    # 类名 BookmarkSite 小写是 bookmarksite，与库表 bookmark_site 不一致
    __tablename__ = "bookmark_site"  # pyright: ignore[reportAssignmentType]

    # 主键，自增
    id: Optional[int] = Field(default=None, primary_key=True)
    # 所属收藏分类；分类删除时级联删站点
    category_id: int = Field(foreign_key="bookmark_category.id")
    # 站点名称
    name: str = Field(max_length=100)
    # 站点地址
    url: str = Field(max_length=300)
    # 图标 URL，最长 500
    icon: str = Field(default="", max_length=500)
    # 站点描述
    description: str = Field(default="", max_length=300)
    # 适用平台，TEXT 存 JSON 数组字符串，如 '["web","ios"]'；空为 '[]'
    platforms: str = Field(default="[]")
    # 排序，越小越靠前
    sort: int = Field(default=0)
    # 创建时间
    created_at: datetime = Field(default_factory=datetime.now)
    # 更新时间
    updated_at: datetime = Field(default_factory=datetime.now)

    __table_args__ = (
        # WHERE category_id=? ORDER BY sort
        Index("idx_bookmark_site_category_sort", "category_id", "sort"),
    )
