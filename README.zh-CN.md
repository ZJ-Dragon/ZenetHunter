

# ZenetHunter

> **网络安全主动防御研究平台**。专注于授权环境下的主动防御技术研究，包含网络扫描、设备发现、主动防御引擎、状态管理和可视化界面。

⚠️ **重要声明**：本项目已通过政府安全认证，仅用于学术研究和授权安全测试环境。所有主动防御技术实现均受严格保密和访问控制。**未经授权使用可能违反法律法规。**

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
├─ docs/               # 文档（主动防御、API、主动探测、外部服务、平台/环境指南）
├─ .github/            # CI 工作流
└─ README.md           # 顶层说明（本文件）
```

## 平台支持

ZenetHunter 支持多平台，并自动检测：

- **Linux**: 完整支持，使用 iptables 防御引擎
- **macOS**: 完整支持，使用 pfctl 防御引擎（详见 [macOS 指南](docs/guides/README-MACOS.md)）
- **Windows**: 完整支持，使用 Windows Firewall (netsh) 防御引擎（详见 [Windows 指南](docs/guides/README-WINDOWS.md)）

系统会自动检测平台并选择相应的实现。

> 文档主页： [docs/index.zh-CN.md](docs/index.zh-CN.md) / [EN](docs/index.md)

---

## 快速开始

### 方式一：一键启动（推荐）

**最简单的方式，一条命令启动前后端：**

**Linux/macOS:**
```bash
./start-local.sh              # 正常启动
./start-local.sh --clean      # 清理缓存后启动
./start-local.sh --clean-all  # 深度清理（包括数据库和虚拟环境）后启动
sudo ./start-local.sh         # 以 root 权限运行（推荐，启用完整网络功能）
```

**Windows:**
```cmd
start-local.bat               # 正常启动
start-local.bat --clean       # 清理缓存后启动
start-local.bat --clean-all   # 深度清理（包括数据库和虚拟环境）后启动
```

**启动脚本自动完成以下操作**：
- ✅ 杀死残留进程（uvicorn、vite）
- ✅ 释放占用端口（8000、5173）
- ✅ 清理 Python/前端/系统缓存（使用 `--clean`）
- ✅ 检测并激活虚拟环境
- ✅ 安装/更新依赖
- ✅ 检查并修复数据库 schema
- ✅ 启动后端和前端服务
- ✅ Ctrl+C 优雅关闭

**访问地址**：
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs
- 前端页面: http://localhost:5173

**注意事项**：
- 确保 Python 3.11+ 已安装
- 首次运行会自动安装依赖
- 使用 SQLite 作为默认数据库（无需额外配置）
- 如需使用 PostgreSQL，设置 `DATABASE_URL` 环境变量

### 方式二：手动启动（备选）

如需手动控制各服务：

**后端：**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -e .
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**前端：**
```bash
cd frontend
npm ci  # 或 npm install / pnpm i / bun install
npm run dev
```

### 方式三：Docker 部署（生产环境）

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

## 核心模块

### 网络扫描与发现
- **Scanner（扫描器）**：ARP扫描、设备发现、拓扑采集、厂商识别
- **Device Management**：设备状态跟踪、指纹识别、分类管理

### 主动防御引擎
- **Active Defense Engine**：基于Scapy的主动防御技术实现
  - WiFi层：Deauthentication、Beacon Flooding
  - 网络层：ARP Spoofing/Flooding、ICMP Redirect
  - 协议层：DHCP Spoofing、DNS Spoofing
  - 交换机层：MAC Flooding、VLAN Hopping
  - 高级技术：Port Scanning、Traffic Shaping

### 状态管理与通信
- **State Manager**：设备状态、拓扑信息、操作日志的统一管理
- **WebSocket**：实时状态更新、操作日志广播
- **REST API**：完整的RESTful接口，支持所有操作

### 前端界面
- **Dashboard**：网络概览、设备统计、操作监控
- **Device List**：设备管理、状态查看、操作控制
- **Topology**：网络拓扑可视化（React Force Graph）
- **Active Defense**：主动防御操作控制面板
- **Logs**：操作日志和事件查看

> API 与消息格式：见 [docs/api/README.zh-CN.md](docs/api/README.zh-CN.md)。  
> 主动防御细节：见 [docs/active-defense/README.zh-CN.md](docs/active-defense/README.zh-CN.md)。

---

## 开发指南入口
- **文档主页**： [docs/index.zh-CN.md](docs/index.zh-CN.md) / [EN](docs/index.md)
- **主动防御**： [docs/active-defense/README.zh-CN.md](docs/active-defense/README.zh-CN.md) / [EN](docs/active-defense/README.md)
- **主动探测**： [docs/active-probe/ACTIVE_PROBE.zh-CN.md](docs/active-probe/ACTIVE_PROBE.zh-CN.md) / [EN](docs/active-probe/ACTIVE_PROBE.md)
- **API 参考**： [docs/api/README.zh-CN.md](docs/api/README.zh-CN.md) / [EN](docs/api/README.md)
- **平台启动**： macOS（[docs/guides/README-MACOS.zh-CN.md](docs/guides/README-MACOS.zh-CN.md) / [EN](docs/guides/README-MACOS.md)），Windows（[docs/guides/README-WINDOWS.zh-CN.md](docs/guides/README-WINDOWS.zh-CN.md) / [EN](docs/guides/README-WINDOWS.md)）
- **运行时配置**： [docs/guides/ENVIRONMENT.zh-CN.md](docs/guides/ENVIRONMENT.zh-CN.md) / [EN](docs/guides/ENVIRONMENT.md)
- **外部识别服务**： [docs/external-services/EXTERNAL_SERVICES.zh-CN.md](docs/external-services/EXTERNAL_SERVICES.zh-CN.md) / [EN](docs/external-services/EXTERNAL_SERVICES.md)
- **隐私与合规**： [docs/external-services/PRIVACY.zh-CN.md](docs/external-services/PRIVACY.zh-CN.md) / [EN](docs/external-services/PRIVACY.md)
- **Conda 环境（中文）**： [docs/guides/CONDA_SETUP.md](docs/guides/CONDA_SETUP.md)
- **强制关闭功能（中文）**： [docs/guides/FORCE_SHUTDOWN_GUIDE.md](docs/guides/FORCE_SHUTDOWN_GUIDE.md)

---

## 约定与规范
- **提交信息**：Conventional Commits（如 `feat:`, `fix:`，含 BREAKING CHANGE）。
- **版本**：SemVer（`MAJOR.MINOR.PATCH`）。
- **代码风格**：EditorConfig + Lint/Formatter（后端 Ruff/Black；前端 ESLint/Prettier）。
- **配置**：12-Factor，使用环境变量/密钥服务，不在仓库存放敏感信息。

---

## 合规与使用限制

### 授权使用范围
本项目**仅限**以下场景使用：
- ✅ 授权的网络安全研究实验室
- ✅ 自有网络环境的安全测试
- ✅ 学术研究和论文实验
- ✅ 获得书面授权的渗透测试

### 严格禁止
- ❌ 未经授权的网络环境
- ❌ 任何非法或恶意用途
- ❌ 商业化未授权使用
- ❌ 传播给未经审查的第三方

### 法律责任
使用者需完全理解并承担以下责任：
- 确保拥有明确的使用授权
- 遵守所在地区的法律法规
- 对使用行为承担全部法律责任
- 不得将本项目用于任何违法活动

**违反上述限制可能导致严重的法律后果。**

---

## 许可证
本项目采用 MIT License，详见 `/LICENSE`。
