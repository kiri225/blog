from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    """登录请求体"""

    # 用户名
    username: str
    # 密码
    password: str


class LoginResponse(BaseModel):
    """登录响应体。"""

    # JSON 用 camelCase，对齐管理后台
    model_config = ConfigDict(populate_by_name=True)

    # 访问令牌；JSON 字段 accessToken
    access_token: str = Field(serialization_alias="accessToken")
    # 刷新令牌，暂未实现；JSON 字段 refreshToken
    refresh_token: str = Field(default="", serialization_alias="refreshToken")
    # 过期时间
    expires: datetime
    # 头像
    avatar: str = ""
    # 用户名
    username: str
    # 昵称
    nickname: str
    # 角色
    roles: list[str] = []
    # 权限
    permissions: list[str] = []


class UserResponse(BaseModel):
    """当前用户响应体。"""

    # 头像
    avatar: str = ""
    # 用户名
    username: str
    # 昵称
    nickname: str
    # 邮箱
    email: str = ""
    # 简介；对应表字段 bio
    description: str = ""
    # 手机号，用户表暂无此列，固定空串
    phone: str = ""
    # 角色
    roles: list[str] = []
    # 权限
    permissions: list[str] = []


class UpdateUserInfoRequest(BaseModel):
    """更新当前用户请求体"""

    # 昵称
    nickname: str | None = None
    # 邮箱
    email: str | None = None
    # 简介；与 description 都写到表字段 bio
    bio: str | None = None
    # 简介别名，与 bio 同义
    description: str | None = None
    # 头像
    avatar: str | None = None
