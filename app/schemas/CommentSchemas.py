from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.GitHubAuthSchemas import GitHubUserResponse


class CreateCommentRequest(BaseModel):
    """发表评论请求体"""

    # 所属文章
    post_id: int
    # 父评论；不传或 null 表示顶层
    parent_id: int | None = None
    # 正文
    content: str


class UpdateCommentStatusRequest(BaseModel):
    """修改评论审核状态请求体"""

    # 审核状态：pending / approved / rejected
    status: str


class CommentResponse(BaseModel):
    """文章评论响应体（含嵌套 replies）。"""

    # 主键
    id: int
    # 所属文章
    post_id: int
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
    replies: list[CommentResponse] = Field(default_factory=list)


class CommentAdminResponse(BaseModel):
    """管理端评论响应体（含 IP 与嵌套 replies）。"""

    # 主键
    id: int
    # 所属文章
    post_id: int
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
    replies: list[CommentAdminResponse] = Field(default_factory=list)


CommentResponse.model_rebuild()
CommentAdminResponse.model_rebuild()
