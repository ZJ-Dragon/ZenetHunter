

# ZenetHunter

> 家用/小型局域网的**设备可视化 + 自适应调度**项目。包含扫描器、调度器、干扰引擎（接口层）、**防御模块（Defender）**、配置/状态管理器以及前端 SPA。目标是在**合法合规**前提下，通过可观测与策略编排，提升自有网络的可控性与可用性。

---

## 仓库结构（Monorepo）
```
.
├─ backend/            # Python 后端（FastAPI）：API、WS、调度、状态/配置、事件总线
│   └─ app/core/
│       ├─ platform/   # 平台检测（Linux/macOS/Windows）
│       └─ engine/
│           ├─ features_macos.py  # macOS 特定网络功能
│           └─ macos_defense.py   # macOS 防御引擎（pfctl）
├─ frontend/           # 前端 SPA（Vite + React + TS）
├─ deploy/             # 部署脚本和文档
├─ docs/               # 文档站（入门、架构、接口、异常规范、数据模型、开发指南）
├─ .github/            # CI 工作流
└─ README.md           # 顶层说明（本文件）
```

## 平台支持

ZenetHunter 支持多平台，并自动检测：

- **Linux**: 完整支持，使用 iptables 防御引擎
- **macOS**: 完整支持，使用 pfctl 防御引擎（详见 [README-MACOS.md](README-MACOS.md)）
- **Windows**: 完整支持，使用 Windows Firewall (netsh) 防御引擎（详见 [README-WINDOWS.md](README-WINDOWS.md)）

系统会自动检测平台并选择相应的实现。

> 详细说明见：`/docs/index.md`（文档站导航）。

---

## 快速开始

### 方式一：本地运行（推荐，无需 Docker）

**最简单的方式，直接打开 HTML 文件即可使用：**

1. **清理缓存（可选，代码更改后推荐）**：
   ```bash
   # Python 脚本（跨平台，推荐）
   python clean-cache.py              # 清理所有缓存（不包括数据库和虚拟环境）
   python clean-cache.py --all        # 清理所有缓存（包括数据库和虚拟环境）
   python clean-cache.py --db         # 同时清理数据库文件
   python clean-cache.py --venv       # 同时清理虚拟环境
   
   # Shell 脚本（Linux/macOS）
   ./clean-cache.sh [--all] [--db] [--venv]
   
   # 批处理脚本（Windows）
   clean-cache.bat [--all] [--db] [--venv]
   ```

2. **启动后端服务**：
   ```bash
   # Linux/macOS
   ./start-local.sh
   
   # Windows
   start-local.bat
   ```

3. **打开前端页面**：
   - 直接在浏览器中打开 `html/index.html`
   - 或使用本地 HTTP 服务器（推荐，避免 CORS 问题）：
     ```bash
     cd html
     python -m http.server 8080
     # 然后访问 http://localhost:8080
     ```

4. **开始使用**：
   - 访问 `http://localhost:8000/docs` 查看 API 文档
   - 在 HTML 页面中执行网络扫描、查看设备等操作

**优势**：
- ✅ 无需 Docker，直接运行
- ✅ 无需构建前端，直接打开 HTML
- ✅ 快速启动，适合开发和测试
- ✅ 所有功能完整可用

**注意事项**：
- 确保 Python 3.11+ 已安装
- 首次运行会自动安装依赖
- 使用 SQLite 作为默认数据库（无需额外配置）
- 如需使用 PostgreSQL，设置 `DATABASE_URL` 环境变量

### 方式二：Docker 部署（生产环境）

## 快速开始（Docker）（最小可运行 · 占位）
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

### 3) Docker 部署（推荐）

ZenetHunter 提供了多种 Docker 运行方式，确保始终使用最新代码（包括未提交的本地更改）。

#### 前置要求

- Docker Engine 20.10+ 和 Docker Compose v2.0+
- Git（用于版本检测，可选）
- 至少 2GB 可用磁盘空间

#### 使用脚本快速启动

**方式一：一键启动（推荐）**
```bash
./docker-run.sh start
```
此脚本会自动：
- 使用 `--no-cache` 构建镜像，确保包含最新代码
- 设置构建时间戳和版本标签
- 启动所有服务（后端、前端、数据库）

**方式二：分别构建和启动**
```bash
# 使用最新代码构建镜像
./docker-build.sh

# 然后启动服务
docker compose up -d
```

**方式三：重建并重启**
```bash
./docker-run.sh rebuild
```
这将使用最新代码重建所有镜像并重启服务。

#### 手动使用 Docker Compose

如果您更喜欢直接使用 `docker compose`：

```bash
# 使用最新代码构建（无缓存）
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
BUILD_VERSION=$(git describe --tags --always --dirty 2>/dev/null || echo "dev")
docker compose build --no-cache --build-arg BUILD_DATE="$BUILD_DATE" --build-arg BUILD_VERSION="$BUILD_VERSION"

# 启动服务
docker compose up -d
```

#### 可用脚本命令

