# Kirameku Backend 开发任务文档

对照源码：`blog/Kirameku/Kirameku-backend`

这套文档把真实博客后端拆成 **12 个可执行阶段**。每做完一阶段，你会多掌握一块 FastAPI 能力，同时得到一套能跑的接口。

目标不是抄代码，而是：**按任务规格自己实现 → 用 `/docs` 自测 → 卡住再对照源码。**

---

## 怎么用

1. 先读 [00-约定与架构.md](./00-约定与架构.md)，后面所有阶段都按这套约定写。
2. 从阶段 01 开始，按顺序做。每个阶段文档结构相同：
   - **学什么**：本阶段对应的 FastAPI / 后端知识点
   - **任务清单**：要写哪些文件、做什么
   - **接口规格**：方法、路径、鉴权、参数、响应
   - **业务规则**：容易漏掉的逻辑
   - **验收标准**：做到什么算过关
3. 对照答案在 `Kirameku-backend/app/`，卡住再看，不要先复制。
4. 每阶段完成后，打开 `http://localhost:8000/docs` 把本阶段接口全部点一遍。

学习阶段可以先用 **SQLite**，不必一上来就配 PostgreSQL / 阿里云 OSS。文档里会标明哪些可以简化。

---

## 阶段总表

| 阶段 | 文档 | 核心接口 | FastAPI 知识点 | 预计 |
|------|------|----------|----------------|------|
| 00 | [约定与架构](./00-约定与架构.md) | — | 分层、鉴权、响应风格 | 阅读 |
| 01 | [环境搭建与项目骨架](./01-环境搭建与项目骨架.md) | `/api/health` | FastAPI 实例、lifespan、CORS、Router、静态文件 | 半天 |
| 02 | [数据库与 SQLModel](./02-数据库与SQLModel.md) | 建表 | SQLModel、Session 依赖注入 | 半天 |
| 03 | [JWT 管理员认证](./03-JWT管理员认证.md) | `/api/auth/*` | Depends、HTTPBearer、Pydantic Body | 半天 |
| 04 | [分类与标签](./04-分类与标签.md) | `/api/categories` `/api/tags` | 第一套完整 CRUD、response_model | 半天 |
| 05 | [文章系统](./05-文章系统.md) | `/api/posts` | 路径参数、Query、分页、多对多、路由顺序 | 1 天 |
| 06 | [GitHub OAuth](./06-GitHub-OAuth.md) | `/api/auth/github/*` | RedirectResponse、外部 HTTP、可选登录 | 半天 |
| 07 | [评论与留言板](./07-评论与留言板.md) | `/api/comments` `/api/messages` | Request、树形数据、IP 提取 | 1 天 |
| 08 | [说说](./08-说说.md) | `/api/chatters` | 静态路径 vs 动态路径、JSON 字段 | 半天 |
| 09 | [相册与图片上传](./09-相册与图片上传.md) | `/api/albums` `/api/upload` | UploadFile、File()、一对多 | 半天 |
| 10 | [项目展示与友链](./10-项目展示与友链.md) | `/api/projects` `/api/friend-links` | 审核字段、公开/管理双列表 | 半天 |
| 11 | [站点配置与收藏夹](./11-站点配置与收藏夹.md) | `/api/site-config` `/api/bookmarks` | KV 配置、嵌套响应 | 半天 |
| 12 | [访客记录与仪表盘](./12-访客记录与仪表盘.md) | `/api/visitors` `/api/dashboard` | 聚合查询、Header、第三方 API | 半天 |

完整接口索引：[附录-接口总表.md](./附录-接口总表.md)

---

## 推荐目录（你自己的练习项目）

建议在 `d:\code-py\Fast-api\` 下新建一个练习目录（不要直接改对照源码）：

```
kirameku-learn/
├── .env
├── requirements.txt
├── start.py
├── uploads/
└── app/
    ├── main.py
    ├── config.py
    ├── database.py
    ├── deps.py
    ├── api/
    │   ├── __init__.py
    │   ├── router.py
    │   └── ...
    ├── models/
    ├── schemas/
    ├── services/
    └── utils/
        └── auth.py
```

---

## 技术栈（对照项目）

| 层 | 技术 | 版本（对照源码） |
|----|------|------------------|
| Web | FastAPI + Uvicorn | 0.115 / 0.34 |
| ORM | SQLModel | 0.0.22 |
| 数据库 | PostgreSQL（学习可用 SQLite） | 14+ |
| 认证 | JWT（python-jose）+ bcrypt | HS256，72 小时 |
| 上传 | 阿里云 OSS（学习可存本地） | oss2 |
| 访客地理 | ipapi.co | httpx |

---

## 鉴权速查

| 角色 | 方式 | 用在哪 |
|------|------|--------|
| 管理员 | `Authorization: Bearer <JWT>`，由 `/api/auth/login` 签发 | 写文章、分类、上传、审核等后台操作 |
| GitHub 访客 | 另一套 JWT，`type=github` | 发评论、留言、说说评论 |
| 公开 | 无 Token | 读文章、列表、点赞 |

管理员接口统一写法：

```python
_: dict = Depends(get_current_user)
```
