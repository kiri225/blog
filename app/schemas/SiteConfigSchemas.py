from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class CreateSiteConfigRequest(BaseModel):
    """创建站点配置请求体"""

    # 配置键，全站唯一
    key: str
    # 配置值，按字符串原样入库（多为 JSON 文本）
    value: str = ""
    # 配置说明
    description: str = ""


class UpdateSiteConfigRequest(BaseModel):
    """更新单条站点配置请求体。value 必填。"""

    # 配置值，按字符串原样入库
    value: str
    # 配置说明；不传则不改
    description: str | None = None


class SiteConfigResponse(BaseModel):
    """站点配置行响应体（管理端，value 未解析）。"""

    # 主键
    id: int
    # 配置键
    key: str
    # 原始字符串，未 json.loads
    value: str = ""
    # 配置说明，空则 ""
    description: str = ""
    # 更新时间
    updated_at: datetime