**docker-run.sh** - 主要编排脚本：
```bash
./docker-run.sh start      # 构建并启动所有服务
./docker-run.sh stop       # 停止所有服务
./docker-run.sh restart    # 重启服务（不重新构建）
./docker-run.sh rebuild    # 重建并重启（使用最新代码）
./docker-run.sh logs       # 查看日志（跟随模式）
./docker-run.sh status     # 检查服务状态
./docker-run.sh build      # 仅构建镜像（无缓存）
```

**docker-build.sh** - 专用构建脚本：
```bash
./docker-build.sh          # 构建所有服务
./docker-build.sh backend  # 仅构建后端
./docker-build.sh frontend # 仅构建前端
```

#### 生产环境部署

使用增强配置进行生产部署：

```bash
cd deploy
./start.sh
```

这将使用 `deploy/docker-compose.yml`，包含额外的安全特性、资源限制和健康检查。

#### 重要说明

- **最新代码**：所有构建脚本都使用 `--no-cache` 选项，确保您最新的本地代码（包括未提交的更改）都会被包含在 Docker 镜像中。
- **构建参数**：脚本会自动生成 `BUILD_DATE` 和 `BUILD_VERSION`（未提交更改时会包含 `--dirty` 标记）。
- **代码更改**：任何本地修改（已提交或未提交）都会包含在构建中。
- **缓存**：Docker 层缓存已禁用，以确保全新构建。开发期间如需更快重建，可移除 `--no-cache`，但可能会使用过时代码。
- **生产环境**：生产部署请参考 `/deploy/README.md` 了解高级配置、安全加固和 NAS 特定说明。

#### 访问地址

启动服务后，可通过以下地址访问：
- **前端界面**：http://localhost:1226
- **后端 API**：http://localhost:8000
- **API 文档**：http://localhost:8000/docs (Swagger UI)
- **ReDoc**：http://localhost:8000/redoc
- **健康检查**：http://localhost:8000/healthz
- **OpenAPI 模式**：http://localhost:8000/openapi.json

#### 故障排除

**问题：重建后更改未生效**
- 解决方案：确保使用 `--no-cache` 标志。运行 `./docker-run.sh rebuild` 强制完全重建。

**问题：端口已被占用**
- 解决方案：停止冲突的服务或在 `docker-compose.yml` 中更改端口：
  - 前端：`1226:8080` → `1227:8080`
  - 后端：`8000:8000` → `8001:8000`

**问题：脚本权限被拒绝**
- 解决方案：使脚本可执行：`chmod +x docker-run.sh docker-build.sh`

**问题：构建失败，提示"模块未找到"**
- 解决方案：确保所有依赖项都列在 `requirements.txt`（后端）或 `package.json`（前端）中。

**问题："Failed to start scan: Network Error" 或扫描功能不可用**
- **当前配置**：默认配置使用 **root 用户** 以获得最佳网络扫描兼容性。
  
  **⚠️ 安全提示**：
  - 后端容器以 **root 用户（UID 0）** 运行以启用网络扫描功能
  - 这会降低容器隔离安全性，但对 Scapy 创建原始套接字是必需的
  - 结合 `network_mode: "host"`，容器拥有对主机网络的完全访问权限
  - **对于生产环境**，建议考虑：
    - 直接在主机上运行后端（不使用容器）
    - 使用具有适当隔离的专用网络扫描服务
    - 实施额外的安全措施（防火墙规则、网络分段）
  
- **当前 Docker 配置**（已应用）：
  ```yaml
  backend:
    user: "0"  # Root 用户用于网络扫描
    network_mode: "host"  # 主机网络访问
    cap_add:
      - NET_RAW    # 原始套接字操作
      - NET_ADMIN  # 网络管理
  ```
  
- **为什么需要 Root**：
  - Scapy 需要创建原始套接字以进行网络数据包注入
  - 原始套接字需要 root 权限或特定的 Linux 能力
  - 即使有 NET_RAW 能力，某些操作仍需要 root
  - Root + host 网络模式提供最可靠的网络扫描体验
  
- **验证**：检查配置是否正确：
  ```bash
  # 检查是否以 root 运行
  docker exec zh-backend id
  # 应显示：uid=0(root) gid=0(root)
  
  # 检查网络模式
  docker inspect zh-backend | grep NetworkMode
  # 应显示："NetworkMode": "host"
  
  # 检查能力
  docker inspect zh-backend | grep -A 5 "CapAdd"
  
  # 测试扫描功能
  docker logs -f zh-backend
  ```
  
- **如果扫描仍然失败**：
  1. 确保 Docker 有权限使用主机网络模式
  2. 检查是否有防火墙阻止原始套接字创建
  3. 验证 Scapy 已安装：`docker exec zh-backend python -c "import scapy; print(scapy.__version__)"`
  4. 检查系统日志：`docker logs zh-backend | grep -i "scan\|network\|permission"`
  
- **安全建议**：
  - 仅在受信任的网络上运行此容器
  - 如需要，使用防火墙规则限制容器网络访问
  - 定期更新 Docker 和容器镜像
  - 监控容器日志以发现可疑活动
  - 考虑网络分段以隔离扫描服务

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
