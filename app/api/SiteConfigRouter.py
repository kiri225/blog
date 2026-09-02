from typing import Any

from fastapi import Depends
from fastapi.routing import APIRouter
from sqlmodel import Session

from app.Deps import get_current_user, get_session
from app.common.Result import Result
from app.schemas.SiteConfigSchemas import (
    CreateSiteConfigRequest,
    SiteConfigResponse,
    UpdateSiteConfigRequest,
)
from app.service import SiteConfigService as site_config_service


router = APIRouter(prefix="/api/site-config", tags=["站点配置"])


@router.get("", response_model=Result[dict[str, Any]])
def get_site_config_map(session: Session = Depends(get_session)):
    """获取全部站点配置（解析后的 dict）。

    公开接口。value 能 json.loads 则解析，否则当普通字符串。

    Args:
        session: 数据库会话，由依赖注入提供。

    Returns:
        统一结果集。成功时 code=200，data 为 {key: 解析后的值}。
    """
    return site_config_service.get_site_config_map(session)


@router.get("/list", response_model=Result[list[SiteConfigResponse]])
def list_site_configs(
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """管理端配置完整列表。

    需管理员 JWT。value 为未解析的原始字符串。
    须写在 /{key} 之前，否则 list 会被当成 key。

    Args:
        session: 数据库会话，由依赖注入提供。
        current_user: JWT payload，用来校验已登录；本接口不用里面的字段。

    Returns:
        统一结果集。成功时 code=200，data 为配置行列表。
    """
    return site_config_service.list_site_configs(session)


@router.put("", response_model=Result[dict[str, Any]])
def batch_update_site_configs(
    payload: dict[str, Any],
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """批量更新已有配置。

    需管理员 JWT。Body 为 {key: value}。已有则改 value，不存在的 key 跳过。

    Args:
        payload: 键值 dict。
        session: 数据库会话，由依赖注入提供。
        current_user: JWT payload，用来校验已登录；本接口不用里面的字段。

    Returns:
        统一结果集。成功时 code=200，data 为解析后的全量 dict。
    """
    return site_config_service.batch_update_site_configs(session, payload)


@router.post("", response_model=Result[SiteConfigResponse])
def create_site_config(
    CreateSiteConfigReq: CreateSiteConfigRequest,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """新建一条站点配置。

    需管理员 JWT。key 已存在则 400。

    Args:
        CreateSiteConfigReq: 创建站点配置请求体。
        session: 数据库会话，由依赖注入提供。
        current_user: JWT payload，用来校验已登录；本接口不用里面的字段。

    Returns:
        统一结果集。成功时 code=200，data 为配置行。
    """
    return site_config_service.create_site_config(session, CreateSiteConfigReq)


@router.get("/{key}", response_model=Result[Any])
def get_site_config_value(key: str, session: Session = Depends(get_session)):
    """按 key 获取解析后的单个 value。

    公开接口。不存在则 404。须写在 /list 之后。

    Args:
        key: 配置键。
        session: 数据库会话，由依赖注入提供。

    Returns:
        统一结果集。成功时 code=200，data 为解析后的值。
    """
    return site_config_service.get_site_config_value(session, key)


@router.put("/{key}", response_model=Result[SiteConfigResponse])
def update_site_config(
    key: str,
    UpdateSiteConfigReq: UpdateSiteConfigRequest,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """按 key 更新配置。

    需管理员 JWT。value 必填；description 不传则不改。不存在则 404。

    Args:
        key: 配置键。
        UpdateSiteConfigReq: 更新站点配置请求体。
        session: 数据库会话，由依赖注入提供。
        current_user: JWT payload，用来校验已登录；本接口不用里面的字段。

    Returns:
        统一结果集。成功时 code=200，data 为配置行。
    """
    return site_config_service.update_site_config(
        session, key, UpdateSiteConfigReq
    )


@router.delete("/{key}", response_model=Result)
def delete_site_config(
    key: str,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """按 key 删除配置。

    需管理员 JWT。不存在则 404。

    Args:
        key: 配置键。
        session: 数据库会话，由依赖注入提供。
        current_user: JWT payload，用来校验已登录；本接口不用里面的字段。

    Returns:
        统一结果集。成功时 code=200，message 为「删除成功」。
    """
    return site_config_service.delete_site_config(session, key)
