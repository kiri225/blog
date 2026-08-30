from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class CategoryResponse(BaseModel):
    """分类响应体。"""

    # 主键
    id: int
    # 名称
    name: str
    # URL 别名
    slug: str
    # 描述
    description: str = ""
    # 排序
    sort: int = 0
    # 文章数量
    post_count: int = 0
    # 创建时间
    created_at: datetime
    # 更新时间
    updated_at: datetime


class CreateCategoryRequest(BaseModel):
    """创建分类请求体"""

    # 名称，唯一
    name: str
    # URL 别名，前台路径用，唯一
    slug: str
    # 描述
    description: str = ""
    # 排序，越小越靠前
    sort: int = 0


class UpdateCategoryRequest(BaseModel):
    """更新分类请求体"""

    # 名称，唯一；不传则不改
    name: str | None = None
    # URL 别名，前台路径用，唯一；不传则不改
    slug: str | None = None
    # 描述；不传则不改
    description: str | None = None
    # 排序，越小越靠前；不传则不改
    sort: int | None = None
