import json
from datetime import datetime

from fastapi import HTTPException
from sqlmodel import Session, select

from app.common.Result import Result
from app.models.BookmarkCategory import BookmarkCategory
from app.models.BookmarkSite import BookmarkSite
from app.schemas.BookmarkSchemas import (
    BookmarkFullResponse,
    BookmarkSiteResponse,
    CreateBookmarkCategoryRequest,
    CreateBookmarkSiteRequest,
    UpdateBookmarkCategoryRequest,
    UpdateBookmarkSiteRequest,
)


def list_bookmarks(session: Session) -> Result:
    """前台：分类按 sort 升序，每项带按 sort 升序的站点。

    Args:
        session: 数据库会话，由路由传入。

    Returns:
        统一结果集。成功时 code=200，data 为嵌套分类列表。
    """
    # 1.分类按 sort 升序
    categories = list(
        session.exec(select(BookmarkCategory).order_by(BookmarkCategory.sort)).all()
    )

    # 2.站点按 sort 升序，再按 category_id 分组
    sites = list(session.exec(select(BookmarkSite).order_by(BookmarkSite.sort)).all())
    sites_by_cat: dict[int, list[BookmarkSite]] = {}
    for site in sites:
        sites_by_cat.setdefault(site.category_id, []).append(site)

    # 3.嵌套组装后统一结果集返回
    return Result.success(
        [
            BookmarkFullResponse(
                id=cat.id,
                name=cat.name,
                icon=cat.icon or "",
                description=cat.description or "",
                sort=cat.sort,
                created_at=cat.created_at,
                updated_at=cat.updated_at,
                sites=[
                    BookmarkSiteResponse.model_validate(site.model_dump())
                    for site in sites_by_cat.get(cat.id, [])
                ],
            )
            for cat in categories
        ]
    )


def list_bookmark_categories(session: Session) -> Result:
    """仅分类列表，按 sort 升序。

    Args:
        session: 数据库会话，由路由传入。

    Returns:
        统一结果集。成功时 code=200，data 为分类列表。
    """
    # 1.按 sort 升序查询
    rows = list(
        session.exec(select(BookmarkCategory).order_by(BookmarkCategory.sort)).all()
    )

    # 2.统一结果集返回
    return Result.success(rows)


def create_bookmark_category(
    session: Session, CreateBookmarkCategoryReq: CreateBookmarkCategoryRequest
) -> Result:
    """管理员创建收藏分类。

    Args:
        session: 数据库会话，由路由传入。
        CreateBookmarkCategoryReq: 创建收藏分类请求体。

    Returns:
        统一结果集。成功时 code=200，data 为分类。
    """
    # 1.落库
    category = BookmarkCategory(
        name=CreateBookmarkCategoryReq.name,
        icon=CreateBookmarkCategoryReq.icon or "",
        description=CreateBookmarkCategoryReq.description or "",
        sort=CreateBookmarkCategoryReq.sort,
    )
    session.add(category)
    session.commit()
    session.refresh(category)

    # 2.统一结果集返回
    return Result.success(category)


def update_bookmark_category(
    session: Session,
    cat_id: int,
    UpdateBookmarkCategoryReq: UpdateBookmarkCategoryRequest,
) -> Result:
    """管理员更新收藏分类。只改传入字段。

    Args:
        session: 数据库会话，由路由传入。
        cat_id: 收藏分类 ID。
        UpdateBookmarkCategoryReq: 更新收藏分类请求体。

    Returns:
        统一结果集。成功时 code=200，data 为分类。
    """
    # 1.分类必须存在
    category = session.get(BookmarkCategory, cat_id)
    if not category:
        raise HTTPException(status_code=404, detail="收藏分类不存在")

    # 2.按传入字段更新
    if UpdateBookmarkCategoryReq.name is not None:
        category.name = UpdateBookmarkCategoryReq.name
    if UpdateBookmarkCategoryReq.icon is not None:
        category.icon = UpdateBookmarkCategoryReq.icon
    if UpdateBookmarkCategoryReq.description is not None:
        category.description = UpdateBookmarkCategoryReq.description
    if UpdateBookmarkCategoryReq.sort is not None:
        category.sort = UpdateBookmarkCategoryReq.sort
    category.updated_at = datetime.now()

    # 3.落库
    session.add(category)
    session.commit()
    session.refresh(category)

    # 4.统一结果集返回
    return Result.success(category)


