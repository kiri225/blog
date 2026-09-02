import ipaddress
import re
from typing import Any

import requests
from fastapi import HTTPException
from sqlmodel import Session, func, select

from app.common.Result import Result
from app.models.Visitor import Visitor
from app.schemas.VisitorSchemas import VisitorCountResponse, VisitorLocationResponse

_HTTP_TIMEOUT = 3
_IPAPI_URL = "https://ipapi.co/{ip}/json"
_GEO_CACHE: dict[str, dict[str, Any]] = {}

_EMPTY_GEO: dict[str, Any] = {
    "city": "",
    "region": "",
    "country": "",
    "district": "",
    "org": "",
    "asn": "",
    "is_mobile": False,
    "is_proxy": False,
    "is_hosting": False,
}


def _is_private_ip(ip: str) -> bool:
    """环回 / 内网 / 无法解析的 IP 不打外部地理接口。"""
    if not ip or ip.lower() in {"unknown", "localhost"}:
        return True
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return True
    return bool(addr.is_private or addr.is_loopback or addr.is_reserved or addr.is_link_local)


def _lookup_geo(ip: str) -> dict[str, Any]:
    """按 IP 查地理。失败或内网返回空字段；结果按 IP 做内存缓存。"""
    if ip in _GEO_CACHE:
        return _GEO_CACHE[ip]
    if _is_private_ip(ip):
        _GEO_CACHE[ip] = dict(_EMPTY_GEO)
        return _GEO_CACHE[ip]
    try:
        resp = requests.get(
            _IPAPI_URL.format(ip=ip),
            timeout=_HTTP_TIMEOUT,
            headers={"User-Agent": "kiri-blog"},
        )
        data = resp.json() if resp.ok else {}
    except (requests.RequestException, ValueError):
        data = {}
    if not isinstance(data, dict) or data.get("error"):
        geo = dict(_EMPTY_GEO)
        _GEO_CACHE[ip] = geo
        return geo
    geo = {
        "city": str(data.get("city") or ""),
        "region": str(data.get("region") or ""),
        "country": str(data.get("country_name") or data.get("country") or ""),
        "district": str(data.get("district") or ""),
        "org": str(data.get("org") or ""),
        "asn": str(data.get("asn") or ""),
        "is_mobile": bool(data.get("is_mobile") or data.get("mobile") or False),
        "is_proxy": bool(data.get("is_proxy") or data.get("proxy") or False),
        "is_hosting": bool(data.get("is_hosting") or data.get("hosting") or False),
    }
    _GEO_CACHE[ip] = geo
    return geo


def _parse_user_agent(ua: str) -> tuple[str, str, str]:
    """简单解析 browser / os / device_type。"""
    ua_l = (ua or "").lower()
    if "ipad" in ua_l or "tablet" in ua_l:
        device_type = "tablet"
    elif "mobile" in ua_l or "android" in ua_l or "iphone" in ua_l:
        device_type = "mobile"
    else:
        device_type = "desktop"

    if "windows" in ua_l:
        os_name = "Windows"
    elif "iphone" in ua_l or "ipad" in ua_l or re.search(r"cpu os|iphone os", ua_l):
        os_name = "iOS"
    elif "mac os" in ua_l or "macintosh" in ua_l:
        os_name = "macOS"
    elif "android" in ua_l:
        os_name = "Android"
    elif "linux" in ua_l:
        os_name = "Linux"
    else:
        os_name = ""

    if "edg/" in ua_l or "edge/" in ua_l:
        browser = "Edge"
    elif "opr/" in ua_l or "opera" in ua_l:
        browser = "Opera"
    elif "chrome/" in ua_l or "crios/" in ua_l:
        browser = "Chrome"
    elif "firefox/" in ua_l or "fxios/" in ua_l:
        browser = "Firefox"
    elif "safari/" in ua_l:
        browser = "Safari"
    else:
        browser = ""
    return browser, os_name, device_type


def list_visitors(session: Session, page: int, size: int) -> Result:
    """最近访客分页，按 created_at 降序。不去重。

    Args:
        session: 数据库会话，由路由传入。
        page: 页码，从 1 开始。
        size: 每页条数。

    Returns:
        统一结果集。成功时 code=200，data 为访客列表。
    """
    # 1.按创建时间降序分页
    rows = list(
        session.exec(
            select(Visitor)
            .order_by(Visitor.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        ).all()
    )

    # 2.统一结果集返回
    return Result.success(rows)


def count_visitors(session: Session) -> Result:
    """访客总条数（不去重）。

    Args:
        session: 数据库会话，由路由传入。

    Returns:
        统一结果集。成功时 code=200，data 含 count。
    """
    # 1.统计全部
    count = session.exec(select(func.count(Visitor.id))).one()

    # 2.统一结果集返回
    return Result.success(VisitorCountResponse(count=count or 0))


def get_location(ip: str) -> Result:
    """查当前 IP 地理，不写库。内网或第三方失败返回空字段，不 500。

    Args:
        ip: 客户端 IP，由路由解析。

    Returns:
        统一结果集。成功时 code=200，data 为地理信息。
    """
    # 1.查地理（缓存 / 内网空字段）
    geo = _lookup_geo(ip or "")

    # 2.统一结果集返回
    return Result.success(VisitorLocationResponse(ip=ip or "", **geo))


def record_visit(session: Session, ip: str, path: str, user_agent: str) -> Result:
    """记录一次访问。地理失败不阻断；同一 IP 多次访问不去重。

    Args:
        session: 数据库会话，由路由传入。
        ip: 客户端 IP。
        path: Header X-Path，没有则为空串。
        user_agent: Header User-Agent。

    Returns:
        统一结果集。成功时 code=200，message 为 ok。
    """
    # 1.查地理、解析 UA
    geo = _lookup_geo(ip or "")
    browser, os_name, device_type = _parse_user_agent(user_agent)

    # 2.落库
    visitor = Visitor(
        ip=ip or "",
        path=path or "",
        user_agent=user_agent or "",
        city=geo["city"],
        region=geo["region"],
        country=geo["country"],
        district=geo["district"],
        org=geo["org"],
        asn=geo["asn"],
        is_mobile=geo["is_mobile"],
        is_proxy=geo["is_proxy"],
        is_hosting=geo["is_hosting"],
        browser=browser,
        os=os_name,
        device_type=device_type,
    )
    session.add(visitor)
    session.commit()

    # 3.统一结果集返回
    return Result.success(message="ok")


def delete_visitor(session: Session, visitor_id: int) -> Result:
    """管理员删除一条访客记录。

    Args:
        session: 数据库会话，由路由传入。
        visitor_id: 访客记录 ID。

    Returns:
        统一结果集。成功时 code=200，message 为「删除成功」。
    """
    # 1.记录必须存在
    visitor = session.get(Visitor, visitor_id)
    if not visitor:
        raise HTTPException(status_code=404, detail="访客不存在")

    # 2.删除并落库
    session.delete(visitor)
    session.commit()

    # 3.统一结果集返回
    return Result.success(message="删除成功")


def clear_visitors(session: Session) -> Result:
    """管理员清空全部访客记录。

    Args:
        session: 数据库会话，由路由传入。

    Returns:
        统一结果集。成功时 code=200，message 为「删除成功」。
    """
    # 1.查出全部再删
    rows = list(session.exec(select(Visitor)).all())
    for row in rows:
        session.delete(row)

    # 2.落库
    session.commit()

    # 3.统一结果集返回
    return Result.success(message="删除成功")
