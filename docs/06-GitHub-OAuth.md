# 06 — GitHub OAuth（访客登录）

对照源码：`app/api/github_auth.py`、`app/models/github_user.py`

前置：管理员 JWT 已完成。本阶段给「前台评论者」做另一套登录。

没有 GitHub OAuth App 时，本阶段可以：

1. 仍建好 `github_user` 表和 `/me`、解析函数；
2. 写一个 **仅开发用** 的假登录接口，插入测试用户并签发 GitHub 类型 JWT；
3. 正式 callback 等有 client_id 再接。

不要用管理员 Token 冒充 GitHub 用户。

---

## 学什么

- `RedirectResponse`：接口不返回 JSON，而是 302 跳走
- 用 `httpx` 调外部 API（换 token、拉用户信息）
- OAuth 授权码模式：redirect → code → access_token → user
- 可选鉴权：Header 没有 Bearer 时返回 `None`，有则解析
- 同一 `SECRET_KEY` 签两种 payload，用 `type` 字段区分

---

## 任务清单

- [ ] Model：`GitHubUser`
- [ ] 环境变量：`GITHUB_CLIENT_ID`、`GITHUB_CLIENT_SECRET`、`FRONTEND_ORIGIN`
- [ ] `GET /api/auth/github/login` 跳转 GitHub
- [ ] `GET /api/auth/github/callback?code=` 换票、落库、签 JWT、跳回前端
- [ ] `GET /api/auth/github/me` 返回当前 GitHub 用户
- [ ] 实现 `_get_github_user` 与 `get_github_user_optional`，供阶段 07 使用
- [ ] （可选）开发用假登录

---

## 数据模型 GitHubUser

| 字段 | 类型 | 约束 |
|------|------|------|
| id | int | PK |
| github_id | int | unique, index（GitHub 的数字 id） |
| login | str(100) | GitHub 用户名 |
| avatar | str(500) | |
| bio | str(500) | |
| created_at | datetime | |

---

## 接口规格

前缀：`/api/auth/github`，tag：`GitHub 登录`

### GET `/api/auth/github/login`

鉴权：无

未配置 `GITHUB_CLIENT_ID` → 500 `未配置 GITHUB_CLIENT_ID`

否则 302 到：

```
https://github.com/login/oauth/authorize?client_id={CLIENT_ID}&scope=read:user
```

在 GitHub OAuth App 里把 Authorization callback URL 设为：

```
http://localhost:8000/api/auth/github/callback
```

### GET `/api/auth/github/callback`

Query：`code: str`（GitHub 带回）

步骤：

1. `POST https://github.com/login/oauth/access_token`  
   JSON：`client_id, client_secret, code`  
   Header：`Accept: application/json`  
   取 `access_token`，没有 → 400 `GitHub 授权失败`
2. `GET https://api.github.com/user`，Header `Authorization: Bearer <access_token>`  
   非 200 → 400 `获取 GitHub 用户信息失败`
3. 用 `gh_user["id"]` 查表。存在则更新 login/avatar/bio；不存在则插入
4. 签发 JWT：
   ```python
   {"sub": str(db_user.id), "login": db_user.login, "type": "github"}
   ```
   注意：`sub` 是 **本地表主键**，不是 github_id
5. 302 到 `{FRONTEND_ORIGIN}/auth/callback?token={jwt}`

`FRONTEND_ORIGIN` 默认对照是 `https://boke.hiromu.top`，练习请设成 `http://localhost:3000`。

### GET `/api/auth/github/me`

鉴权：GitHub JWT（不是管理员 Token）

响应：

```json
{ "id": 1, "login": "octocat", "avatar": "https://...", "bio": "" }
```

未登录 → 401 `未登录`；过期 → 401 `登录已过期，请重新登录`；用户删了 → 401 `用户不存在`

---

## 两个解析函数（阶段 07 要用）

放在 `github_auth.py` 即可（对照就是这样）。

```python
def _get_github_user(request, session) -> GitHubUser:
    # Authorization 必须以 "Bearer " 开头，否则 401
    # decode，sub 转 int，session.get(GitHubUser, id)

def get_github_user_optional(request, session) -> GitHubUser | None:
    # 没有 Bearer 或 decode 失败 → 返回 None，不要抛错
```

评论创建会调用 optional 版，再在 service 里若为 None 则 401「请先登录 GitHub」。

---

## 开发用假登录（推荐，方便自测）

仅当 `os.getenv("DEV_FAKE_GITHUB") == "1"` 时启用：

`POST /api/auth/github/dev-login` Body：`{ "login": "tester" }`

找不到就插入一个 `github_id=0` 或负数的测试用户，返回和正式 callback 一样的 JWT（JSON 即可，不必 redirect）。

**不要在生产环境打开。**

---

## 验收标准

1. 未配置 client_id 时 `/login` 返回 500
2. 配置后 `/login` 会跳到 github.com
3. （有 OAuth App）走完 callback，库里有 github_user，浏览器落到前端并带 token
4. 用该 token 调 `/me` 成功
5. 用**管理员** Token 调 `/api/auth/github/me` 应失败（sub 对不上 GitHubUser）
6. `get_github_user_optional` 无 Header 时返回 None

---

## 易错点

- GitHub 的 `id` 存 `github_id` 列；JWT 的 `sub` 用本地 `GitHubUser.id`。搞反了评论外键会错。
- callback 里用 `httpx.post/get`，记得 `timeout=10`。
- 管理员 `get_current_user` 用 HTTPBearer；GitHub 这套对照是手动读 `Request.headers`。两套不要强行合成一个 Depends，除非你能按 `type` 分支。
- Token 出现在 URL query 上并不理想（会进日志/Referer）。对照项目就是这样做的，练习阶段保持一致即可，心里知道这是简化。

下一阶段：[07-评论与留言板.md](./07-评论与留言板.md)
