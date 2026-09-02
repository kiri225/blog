import json
from datetime import datetime
from typing import Any

from fastapi import HTTPException
from sqlmodel import Session, select

from app.common.Result import Result
from app.models.SiteConfig import SiteConfig
from app.schemas.SiteConfigSchemas import (
    CreateSiteConfigRequest,
    UpdateSiteConfigRequest,
)

_DEFAULT_CONFIGS = (
    ("site_title", '"Kirameku"', "站点标题"),
    ("site_description", '"煌めく — 一个个人博客"', "站点描述"),
    ("icp_number", '""', "ICP备案号"),
    ("icp_link", '""', "ICP备案链接"),
)


def parse_config_value(raw: str) -> Any:
    """能 json.loads 就解析，否则当普通字符串。"""
    if not raw:
        return ""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def _as_store_value(value: Any) -> str:
    """批量更新时非字符串用 JSON 文本入库。"""
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


def seed_site_configs(session: Session) -> None:
    """表为空时写入默认站点配置。已有行则跳过。"""
    existed = session.exec(select(SiteConfig).limit(1)).first()
    if existed:
        return
    for key, value, description in _DEFAULT_CONFIGS:
        session.add(SiteConfig(key=key, value=value, description=description))
    session.commit()


def get_site_config_map(session: Session) -> Result:
    """前台：全部配置解析成 {key: 值}。

    Args:
        session: 数据库会话，由路由传入。

    Returns:
        统一结果集。成功时 code=200，data 为键值 dict。
    """
    # 1.查出全部配置
    rows = list(session.exec(select(SiteConfig)).all())

    # 2.解析 value 后组成 dict
    data = {row.key: parse_config_value(row.value or "") for row in rows}

    # 3.统一结果集返回
    return Result.success(data)


def list_site_configs(session: Session) -> Result:
    """管理端：完整行列表，value 不解析。

    Args:
        session: 数据库会话，由路由传入。

    Returns:
        统一结果集。成功时 code=200，data 为配置行列表。
    """
    # 1.按 id 升序查询
    rows = list(session.exec(select(SiteConfig).order_by(SiteConfig.id)).all())

    # 2.统一结果集返回
    return Result.success(rows)


def get_site_config_value(session: Session, key: str) -> Result:
    """按 key 取解析后的单个 value。

    Args:
        session: 数据库会话，由路由传入。
        key: 配置键。

    Returns:
        统一结果集。成功时 code=200，data 为解析后的值。
    """
    # 1.按 key 取配置
    row = session.exec(select(SiteConfig).where(SiteConfig.key == key)).first()
    if not row:
        raise HTTPException(status_code=404, detail=f"配置 {key} 不存在")

    # 2.统一结果集返回解析后的值
    return Result.success(parse_config_value(row.value or ""))


def create_site_config(
    session: Session, CreateSiteConfigReq: CreateSiteConfigRequest
) -> Result:
    """管理员新建一条配置。

    Args:
        session: 数据库会话，由路由传入。
        CreateSiteConfigReq: 创建站点配置请求体。

    Returns:
        统一结果集。成功时 code=200，data 为配置行。
    """
    # 1.key 必须唯一
    existed = session.exec(
        select(SiteConfig).where(SiteConfig.key == CreateSiteConfigReq.key)
    ).first()
    if existed:
        raise HTTPException(
            status_code=400, detail=f"配置 {CreateSiteConfigReq.key} 已存在"
        )

    # 2.落库
    row = SiteConfig(
        key=CreateSiteConfigReq.key,
        value=CreateSiteConfigReq.value or "",
        description=CreateSiteConfigReq.description or "",
    )
    session.add(row)
    session.commit()
    session.refresh(row)

    # 3.统一结果集返回
    return Result.success(row)


def update_site_config(
    session: Session, key: str, UpdateSiteConfigReq: UpdateSiteConfigRequest
) -> Result:
    """管理员按 key 更新 value；description 不传则不改。

    Args:
        session: 数据库会话，由路由传入。
        key: 配置键。
        UpdateSiteConfigReq: 更新站点配置请求体。

    Returns:
        统一结果集。成功时 code=200，data 为配置行。
    """
    # 1.配置必须存在
    row = session.exec(select(SiteConfig).where(SiteConfig.key == key)).first()
    if not row:
        raise HTTPException(status_code=404, detail=f"配置 {key} 不存在")

    # 2.更新字段
    row.value = UpdateSiteConfigReq.value
    if UpdateSiteConfigReq.description is not None:
        row.description = UpdateSiteConfigReq.description
    row.updated_at = datetime.now()

    # 3.落库
    session.add(row)
    session.commit()
    session.refresh(row)

    # 4.统一结果集返回
    return Result.success(row)


def batch_update_site_configs(session: Session, payload: dict[str, Any]) -> Result:
    """管理员批量更新已有 key 的 value；不存在的 key 跳过、不创建。

    Args:
        session: 数据库会话，由路由传入。
        payload: {key: value}，value 原样或 JSON 文本入库。

    Returns:
        统一结果集。成功时 code=200，data 为解析后的全量 dict。
    """
    # 1.按传入 key 更新已有行
    for key, value in payload.items():
        row = session.exec(select(SiteConfig).where(SiteConfig.key == key)).first()
        if not row:
            continue
        row.value = _as_store_value(value)
        row.updated_at = datetime.now()
        session.add(row)

    # 2.落库
    session.commit()

    # 3.返回与前台 GET / 相同的解析 dict
    return get_site_config_map(session)


def delete_site_config(session: Session, key: str) -> Result:
    """管理员按 key 删除配置。

    Args:
        session: 数据库会话，由路由传入。
        key: 配置键。

    Returns:
        统一结果集。成功时 code=200，message 为「删除成功」。
    """
    # 1.配置必须存在
    row = session.exec(select(SiteConfig).where(SiteConfig.key == key)).first()
    if not row:
        raise HTTPException(status_code=404, detail=f"配置 {key} 不存在")

    # 2.删除并落库
    session.delete(row)
    session.commit()

    # 3.统一结果集返回
    return Result.success(message="删除成功")
