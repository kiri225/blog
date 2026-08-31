---
name: git-commit-zh
description: >-
  Creates git commits with Chinese Conventional Commits messages that explain
  what changed, and never adds AI as a co-author. Use when the user asks to
  commit, 提交, git commit, write a commit message, or push changes to GitHub.
  Before commit or push, if api/service/schema/models changed, verify
  docs/modules development records are updated.
---

# GitHub 中文规范提交

用户要求提交时按本规范执行。只在用户明确要求 commit / 提交时才提交。

## 禁止共创署名

**不要把助手加入共创。** 提交里不得出现任何 AI / Cursor 共创信息，包括但不限于：

- `Co-authored-by:`
- `Co-authored-by: Cursor`
- `Made-with: Cursor`
- `--trailer "Co-authored-by: ..."`

`git commit` 不要加会写入上述 trailer 的参数。

## 提交前检查

并行执行：

- `git status`
- `git diff` 与 `git diff --staged`
- `git log -8 --oneline`（标题风格对齐本仓库；正文按本规范写全，不要为了「短」而省略）

然后：

1. 只暂存本次相关文件；不要 `git add .` 一把梭。
2. **不要提交** `.env`、密钥、`credentials.json`、`.venv/`。若用户点名要提交这类文件，先警告再等确认。
3. 没有变更则不要空提交。
4. 不要改 git config；不要 `--no-verify` / `--no-gpg-sign`（用户明确要求除外）。
5. 不要 `push`，除非用户明确要求。
6. **开发记录**：若本次改了接口相关代码，先按下面「开发记录必须同步」做完，再 `git add` / commit。

## 开发记录必须同步

改了 `app/api/`、`app/service/`、`app/schemas/`、`app/models/`（含 `router.py`）时，提交和推送都不能跳过文档。写法见 skill `module-dev-docs`。

提交前：

1. 对照 `docs/modules/` 对应 md，以及 `docs/README.md` 模块总表。
2. 接口增删改、字段、鉴权、错误文案、自动规则有变 → **先改文档**，和代码放进同一次 commit。
3. 新模块还没有 `docs/modules/{序号}-{模块名}.md` 或总表缺行 → 先补再提交，不要只交代码。
4. 对外 JSON 完全不变的内部重构：流程节没有过时可以不改文档。
5. 文档仍落后就不要 commit 接口代码。

文件对应：Auth* → `01-用户认证.md`；Categories* / Tags* → `02-分类与标签.md`；Posts* / Post / PostTag → `03-文章模块.md`；新 Router → 新建下一序号。

推送前（用户明确要求 push 时）：

1. 再看工作区和将要 push 的提交：接口已变但 `docs/modules/` 没跟上 → 先补文档并 commit，再 push。
2. 不要在文档未同步时把接口改动推到远程。

## 中文 Conventional Commits

标题一行：

```text
<type>(<scope>): <中文简述>
```

- `type` 用英文小写；`scope` 可选，用英文模块名（如 `tags`、`AuthRouter.py`、`docs`）。
- 简述用中文，不超过约 50 字，说这次提交的结果（新增了什么 / 修了什么）。
- 动词约定：`feat` 用「新增」，`fix` 用「修复」，`docs` 用「补充/更正」，`refactor` 用「重构」，`chore` 用「调整」。

| type | 何时用 |
|------|--------|
| `feat` | 新功能 |
| `fix` | 修 bug |
| `docs` | 只改文档 |
| `style` | 格式/空格，不影响逻辑 |
| `refactor` | 重构，行为不变 |
| `perf` | 性能 |
| `test` | 测试 |
| `chore` | 依赖、脚手架、杂项 |
| `ci` | CI 配置 |
| `build` | 构建脚本 |

### 正文必写，让人知道做了什么

标题下面空一行，**必须写正文**。看提交记录的人通常不打开 diff，正文要能独立说清改动。

要写：

- 具体做了哪些事：接口路径与方法、模块、可见行为（3–8 条短句或列表）。
- 关键约束或行为变化：鉴权、成功/失败码与文案、未传字段是否覆盖、删除返回什么。
- 有意偏离对照文档或旧实现时，写一句为什么（例如统一走 Result 信封）。

不要写：

- 只有一句空话：「完善功能」「对齐规范」「补充代码」。
- 只写动机、不写做了什么。
- 把每个文件名列一遍（可以说「标签 CRUD」，不要 `TagsRouter.py` / `TagService.py` 清单）。

粒度：按**能力/接口/行为**写，不要按文件写。一条列表对应一件读者能验证的事。

## 提交命令（Windows PowerShell）

不要用 bash 的 `$(cat <<'EOF')`。用 here-string：

```powershell
git commit -m @"
feat(tags): 新增标签 CRUD 并修分类局部更新

- 新增 GET/POST/PUT/DELETE /api/tags：列表公开，写操作需管理员 JWT
- 名称或别名冲突返回 400「标签已存在」；不存在返回 404
- 删除成功只返回 code=200 与「删除成功」；仍有文章占用则 400
- 分类更新改为只改传入字段，避免只改 description 时清空 name/slug
- 同步 docs/modules/02-分类与标签.md 交接字段与流程图
"@
```

提交后执行 `git status` 确认成功。hook 失败则修好再 **新开** 一次 commit，不要 `--amend` 除非用户要求且符合安全条件。

## 示例

差（正文太少，看不出做了什么）：

```text
feat(tags): 新增标签 CRUD 并修分类局部更新

分类与标签四套接口已齐；未传字段不再覆盖成空。
```

好：

```text
feat(tags): 新增标签 CRUD 并修分类局部更新

- 新增 GET/POST/PUT/DELETE /api/tags：列表公开，写操作需管理员 JWT
- 名称或别名冲突返回 400；不存在返回 404；删除成功只带「删除成功」
- 分类 PUT 只更新传入字段，只改 description 时 name/slug 保持不变
- 无 Token 的 POST/PUT/DELETE 会被拒绝
```

```text
feat(categories): 新增分类 CRUD 并对齐失败响应

- 新增 GET/POST/PUT/DELETE /api/categories，列表按 sort 升序
- 成功体为 {code, message, data}，失败只返回中文 message，不把校验明细塞进 data
- 重名或别名冲突 400「分类已存在」；删除有文章占用则 400
```

```text
fix(cors): 拆分来源列表时去掉首尾空格

- CORS_ORIGINS 按逗号拆分后 strip，避免带空格的来源匹配失败
```