def delete_bookmark_category(session: Session, cat_id: int) -> Result:
    """管理员删除收藏分类，并级联删除其下全部站点。

    Args:
        session: 数据库会话，由路由传入。
        cat_id: 收藏分类 ID。

    Returns:
        统一结果集。成功时 code=200，message 为「删除成功」。
    """
    # 1.分类必须存在
    category = session.get(BookmarkCategory, cat_id)
    if not category:
        raise HTTPException(status_code=404, detail="收藏分类不存在")

    # 2.先删该分类下全部站点
    sites = list(
        session.exec(
            select(BookmarkSite).where(BookmarkSite.category_id == cat_id)
        ).all()
    )
    for site in sites:
        session.delete(site)

    # 3.删除分类并落库
    session.delete(category)
    session.commit()

    # 4.统一结果集返回
    return Result.success(message="删除成功")


def list_bookmark_sites(session: Session, category_id: int | None) -> Result:
    """站点列表，可按分类筛选，按 sort 升序。

    Args:
        session: 数据库会话，由路由传入。
        category_id: 收藏分类 ID；None 表示全部。

    Returns:
        统一结果集。成功时 code=200，data 为站点列表。
    """
    # 1.可选按分类筛选，按 sort 升序
    query = select(BookmarkSite)
    if category_id is not None:
        query = query.where(BookmarkSite.category_id == category_id)
    rows = list(session.exec(query.order_by(BookmarkSite.sort)).all())

    # 2.统一结果集返回
    return Result.success(rows)


def create_bookmark_site(
    session: Session, CreateBookmarkSiteReq: CreateBookmarkSiteRequest
) -> Result:
    """管理员创建收藏站点。

    Args:
        session: 数据库会话，由路由传入。
        CreateBookmarkSiteReq: 创建收藏站点请求体。

    Returns:
        统一结果集。成功时 code=200，data 为站点。
    """
    # 1.分类必须存在
    category = session.get(BookmarkCategory, CreateBookmarkSiteReq.category_id)
    if not category:
        raise HTTPException(status_code=404, detail="收藏分类不存在")

    # 2.落库（platforms 转 JSON 字符串）
    site = BookmarkSite(
        category_id=CreateBookmarkSiteReq.category_id,
        name=CreateBookmarkSiteReq.name,
        url=CreateBookmarkSiteReq.url,
        icon=CreateBookmarkSiteReq.icon or "",
        description=CreateBookmarkSiteReq.description or "",
        platforms=json.dumps(CreateBookmarkSiteReq.platforms, ensure_ascii=False),
        sort=CreateBookmarkSiteReq.sort,
    )
    session.add(site)
    session.commit()
    session.refresh(site)

    # 3.统一结果集返回
    return Result.success(site)


def update_bookmark_site(
    session: Session,
    site_id: int,
    UpdateBookmarkSiteReq: UpdateBookmarkSiteRequest,
) -> Result:
    """管理员更新收藏站点。只改传入字段。

    Args:
        session: 数据库会话，由路由传入。
        site_id: 收藏站点 ID。
        UpdateBookmarkSiteReq: 更新收藏站点请求体。

    Returns:
        统一结果集。成功时 code=200，data 为站点。
    """
    # 1.站点必须存在
    site = session.get(BookmarkSite, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="收藏站点不存在")

    # 2.若换分类，新分类必须存在
    if UpdateBookmarkSiteReq.category_id is not None:
        category = session.get(BookmarkCategory, UpdateBookmarkSiteReq.category_id)
        if not category:
            raise HTTPException(status_code=404, detail="收藏分类不存在")
        site.category_id = UpdateBookmarkSiteReq.category_id

    # 3.按传入字段更新
    if UpdateBookmarkSiteReq.name is not None:
        site.name = UpdateBookmarkSiteReq.name
    if UpdateBookmarkSiteReq.url is not None:
        site.url = UpdateBookmarkSiteReq.url
    if UpdateBookmarkSiteReq.icon is not None:
        site.icon = UpdateBookmarkSiteReq.icon
    if UpdateBookmarkSiteReq.description is not None:
        site.description = UpdateBookmarkSiteReq.description
    if UpdateBookmarkSiteReq.platforms is not None:
        site.platforms = json.dumps(
            UpdateBookmarkSiteReq.platforms, ensure_ascii=False
        )
    if UpdateBookmarkSiteReq.sort is not None:
        site.sort = UpdateBookmarkSiteReq.sort
    site.updated_at = datetime.now()

    # 4.落库
    session.add(site)
    session.commit()
    session.refresh(site)

    # 5.统一结果集返回
    return Result.success(site)


def delete_bookmark_site(session: Session, site_id: int) -> Result:
    """管理员删除收藏站点。

    Args:
        session: 数据库会话，由路由传入。
        site_id: 收藏站点 ID。

    Returns:
        统一结果集。成功时 code=200，message 为「删除成功」。
    """
    # 1.站点必须存在
    site = session.get(BookmarkSite, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="收藏站点不存在")

    # 2.删除并落库
    session.delete(site)
    session.commit()

    # 3.统一结果集返回
    return Result.success(message="删除成功")
