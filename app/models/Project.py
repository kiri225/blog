from __future__ import annotations

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class Project(SQLModel, table=True):
    """项目展示。读按 slug，写按 id；tech_stack 库内为 JSON 数组字符串。"""

    # 主键，自增
    id: Optional[int] = Field(default=None, primary_key=True)
    # 名称
    name: str = Field(max_length=100)
    # URL 别名，前台按此访问，唯一
    slug: str = Field(max_length=200, unique=True)
    # 短描述
    description: str = Field(default="", max_length=500)
    # 长描述，Markdown
    long_description: str = Field(default="")
    # 封面图 URL
    cover_image: str = Field(default="")
    # 技术栈，TEXT 存 JSON 数组字符串，如 '["Python","FastAPI"]'；空为 '[]'
    tech_stack: str = Field(default="[]")
    # GitHub 仓库地址
    link_github: str = Field(default="")
    # Gitee 仓库地址
    link_gitee: str = Field(default="")
    # 线上地址
    link_live: str = Field(default="")
    # 文档地址
    link_docs: str = Field(default="")
    # 状态：developing / active / archived
    status: str = Field(default="developing", max_length=20)
    # 状态展示文案，如「维护中」
    status_label: str = Field(default="", max_length=50)
    # 是否精选
    is_featured: bool = Field(default=False)
    # 排序，越小越靠前
    sort: int = Field(default=0)
    # 创建时间
    created_at: datetime = Field(default_factory=datetime.now)
    # 更新时间
    updated_at: datetime = Field(default_factory=datetime.now)
