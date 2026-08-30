from __future__ import annotations

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class User(SQLModel, table=True):
    """管理员账号。表名由类名小写得到，即 user（PostgreSQL 保留字，建表时需加引号）。"""

    # 主键，自增；写入时不传，由数据库生成
    id: Optional[int] = Field(default=None, primary_key=True)
    # 登录用户名，唯一
    username: str = Field(max_length=50, unique=True, index=True)
    # 密码哈希，禁止存明文
    hashed_password: str = Field(max_length=128)
    # 昵称，展示用
    nickname: str = Field(default="", max_length=50)
    # 头像 URL
    avatar: str = Field(default="", max_length=500)
    # 邮箱
    email: str = Field(default="", max_length=100)
    # 个人简介
    bio: str = Field(default="", max_length=500)
    # 是否管理员；后台写操作依赖此字段
    is_admin: bool = Field(default=False)
    # 创建时间
    created_at: datetime = Field(default_factory=datetime.now)
    # 更新时间
    updated_at: datetime = Field(default_factory=datetime.now)
