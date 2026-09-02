from __future__ import annotations

import json
from datetime import datetime

from pydantic import BaseModel, field_validator


class CreateBookmarkCategoryRequest(BaseModel):
    """创建收藏分类请求体"""

    # 分类名称
    name: str
    # 短图标名
    icon: str = ""
    # 分类描述
    description: str = ""
    # 排序，越小越靠前
    sort: int = 0


class UpdateBookmarkCategoryRequest(BaseModel):
    """更新收藏分类请求体。全部可选。"""

    # 分类名称；不传则不改
    name: str | None = None
    # 短图标名；不传则不改，传 "" 表示清空
    icon: str | None = None
    # 分类描述；不传则不改
    description: str | None = None
    # 排序，越小越靠前；不传则不改
    sort: int | None = None


class CreateBookmarkSiteRequest(BaseModel):
    """创建收藏站点请求体"""

    # 所属收藏分类
    category_id: int
    # 站点名称
    name: str
    # 站点地址
    url: str
    # 图标 URL
    icon: str = ""
    # 站点描述
    description: str = ""
    # 适用平台列表；库内是 JSON 字符串
    platforms: list[str] = []
    # 排序，越小越靠前
    sort: int = 0


class UpdateBookmarkSiteRequest(BaseModel):
    """更新收藏站点请求体。全部可选。"""

    # 所属收藏分类；不传则不改
    category_id: int | None = None
    # 站点名称；不传则不改
    name: str | None = None
    # 站点地址；不传则不改
    url: str | None = None
    # 图标 URL；不传则不改，传 "" 表示清空
    icon: str | None = None
    # 站点描述；不传则不改
    description: str | None = None
    # 适用平台列表；不传则不改，传 [] 表示清空
    platforms: list[str] | None = None
    # 排序，越小越靠前；不传则不改
    sort: int | None = None


class BookmarkSiteResponse(BaseModel):
    """收藏站点响应体。"""

    # 主键
    id: int
    # 所属收藏分类
    category_id: int
    # 站点名称
    name: str
    # 站点地址
    url: str
    # 图标 URL，空则 ""
    icon: str = ""
    # 站点描述，空则 ""
    description: str = ""
    # 适用平台；库内是 JSON 字符串，读出时转成数组
    platforms: list[str] = []
    # 排序
    sort: int = 0
    # 创建时间
    created_at: datetime
    # 更新时间
    updated_at: datetime

    @field_validator("platforms", mode="before")
    @classmethod
    def platforms_from_json(cls, value: object) -> list[str]:
        if isinstance(value, list):
            return [str(item) for item in value]
        if not isinstance(value, str) or not value:
            return []
        try:
            data = json.loads(value)
        except json.JSONDecodeError:
            return []
        return [str(item) for item in data] if isinstance(data, list) else []


class BookmarkCategoryResponse(BaseModel):
    """收藏分类响应体。不含站点。"""

    # 主键
    id: int
    # 分类名称
    name: str
    # 短图标名，空则 ""
    icon: str = ""
    # 分类描述，空则 ""
    description: str = ""
    # 排序
    sort: int = 0
    # 创建时间
    created_at: datetime
    # 更新时间
    updated_at: datetime


class BookmarkFullResponse(BookmarkCategoryResponse):
    """收藏分类嵌套响应体。含该分类下站点。"""

    # 该分类下站点，按 sort 升序
    sites: list[BookmarkSiteResponse] = []
