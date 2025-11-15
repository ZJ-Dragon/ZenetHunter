

# ZenetHunter – 后端（FastAPI）

提供 REST/WS API、编排（Scanner/Defender/干扰接口层）以及状态/配置管理的后端服务。

> 运行环境：**Python 3.11+**。Web 框架：**FastAPI**；ASGI 服务器：**Uvicorn**。测试：**pytest**。规范：**Ruff + Black**。

---

## 1) 快速开始（开发）

### 创建并激活虚拟环境
```bash
cd backend
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

### 安装依赖（可编辑安装 + 开发工具）
```bash
pip install -e .[dev]
```

### 启动开发服务器（自动重载）
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- `app.main:app` 遵循 FastAPI/Uvicorn 的导入约定（`main.py` 内暴露 `app = FastAPI()`）；`--reload` 仅用于**开发**。
- 打开 **http://localhost:8000/docs**（Swagger UI）查看交互式 API 文档。

### 运行测试
```bash
pytest -q
```

### 本地格式化与静态检查
```bash
# 与 CI 一致的本地预提交检查
pre-commit run --all-files
# 或直接调用工具
ruff check --fix . && ruff format . && black .
```

---

## 2) 配置与环境变量
遵循 **12‑Factor**：配置经由**环境变量**注入。以下示例为**占位**，按需调整。样例文件在 `../deploy/env/.env.example`。

> 不要把秘密信息提交到仓库。生产环境请使用真实环境变量；`.env` 仅供本地开发。

| 变量 | 示例值 | 说明 |
|---|---|---|
| `APP_ENV` | `development` | 运行环境：`development`/`staging`/`production` |
| `APP_HOST` | `0.0.0.0` | 开发时 ASGI 监听地址 |
| `APP_PORT` | `8000` | 开发时 ASGI 监听端口 |
| `LOG_LEVEL` | `info` | 日志级别：`debug`/`info`/`warning`/`error` |
| `API_TITLE` | `ZenetHunter API` | API 标题（用于 OpenAPI 文档） |
| `API_VERSION` | `0.1.0` | API 版本（用于 OpenAPI 文档） |
| `DATABASE_URL` | `postgresql://user:pass@localhost:5432/zenethunter` | 主数据库 DSN（占位） |
| `SECRET_KEY` | `...` | 会话/签名密钥（**勿入库**） |
| `CORS_ALLOW_ORIGINS` | `http://localhost:5173` | 逗号分隔的前端来源（开发，也接受 `CORS_ORIGINS`） |

**实施说明（计划）**：通过 `pydantic-settings` 加载设置，支持可选 `.env`；见 `app/core/config.py`。

---

## 3) 后端目录结构
```
backend/
├─ app/
│  ├─ __init__.py        # 包初始化
│  ├─ main.py            # FastAPI 入口（创建 `app`）、CORS、路由装配
│  ├─ core/              # 配置、日志、鉴权、中间件
│  │  └─ config.py       # Settings（pydantic-settings）用于 12-Factor 配置
│  ├─ routes/            # 按功能组织的 API 路由
│  │  ├─ __init__.py     # 路由包
│  │  └─ health.py       # 健康检查路由（GET /healthz）
│  ├─ services/          # 编排与领域服务（计划）
│  └─ models/            # pydantic 模型/Schema（计划）
├─ tests/                # pytest 测试套件
│  └─ test_healthz.py    # 健康检查和 OpenAPI 文档测试
└─ pyproject.toml        # PEP 621 元数据 + 工具配置（ruff/black/pytest）
```

---

## 4) 常用任务（脚本占位）
> 暂未引入任务运行器；可直接使用下列命令，或后续增加 `Makefile`/`poe` 等。

- **开发运行**：`uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- **单元测试**：`pytest -q`
- **Lint/格式化**：`pre-commit run --all-files`
- **类型检查（可选）**：后续加入 `mypy` 后可运行 `mypy app/`

---

## 5) 生产环境提示（指引）
- 生产建议使用进程管理/多进程模式，例如 `gunicorn -k uvicorn.workers.UvicornWorker`，并**关闭** `--reload`。
- 如需自建，推荐置于反向代理之后；容器/NAS 部署见 `../deploy/`（多阶段构建、非 root 用户优先）。

---

## 6) 健康检查与文档
- **健康检查**：`GET /healthz` → `200 OK`，返回 `{"status": "ok"}`。用于容器编排系统（Kubernetes、Docker 健康检查）。
- **API 文档**：
  - `GET /docs` - Swagger UI（交互式 API 文档）
  - `GET /redoc` - ReDoc（替代文档视图）
  - `GET /openapi.json` - OpenAPI 模式（机器可读，用于客户端 SDK 生成）

---

## 7) 常见问题
- **端口被占用**：更换 `--port` 或释放端口。
- **无法导入 `app.main:app`**：确认工作目录在 `backend/`，且 `app/main.py` 内有 `app = FastAPI()`。
- **虚拟环境异常**：确认已激活（`which python` 输出位于 `.venv` 目录）。

---

## 8) 许可证
MIT — 见仓库根目录 `/LICENSE`。
