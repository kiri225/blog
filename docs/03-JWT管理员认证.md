# 03 — JWT 管理员认证

对照源码：`../app/utils/JWTUtils.py`、`../app/api/AuthRouter.py`、`../app/schemas/AuthSchemas.py`、`../app/Deps.py`

前置：库里已有管理员账号。

---

## 学什么

- Pydantic 请求体：`LoginRequest`
- `HTTPBearer`：从 Header 取 Token
- `Depends` 做鉴权依赖，未登录自动 403/401
- `jose.jwt` 签发与解码
- bcrypt 哈希密码（不要用明文对比）

---

## 任务清单

- [x] `../app/utils/JWTUtils.py`：hash / verify / create_token / decode_token / get_current_user
- [x] `../app/schemas/AuthSchemas.py`：`LoginRequest`、`Token`（Token 可留着不用）
- [x] `../app/Deps.py` 导出 `get_session`、`get_current_user`
- [x] `../app/api/AuthRouter.py`：login / me / update_me
- [x] 在 `router.py` 注册 `auth_router`
- [x] Swagger 里点 Authorize，带 Token 调 `/me`

---

## 工具函数规格

| 函数 | 输入 | 输出 / 行为 |
|------|------|-------------|
| `hash_password(password)` | 明文 | bcrypt hash 字符串 |
| `verify_password(plain, hashed)` | 明文 + hash | bool |
| `create_token(data: dict)` | 如 `{"sub": username, "admin": True}` | JWT，带 `exp`（现在 + 72h） |
| `decode_token(token)` | JWT | payload dict；失败 `HTTPException(401, "无效的令牌")` |
| `get_current_user(credentials)` | `Depends(HTTPBearer())` | decode 后的 payload |

算法：`HS256`，密钥来自 `SECRET_KEY`。

对照实现用的是 `bcrypt` 直接 `hashpw/checkpw`，不是 `passlib` 的 `CryptContext`。两种都可以，验收只要求能验证种子账号。

---

## 接口规格

前缀：`/api/auth`，Swagger tag：`认证`

### POST `/api/auth/login`

鉴权：无

Body：

| 字段 | 类型 | 必填 |
|------|------|------|
| username | string | 是 |
| password | string | 是 |

成功响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "accessToken": "<jwt>",
    "refreshToken": "",
    "expires": "2026-09-02T12:00:00",
    "avatar": "",
    "username": "admin",
    "nickname": "管理员",
    "roles": ["admin"],
    "permissions": ["*:*:*"]
  }
}
```

业务：

- 按 username 查 User，不存在或密码错误 → **401** `用户名或密码错误`（不要区分「用户不存在」和「密码错」，避免被枚举）
- `roles`：`is_admin` 为真则 `["admin"]`，否则 `[]`
- `permissions`：管理员 `["*:*:*"]`，否则 `[]`
- `nickname` 空时回退为 `username`

### GET `/api/auth/me`

鉴权：管理员 JWT

响应同样是 `{code, message, data}`，data 含：`avatar, username, nickname, email, description`（bio 映射成 description）、`phone`（空字符串即可）、`roles, permissions`。

用户不存在 → 404 `用户不存在`

### PUT `/api/auth/me`

鉴权：管理员 JWT

Body：随意 dict，处理这些键（有则更新）：

| 键 | 写到字段 |
|------|----------|
| nickname | nickname |
| email | email |
| bio 或 description | bio |
| avatar | avatar |

更新后写 `updated_at`。成功：`{"code": 0, "message": "更新成功"}`

---

## 如何在后续接口上锁管理员

```python
@router.post("")
def create_xxx(
    data: XxxCreate,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    ...
```

`current_user` 表示「必须带管理员 JWT」。函数里不用 payload 就别读；需要用户名时 `current_user.get("sub")`。

Swagger：点击右上角 **Authorize**，填 `Bearer` 的 token（有的 UI 只填 token 本身，HTTPBearer 会自动加前缀）。

---

## 验收标准

1. 错误密码 → 401
2. 正确密码 → 返回 `accessToken`
3. 不带 Token 调 `/me` → 403 或 401
4. 带 Token 调 `/me` → 返回当前用户
5. PUT `/me` 改 nickname，再 GET `/me` 能看到新昵称
6. 伪造 Token → 401 `无效的令牌`

---

## 易错点

- 种子密码的 hash 必须和 `verify_password` 同一套算法。对照 SQL 里的 hash 是 bcrypt；如果你改用 passlib 的 sha256_crypt，种子账号会登录失败。
- `datetime.utcnow()` 已过时，对照代码仍在用。练习项目可用 `datetime.now(timezone.utc)`，但要保证 jwt `exp` 是 Unix 时间或 datetime，与 `jose` 用法一致。
- `HTTPBearer` 默认不带 Token 是 403 Forbidden，不是 401。这是 Starlette 行为，不要为此纠结。
- 登录响应字段是 **camelCase**（`accessToken`），因为要对齐 Vue 后台。不要改成 snake_case，除非你不接那个后台。

下一阶段：[04-分类与标签.md](./04-分类与标签.md)
