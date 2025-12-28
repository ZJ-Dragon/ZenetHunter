# ZenetHunter – 后端 (FastAPI)

提供 REST/WS API、编排（扫描器/防御器/干扰接口）和状态/配置管理的后端服务。

> 运行环境：**Python 3.11+**。Web 框架：**FastAPI**；ASGI 服务器：**Uvicorn**。测试框架：**pytest**。代码检查/格式化：**Ruff + Black**。

---

## 1) 快速开始（开发）

### 创建并激活虚拟环境
```bash
cd backend
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
```

### 安装依赖（可编辑安装 + 开发工具）
```bash
pip install -e .[dev]
```

### 运行开发服务器（自动重载）
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- `app.main:app` 遵循 FastAPI/Uvicorn 的导入字符串约定（`main.py` 模块暴露 `app = FastAPI()`），`--reload` 仅用于**开发环境**。
- 打开 **http://localhost:8000/docs** 查看交互式 API 文档（Swagger UI）。

### 运行测试
```bash
pytest -q
```

### 本地运行格式化和代码检查
```bash
# 运行与 CI 相同的钩子
pre-commit run --all-files
# 或直接运行工具
ruff check --fix . && ruff format . && black .
```

---

## 2) 配置和环境变量
我们遵循**12 要素**原则：配置通过**环境变量**提供。下面的示例变量是**占位符**；根据您的环境调整。示例文件位于 `../deploy/env/.env.example`。

> 永远不要将密钥提交到仓库。生产环境优先使用真实环境变量；`.env` 仅用于本地开发。

| 变量 | 示例 | 描述 |
|---|---|---|
| `APP_ENV` | `development` | 环境名称：`development`/`staging`/`production` |
| `APP_HOST` | `0.0.0.0` | ASGI 服务器的绑定主机（开发） |
| `APP_PORT` | `8000` | ASGI 服务器的绑定端口（开发） |
| `LOG_LEVEL` | `info` | 日志级别：`debug`/`info`/`warning`/`error` |
| `API_TITLE` | `ZenetHunter API` | API 标题（用于 OpenAPI 文档） |
| `API_VERSION` | `0.1.0` | API 版本（用于 OpenAPI 文档） |
| `DATABASE_URL` | `postgresql://user:pass@localhost:5432/zenethunter` | 主数据库 DSN（占位符） |
| `SECRET_KEY` | `...` | 会话/签名的密钥材料（**不要**提交） |
| `CORS_ALLOW_ORIGINS` | `http://localhost:5173` | 开发 UI 访问的逗号分隔列表（也接受 `CORS_ORIGINS`） |

**实现说明（计划中）：** 通过 `pydantic-settings` 加载设置，可选支持 `.env`。参见 `app/core/config.py`。

---

## 3) 项目布局（后端）
```
backend/
├─ app/
│  ├─ __init__.py        # 包初始化
│  ├─ main.py            # FastAPI 应用入口点（创建 `app`），CORS，API 连接
│  ├─ core/              # 配置、日志、认证、中间件
│  │  └─ config.py       # 设置（pydantic-settings）用于 12 要素配置
│  ├─ routes/            # 按功能组织的 API 路由器
│  │  ├─ __init__.py     # 路由包
│  │  └─ health.py       # 健康检查路由器（GET /healthz）
│  ├─ services/          # 编排和领域服务（计划中）
│  └─ models/            # pydantic 模型/模式（计划中）
├─ tests/                # pytest 测试套件
│  └─ test_healthz.py    # 健康检查和 OpenAPI 文档测试
└─ pyproject.toml        # PEP 621 元数据 + 工具配置（ruff/black/pytest）
```

---

## 4) 常见任务（脚本 – 占位符）
> 我们还没有提供任务运行器；使用下面的命令或在未来的 PR 中添加 `Makefile`/`poe`。

- **运行开发服务器**：`uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- **运行单元测试**：`pytest -q`
- **代码检查/格式化**：`pre-commit run --all-files`
- **类型检查（可选）**：稍后添加 `mypy` 并运行 `mypy app/`

---

## 5) 生产环境注意事项（指针）
- 对于生产环境，优先使用进程管理器（例如 `gunicorn -k uvicorn.workers.UvicornWorker`）并**禁用** `--reload`。
- 容器化和 NAS 部署在 `../deploy/` 中定义。镜像使用多阶段构建，在可行的地方使用非 root。

---

## 6) 健康检查和文档
- **健康检查**：`GET /healthz` → `200 OK` 带 `{"status": "ok"}`。用于容器编排系统（Kubernetes、Docker 健康检查）。
- **API 文档**：
  - `GET /docs` - Swagger UI（交互式 API 文档）
  - `GET /redoc` - ReDoc（替代文档视图）
  - `GET /openapi.json` - OpenAPI 模式（机器可读，用于客户端 SDK 生成）

---

## 7) 故障排除（快速）
- **端口已被使用**：更改 `--port` 或释放端口。
- **无法导入 `app.main:app`**：确保 `backend/` 是当前工作目录，且 `app/main.py` 暴露 `app = FastAPI()`。
- **虚拟环境问题**：确认激活（`which python` → `.venv` 下的路径）。

---

## 8) 许可证
MIT — 参见仓库根目录的 `/LICENSE`。
