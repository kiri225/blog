from __future__ import annotations

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class SiteConfig(SQLModel, table=True):
    """站点 KV 配置。value 库内永远是字符串（多为 JSON 文本）。"""

    # 类名 SiteConfig 小写是 siteconfig，与库表 site_config 不一致，必须显式指定
    __tablename__ = "site_config"  # pyright: ignore[reportAssignmentType]

    # 主键，自增
    id: Optional[int] = Field(default=None, primary_key=True)
    # 配置键，全站唯一
    key: str = Field(max_length=100, unique=True)
    # 配置值，TEXT 存 JSON 字符串或普通字符串
    value: str = Field(default="")
    # 配置说明
    description: str = Field(default="", max_length=200)
    # 更新时间
    updated_at: datetime = Field(default_factory=datetime.now)
