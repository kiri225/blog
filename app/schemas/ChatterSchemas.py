from __future__ import annotations

import json
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.schemas.GitHubAuthSchemas import GitHubUserResponse


class ChatterCountResponse(BaseModel):
    """说说计数响应体。"""

    # 说说数量
    count: int


class ChatterLikeResponse(BaseModel):
    """说说点赞响应体。"""

    # 当前点赞数
    likes: int


class CreateChatterRequest(BaseModel):
    """创建说说请求体"""

    # Markdown 正文
    content: str
    # 图片 URL 列表
    images: list[str] = []
    # 心情
    mood: str = ""
    # 状态：draft / published
    status: str = "draft"


class UpdateChatterRequest(BaseModel):
    """更新说说请求体。全部可选。"""

    # Markdown 正文；不传则不改
    content: str | None = None
    # 图片 URL 列表；不传则不改，传 [] 表示清空
    images: list[str] | None = None
    # 心情；不传则不改
    mood: str | None = None
    # 状态：draft / published；不传则不改
    status: str | None = None


class CreateChatterCommentRequest(BaseModel):
    """发表说说评论请求体"""

    # 所属说说
    chatter_id: int
    # 父评论；不传或 null 表示顶层
    parent_id: int | None = None
    # 正文
    content: str


class UpdateChatterCommentStatusRequest(BaseModel):
    """修改说说评论审核状态请求体"""

    # 审核状态：pending / approved / rejected
    status: str


class ChatterResponse(BaseModel):
    """说说响应体。"""

    # 主键
    id: int
    # Markdown 正文
    content: str
    # 图片 URL 列表；库内是 JSON 字符串，读出时转成数组
    images: list[str] = []
    # 心情，空则 ""
    mood: str = ""
    # 点赞数
    likes: int = 0
    # 评论数
    comments_count: int = 0
    # 状态：draft / published
    status: str
    # 创建时间
    created_at: datetime
    # 更新时间
    updated_at: datetime

    @field_validator("images", mode="before")
    @classmethod
    def images_from_json(cls, value: object) -> list[str]:
        if isinstance(value, list):
            return [str(item) for item in value]
        if not isinstance(value, str) or not value:
            return []
        try:
            data = json.loads(value)
        except json.JSONDecodeError:
            return []
        return [str(item) for item in data] if isinstance(data, list) else []


class ChatterCommentResponse(BaseModel):
    """说说评论响应体（含嵌套 replies）。"""

    # 主键
    id: int
    # 所属说说
    chatter_id: int
    # 父评论，顶层为 null
    parent_id: int | None = None
    # 正文
    content: str
    # 点赞数
    likes: int = 0
    # 审核状态：pending / approved / rejected
    status: str
    # 创建时间
    created_at: datetime
    # 评论者；用户已删则为 null
    github_user: GitHubUserResponse | None = None
    # 子回复；顶层按时间降序，回复按时间升序
    replies: list[ChatterCommentResponse] = Field(default_factory=list)


class ChatterCommentAdminResponse(BaseModel):
    """管理端说说评论响应体（含 IP 与嵌套 replies）。"""

    # 主键
    id: int
    # 所属说说
    chatter_id: int
    # 父评论，顶层为 null
    parent_id: int | None = None
    # 正文
    content: str
    # 点赞数
    likes: int = 0
    # 审核状态：pending / approved / rejected
    status: str
    # 评论者 IP；仅管理端返回
    ip: str = ""
    # 创建时间
    created_at: datetime
    # 评论者；用户已删则为 null
    github_user: GitHubUserResponse | None = None
    # 子回复（各状态都带，不只 approved）
    replies: list[ChatterCommentAdminResponse] = Field(default_factory=list)


ChatterCommentResponse.model_rebuild()
ChatterCommentAdminResponse.model_rebuild()
