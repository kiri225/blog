from fastapi import Depends
from fastapi.routing import APIRouter
from sqlmodel import Session

from app.Deps import get_current_user, get_session
from app.common.Result import Result
from app.schemas.TagSchemas import CreateTagRequest, TagResponse, UpdateTagRequest
from app.service import TagService as tag_service


router = APIRouter(prefix="/api/tags", tags=["文章标签模块"])


@router.get("", response_model=Result[list[TagResponse]])
def list_tags(session: Session = Depends(get_session)):
    """获取标签列表。

    按 id 正序返回全部标签。公开接口。

    Args:
        session: 数据库会话，由依赖注入提供。

    Returns:
        统一结果集。成功时 code=200，data 为标签列表。
    """
    return tag_service.get_tags(session)


@router.post("", response_model=Result[TagResponse])
def create_tag(
    CreateTagReq: CreateTagRequest,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """创建标签。

    需管理员 JWT。名称、URL 别名必须唯一，冲突则 400。

    Args:
        CreateTagReq: 创建标签请求体。
        session: 数据库会话，由依赖注入提供。
        current_user: JWT payload，用来校验已登录；本接口不用里面的字段。

    Returns:
        统一结果集。成功时 code=200，data 为标签。
    """
    return tag_service.create_tag(session, CreateTagReq)


@router.put("/{tag_id}", response_model=Result[TagResponse])
def update_tag(
    tag_id: int,
    UpdateTagReq: UpdateTagRequest,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """更新标签。

    需管理员 JWT。名称、URL 别名必须唯一（排除自身），冲突则 400。
    标签不存在则 404。

    Args:
        tag_id: 标签 ID。
        UpdateTagReq: 更新标签请求体。
        session: 数据库会话，由依赖注入提供。
        current_user: JWT payload，用来校验已登录；本接口不用里面的字段。

    Returns:
        统一结果集。成功时 code=200，data 为标签。
    """
    return tag_service.update_tag(session, tag_id, UpdateTagReq)


@router.delete("/{tag_id}", response_model=Result)
def delete_tag(
    tag_id: int,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """删除标签。

    需管理员 JWT。标签不存在则 404；仍有文章占用则 400。

    Args:
        tag_id: 标签 ID。
        session: 数据库会话，由依赖注入提供。
        current_user: JWT payload，用来校验已登录；本接口不用里面的字段。

    Returns:
        统一结果集。成功时 code=200，message 为「删除成功」。
    """
    return tag_service.delete_tag(session, tag_id)

