

# ZenetHunter

> 家用/小型局域网的**设备可视化 + 自适应调度**项目。包含扫描器、调度器、干扰引擎（接口层）、**防御模块（Defender）**、配置/状态管理器以及前端 SPA。目标是在**合法合规**前提下，通过可观测与策略编排，提升自有网络的可控性与可用性。

---

## 仓库结构（Monorepo）
```
.
├─ backend/            # Python 后端（FastAPI）：API、WS、调度、状态/配置、事件总线
├─ frontend/           # 前端 SPA（Vite + React + TS）
├─ deploy/             # Dockerfile、docker-compose、环境变量样例、NAS/服务器部署脚本
├─ docs/               # 文档站（入门、架构、接口、异常规范、数据模型、开发指南）
├─ .github/            # CI 工作流
└─ README.md           # 顶层说明（本文件）
```

> 详细说明见：`/docs/index.md`（文档站导航）。

---

## 快速开始（最小可运行 · 占位）
> 以下为**开发环境**最小启动命令，具体参数与脚本以各模块 README 为准；生产/容器见 `deploy/`。

### 1) 后端（开发）
```bash
cd backend
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -e .  # 如使用 PEP 621/pyproject；或改用项目内的 dev 脚本
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
\- `uvicorn app.main:app --reload` 为开发模式；生产部署请使用进程管理/ASGI 服务器与关闭 `--reload`。

### 2) 前端（开发）
```bash
cd frontend
npm ci  # 或 npm install / pnpm i / bun install
npm run dev
```
默认开发端口（Vite）通常为 `5173`；可在 `vite.config.*` 中调整。

### 3) 一键编排（可选）
```bash
cd deploy
docker compose up -d  # 以 compose 文件为准，首次请先修改 .env
```
> 生产镜像采用多阶段构建与非 root 用户运行（详见 `deploy/`）。

---

## 模块概览
- **Scanner（扫描器）**：网段扫描、设备发现与拓扑采集；向状态管理器上报。
- **Dispatcher（调度器）**：承接前端/策略请求，编排扫描器、干扰引擎、**防御模块**。
- **Attack Engine（接口层）**：规范化干预接口（实现受权限/环境约束，默认占位）。
- **Defender（防御模块）**：SYNPROXY/限速整形/DNS RPZ/Walled Garden/TCP Reset 等**合法防护**能力抽象与接入。
- **Config/State Manager**：设备/拓扑/名单/日志等核心模型与统一查询/写入 API。
- **Frontend SPA**：设备列表、拓扑图、策略触发与状态订阅（WS）。

> 详细 API/消息格式：见《模块交互接口文档》；数据模型：见《数据结构与数据库模型》。

---

## 开发指南入口
- **入门**：`/docs/入门.md`
- **架构**：`/docs/架构设计.md`
- **模块交互接口**：`/docs/模块交互接口文档.md`
- **AI 调度设计**：`/docs/AI 调度器设计文档.md`
- **防御模块说明**：`/docs/Defender 模块说明.md`
- **错误与异常处理规范**：`/docs/错误与异常处理规范.md`
- **数据结构与数据库模型**：`/docs/数据结构与数据库模型.md`
- **部署（Ugreen / Docker）**：`/deploy/README.md`

> 上述文档文件名为占位，实际以仓库内文件为准。

---

## 约定与规范
- **提交信息**：Conventional Commits（如 `feat:`, `fix:`，含 BREAKING CHANGE）。
- **版本**：SemVer（`MAJOR.MINOR.PATCH`）。
- **代码风格**：EditorConfig + Lint/Formatter（后端 Ruff/Black；前端 ESLint/Prettier）。
- **配置**：12-Factor，使用环境变量/密钥服务，不在仓库存放敏感信息。

---

## 合规与边界
本项目仅面向**自有网络**的**可观测/接入控制/服务质量管理**与**合法防护**实践；严禁将本项目用于任何未授权的环境。

---

## 许可证
本项目采用 MIT License，详见 `/LICENSE`。
