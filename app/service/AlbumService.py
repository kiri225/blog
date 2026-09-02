from datetime import datetime

from fastapi import HTTPException
from sqlmodel import Session, func, select

from app.common.Result import Result
from app.models.Album import Album
from app.models.Photo import Photo
from app.schemas.AlbumSchemas import (
    CreateAlbumRequest,
    CreatePhotoRequest,
    UpdateAlbumRequest,
)

_ALLOWED_ORIENTATION = {"landscape", "portrait"}


def _recount_photos(session: Session, album: Album) -> None:
    """按 photo 表实际条数回写 album.photo_count，避免增减不同步。"""
    count = session.exec(
        select(func.count(Photo.id)).where(Photo.album_id == album.id)
    ).one()
    album.photo_count = int(count or 0)
    album.updated_at = datetime.now()
    session.add(album)


def list_albums(session: Session) -> Result:
    """按 sort 升序返回全部相册。

    Args:
        session: 数据库会话，由路由传入。

    Returns:
        统一结果集。成功时 code=200，data 为相册列表。
    """
    # 1.按 sort 升序查询
    rows = list(session.exec(select(Album).order_by(Album.sort)).all())

    # 2.统一结果集返回
    return Result.success(rows)


def get_album_by_id(session: Session, album_id: int) -> Result:
    """按主键取相册详情。

    Args:
        session: 数据库会话，由路由传入。
        album_id: 相册 ID。

    Returns:
        统一结果集。成功时 code=200，data 为相册。
    """
    # 1.按主键取相册
    album = session.get(Album, album_id)
    if not album:
        raise HTTPException(status_code=404, detail="相册不存在")

    # 2.统一结果集返回
    return Result.success(album)


def get_album_photos(session: Session, album_id: int) -> Result:
    """按相册取照片列表，按 sort 升序。

    Args:
        session: 数据库会话，由路由传入。
        album_id: 相册 ID。

    Returns:
        统一结果集。成功时 code=200，data 为照片列表。
    """
    # 1.相册必须存在
    album = session.get(Album, album_id)
    if not album:
        raise HTTPException(status_code=404, detail="相册不存在")

    # 2.按 sort 升序查该相册照片
    rows = list(
        session.exec(
            select(Photo)
            .where(Photo.album_id == album_id)
            .order_by(Photo.sort)
        ).all()
    )

    # 3.统一结果集返回
    return Result.success(rows)


def create_album(session: Session, CreateAlbumReq: CreateAlbumRequest) -> Result:
    """管理员创建相册。

    Args:
        session: 数据库会话，由路由传入。
        CreateAlbumReq: 创建相册请求体。

    Returns:
        统一结果集。成功时 code=200，data 为相册。
    """
    # 1.落库
    album = Album(
        title=CreateAlbumReq.title,
        description=CreateAlbumReq.description or "",
        cover=CreateAlbumReq.cover or "",
        sort=CreateAlbumReq.sort,
    )
    session.add(album)
    session.commit()
    session.refresh(album)

    # 2.统一结果集返回
    return Result.success(album)


def update_album(
    session: Session, album_id: int, UpdateAlbumReq: UpdateAlbumRequest
) -> Result:
    """管理员更新相册。只改传入字段。

    Args:
        session: 数据库会话，由路由传入。
        album_id: 相册 ID。
        UpdateAlbumReq: 更新相册请求体。

    Returns:
        统一结果集。成功时 code=200，data 为相册。
    """
    # 1.相册必须存在
    album = session.get(Album, album_id)
    if not album:
        raise HTTPException(status_code=404, detail="相册不存在")

    # 2.按传入字段更新
    if UpdateAlbumReq.title is not None:
        album.title = UpdateAlbumReq.title
    if UpdateAlbumReq.description is not None:
        album.description = UpdateAlbumReq.description
    if UpdateAlbumReq.cover is not None:
        album.cover = UpdateAlbumReq.cover
    if UpdateAlbumReq.sort is not None:
        album.sort = UpdateAlbumReq.sort
    album.updated_at = datetime.now()

    # 3.落库
    session.add(album)
    session.commit()
    session.refresh(album)

    # 4.统一结果集返回
    return Result.success(album)


def delete_album(session: Session, album_id: int) -> Result:
    """管理员删除相册。先删该相册下全部照片再删相册。

    Args:
        session: 数据库会话，由路由传入。
        album_id: 相册 ID。

    Returns:
        统一结果集。成功时 code=200，message 为「删除成功」。
    """
    # 1.相册必须存在
    album = session.get(Album, album_id)
    if not album:
        raise HTTPException(status_code=404, detail="相册不存在")

    # 2.先删该相册下全部照片
    photos = list(
        session.exec(select(Photo).where(Photo.album_id == album_id)).all()
    )
    for photo in photos:
        session.delete(photo)

    # 3.删除相册并落库
    session.delete(album)
    session.commit()

    # 4.统一结果集返回
    return Result.success(message="删除成功")


def create_photo(session: Session, CreatePhotoReq: CreatePhotoRequest) -> Result:
    """管理员向相册添加一张照片。成功后相册 photo_count +1。

    Args:
        session: 数据库会话，由路由传入。
        CreatePhotoReq: 添加照片请求体。

    Returns:
        统一结果集。成功时 code=200，data 为照片。
    """
    # 1.校验 orientation
    if CreatePhotoReq.orientation not in _ALLOWED_ORIENTATION:
        raise HTTPException(status_code=400, detail="方向不合法")

    # 2.相册必须存在
    album = session.get(Album, CreatePhotoReq.album_id)
    if not album:
        raise HTTPException(status_code=404, detail="相册不存在")

    # 3.落库，并按实际条数回写 photo_count
    photo = Photo(
        album_id=CreatePhotoReq.album_id,
        url=CreatePhotoReq.url,
        caption=CreatePhotoReq.caption or "",
        orientation=CreatePhotoReq.orientation,
        sort=CreatePhotoReq.sort,
    )
    session.add(photo)
    session.flush()
    _recount_photos(session, album)
    session.commit()
    session.refresh(photo)

    # 4.统一结果集返回
    return Result.success(photo)


def delete_photo(session: Session, photo_id: int) -> Result:
    """管理员删除一张照片。相册 photo_count 按 1 回减（最小 0）。

    Args:
        session: 数据库会话，由路由传入。
        photo_id: 照片 ID。

    Returns:
        统一结果集。成功时 code=200，message 为「删除成功」。
    """
    # 1.照片必须存在
    photo = session.get(Photo, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="照片不存在")

    album_id = photo.album_id

    # 2.删除照片
    session.delete(photo)
    session.flush()

    # 3.按实际条数回写 photo_count
    album = session.get(Album, album_id)
    if album:
        _recount_photos(session, album)

    session.commit()

    # 4.统一结果集返回
    return Result.success(message="删除成功")
