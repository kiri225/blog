from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from sqlmodel import Session, select
from app.Config import ACCESS_TOKEN_EXPIRE_HOURS
from app.common.Result import Result
from app.models.User import User
from app.schemas.AuthSchemas import LoginResponse, UserResponse, UpdateUserInfoRequest
from app.utils.JWTUtils import create_token, verify_password


def login(session: Session, username: str, password: str) -> Result:
    """校验账号密码并签发 JWT。
    
    Args:
        session: 数据库会话，由依赖注入提供。
        username: 用户名。
        password: 密码。

    Returns:
        统一结果集。成功时 code=200，data 为 LoginResponse。
    """
    # 1.查询账号
    user = session.exec(select(User).where(User.username == username)).first()

    # 2.校验账号密码
    if not user or not verify_password(password, user.hashed_password):
        # 统一结果集返回
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 3.签发 JWT
    token = create_token({"sub": user.username, "admin": user.is_admin})

    # 4.设置过期时间
    expires = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)

    # 5.统一结果集返回
    return Result.success(
        LoginResponse(
            access_token=token,
            expires=expires,
            avatar=user.avatar or "",
            username=user.username,
            nickname=user.nickname or user.username,
            roles=["admin"] if user.is_admin else [],
            permissions=["*:*:*"] if user.is_admin else [],
        )
    )

def get_user_info(session: Session, username: str) -> Result:
    """按 JWT 中的用户名取当前用户资料。

    Args:
        session: 数据库会话，由路由传入。
        username: JWT payload 的 sub。

    Returns:
        统一结果集。成功时 code=200，data 为 UserResponse。
    """
    # 1.查询用户
    user_info = session.exec(select(User).where(User.username == username)).first()
    if not user_info:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 2.统一结果集返回
    return Result.success(
        UserResponse(
            avatar=user_info.avatar or "",
            username=user_info.username,
            nickname=user_info.nickname or user_info.username,
            email=user_info.email or "",
            description=user_info.bio or "",
            phone="",
            roles=["admin"] if user_info.is_admin else [],
            permissions=["*:*:*"] if user_info.is_admin else [],
        )
    )


def update_user_info(session: Session, username: str, data: UpdateUserInfoRequest) -> Result:
    """按传入字段更新当前用户资料。

    Args:
        session: 数据库会话，由路由传入。
        username: JWT payload 的 sub。
        data: 要更新的字段，未传的键不改。

    Returns:
        统一结果集。成功时 code=200，message 为「更新成功」。
    """
    # 1.查询用户
    user_info = session.exec(select(User).where(User.username == username)).first()
    if not user_info:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 2.按传入字段更新
    payload = data.model_dump(exclude_unset=True)
    # 2.1 更新昵称
    if "nickname" in payload:
        user_info.nickname = payload["nickname"]
    # 2.2 更新邮箱
    if "email" in payload:
        user_info.email = payload["email"]
    # 2.3 更新简介
    if "bio" in payload or "description" in payload:
        user_info.bio = payload.get("bio") or payload.get("description") or ""
    # 2.4 更新头像
    if "avatar" in payload:
        user_info.avatar = payload["avatar"]

    # 3.落库
    user_info.updated_at = datetime.now()
    session.add(user_info)
    session.commit()
    session.refresh(user_info)

    # 4.统一结果集返回
    return Result.success(message="更新成功")