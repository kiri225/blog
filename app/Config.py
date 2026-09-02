import os
from pathlib import Path
from dotenv import load_dotenv
# 项目根目录（app/ 的上一级），用于定位 .env
BASE_DIR = Path(__file__).resolve().parent.parent
# 本地上传目录；main 挂载为 /uploads
UPLOADS_DIR = BASE_DIR / "uploads"
# 读取 .env；override=True 表示环境变量已存在时仍以文件为准
load_dotenv(BASE_DIR / ".env", override=True)

# 数据库连接串（SQLAlchemy 格式，如 postgresql+psycopg://...）
DATABASE_URL = os.environ["DATABASE_URL"]
# JWT 签名密钥，生产环境必须足够随机、保密
SECRET_KEY = os.environ["SECRET_KEY"]
# JWT 签名算法
ALGORITHM = "HS256"
# Access Token 过期时间（小时），管理员与访客共用
ACCESS_TOKEN_EXPIRE_HOURS = 72

# 允许跨域的前端来源，逗号分隔后拆成 list
_cors = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8848,http://127.0.0.1:8848,http://localhost:5173",
)
CORS_ORIGINS = [o.strip() for o in _cors.split(",") if o.strip()]

# GitHub OAuth（访客登录；未配置时为空字符串，相关接口不可用）
GITHUB_CLIENT_ID = os.environ.get("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET", "")
# OAuth 成功后 302 回去的前端源，练习默认本机
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000").rstrip("/")
# 仅开发：为 "1" 时开放 POST /api/auth/github/dev-login，生产不要开
DEV_FAKE_GITHUB = os.getenv("DEV_FAKE_GITHUB", "") == "1"

# 阿里云 OSS：上传图片等静态资源
OSS_ACCESS_KEY_ID = os.environ["OSS_ACCESS_KEY_ID"]
OSS_ACCESS_KEY_SECRET = os.environ["OSS_ACCESS_KEY_SECRET"]
OSS_BUCKET_NAME = os.environ["OSS_BUCKET_NAME"]
OSS_ENDPOINT = os.environ["OSS_ENDPOINT"]
# 自定义访问域名（CDN / 绑定域名），拼资源 URL 时用
OSS_CUSTOM_DOMAIN = os.environ["OSS_CUSTOM_DOMAIN"]
# 对象 key 前缀，用于按目录隔离（如 blog/）
OSS_PREFIX = os.environ["OSS_PREFIX"]

