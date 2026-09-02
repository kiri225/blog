from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.GitHubAuthSchemas import GitHubUserResponse


class CreateMessageRequest(BaseModel):
    """发表留言请求体"""

    # 正文
    content: str
    # 父留言；不传或 null 表示顶层
    parent_id: int | None = None


class UpdateMessageStatusRequest(BaseModel):
    """修改留言审核状态请求体"""

    # 审核状态：pending / approved / rejected
    status: str


class MessageCountResponse(BaseModel):
    """留言计数响应体。"""

    # 顶层留言数量（公开接口仅已审核；管理端可按 status 筛选）
    count: int


class MessageResponse(BaseModel):
    """留言响应体（含 IP 与嵌套 replies）。"""

    # 主键
    id: int
    # 留言者本地主键；用户已删可为 null
    github_user_id: int | None = None
    # 父留言，顶层为 null
    parent_id: int | None = None
    # 正文
    content: str
    # 留言者 IP；前台可忽略不展示
    ip: str = ""
    # 审核状态：pending / approved / rejected
    status: str
    # 点赞数
    likes: int = 0
    # 创建时间
    created_at: datetime
    # 留言者；用户已删则为 null
    github_user: GitHubUserResponse | None = None
    # 子回复
    replies: list[MessageResponse] = Field(default_factory=list)


MessageResponse.model_rebuild()
