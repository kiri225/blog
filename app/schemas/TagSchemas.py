from __future__ import annotations

from pydantic import BaseModel


class TagResponse(BaseModel):
    """标签响应体。"""

    # 主键
    id: int
    # 名称
    name: str
    # URL 别名
    slug: str
    # 文章数量
    post_count: int = 0


class CreateTagRequest(BaseModel):
    """创建标签请求体"""

    # 名称，唯一
    name: str
    # URL 别名，唯一
    slug: str


class UpdateTagRequest(BaseModel):
    """更新标签请求体"""

    # 名称，唯一；不传则不改
    name: str | None = None
    # URL 别名，唯一；不传则不改
    slug: str | None = None
