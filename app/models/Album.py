from __future__ import annotations

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class Album(SQLModel, table=True):
    """相册。Photo.album_id 指向本表；photo_count 由照片增删维护。"""

    # 主键，自增
    id: Optional[int] = Field(default=None, primary_key=True)
    # 标题
    title: str = Field(max_length=100)
    # 描述
    description: str = Field(default="", max_length=500)
    # 封面图 URL，空则 ""
    cover: str = Field(default="")
    # 照片数量；加照片 +1，删照片 -1（最小 0）
    photo_count: int = Field(default=0)
    # 排序，越小越靠前
    sort: int = Field(default=0)
    # 创建时间
    created_at: datetime = Field(default_factory=datetime.now)
    # 更新时间
    updated_at: datetime = Field(default_factory=datetime.now)
