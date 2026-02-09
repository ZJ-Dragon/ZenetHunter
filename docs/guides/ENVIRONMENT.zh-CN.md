# 环境变量

本文合并了所有与 ZenetHunter 相关的环境变量，包括系统级/运行时变量和应用配置变量。配置遵循 12‑Factor 模式：优先读取环境变量，`backend/.env` 仅作为本地开发的可选覆盖。

## 配置加载方式
- 优先级：**系统环境变量** → **`backend/.env`** → **代码默认值**（`pydantic-settings`）
- `.env` 位置：在 `backend/.env` 创建文件即可让本地运行读取。
- `start-local.sh` 会在缺省时预填常用值（如 `APP_ENV=development`、`APP_HOST=0.0.0.0`、`APP_PORT=8000`、`LOG_LEVEL=info`、`DATABASE_URL=sqlite+aiosqlite:///./data/zenethunter.db` 以及宽松的 `CORS_ALLOW_ORIGINS`）。

## 本地环境检测（`start-local.sh`）
启动脚本的环境检测顺序：
1) `CONDA_DEFAULT_ENV` 存在且不是 `base` → 使用当前 Conda 环境。
2) `VIRTUAL_ENV` 存在 → 使用已激活的 venv。
3) 存在 `.venv/` 目录 → 自动激活并使用。
4) 否则提示是否继续在系统解释器中运行（不推荐）。

**推荐工作流**
- Conda：`conda env create -f environment.yml && conda activate zenethunter && ./start-local.sh`
- venv：`python3 -m venv .venv && source .venv/bin/activate && ./start-local.sh`
- 需要完整网络扫描时：`sudo ./start-local.sh` 以获取原始套接字权限。

## 系统级与运行时变量
| 变量 | 设置者 | 作用 / 使用位置 |
| --- | --- | --- |
| `CONDA_DEFAULT_ENV` | Conda | `start-local.sh` 环境检测；`base` 视为“无环境”以避免污染。 |
| `VIRTUAL_ENV` | Python venv | `start-local.sh` 环境检测与安装目标选择。 |
| `PYTHONPATH` | 用户/系统 | 可选的导入路径追加；正常安装依赖时通常不需要。 |
| `PATH` | 系统/Shell | 脚本中检测命令（`python3`、`node`、`npm`、`conda`、`lsof`、`netstat`）。 |
| `EUID` / `id -u` | Shell | `start-local.sh` 检测是否具备 root 权限，用于原始网络扫描。 |
| `DOCKER_CONTAINER` / `container` | Docker 运行时 | `backend/app/core/platform/detect.py` 中的 Docker 检测与平台判定。 |
| `LOCAL_IP`（计算得出） | `start-local.sh` | 通过 `ip`/`ifconfig` 获取，本地启动时自动追加到 `CORS_ALLOW_ORIGINS`。 |
| `BACKEND_PID` / `FRONTEND_PID` | `start-local.sh` | 记录 Uvicorn 与 Vite 进程 ID 以便清理。 |
| `npm_package_version` | npm | `frontend/vite.config.ts` 中注入 `__APP_VERSION__` 的构建时版本。 |

## 应用配置变量
以下变量由 `backend/app/core/config.py`（Pydantic Settings）读取，除特别说明外类型为字符串。

### 应用基础
- `APP_ENV`（默认 `development`）：`development` | `staging` | `production`；影响日志默认值与 CORS 期望。
- `API_TITLE` / `APP_NAME`（默认 `ZenetHunter API`）：API 文档显示名称。
- `API_VERSION` / `APP_VERSION`（默认 `0.1.0`）：版本号。
- `APP_HOST`（默认 `0.0.0.0`）：Uvicorn 绑定地址。
- `APP_PORT`（默认 `8000`）：API 端口。

### 日志
- `LOG_LEVEL`（默认 `info`；未显式设置时会随 `APP_ENV` 自动调整到开发 `debug`、生产 `warning`）。可选：`debug`、`info`、`warning`、`error`、`critical`。

### 安全与 CORS
- `SECRET_KEY`（默认值不安全）：**生产必须更换**。
- `ACTIVE_DEFENSE_ENABLED`（布尔，默认 `false`）：主动防御全局开关。
- `ACTIVE_DEFENSE_READONLY`（布尔，默认 `false`）：只读查询模式。
- `CORS_ALLOW_ORIGINS` / `CORS_ORIGINS`（逗号分隔；代码默认 `http://localhost:5173`，`start-local.sh` 会附加本地 IP）：允许的前端来源。

