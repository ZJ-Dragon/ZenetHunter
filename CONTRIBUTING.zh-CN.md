

# Contributing to **ZenetHunter**

感谢你愿意为 ZenetHunter 做贡献！本指南聚焦**协作流程、分支命名、提交信息规范**以及必要的本地校验步骤，帮助你快速、高质量地完成变更。

> TL;DR：**主干开发 + 短生命周期特性分支**；提交信息使用 **Conventional Commits**；所有 PR 通过 CI/预提交钩子后合并。

---

## 0. 行为准则
请以专业、友善的方式参与交流与评审。若报告安全问题，请阅读 `/SECURITY.md` 并使用其中的私密渠道。

---

## 1. 分支策略（Trunk‑Based + GitHub Flow）
- 受保护分支：`main`（仅通过 PR 合并）。
- 工作方式：**小步快跑**，从 `main` 切出**短生命周期**特性分支，完成后创建 PR 合回 `main`。
- 分支命名：`<板块>/<功能>-<简述>`，全部小写，分隔使用中横线（`-`）。
  - 示例：
    - `foundation/repo-scaffold`
    - `backend-core/scanner-api`
    - `defender/synproxy`
    - `frontend/topology`
    - `ai-scheduler/policy-core`
    - `ops/dockerfile-prod`
- PR 基本要求：
  - 小而清晰；描述**做了什么/为什么**；必要时 `Closes #123` 关联议题。
  - 通过 CI（lint/test/build）与预提交钩子（见下）。
  - 至少 1 名 Reviewer 通过后合并（避免自合）。

---

## 2. 提交信息规范（Conventional Commits）
我们使用 **Conventional Commits** 规范，配合 `commitlint` 进行校验，便于自动生成变更日志与版本。

**格式**
```
<type>(<scope>): <subject>

<body>

<footer>
```
- `type`：常用值
  - `feat`（新功能）、`fix`（缺陷修复）、`docs`、`style`（非语义代码风格）、`refactor`、`perf`、`test`、`build`、`ci`、`chore`、`revert`
- `scope`：可选；推荐与**板块/子系统**一致，例如 `scanner`、`defender`、`frontend`、`ops` 等。
- `subject`：一句话概述（不以句号结尾）。
- `BREAKING CHANGE`：在正文或页脚注明重大变更说明。

**示例**
```
feat(scanner): add subnet discovery via ARP sweep
fix(defender): handle tc shaping errors on startup
docs(readme): add English quick start and repo layout
chore(gitignore): exclude venv and node_modules
```

> 本仓库已提供 `commitlint.config.cjs` 与 GitHub CI 校验；本地可通过 **pre-commit** 钩子先行检查。

---

## 3. 预提交钩子与本地校验
- 安装并启用：
  ```bash
  pip install pre-commit && pre-commit install
  pre-commit run --all-files
  ```
- 已集成的检查：
  - `trailing-whitespace`、`end-of-file-fixer`
  - Python：`ruff`（lint+format）、`black`
  - 其他：可逐步补充（如 `eslint --max-warnings=0` 等）

---

## 4. 开发与测试基线
- 后端（FastAPI）：
  - 开发：`uvicorn app.main:app --reload`
  - 单测：`pytest -q`
- 前端（Vite + React + TS）：
  - 开发：`npm run dev`
  - 构建：`npm run build`

> 详细运行方式见各子目录 `README.md`。

---

## 5. 版本与变更日志
- 版本遵循 **SemVer**（`MAJOR.MINOR.PATCH`）。
- 变更记录维护在 `CHANGELOG.md`（合并时由 Conventional Commits 驱动的工具生成/辅助）。

---

## 6. 提交/评审清单（Checklist）
- [ ] 提交信息符合 Conventional Commits（含 `type(scope): subject`）。
- [ ] 代码通过本地 `pre-commit` 与 CI。
- [ ] 新增/变更的接口与行为已在文档中更新。
- [ ] 涉及配置/安全相关变更，已在 `SECURITY.md`/部署文档注明。
- [ ] PR 描述清晰、最小化变更范围，必要时附截图/日志片段。

---

欢迎通过 Issue 提出建议，或直接提交 PR！
