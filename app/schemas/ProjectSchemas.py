from __future__ import annotations

import json
from datetime import datetime

from pydantic import BaseModel, field_validator


class CreateProjectRequest(BaseModel):
    """创建项目请求体"""

    # 名称
    name: str
    # URL 别名，全站唯一
    slug: str
    # 短描述
    description: str = ""
    # 长描述，Markdown
    long_description: str = ""
    # 封面图 URL
    cover_image: str = ""
    # 技术栈名称列表；库内是 JSON 字符串
    tech_stack: list[str] = []
    # GitHub 仓库地址
    link_github: str = ""
    # Gitee 仓库地址
    link_gitee: str = ""
    # 线上地址
    link_live: str = ""
    # 文档地址
    link_docs: str = ""
    # 状态：developing / active / archived
    status: str = "developing"
    # 状态展示文案，如「维护中」
    status_label: str = ""
    # 是否精选
    is_featured: bool = False
    # 排序，越小越靠前
    sort: int = 0


class UpdateProjectRequest(BaseModel):
    """更新项目请求体。全部可选。"""

    # 名称；不传则不改
    name: str | None = None
    # URL 别名，全站唯一；不传则不改
    slug: str | None = None
    # 短描述；不传则不改
    description: str | None = None
    # 长描述，Markdown；不传则不改
    long_description: str | None = None
    # 封面图 URL；不传则不改，传 "" 表示清空
    cover_image: str | None = None
    # 技术栈名称列表；不传则不改，传 [] 表示清空
    tech_stack: list[str] | None = None
    # GitHub 仓库地址；不传则不改
    link_github: str | None = None
    # Gitee 仓库地址；不传则不改
    link_gitee: str | None = None
    # 线上地址；不传则不改
    link_live: str | None = None
    # 文档地址；不传则不改
    link_docs: str | None = None
    # 状态：developing / active / archived；不传则不改
    status: str | None = None
    # 状态展示文案；不传则不改
    status_label: str | None = None
    # 是否精选；不传则不改
    is_featured: bool | None = None
    # 排序，越小越靠前；不传则不改
    sort: int | None = None


class ProjectResponse(BaseModel):
    """项目响应体。"""

    # 主键
    id: int
    # 名称
    name: str
    # URL 别名
    slug: str
    # 短描述，空则 ""
    description: str = ""
    # 长描述 Markdown，空则 ""
    long_description: str = ""
    # 封面图 URL，空则 ""
    cover_image: str = ""
    # 技术栈；库内是 JSON 字符串，读出时转成数组
    tech_stack: list[str] = []
    # GitHub 仓库地址，空则 ""
    link_github: str = ""
    # Gitee 仓库地址，空则 ""
    link_gitee: str = ""
    # 线上地址，空则 ""
    link_live: str = ""
    # 文档地址，空则 ""
    link_docs: str = ""
    # 状态：developing / active / archived
    status: str
    # 状态展示文案，空则 ""
    status_label: str = ""
    # 是否精选
    is_featured: bool = False
    # 排序
    sort: int = 0
    # 创建时间
    created_at: datetime
    # 更新时间
    updated_at: datetime

    @field_validator("tech_stack", mode="before")
    @classmethod
    def tech_stack_from_json(cls, value: object) -> list[str]:
        if isinstance(value, list):
            return [str(item) for item in value]
        if not isinstance(value, str) or not value:
            return []
        try:
            data = json.loads(value)
        except json.JSONDecodeError:
            return []
        return [str(item) for item in data] if isinstance(data, list) else []
