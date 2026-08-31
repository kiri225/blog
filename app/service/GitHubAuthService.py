from urllib.parse import urlencode

import requests
from fastapi import HTTPException
from fastapi.requests import Request
from sqlmodel import Session, select

from app.Config import (
    DEV_FAKE_GITHUB,
    FRONTEND_ORIGIN,
    GITHUB_CLIENT_ID,
    GITHUB_CLIENT_SECRET,
)
from app.common.Result import Result
from app.models.GitHubUser import GitHubUser
from app.schemas.GitHubAuthSchemas import GitHubDevLoginResponse, GitHubUserResponse
from app.utils.JWTUtils import create_token, decode_github_token, try_decode_github_token
# GitHub API 地址
_GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
# GitHub OAuth 获取 access_token 地址
_GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
# GitHub API 获取用户信息地址
_GITHUB_USER_URL = "https://api.github.com/user"
# 请求超时时间
_HTTP_TIMEOUT = 10
# GitHub API 请求头
_GITHUB_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "kiri-blog",
}


def get_github_user_optional(request: Request, session: Session) -> GitHubUser | None:
    """解析 GitHub JWT。没有 Bearer 或解码失败返回 None，不抛错。

    Args:
        request: 当前请求，用来读 Authorization。
        session: 数据库会话。

    Returns:
        本地 GitHubUser；未登录或 Token 无效时为 None。
    """
    # 1.取出 Bearer Token
    authorization = request.headers.get("Authorization")
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization[7:].strip()
    if not token:
        return None

    # 2.解析 GitHub JWT
    payload = try_decode_github_token(token)
    if not payload:
        return None
    try:
        user_id = int(payload.get("sub"))
    except (TypeError, ValueError):
        return None

    # 3.按本地主键查用户
    return session.get(GitHubUser, user_id)


def _issue_github_token(github_user: GitHubUser) -> str:
    """签发访客 JWT。sub 是本地主键，不是 github_id。"""
    return create_token(
        {"sub": str(github_user.id), "login": github_user.login, "type": "github"}
    )


def build_authorize_url() -> str:
    """拼 GitHub 授权地址。未配置 client_id 则 500。

    Returns:
        GitHub authorize URL。
    """
    # 1.检查 client_id
    if not GITHUB_CLIENT_ID:
        raise HTTPException(status_code=500, detail="未配置 GITHUB_CLIENT_ID")

    # 2.拼授权 URL
    return f"{_GITHUB_AUTHORIZE_URL}?client_id={GITHUB_CLIENT_ID}&scope=read:user"


def handle_callback(session: Session, github_authorization: str) -> str:
    """用授权码换票、落库、签发 JWT，返回前端回调地址。

    Args:
        session: 数据库会话，由路由传入。
        github_authorization: GitHub 下发的一次性授权码（query 名是 code）。

    Returns:
        前端地址 `{FRONTEND_ORIGIN}/auth/callback?token=`。
    """
    # 1.用 GitHub 授权码换 access_token
    try:
        token_res = requests.post(
            _GITHUB_TOKEN_URL,
            json={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": github_authorization,
            },
            headers=_GITHUB_HEADERS,
            timeout=_HTTP_TIMEOUT,
        )
        access_token = token_res.json().get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="GitHub 授权失败")

        # 2.拉 GitHub 用户信息
        user_info_req = requests.get(
            # GitHub API 获取用户信息地址
            _GITHUB_USER_URL,
            # 请求头
            headers={
                # 请求头
                **_GITHUB_HEADERS,
                # 授权头
                "Authorization": f"Bearer {access_token}",
            },
            # 请求超时时间
            timeout=_HTTP_TIMEOUT,
        )
        # 如果响应状态码不为 200，则抛出异常
        if user_info_req.status_code != 200:
            # 获取错误信息
            raise HTTPException(status_code=400, detail="获取 GitHub 用户信息失败")
        # 获取用户信息
        user_info_data = user_info_req.json()
    except HTTPException:
        raise
    except (requests.RequestException, ValueError):
        raise HTTPException(status_code=400, detail="GitHub 授权失败")

    # 3.获取 GitHub ID
    github_id = user_info_data.get("id")
    # 如果 GitHub ID 为空，则抛出异常
    if github_id is None:
        raise HTTPException(status_code=400, detail="获取 GitHub 用户信息失败")

    # 4.按 github_id 查表，存在则更新 login/avatar/bio，不存在则插入
    db_user = session.exec(select(GitHubUser).where(GitHubUser.github_id == github_id)).first()
    # 5.获取登录名
    login = user_info_data.get("login") or ""
    # 6.获取头像
    avatar = user_info_data.get("avatar_url") or ""
    # 7.获取简介
    bio = user_info_data.get("bio") or ""
    # 8.如果用户存在，则更新登录名/头像/简介
    if db_user:
        db_user.login = login
        db_user.avatar = avatar
        db_user.bio = bio
    # 9.如果用户不存在，则插入
    else:
        db_user = GitHubUser(github_id=github_id, login=login, avatar=avatar, bio=bio)
        session.add(db_user)
    session.commit()
    session.refresh(db_user)

    # 10.签发 JWT（sub 为本地主键）
    token = _issue_github_token(db_user)

    # 11.拼前端回调地址
    query = urlencode({"token": token})
    # 12.返回前端回调地址
    return f"{FRONTEND_ORIGIN}/auth/callback?{query}"