### 数据库
- `DATABASE_URL`（默认 `None` → 使用 `backend/data/zenethunter.db` SQLite；`start-local.sh` 若未设置会显式导出 SQLite DSN）：SQLAlchemy 连接串。

### 路由器集成
- `ROUTER_ADAPTER`（默认 `dummy`）：如 `dummy`、`xiaomi`、`tp-link`。
- `ROUTER_HOST` / `ROUTER_PORT`：路由器 API 地址与端口。
- `ROUTER_USERNAME` / `ROUTER_PASSWORD`：路由器适配器凭据。

### Webhook 验证
- `WEBHOOK_SECRET`（默认 `dev-webhook-secret`）：Webhook 签名密钥。
- `WEBHOOK_TOLERANCE_SEC`（整数，默认 `300`）：时间戳容差（秒）。

### 扫描配置
- `SCAN_MODE`（默认 `hybrid`）：`hybrid`（基于缓存）或 `full`（完整子网）。
- `SCAN_ALLOW_FULL_SUBNET`（布尔，默认 `false`）：允许资源占用较大的完整扫描。
- `SCAN_RANGE`（默认 `192.168.1.0/24`）：完整扫描 CIDR。
- `SCAN_TIMEOUT_SEC`（整数，默认 `30`）：完整扫描超时。
- `SCAN_CONCURRENCY`（整数，默认 `10`）：扫描并发数。
- `SCAN_INTERVAL_SEC`（整数/空，默认 `None`）：自动扫描间隔（秒）。
- `SCAN_REFRESH_WINDOW`（整数，默认 `10`）：混合模式刷新窗口。
- `SCAN_REFRESH_CONCURRENCY`（整数，默认 `10`）：刷新并发数。
- `SCAN_REFRESH_TIMEOUT`（浮点，默认 `1.0`）：单设备刷新超时。

### 功能开关（识别增强）
- `FEATURE_MDNS`（布尔，默认 `true`）：启用 mDNS。
- `FEATURE_SSDP`（布尔，默认 `true`）：启用 SSDP/UPnP。
- `FEATURE_NBNS`（布尔，默认 `false`）：启用 NBNS（Windows 发现）。
- `FEATURE_SNMP`（布尔，默认 `false`）：启用 SNMP（需要凭据）。
- `FEATURE_ACTIVE_PROBE`（布尔，默认 `true`）：启用主动探测（HTTP/Telnet/SSH/打印/IoT）。
- 外部识别服务已移除，默认离线，不会对外请求。

## `backend/.env` 示例
```bash
# 应用
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=debug

# 安全
SECRET_KEY=change-me-32-bytes-min
ACTIVE_DEFENSE_ENABLED=false
ACTIVE_DEFENSE_READONLY=false
CORS_ALLOW_ORIGINS=http://localhost:5173

# 数据库（可选，未设置则使用 SQLite）
# DATABASE_URL=postgresql://user:password@localhost:5432/zenethunter

# 扫描
SCAN_MODE=hybrid
SCAN_ALLOW_FULL_SUBNET=false
SCAN_RANGE=192.168.31.0/24

# 功能开关
FEATURE_MDNS=true
FEATURE_SSDP=true
FEATURE_ACTIVE_PROBE=true
```

## 生产环境检查清单
- 设置 `APP_ENV=production`，并将 `LOG_LEVEL` 调整为 `warning` 或 `error`。
- 生成强随机的 `SECRET_KEY`，敏感信息使用安全存储。
- 明确配置 `CORS_ALLOW_ORIGINS` 为前端域名。
- 需要时提供非 SQLite 的 `DATABASE_URL`。
- 谨慎开启 `ACTIVE_DEFENSE_ENABLED`。

## 故障排查
- 变量未加载：确认 `.env` 位于 `backend/`，使用 `KEY=value`（无空格），修改后重启服务。
- 环境默认值：`LOG_LEVEL` 只有在未显式设置时才会随 `APP_ENV` 自动调整。
- 查看当前配置：`cd backend && python -m app.core.config`（敏感值会被掩码）。
- 本地 CORS：`start-local.sh` 会追加当前局域网 IP 到 `CORS_ALLOW_ORIGINS`；IP 变化时重新运行脚本。
