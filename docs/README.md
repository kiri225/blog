# 开发记录

按**已完成的业务模块**归档：每次开发一个模块，就新增一份同名 md。

每份模块文档固定两块：

1. **前后端交接规范**：路径、鉴权、字段、成功/失败体，给前端对齐用。
2. **后端接口执行流程**：每个接口从路由进 service、到 `Result` / 拦截器的步骤图，给后端对照实现用。

对照样例：[01-用户认证](./modules/01-用户认证.md)。写法规范见仓库 skill `module-dev-docs`。

改接口代码后，**提交 / 推送前必须核对**对应模块文档是否已跟上（字段、鉴权、错误文案、流程图步骤）。没更新就先改文档再提交。

---

## 怎么用

- 前端只看各模块「前后端交接规范」，不要对着源码猜字段。按页怎么接、岛民壳怎么做，走 [前端任务文档](./前端任务文档/README.md)。
- 后端实现或排查时看「接口执行流程」，步骤编号与 service 里 `# 1.` `# 2.` 一致。
- 新模块开发完成后，按 01 的章节结构再写一份，放到 `docs/modules/`，并在下面总表加一行。

早期后端 `docs/后端任务文档/`、前端 `docs/前端任务文档/` 是学习路径；**字段以后端真实代码 + `docs/modules/` 为准**。

---

## 全局约定（所有模块共用）

| 项 | 约定 |
|----|------|
| 成功 | HTTP 200，body `{code: 200, message, data}` |
| 失败 | HTTP 状态码与 body `code` 相同（401 / 403 / 404 / 422 / 500），`data` 为 `null` |
| 鉴权 | 写操作：`Authorization: Bearer <JWT>`；未带 Token → **403**；Token 无效/过期 → **401** `无效的令牌` |
| 校验失败 | HTTP 422，`message` 为「参数校验失败」 |
| JSON 命名 | 认证令牌字段 camelCase（`accessToken`）；其余模块目前为 snake_case |

管理员 JWT payload：`sub`（username）、`admin`（bool）、`exp`。有效期 72 小时，算法 HS256。

GitHub 访客 JWT 同一 `SECRET_KEY`，payload：`sub`（本地 `github_user.id` 字符串）、`login`、`type: "github"`、`exp`。不要和管理员 Token 混用。访客接口手动读 Header，缺 Bearer 是 **401** `未登录`（不是 403）。

非模块接口（写在 `app/main.py`，不单独建 md）：

| 方法 | 路径 | 响应 |
|------|------|------|
| GET | `/api/health` | `{"status": "ok"}`（不是 Result 信封） |
| GET | `/api/routes` | `{code: 200, message: "success", data: []}` 菜单占位 |

---

## 模块总表

| 序号 | 模块 | 文档 | 前缀 | Swagger tag |
|------|------|------|------|-------------|
| 01 | 用户认证 | [01-用户认证](./modules/01-用户认证.md) | `/api/auth` | 用户认证模块 |
| 02 | 分类与标签 | [02-分类与标签](./modules/02-分类与标签.md) | `/api/categories` `/api/tags` | 分类模块 / 文章标签模块 |
| 03 | 文章 | [03-文章模块](./modules/03-文章模块.md) | `/api/posts` | 文章模块 |
| 04 | GitHub 登录 | [04-GitHub-OAuth](./modules/04-GitHub-OAuth.md) | `/api/auth/github` | GitHub 登录 |
| 05 | 评论 | [05-评论](./modules/05-评论.md) | `/api/comments` | 评论模块 |
| 06 | 留言板 | [06-留言板](./modules/06-留言板.md) | `/api/messages` | 留言板 |

后续模块按开发顺序追加行。不要回头改已发布模块的字段含义；要改就在该模块文档里写变更说明。
