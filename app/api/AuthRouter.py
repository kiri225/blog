from fastapi import Depends
from fastapi.routing import APIRouter
from sqlmodel import Session

from app.Deps import get_session, get_current_user
from app.common.Result import Result
from app.schemas.AuthSchemas import LoginRequest, LoginResponse, UserResponse, UpdateUserInfoRequest
from app.service import AuthService as auth_service


router = APIRouter(prefix="/api/auth", tags=["用户认证模块"])


@router.post("/login", response_model=Result[LoginResponse])
def login(LoginReq: LoginRequest, session: Session = Depends(get_session)):
    """管理员登录。

    校验用户名和密码后签发 JWT。账号不存在与密码错误
    统一返回 401，避免被枚举。

    Args:
        LoginReq: 登录请求体，含 username、password。
        session: 数据库会话，由依赖注入提供。

    Returns:
        统一结果集。成功时 code=200，data 为 LoginResponse
        （accessToken、expires、用户信息、roles、permissions）。
    """
    return auth_service.login(session, LoginReq.username, LoginReq.password)


@router.get("/me", response_model=Result[UserResponse])
def me(user: dict = Depends(get_current_user), session: Session = Depends(get_session)):
    """获取当前用户信息。

    需管理员 JWT。用户已删除则 404。

    Args:
        user: JWT payload，由依赖注入提供。
        session: 数据库会话，由依赖注入提供。

    Returns:
        统一结果集。成功时 code=200，data 为 UserResponse。
    """
    return auth_service.get_user_info(session, user.get("sub"))


@router.put("/me", response_model=Result)
def update_me(
    UpdateUserInfoReq: UpdateUserInfoRequest,
    user: dict = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """更新当前用户资料。

    需管理员 JWT。只更新请求里出现的字段；bio 与 description 都写到 bio。
    用户不存在则 404。

    Args:
        UpdateUserInfoReq: 更新请求体，字段均可选。
        user: JWT payload，由依赖注入提供。
        session: 数据库会话，由依赖注入提供。

    Returns:
        统一结果集。成功时 code=200，message 为「更新成功」。
    """
    return auth_service.update_user_info(session, user.get("sub"), UpdateUserInfoReq)