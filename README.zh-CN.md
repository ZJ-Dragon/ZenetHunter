

# ZenetHunter

> **网络安全主动防御研究平台**。专注于授权环境下的主动防御技术研究，包含网络扫描、设备发现、主动防御引擎、状态管理和可视化界面。

⚠️ **安全声明**：仓库包含网络扫描/主动干扰脚本，仅可在**自有或获授权的局域网/实验环境**使用；在未授权网络上使用可能违法。

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

> Docker/Compose 工作流已移除，使用上述本地脚本进行开发运行。

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
