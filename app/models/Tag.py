from __future__ import annotations

from typing import Optional
from sqlmodel import SQLModel, Field


class Tag(SQLModel, table=True):
    """文章标签。与 Post 通过 PostTag 多对多。"""

    # 主键
    id: Optional[int] = Field(default=None, primary_key=True)
    # 标签名称，唯一
    name: str = Field(max_length=50, unique=True)
    # URL 别名，唯一
    slug: str = Field(max_length=50, unique=True)
    # 使用该标签的文章数量（冗余计数）
    post_count: int = Field(default=0)
