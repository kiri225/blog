from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class PostResponse(BaseModel):
    """文章列表响应体。不含正文。"""

    # 主键
    id: int
    # 标题
    title: str
    # URL 别名
    slug: str
    # 摘要
    description: str = ""
    # 封面图 URL
    cover: str = ""
    # 分类名称；无分类则为空串，不是 category_id
    category: str = ""
    # 标签名称列表
    tags: list[str] = []
    # 状态：draft / published / archived
    status: str
    # 是否置顶
    is_pinned: bool = False
    # 浏览量
    views: int = 0
    # 点赞数
    likes: int = 0
    # 字数
    word_count: int = 0
    # 预计阅读分钟数
    reading_time: int = 0
    # 首次发布时间；草稿为 None
    published_at: datetime | None = None
    # 创建时间
    created_at: datetime
    # 更新时间
    updated_at: datetime


class PostCountResponse(BaseModel):
    """文章计数响应体。"""

    # 文章数量
    count: int


class PostDetailResponse(PostResponse):
    """文章详情响应体。含正文。"""

    # 正文 Markdown
    content: str = ""


class CreatePostRequest(BaseModel):
    """创建文章请求体"""

    # 标题
    title: str
    # URL 别名，全站唯一
    slug: str
    # 摘要
    description: str = ""
    # 正文 Markdown
    content: str = ""
    # 封面图 URL
    cover: str = ""
    # 所属分类 ID；不传则无分类
    category_id: int | None = None
    # 标签名称列表，不是 id
    tags: list[str] = []
    # 状态：draft / published / archived
    status: str = "draft"
    # 是否置顶
    is_pinned: bool = False
    # 预计阅读分钟数；0 表示按正文自动算
    reading_time: int = 0
    # 字数；0 表示按正文自动算
    word_count: int = 0


class UpdatePostRequest(BaseModel):
    """更新文章请求体。全部可选。"""

    # 标题；不传则不改
    title: str | None = None
    # URL 别名，全站唯一；不传则不改
    slug: str | None = None
    # 摘要；不传则不改
    description: str | None = None
    # 正文 Markdown；不传则不改
    content: str | None = None
    # 封面图 URL；不传则不改
    cover: str | None = None
    # 所属分类 ID；不传则不改，传 null 表示去掉分类
    category_id: int | None = None
    # 标签名称列表；不传则不改，传 [] 表示清空
    tags: list[str] | None = None
    # 状态：draft / published / archived；不传则不改
    status: str | None = None
    # 是否置顶；不传则不改
    is_pinned: bool | None = None
    # 预计阅读分钟数；不传则按正文自动算
    reading_time: int | None = None
    # 字数；不传则按正文自动算
    word_count: int | None = None


class PostLikeResponse(BaseModel):
    """点赞响应体。"""

    # 当前点赞数
    likes: int
