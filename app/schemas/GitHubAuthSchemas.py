from pydantic import BaseModel, ConfigDict, Field


class GitHubUserResponse(BaseModel):
    """当前 GitHub 访客响应体。"""

    # 本地表主键，不是 github_id
    id: int
    # GitHub 用户名
    login: str
    # 头像 URL
    avatar: str = ""
    # 简介
    bio: str = ""


class GitHubDevLoginRequest(BaseModel):
    """开发假登录请求体"""

    # GitHub 用户名（测试用，不走 OAuth）
    login: str


class GitHubDevLoginResponse(BaseModel):
    """开发假登录响应体。"""

    # JSON 用 camelCase，对齐认证模块的 accessToken
    model_config = ConfigDict(populate_by_name=True)

    # 访问令牌；JSON 字段 accessToken
    access_token: str = Field(serialization_alias="accessToken")
    # 本地表主键
    id: int
    # GitHub 用户名
    login: str
    # 头像 URL
    avatar: str = ""
    # 简介
    bio: str = ""
