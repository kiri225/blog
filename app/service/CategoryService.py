from datetime import datetime

from fastapi import HTTPException
from sqlmodel import Session, select

from app.common.Result import Result
from app.models.Category import Category
from app.schemas.CategorySchemas import (
    CategoryResponse,
    CreateCategoryRequest,
    UpdateCategoryRequest,
)


def list_categories(session: Session) -> Result:
    """按排序返回全部分类。

    Args:
        session: 数据库会话，由路由传入。

    Returns:
        统一结果集。成功时 code=200，data 为分类列表。
    """
    # 1.按 sort 升序查询
    rows = session.exec(select(Category).order_by(Category.sort)).all()

    # 2.统一结果集返回
    items = [
        CategoryResponse(
            id=row.id,
            name=row.name,
            slug=row.slug,
            description=row.description or "",
            sort=row.sort,
            post_count=row.post_count,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
        for row in rows
    ]
    return Result.success(items)


def create_category(
    session: Session, CreateCategoryReq: CreateCategoryRequest
) -> Result:
    """创建分类。

    Args:
        session: 数据库会话，由路由传入。
        CreateCategoryReq: 创建分类请求体。

    Returns:
        统一结果集。成功时 code=200，data 为分类。
    """
    # 1.判断名称或别名是否已存在
    existed = session.exec(
        select(Category).where(
            (Category.name == CreateCategoryReq.name)
            | (Category.slug == CreateCategoryReq.slug)
        )
    ).first()
    if existed:
        raise HTTPException(status_code=400, detail="分类已存在")

    # 2.落库
    category = Category(
        name=CreateCategoryReq.name,
        slug=CreateCategoryReq.slug,
        description=CreateCategoryReq.description,
        sort=CreateCategoryReq.sort,
    )
    session.add(category)
    session.commit()
    session.refresh(category)

    # 3.统一结果集返回
    return Result.success(
        CategoryResponse(
            id=category.id,
            name=category.name,
            slug=category.slug,
            description=category.description or "",
            sort=category.sort,
            post_count=category.post_count,
            created_at=category.created_at,
            updated_at=category.updated_at,
        )
    )


def update_category(
    session: Session, cat_id: int, UpdateCategoryReq: UpdateCategoryRequest
) -> Result:
    """更新分类。

    Args:
        session: 数据库会话，由路由传入。
        cat_id: 分类 ID。
        UpdateCategoryReq: 更新分类请求体。

    Returns:
        统一结果集。成功时 code=200，data 为分类。
    """
    # 1.判断分类是否存在
    category = session.get(Category, cat_id)
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")

    # 2.判断名称或别名是否被其它分类占用
    name = (
        UpdateCategoryReq.name
        if UpdateCategoryReq.name is not None
        else category.name
    )
    slug = (
        UpdateCategoryReq.slug
        if UpdateCategoryReq.slug is not None
        else category.slug
    )
    existed = session.exec(
        select(Category).where(
            ((Category.name == name) | (Category.slug == slug))
            & (Category.id != cat_id)
        )
    ).first()
    if existed:
        raise HTTPException(status_code=400, detail="分类已存在")

    # 3.按传入字段更新
    if UpdateCategoryReq.name is not None:
        category.name = UpdateCategoryReq.name
    if UpdateCategoryReq.slug is not None:
        category.slug = UpdateCategoryReq.slug
    if UpdateCategoryReq.description is not None:
        category.description = UpdateCategoryReq.description
    if UpdateCategoryReq.sort is not None:
        category.sort = UpdateCategoryReq.sort
    category.updated_at = datetime.now()

    # 4.落库
    session.commit()
    session.refresh(category)

    # 5.统一结果集返回
    return Result.success(
        CategoryResponse(
            id=category.id,
            name=category.name,
            slug=category.slug,
            description=category.description or "",
            sort=category.sort,
            post_count=category.post_count,
            created_at=category.created_at,
            updated_at=category.updated_at,
        )
    )


def delete_category(session: Session, cat_id: int) -> Result:
    """删除分类。

    Args:
        session: 数据库会话，由路由传入。
        cat_id: 分类 ID。

    Returns:
        统一结果集。成功时 code=200，message 为「删除成功」。
    """
    # 1.判断分类是否存在
    category = session.get(Category, cat_id)
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")

    # 2.判断是否仍有文章占用
    if category.post_count > 0:
        raise HTTPException(status_code=400, detail="分类被文章引用，不能删除")

    # 3.删除并落库
    session.delete(category)
    session.commit()

    # 4.统一结果集返回
    return Result.success(message="删除成功")
