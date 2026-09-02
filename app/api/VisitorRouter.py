from fastapi import Depends, Query
from fastapi.requests import Request
from fastapi.routing import APIRouter
from sqlmodel import Session

from app.Deps import get_current_user, get_session
from app.common.Result import Result
from app.schemas.VisitorSchemas import (
    VisitorCountResponse,
    VisitorLocationResponse,
    VisitorResponse,
)
from app.service import VisitorService as visitor_service


router = APIRouter(prefix="/api/visitors", tags=["访客记录"])


def _client_ip(request: Request) -> str:
    """同评论：X-Forwarded-For → X-Real-IP → client.host。"""
    ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    if not ip:
        ip = request.headers.get("x-real-ip", "")
    if not ip:
        ip = request.client.host if request.client else ""
    return ip


@router.get("/count", response_model=Result[VisitorCountResponse])
def count_visitors(session: Session = Depends(get_session)):
    """访客总条数。

    公开接口。不去重。须写在 /{visitor_id} 之前。

    Args:
        session: 数据库会话，由依赖注入提供。

    Returns:
        统一结果集。成功时 code=200，data 含 count。
    """
    return visitor_service.count_visitors(session)


@router.get("/location", response_model=Result[VisitorLocationResponse])
def get_location(request: Request):
    """当前请求者的地理信息。

    公开接口。不落库。内网或第三方失败返回空字段，不 500。
    须写在 /{visitor_id} 之前。

    Args:
        request: 当前请求，用来解析客户端 IP。

    Returns:
        统一结果集。成功时 code=200，data 为地理信息。
    """
    return visitor_service.get_location(_client_ip(request))


@router.post("/record", response_model=Result)
def record_visit(request: Request, session: Session = Depends(get_session)):
    """记录一次访问。

    公开接口。从 Header 取 IP、X-Path、User-Agent。不去重。
    地理失败仍成功，城市等为空。须写在 /{visitor_id} 之前。

    Args:
        request: 当前请求，用来读 IP 与 Header。
        session: 数据库会话，由依赖注入提供。

    Returns:
        统一结果集。成功时 code=200，message 为 ok。
    """
    return visitor_service.record_visit(
        session,
        _client_ip(request),
        request.headers.get("x-path", "") or "",
        request.headers.get("user-agent", "") or "",
    )


@router.get("", response_model=Result[list[VisitorResponse]])
def list_visitors(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
):
    """最近访客分页列表。

    公开接口。按 created_at 降序。不去重。

    Args:
        page: 页码，从 1 开始。
        size: 每页条数，最大 100。
        session: 数据库会话，由依赖注入提供。

    Returns:
        统一结果集。成功时 code=200，data 为访客列表。
    """
    return visitor_service.list_visitors(session, page, size)


@router.delete("", response_model=Result)
def clear_visitors(
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """清空全部访客记录。

    需管理员 JWT。对照源码未加锁，本项目加上以免被随便清空。

    Args:
        session: 数据库会话，由依赖注入提供。
        current_user: JWT payload，用来校验已登录；本接口不用里面的字段。

    Returns:
        统一结果集。成功时 code=200，message 为「删除成功」。
    """
    return visitor_service.clear_visitors(session)


@router.delete("/{visitor_id}", response_model=Result)
def delete_visitor(
    visitor_id: int,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """删除一条访客记录。

    需管理员 JWT。对照源码未加锁，本项目加上。不存在则 404。

    Args:
        visitor_id: 访客记录 ID。
        session: 数据库会话，由依赖注入提供。
        current_user: JWT payload，用来校验已登录；本接口不用里面的字段。

    Returns:
        统一结果集。成功时 code=200，message 为「删除成功」。
    """
    return visitor_service.delete_visitor(session, visitor_id)
