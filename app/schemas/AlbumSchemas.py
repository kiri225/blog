from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class CreateAlbumRequest(BaseModel):
    """创建相册请求体"""

    # 标题
    title: str
    # 描述
    description: str = ""
    # 封面图 URL
    cover: str = ""
    # 排序，越小越靠前
    sort: int = 0


class UpdateAlbumRequest(BaseModel):
    """更新相册请求体。全部可选。"""

    # 标题；不传则不改
    title: str | None = None
    # 描述；不传则不改
    description: str | None = None
    # 封面图 URL；不传则不改，传 "" 表示清空
    cover: str | None = None
    # 排序，越小越靠前；不传则不改
    sort: int | None = None


class CreatePhotoRequest(BaseModel):
    """添加相册照片请求体"""

    # 所属相册
    album_id: int
    # 图片 URL，来自上传接口
    url: str
    # 说明
    caption: str = ""
    # 方向：landscape / portrait
    orientation: str = "landscape"
    # 排序，越小越靠前
    sort: int = 0


class AlbumResponse(BaseModel):
    """相册响应体。"""

    # 主键
    id: int
    # 标题
    title: str
    # 描述，空则 ""
    description: str = ""
    # 封面图 URL，空则 ""
    cover: str = ""
    # 照片数量
    photo_count: int = 0
    # 排序
    sort: int = 0
    # 创建时间
    created_at: datetime
    # 更新时间
    updated_at: datetime


class PhotoResponse(BaseModel):
    """相册照片响应体。"""

    # 主键
    id: int
    # 所属相册
    album_id: int
    # 图片 URL
    url: str
    # 说明，空则 ""
    caption: str = ""
    # 方向：landscape / portrait
    orientation: str
    # 排序
    sort: int = 0
    # 创建时间
    created_at: datetime
