from __future__ import annotations

from datetime import datetime
from typing import Optional
from sqlalchemy import Index
from sqlmodel import SQLModel, Field


class Visitor(SQLModel, table=True):
    """访客记录。不去重；地理查询失败时城市等字段为空。"""

    # 主键，自增
    id: Optional[int] = Field(default=None, primary_key=True)
    # 访客 IP，IPv6 最长 45
    ip: str = Field(max_length=45)
    # 访问路径，来自 Header X-Path
    path: str = Field(default="", max_length=500)
    # 原始 User-Agent
    user_agent: str = Field(default="")
    # 城市
    city: str = Field(default="", max_length=100)
    # 省份 / 地区
    region: str = Field(default="", max_length=100)
    # 国家
    country: str = Field(default="", max_length=100)
    # 区县
    district: str = Field(default="", max_length=100)
    # 网络运营商 / 组织
    org: str = Field(default="", max_length=200)
    # ASN
    asn: str = Field(default="", max_length=50)
    # 是否移动网络
    is_mobile: bool = Field(default=False)
    # 是否代理
    is_proxy: bool = Field(default=False)
    # 是否机房 / 托管 IP
    is_hosting: bool = Field(default=False)
    # 浏览器解析结果，空则 ""
    browser: str = Field(default="", max_length=50)
    # 操作系统解析结果，空则 ""
    os: str = Field(default="", max_length=50)
    # 设备类型：mobile / tablet / desktop，空则 ""
    device_type: str = Field(default="", max_length=20)
    # 访问时间
    created_at: datetime = Field(default_factory=datetime.now)

    __table_args__ = (
        Index("idx_visitor_ip", "ip"),
        # 列表倒序、仪表盘近 30 天 WHERE created_at >= ?
        Index("idx_visitor_created", "created_at"),
    )
