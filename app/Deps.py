"""公共依赖 — 统一从这里导入 get_session / get_current_user"""

from app.Database import get_session
from app.service.GitHubAuthService import get_github_user_optional
from app.utils.JWTUtils import get_current_user
