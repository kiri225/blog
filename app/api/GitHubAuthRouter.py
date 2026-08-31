from fastapi import Depends
from fastapi.requests import Request
from fastapi.responses import RedirectResponse
from fastapi.routing import APIRouter
from sqlmodel import Session

from app.Deps import get_session
from app.common.Result import Result
from app.schemas.GitHubAuthSchemas import (
    GitHubDevLoginRequest,
    GitHubDevLoginResponse,
    GitHubUserResponse,
)
from app.service import GitHubAuthService as github_auth_service


router = APIRouter(prefix="/api/auth/github", tags=["GitHub 登录"])


@router.get("/login")
def login() -> RedirectResponse:
    """跳转 GitHub 授权页。

    未配置 GITHUB_CLIENT_ID 则 500。成功时 302 到 GitHub authorize。

    Returns:
        302 RedirectResponse，Location 为 GitHub 授权地址。
    """
    return RedirectResponse(github_auth_service.build_authorize_url(), status_code=302)


@router.get("/callback")
def callback(code: str, session: Session = Depends(get_session)) -> RedirectResponse:
    """GitHub OAuth 回调。

    用 code 换票、落库、签发访客 JWT，再 302 回前端并带 token。

    Args:
        code: GitHub 回调 query 里的授权码（GitHub 固定叫 code）。
        session: 数据库会话，由依赖注入提供。

    Returns:
        302 RedirectResponse，Location 为前端 /auth/callback?token=。
    """
    return RedirectResponse(
        github_auth_service.handle_callback(session, github_authorization=code),
        status_code=302,
    )


@router.get("/me", response_model=Result[GitHubUserResponse])
def me(request: Request, session: Session = Depends(get_session)):
    """获取当前 GitHub 访客资料。

    需 GitHub JWT（不要用管理员 Token）。未登录、过期、用户已删均 401。

    Args:
        request: 当前请求，用来读 Authorization。
        session: 数据库会话，由依赖注入提供。

    Returns:
        统一结果集。成功时 code=200，data 为 GitHubUserResponse
        （id、login、avatar、bio）。
    """
    return github_auth_service.get_github_user(session, request)


@router.post("/dev-login", response_model=Result[GitHubDevLoginResponse])
def dev_login(
    GitHubDevLoginReq: GitHubDevLoginRequest,
    session: Session = Depends(get_session),
):
    """开发用假登录。

    仅当环境变量 DEV_FAKE_GITHUB=1 时可用，生产不要打开。
    按 login 复用或插入测试用户，签发与正式 callback 相同的 GitHub JWT。

    Args:
        GitHubDevLoginReq: 假登录请求体，含 login。
        session: 数据库会话，由依赖注入提供。

    Returns:
        统一结果集。成功时 code=200，data 含 accessToken 与用户资料。
    """
    return github_auth_service.dev_login(session, GitHubDevLoginReq.login)
