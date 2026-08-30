from fastapi import Depends
from fastapi.routing import APIRouter
from sqlmodel import Session

from app.Deps import get_current_user, get_session
from app.common.Result import Result
from app.schemas.CategorySchemas import (
    CategoryResponse,
    CreateCategoryRequest,
    UpdateCategoryRequest,
)
from app.service import CategoryService as category_service


router = APIRouter(prefix="/api/categories", tags=["分类模块"])


@router.get("", response_model=Result[list[CategoryResponse]])
def list_categories(session: Session = Depends(get_session)):
    """获取分类列表。

    按 sort 升序返回全部分类。公开接口。

    Args:
        session: 数据库会话，由依赖注入提供。

    Returns:
        统一结果集。成功时 code=200，data 为分类列表。
    """
    return category_service.list_categories(session)


@router.post("", response_model=Result[CategoryResponse])
def create_category(
    CreateCategoryReq: CreateCategoryRequest,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """创建分类。

    需管理员 JWT。名称、URL 别名必须唯一，冲突则 400。

    Args:
        CreateCategoryReq: 创建分类请求体。
        session: 数据库会话，由依赖注入提供。
        current_user: JWT payload，用来校验已登录；本接口不用里面的字段。

    Returns:
        统一结果集。成功时 code=200，data 为分类。
    """
    return category_service.create_category(session, CreateCategoryReq)


@router.put("/{cat_id}", response_model=Result[CategoryResponse])
def update_category(
    cat_id: int,
    UpdateCategoryReq: UpdateCategoryRequest,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """更新分类。

    需管理员 JWT。名称、URL 别名必须唯一（排除自身），冲突则 400。
    分类不存在则 404。

    Args:
        cat_id: 分类 ID。
        UpdateCategoryReq: 更新分类请求体。
        session: 数据库会话，由依赖注入提供。
        current_user: JWT payload，用来校验已登录；本接口不用里面的字段。

    Returns:
        统一结果集。成功时 code=200，data 为分类。
    """
    return category_service.update_category(session, cat_id, UpdateCategoryReq)


@router.delete("/{cat_id}", response_model=Result)
def delete_category(
    cat_id: int,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """删除分类。

    需管理员 JWT。分类不存在则 404；仍有文章占用则 400。

    Args:
        cat_id: 分类 ID。
        session: 数据库会话，由依赖注入提供。
        current_user: JWT payload，用来校验已登录；本接口不用里面的字段。

    Returns:
        统一结果集。成功时 code=200，message 为「删除成功」。
    """
    return category_service.delete_category(session, cat_id)
