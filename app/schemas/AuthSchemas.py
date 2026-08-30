from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    """登录请求体"""
    username: str
    password: str


class LoginResponse(BaseModel):
    """登录响应体。"""

    model_config = ConfigDict(populate_by_name=True)

    access_token: str = Field(serialization_alias="accessToken")
    refresh_token: str = Field(default="", serialization_alias="refreshToken")
    expires: datetime
    avatar: str = ""
    username: str
    nickname: str
    roles: list[str] = []
    permissions: list[str] = []


class UserResponse(BaseModel):
    """当前用户响应体。"""

    avatar: str = ""
    username: str
    nickname: str
    email: str = ""
    description: str = ""  # 对应表字段 bio
    phone: str = ""
    roles: list[str] = []
    permissions: list[str] = []


class UpdateUserInfoRequest(BaseModel):
    """更新当前用户请求体"""
    nickname: str | None = None
    email: str | None = None
    bio: str | None = None
    description: str | None = None
    avatar: str | None = None
