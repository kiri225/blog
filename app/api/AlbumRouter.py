from fastapi import Depends
from fastapi.routing import APIRouter
from sqlmodel import Session

from app.Deps import get_current_user, get_session
from app.common.Result import Result
from app.schemas.AlbumSchemas import (
    AlbumResponse,
    CreateAlbumRequest,
    CreatePhotoRequest,
    PhotoResponse,
    UpdateAlbumRequest,
)
from app.service import AlbumService as album_service


router = APIRouter(prefix="/api/albums", tags=["相册模块"])


@router.get("", response_model=Result[list[AlbumResponse]])
def list_albums(session: Session = Depends(get_session)):
    """获取相册列表。

    公开接口。按 sort 升序返回全部相册。

    Args:
        session: 数据库会话，由依赖注入提供。

    Returns:
        统一结果集。成功时 code=200，data 为相册列表。
    """
    return album_service.list_albums(session)


@router.post("", response_model=Result[AlbumResponse])
def create_album(
    CreateAlbumReq: CreateAlbumRequest,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """创建相册。

    需管理员 JWT。

    Args:
        CreateAlbumReq: 创建相册请求体。
        session: 数据库会话，由依赖注入提供。
        current_user: JWT payload，用来校验已登录；本接口不用里面的字段。

    Returns:
        统一结果集。成功时 code=200，data 为相册。
    """
    return album_service.create_album(session, CreateAlbumReq)


@router.post("/photos", response_model=Result[PhotoResponse])
def create_photo(
    CreatePhotoReq: CreatePhotoRequest,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """向相册添加一张照片。

    需管理员 JWT。url 为上传接口返回的地址。相册不存在则 404。
    须写在裸 /{album_id} 之前。

    Args:
        CreatePhotoReq: 添加照片请求体。
        session: 数据库会话，由依赖注入提供。
        current_user: JWT payload，用来校验已登录；本接口不用里面的字段。

    Returns:
        统一结果集。成功时 code=200，data 为照片。
    """
    return album_service.create_photo(session, CreatePhotoReq)


@router.delete("/photos/{photo_id}", response_model=Result)
def delete_photo(
    photo_id: int,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """删除一张照片。

    需管理员 JWT。会回减所属相册 photo_count。照片不存在则 404。
    须写在裸 /{album_id} 之前。

    Args:
        photo_id: 照片 ID。
        session: 数据库会话，由依赖注入提供。
        current_user: JWT payload，用来校验已登录；本接口不用里面的字段。

    Returns:
        统一结果集。成功时 code=200，message 为「删除成功」。
    """
    return album_service.delete_photo(session, photo_id)


@router.get(
    "/{album_id}/photos",
    response_model=Result[list[PhotoResponse]],
)
def get_album_photos(album_id: int, session: Session = Depends(get_session)):
    """按相册获取照片列表。

    公开接口。按 sort 升序。相册不存在则 404。须写在裸 /{album_id} 之前。

    Args:
        album_id: 相册 ID。
        session: 数据库会话，由依赖注入提供。

    Returns:
        统一结果集。成功时 code=200，data 为照片列表。
    """
    return album_service.get_album_photos(session, album_id)


@router.get("/{album_id}", response_model=Result[AlbumResponse])
def get_album(album_id: int, session: Session = Depends(get_session)):
    """按 ID 获取相册详情。

    公开接口。不存在则 404。

    Args:
        album_id: 相册 ID。
        session: 数据库会话，由依赖注入提供。

    Returns:
        统一结果集。成功时 code=200，data 为相册。
    """
    return album_service.get_album_by_id(session, album_id)


@router.put("/{album_id}", response_model=Result[AlbumResponse])
def update_album(
    album_id: int,
    UpdateAlbumReq: UpdateAlbumRequest,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """更新相册。

    需管理员 JWT。全部字段可选。相册不存在则 404。

    Args:
        album_id: 相册 ID。
        UpdateAlbumReq: 更新相册请求体。
        session: 数据库会话，由依赖注入提供。
        current_user: JWT payload，用来校验已登录；本接口不用里面的字段。

    Returns:
        统一结果集。成功时 code=200，data 为相册。
    """
    return album_service.update_album(session, album_id, UpdateAlbumReq)


@router.delete("/{album_id}", response_model=Result)
def delete_album(
    album_id: int,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """删除相册。

    需管理员 JWT。会先删该相册下全部照片再删自身。相册不存在则 404。

    Args:
        album_id: 相册 ID。
        session: 数据库会话，由依赖注入提供。
        current_user: JWT payload，用来校验已登录；本接口不用里面的字段。

    Returns:
        统一结果集。成功时 code=200，message 为「删除成功」。
    """
    return album_service.delete_album(session, album_id)
