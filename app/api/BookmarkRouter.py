from fastapi import Depends, Query
from fastapi.routing import APIRouter
from sqlmodel import Session

from app.Deps import get_current_user, get_session
from app.common.Result import Result
from app.schemas.BookmarkSchemas import (
    BookmarkCategoryResponse,
    BookmarkFullResponse,
    BookmarkSiteResponse,
    CreateBookmarkCategoryRequest,
    CreateBookmarkSiteRequest,
    UpdateBookmarkCategoryRequest,
    UpdateBookmarkSiteRequest,
)
from app.service import BookmarkService as bookmark_service


router = APIRouter(prefix="/api/bookmarks", tags=["收藏夹"])


@router.get("", response_model=Result[list[BookmarkFullResponse]])
def list_bookmarks(session: Session = Depends(get_session)):
    """获取收藏夹（分类嵌套站点）。

    公开接口。分类与站点均按 sort 升序。

    Args:
        session: 数据库会话，由依赖注入提供。

    Returns:
        统一结果集。成功时 code=200，data 为分类列表，每项含 sites。
    """
    return bookmark_service.list_bookmarks(session)


@router.get("/categories", response_model=Result[list[BookmarkCategoryResponse]])
def list_bookmark_categories(session: Session = Depends(get_session)):
    """获取收藏分类列表。

    公开接口。不含站点。按 sort 升序。须写在若以后加裸 /{id} 之前。

    Args:
        session: 数据库会话，由依赖注入提供。

    Returns:
        统一结果集。成功时 code=200，data 为分类列表。
    """
    return bookmark_service.list_bookmark_categories(session)


@router.post("/categories", response_model=Result[BookmarkCategoryResponse])
def create_bookmark_category(
    CreateBookmarkCategoryReq: CreateBookmarkCategoryRequest,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """创建收藏分类。

    需管理员 JWT。

    Args:
        CreateBookmarkCategoryReq: 创建收藏分类请求体。
        session: 数据库会话，由依赖注入提供。
        current_user: JWT payload，用来校验已登录；本接口不用里面的字段。

    Returns:
        统一结果集。成功时 code=200，data 为分类。
    """
    return bookmark_service.create_bookmark_category(
        session, CreateBookmarkCategoryReq
    )


@router.put(
    "/categories/{cat_id}", response_model=Result[BookmarkCategoryResponse]
)
def update_bookmark_category(
    cat_id: int,
    UpdateBookmarkCategoryReq: UpdateBookmarkCategoryRequest,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """更新收藏分类。

    需管理员 JWT。全部字段可选。分类不存在则 404。

    Args:
        cat_id: 收藏分类 ID。
        UpdateBookmarkCategoryReq: 更新收藏分类请求体。
        session: 数据库会话，由依赖注入提供。
        current_user: JWT payload，用来校验已登录；本接口不用里面的字段。

    Returns:
        统一结果集。成功时 code=200，data 为分类。
    """
    return bookmark_service.update_bookmark_category(
        session, cat_id, UpdateBookmarkCategoryReq
    )


@router.delete("/categories/{cat_id}", response_model=Result)
def delete_bookmark_category(
    cat_id: int,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """删除收藏分类及其下全部站点。

    需管理员 JWT。分类不存在则 404。级联删除站点。

    Args:
        cat_id: 收藏分类 ID。
        session: 数据库会话，由依赖注入提供。
        current_user: JWT payload，用来校验已登录；本接口不用里面的字段。

    Returns:
        统一结果集。成功时 code=200，message 为「删除成功」。
    """
    return bookmark_service.delete_bookmark_category(session, cat_id)


@router.get("/sites", response_model=Result[list[BookmarkSiteResponse]])
def list_bookmark_sites(
    category_id: int | None = Query(default=None),
    session: Session = Depends(get_session),
):
    """获取收藏站点列表。

    公开接口。可按 category_id 筛选，按 sort 升序。

    Args:
        category_id: 收藏分类 ID，可选。
        session: 数据库会话，由依赖注入提供。

    Returns:
        统一结果集。成功时 code=200，data 为站点列表。
    """
    return bookmark_service.list_bookmark_sites(session, category_id)


@router.post("/sites", response_model=Result[BookmarkSiteResponse])
def create_bookmark_site(
    CreateBookmarkSiteReq: CreateBookmarkSiteRequest,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """创建收藏站点。

    需管理员 JWT。分类不存在则 404。

    Args:
        CreateBookmarkSiteReq: 创建收藏站点请求体。
        session: 数据库会话，由依赖注入提供。
        current_user: JWT payload，用来校验已登录；本接口不用里面的字段。

    Returns:
        统一结果集。成功时 code=200，data 为站点。
    """
    return bookmark_service.create_bookmark_site(session, CreateBookmarkSiteReq)


@router.put("/sites/{site_id}", response_model=Result[BookmarkSiteResponse])
def update_bookmark_site(
    site_id: int,
    UpdateBookmarkSiteReq: UpdateBookmarkSiteRequest,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """更新收藏站点。

    需管理员 JWT。全部字段可选。站点或新分类不存在则 404。

    Args:
        site_id: 收藏站点 ID。
        UpdateBookmarkSiteReq: 更新收藏站点请求体。
        session: 数据库会话，由依赖注入提供。
        current_user: JWT payload，用来校验已登录；本接口不用里面的字段。

    Returns:
        统一结果集。成功时 code=200，data 为站点。
    """
    return bookmark_service.update_bookmark_site(
        session, site_id, UpdateBookmarkSiteReq
    )


@router.delete("/sites/{site_id}", response_model=Result)
def delete_bookmark_site(
    site_id: int,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """删除收藏站点。

    需管理员 JWT。站点不存在则 404。

    Args:
        site_id: 收藏站点 ID。
        session: 数据库会话，由依赖注入提供。
        current_user: JWT payload，用来校验已登录；本接口不用里面的字段。

    Returns:
        统一结果集。成功时 code=200，message 为「删除成功」。
    """
    return bookmark_service.delete_bookmark_site(session, site_id)
