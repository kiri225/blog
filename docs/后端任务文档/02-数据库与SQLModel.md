# 02 — 数据库与 SQLModel

对照源码：`../app/Database.py`、`app/models/`、`init_db.sql`、`DATABASE.md`

前置：阶段 01 已能启动。

---

## 学什么

- SQLModel = SQLAlchemy 表 + Pydantic 模型
- `create_engine` + `Session`
- FastAPI 依赖注入：`yield` 生成器关闭 Session
- `SQLModel.metadata.create_all` 启动时建表
- 表之间的 FK、多对多中间表

本阶段**先把表建出来**，可以只实现 User / Category / Tag / Post / PostTag。其余表在对应功能阶段再加，避免一次写 18 张表劝退。

也可以一次按 `init_db.sql` 全部建完，后面阶段只填接口。两种都行，任务清单按「按需加表」写。

---

## 任务清单

- [ ] 写 `../app/Database.py`：engine、`init_db`、`get_session`
- [ ] `lifespan` 启动时调用 `init_db()`
- [ ] 写 `../app/models/User.py`（本阶段就要用，阶段 03 登录）
- [ ] 写 `../app/models/Post.py`：Category、Tag、PostTag、Post（阶段 04/05 用）
- [ ] `app/models/__init__.py` 导入所有模型（**必须导入**，否则 `create_all` 建不出表）
- [ ] 启动后确认表已创建；插入一个管理员账号

---

## `Database.py` 规格

```python
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
```

要点：

- `get_session` 必须是生成器，`yield session`。路由里 `session: Session = Depends(get_session)`。
- SQLite 连接串：`sqlite:///./kirameku.db`（相对项目根）。
- PostgreSQL：`postgresql://user:password@host:5432/kirameku`，需要 `psycopg2-binary`。
- SQLite 多线程时可能要 `connect_args={"check_same_thread": False}`。对照项目用的是 PostgreSQL，没有这一行。

---

## 本阶段最低模型

### User

| 字段 | 类型 | 约束 |
|------|------|------|
| id | int | PK，自增 |
| username | str(50) | unique, index |
| hashed_password | str(128) | |
| nickname | str(50) | 默认 `""` |
| avatar | str(500) | 默认 `""` |
| email | str(100) | 默认 `""` |
| bio | str(500) | 默认 `""` |
| is_admin | bool | 默认 False |
| created_at / updated_at | datetime | `default_factory=datetime.now` |

表名：`user`（SQLModel `__tablename__ = "user"`）。`user` 在 PostgreSQL 里是保留字，SQL 脚本里要加引号。

### Category / Tag / Post / PostTag

字段以对照 `../app/models/Post.py` 为准，完整表结构见源码或 [附录](./附录-接口总表.md) 不做接口也能先建表。

关系：

```
User（独立）
Post ── category_id → Category
Post ── PostTag ←→ Tag
```

---

## 种子管理员

对照 SQL 插入了 `admin` / `admin123`。练习项目可在第一次启动时判断：没有用户就插入一个。

**不要**把明文密码存库。用阶段 03 的 `hash_password`。可以临时在 Python 里：

```python
from app.utils.JWTUtils import hash_password

print(hash_password("admin123"))
```

或本阶段先手写一段启动脚本插入，阶段 03 再把 hash 函数补全。

---

## 全部 18 张表（对照）

做完全部阶段后应有：

| 表 | 用途 | 引入阶段 |
|----|------|----------|
| user | 管理员 | 02 / 03 |
| category / tag / post_tag / post | 文章 | 02 / 04 / 05 |
| github_user | GitHub 访客 | 06 |
| comment | 文章评论 | 07 |
| message | 留言板 | 07 |
| chatter / chatter_comment | 说说 | 08 |
| album / photo | 相册 | 09 |
| project | 项目展示 | 10 |
| friend_link | 友链 | 10 |
| bookmark_category / bookmark_site | 收藏夹 | 11 |
| site_config | KV 配置 | 11 |
| visitor | 访客 | 12 |

完整字段说明对照 `DATABASE.md` 和 `init_db.sql`。注意：`DATABASE.md` 里评论还写着 nickname/email 访客填写，**实际代码**已改成 GitHub 用户 + `github_user_id`。以代码为准。

---

## 验收标准

1. 启动不报错，`init_db()` 会建表
2. SQLite 能在项目根看到 `kirameku.db`；或 PostgreSQL 里能 `\dt` 看到表
3. `models/__init__.py` 漏导入某张表时，该表不会被创建——验证方法：注释掉导入再启动，表不应出现
4. 库里至少有一个 `is_admin=true` 的用户，供下一阶段登录

---

## 易错点

- 只写了 model 文件但没在 `__init__.py` import，`create_all` 不知道这张表。
- `lifespan` 里调用 `init_db()` 必须发生在 `yield` 之前。
- 学习用 SQLite 时，JSON 数组字段（images、tech_stack、platforms）用 `TEXT` 存 `'[]'` 字符串，和对照项目一致。
- 不要用 `SQLModel` 同一个类既当表又当请求体（Create 里会把 `id` 搞乱）。表和 Schema 分开。

下一阶段：[03-JWT管理员认证.md](./03-JWT管理员认证.md)
