from datetime import datetime, timedelta, timezone
import bcrypt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

from app.Config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_HOURS

# 从 Authorization: Bearer <token> 取凭证；未带 Token 时 FastAPI 直接 403
security = HTTPBearer()


def hash_password(password: str) -> str:
    """明文密码 → bcrypt 哈希字符串。hashpw 只接受 bytes，入库前 decode。"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """校验明文是否匹配库里的哈希。不要用 == 比明文。"""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def create_token(data: dict) -> str:
    """签发 JWT。payload 至少含 sub / admin，这里补上 exp（默认 72 小时）。"""
    expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    return jwt.encode({**data, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """解析 JWT。签名错误、过期、格式不对一律 401。"""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="无效的令牌")


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """鉴权依赖：取出 Bearer Token 并解码，路由里 Depends 即可拿到 payload。"""
    return decode_token(credentials.credentials)