def get_github_user(session: Session, request: Request) -> Result:
    """取当前 GitHub 访客资料。

    Args:
        session: 数据库会话，由路由传入。
        request: 当前请求，只用来读 Authorization。

    Returns:
        统一结果集。成功时 code=200，data 为 GitHubUserResponse。
    """
    # 1.取出 Bearer Token
    authorization = request.headers.get("Authorization")
    # 没有 Header，或不是「Bearer 」开头
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录")
    # 「Bearer 」后面才是 JWT，去掉首尾空格
    token = authorization[7:].strip()
    # 前缀有了但后面是空串
    if not token:
        raise HTTPException(status_code=401, detail="未登录")

    # 2.解析 GitHub JWT（过期会 401「登录已过期，请重新登录」；管理员 Token 或签名不对会 401「未登录」）
    payload = decode_github_token(token)
    # sub 必须是本地 github_user.id 的数字字符串
    try:
        user_id = int(payload.get("sub"))
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="未登录")

    # 3.按本地主键查用户
    github_user = session.get(GitHubUser, user_id)
    # Token 有效但库里已经删了这条访客
    if not github_user:
        raise HTTPException(status_code=401, detail="用户不存在")

    # 4.统一结果集返回
    return Result.success(
        GitHubUserResponse(
            id=github_user.id,
            login=github_user.login,
            avatar=github_user.avatar or "",
            bio=github_user.bio or "",
        )
    )


def dev_login(session: Session, login: str) -> Result:
    """开发假登录：插入或复用测试用户并签发 GitHub JWT。

    Args:
        session: 数据库会话，由路由传入。
        login: 测试用 GitHub 用户名。

    Returns:
        统一结果集。成功时 code=200，data 含 accessToken 与用户资料。
    """
    # 1.仅开发环境可用
    if not DEV_FAKE_GITHUB:
        raise HTTPException(status_code=404, detail="开发假登录未开启")

    # 2.按 login 查测试用户
    github_user = session.exec(
        select(GitHubUser).where(GitHubUser.login == login)
    ).first()

    # 3.没有则插入（github_id 为 0 或负数）
    if not github_user:
        min_github_id = session.exec(
            select(GitHubUser.github_id).order_by(GitHubUser.github_id)
        ).first()
        fake_github_id = (
            0 if min_github_id is None or min_github_id > 0 else min_github_id - 1
        )
        github_user = GitHubUser(
            github_id=fake_github_id,
            login=login,
            avatar="",
            bio="",
        )
        session.add(github_user)
        session.commit()
        session.refresh(github_user)

    # 4.签发 GitHub 类型 JWT
    token = _issue_github_token(github_user)

    # 5.统一结果集返回
    return Result.success(
        GitHubDevLoginResponse(
            access_token=token,
            id=github_user.id,
            login=github_user.login,
            avatar=github_user.avatar or "",
            bio=github_user.bio or "",
        )
    )
