from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class VisitorCountResponse(BaseModel):
    """访客计数响应体。"""

    # 访客总条数（不去重）
    count: int


class VisitorLocationResponse(BaseModel):
    """当前请求者地理响应体。不落库。"""

    # 访客 IP
    ip: str = ""
    # 城市
    city: str = ""
    # 省份 / 地区
    region: str = ""
    # 国家
    country: str = ""
    # 区县
    district: str = ""
    # 网络运营商 / 组织
    org: str = ""
    # ASN
    asn: str = ""
    # 是否移动网络
    is_mobile: bool = False
    # 是否代理
    is_proxy: bool = False
    # 是否机房 / 托管 IP
    is_hosting: bool = False


class VisitorResponse(BaseModel):
    """访客记录响应体。"""

    # 主键
    id: int
    # 访客 IP
    ip: str
    # 访问路径
    path: str = ""
    # 原始 User-Agent
    user_agent: str = ""
    # 城市
    city: str = ""
    # 省份 / 地区
    region: str = ""
    # 国家
    country: str = ""
    # 区县
    district: str = ""
    # 网络运营商 / 组织
    org: str = ""
    # ASN
    asn: str = ""
    # 是否移动网络
    is_mobile: bool = False
    # 是否代理
    is_proxy: bool = False
    # 是否机房 / 托管 IP
    is_hosting: bool = False
    # 浏览器，空则 ""
    browser: str = ""
    # 操作系统，空则 ""
    os: str = ""
    # 设备类型：mobile / tablet / desktop，空则 ""
    device_type: str = ""
    # 访问时间
    created_at: datetime
