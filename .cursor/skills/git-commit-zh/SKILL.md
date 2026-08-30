---
name: git-commit-zh
description: >-
  Creates git commits with Chinese Conventional Commits messages and never
  adds AI as a co-author. Use when the user asks to commit, 提交, git commit,
  write a commit message, or push changes to GitHub.
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
- `git log -8 --oneline`（对齐本仓库已有风格）

然后：

1. 只暂存本次相关文件；不要 `git add .` 一把梭。
2. **不要提交** `.env`、密钥、`credentials.json`、`.venv/`。若用户点名要提交这类文件，先警告再等确认。
3. 没有变更则不要空提交。
4. 不要改 git config；不要 `--no-verify` / `--no-gpg-sign`（用户明确要求除外）。
5. 不要 `push`，除非用户明确要求。

## 中文 Conventional Commits

标题一行：

```text
<type>(<scope>): <中文简述>
```

- `type` 用英文小写；`scope` 可选，用英文模块名（如 `AuthRouter.py`、`Config.py`、`docs`）。
- 简述用中文，不超过约 50 字，说「为什么 / 结果」，不要堆文件清单。
- 动词约定：`feat` 用「新增」，`fix` 用「修复」，`docs` 用「补充/更正」，`refactor` 用「重构」，`chore` 用「调整」。
- 正文可选：空一行后写中文说明（1–3 句）。只写需要解释的动机，不要复述 diff。

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

## 提交命令（Windows PowerShell）

不要用 bash 的 `$(cat <<'EOF')`。用 here-string：

```powershell
git commit -m @"
feat(config): 从环境变量读取数据库与密钥

保证密钥不写进代码，后续阶段可直接复用。
"@
```

提交后执行 `git status` 确认成功。hook 失败则修好再 **新开** 一次 commit，不要 `--amend` 除非用户要求且符合安全条件。

## 示例

```text
feat(api): 新增健康检查与路由占位接口
fix(cors): 拆分来源列表时去掉首尾空格
docs(01): 补充虚拟环境启动步骤
chore(deps): 用 psycopg3 替换无法安装的 psycopg2
```
