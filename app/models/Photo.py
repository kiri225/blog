from __future__ import annotations

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class Photo(SQLModel, table=True):
    """相册照片。url 来自上传接口；orientation 为 landscape / portrait。"""

    # 主键，自增
    id: Optional[int] = Field(default=None, primary_key=True)
    # 所属相册
    album_id: int = Field(foreign_key="album.id", index=True)
    # 图片 URL（上传接口返回的 url）
    url: str
    # 说明
    caption: str = Field(default="", max_length=500)
    # 方向：landscape 横图 / portrait 竖图
    orientation: str = Field(default="landscape", max_length=20)
    # 排序，越小越靠前
    sort: int = Field(default=0)
    # 创建时间
    created_at: datetime = Field(default_factory=datetime.now)
