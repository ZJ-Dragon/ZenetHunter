# 环境变量配置说明

## 概述

ZenetHunter 遵循 [12-Factor App](https://12factor.net/config) 方法论，使用环境变量进行配置。所有配置都从环境变量加载，本地开发时支持可选的 `.env` 文件。

## 环境变量文件位置

### 主要位置：`.env` 文件

在 **backend 目录**（`backend/.env`）中创建 `.env` 文件：

```bash
cd backend
touch .env
```

使用 `pydantic-settings` 时，应用程序会自动从此文件加载变量。

### 替代方案：系统环境变量

您也可以在 shell 中直接设置环境变量：

```bash
# Linux/macOS
export APP_ENV=production
export APP_PORT=8000

# Windows (PowerShell)
$env:APP_ENV="production"
$env:APP_PORT="8000"
```

### 优先级顺序

1. **系统环境变量**（最高优先级）
2. **`.env` 文件**（在 `backend/` 目录中）
3. **默认值**（最低优先级）

---

## 配置分类

### 1. 应用基础配置

#### `APP_ENV`
- **类型**: 字符串
- **默认值**: `development`
- **可选值**: `development`, `staging`, `production`
- **说明**: 应用运行环境。影响日志级别和 CORS 默认值。
- **示例**:
  ```bash
  APP_ENV=production
  ```

#### `API_TITLE` / `APP_NAME`
- **类型**: 字符串
- **默认值**: `ZenetHunter API`
- **说明**: 在 API 文档中显示的应用名称。
- **示例**:
  ```bash
  API_TITLE=ZenetHunter 网络扫描器
  ```

#### `API_VERSION` / `APP_VERSION`
- **类型**: 字符串
- **默认值**: `0.1.0`
- **说明**: 应用版本号。
- **示例**:
  ```bash
  API_VERSION=1.0.0
  ```

#### `APP_HOST`
- **类型**: 字符串
- **默认值**: `0.0.0.0`
- **说明**: 服务器绑定的主机地址。
- **示例**:
  ```bash
  APP_HOST=0.0.0.0  # 监听所有网络接口
  APP_HOST=127.0.0.1  # 仅监听本地回环
  ```

#### `APP_PORT`
- **类型**: 整数
- **默认值**: `8000`
- **说明**: API 服务器的端口号。
- **示例**:
  ```bash
  APP_PORT=8000
  ```

---

### 2. 日志配置

#### `LOG_LEVEL`
- **类型**: 字符串
- **默认值**: `info`（根据 `APP_ENV` 自动调整）
- **可选值**: `debug`, `info`, `warning`, `error`, `critical`
- **说明**: 日志详细程度级别。
  - **开发环境**: 默认为 `debug`
  - **预发布环境**: 默认为 `info`
  - **生产环境**: 默认为 `warning`
- **示例**:
  ```bash
  LOG_LEVEL=debug  # 显示所有日志，包括调试信息
  LOG_LEVEL=warning  # 仅显示警告和错误
  ```

---

### 3. 安全配置

#### `SECRET_KEY`
- **类型**: 字符串
- **默认值**: `insecure-dev-secret-key-do-not-use-in-production`
- **说明**: 用于加密操作的密钥。**生产环境必须修改！**
- **示例**:
  ```bash
  SECRET_KEY=your-super-secret-key-here-min-32-chars
  ```
- **⚠️ 警告**: 生产环境切勿使用默认值。生成安全的随机密钥：
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(32))"
  ```

#### `ACTIVE_DEFENSE_ENABLED`
- **类型**: 布尔值
- **默认值**: `false`
- **说明**: 主动防御功能的全局开关。必须显式启用。
- **示例**:
  ```bash
  ACTIVE_DEFENSE_ENABLED=true  # 启用主动防御
  ACTIVE_DEFENSE_ENABLED=false  # 禁用（安全默认值）
  ```

#### `ACTIVE_DEFENSE_READONLY`
- **类型**: 布尔值
- **默认值**: `false`
- **说明**: 只读模式：允许查询主动防御状态，但禁止执行操作。
- **示例**:
  ```bash
  ACTIVE_DEFENSE_READONLY=true  # 仅查询，不执行
  ```

#### `CORS_ALLOW_ORIGINS` / `CORS_ORIGINS`
- **类型**: 字符串（逗号分隔）
- **默认值**: `http://localhost:5173`（开发环境）
- **说明**: 允许的前端 CORS 源。逗号分隔的列表。
- **示例**:
  ```bash
  # 单个源
  CORS_ALLOW_ORIGINS=http://localhost:5173
  
  # 多个源
  CORS_ALLOW_ORIGINS=http://localhost:5173,https://zenethunter.example.com
  
  # 生产环境（必须显式设置）
  CORS_ALLOW_ORIGINS=https://zenethunter.example.com
  ```

---

### 4. 数据库配置

#### `DATABASE_URL`
- **类型**: 字符串（SQLAlchemy 连接字符串）
- **默认值**: `None`（使用 `backend/data/` 中的 SQLite）
- **说明**: 数据库连接 URL。如果未设置，使用 SQLite。
- **示例**:
  ```bash
  # SQLite（默认，无需配置）
  # 数据库文件：backend/data/zenethunter.db
  
  # PostgreSQL
  DATABASE_URL=postgresql://user:password@localhost:5432/zenethunter
  
  # MySQL
  DATABASE_URL=mysql+pymysql://user:password@localhost:3306/zenethunter
  
  # SQLite（显式）
  DATABASE_URL=sqlite:///./data/zenethunter.db
  ```

---

### 5. 路由器集成配置

#### `ROUTER_ADAPTER`
- **类型**: 字符串
- **默认值**: `dummy`
- **可选值**: `dummy`, `xiaomi`, `tp-link` 等
- **说明**: 用于集成的路由器适配器类型。
- **示例**:
  ```bash
  ROUTER_ADAPTER=xiaomi
  ```

#### `ROUTER_HOST`
- **类型**: 字符串
- **默认值**: `None`
- **说明**: 路由器 IP 地址或主机名。
- **示例**:
  ```bash
  ROUTER_HOST=192.168.31.1
  ROUTER_HOST=router.example.com
  ```

#### `ROUTER_PORT`
- **类型**: 整数
- **默认值**: `None`
- **说明**: 路由器 API 端口。
- **示例**:
  ```bash
  ROUTER_PORT=8080
  ```

#### `ROUTER_USERNAME`
- **类型**: 字符串
- **默认值**: `None`
- **说明**: 路由器 API 用户名。
- **示例**:
  ```bash
  ROUTER_USERNAME=admin
  ```

#### `ROUTER_PASSWORD`
- **类型**: 字符串
- **默认值**: `None`
- **说明**: 路由器 API 密码。
- **示例**:
  ```bash
  ROUTER_PASSWORD=your-router-password
  ```
- **⚠️ 安全**: 生产环境请考虑使用密钥管理。

---

### 6. Webhook 配置

#### `WEBHOOK_SECRET`
- **类型**: 字符串
- **默认值**: `dev-webhook-secret`
- **说明**: Webhook 签名验证密钥。
- **示例**:
  ```bash
  WEBHOOK_SECRET=your-webhook-secret-key
  ```

#### `WEBHOOK_TOLERANCE_SEC`
- **类型**: 整数
- **默认值**: `300`（5 分钟）
- **说明**: Webhook 时间戳验证的时间容差（秒）。
- **示例**:
  ```bash
  WEBHOOK_TOLERANCE_SEC=300
  ```

---

### 7. 扫描配置

#### `SCAN_MODE`
- **类型**: 字符串
- **默认值**: `hybrid`
- **可选值**: `hybrid`, `full`
- **说明**: 扫描模式。
  - `hybrid`: 基于缓存的扫描（快速，使用 ARP/DHCP 缓存）
  - `full`: 完整子网扫描（较慢，全面）
- **示例**:
  ```bash
  SCAN_MODE=hybrid  # 大多数用例推荐
  SCAN_MODE=full  # 完整子网扫描
  ```

#### `SCAN_ALLOW_FULL_SUBNET`
- **类型**: 布尔值
- **默认值**: `false`
- **说明**: 允许完整子网扫描（高资源消耗）。
- **示例**:
  ```bash
  SCAN_ALLOW_FULL_SUBNET=true  # 启用完整子网扫描
  ```

#### `SCAN_RANGE`
- **类型**: 字符串（CIDR 表示法）
- **默认值**: `192.168.1.0/24`
- **说明**: 完整子网扫描的 CIDR 范围（仅高级模式）。通常从网络自动检测。
- **示例**:
  ```bash
  SCAN_RANGE=192.168.31.0/24
  SCAN_RANGE=10.0.0.0/16
  ```

#### `SCAN_TIMEOUT_SEC`
- **类型**: 整数
- **默认值**: `30`
- **说明**: 完整扫描超时时间（秒）。
- **示例**:
  ```bash
  SCAN_TIMEOUT_SEC=60  # 增加大型网络的超时时间
  ```

#### `SCAN_CONCURRENCY`
- **类型**: 整数
- **默认值**: `10`
- **说明**: 完整扫描的最大并发探测数。
- **示例**:
  ```bash
  SCAN_CONCURRENCY=20  # 增加并发数以加快扫描（更多 CPU/网络）
  ```

#### `SCAN_INTERVAL_SEC`
- **类型**: 整数或空
- **默认值**: `None`（仅手动扫描）
- **说明**: 定期自动扫描的间隔（秒）。设置为 `None` 或空表示仅手动扫描。
- **示例**:
  ```bash
  SCAN_INTERVAL_SEC=300  # 每 5 分钟自动扫描
  # 留空表示仅手动扫描
  ```

#### `SCAN_REFRESH_WINDOW`
- **类型**: 整数
- **默认值**: `10`
- **说明**: 候选刷新窗口（秒，用于混合模式）。
- **示例**:
  ```bash
  SCAN_REFRESH_WINDOW=10
  ```

#### `SCAN_REFRESH_CONCURRENCY`
- **类型**: 整数
- **默认值**: `10`
- **说明**: 最大并发刷新探测数。
- **示例**:
  ```bash
  SCAN_REFRESH_CONCURRENCY=10
  ```

#### `SCAN_REFRESH_TIMEOUT`
- **类型**: 浮点数
- **默认值**: `1.0`
- **说明**: 每个设备的刷新探测超时时间（秒）。
- **示例**:
  ```bash
  SCAN_REFRESH_TIMEOUT=1.0
  ```

---

### 8. 功能开关（设备识别增强）

#### `FEATURE_MDNS`
- **类型**: 布尔值
- **默认值**: `true`
- **说明**: 启用 mDNS（组播 DNS）增强以发现设备。
- **示例**:
  ```bash
  FEATURE_MDNS=true
  FEATURE_MDNS=false  # 禁用 mDNS
  ```

#### `FEATURE_SSDP`
- **类型**: 布尔值
- **默认值**: `true`
- **说明**: 启用 SSDP/UPnP 增强以发现设备。
- **示例**:
  ```bash
  FEATURE_SSDP=true
  ```

#### `FEATURE_NBNS`
- **类型**: 布尔值
- **默认值**: `false`
- **说明**: 启用 NBNS（NetBIOS 名称服务）以发现 Windows 设备。
- **示例**:
  ```bash
  FEATURE_NBNS=true  # 为 Windows 网络启用
  ```

#### `FEATURE_SNMP`
- **类型**: 布尔值
- **默认值**: `false`
- **说明**: 启用 SNMP 查询（需要凭据）。
- **示例**:
  ```bash
  FEATURE_SNMP=true  # 需要 SNMP 凭据
  ```

#### `FEATURE_ACTIVE_PROBE`
- **类型**: 布尔值
- **默认值**: `true`
- **说明**: 启用主动探测（HTTP、Telnet、SSH、打印机、IoT 协议）。模拟正常服务器连接以获取设备信息。
- **示例**:
  ```bash
  FEATURE_ACTIVE_PROBE=true  # 启用主动设备探测
  FEATURE_ACTIVE_PROBE=false  # 禁用（更快但准确性较低）
  ```

#### `FEATURE_FINGERBANK`
- **类型**: 布尔值
- **默认值**: `false`
- **说明**: 启用 Fingerbank API 进行外部设备指纹识别（需要 API 密钥）。
- **示例**:
  ```bash
  FEATURE_FINGERBANK=true  # 需要 FINGERBANK_API_KEY
  ```

---

### 9. 外部识别服务提供商

#### `FEATURE_EXTERNAL_LOOKUP`
- **类型**: 布尔值
- **默认值**: `false`
- **说明**: 启用外部识别服务提供商（MACVendors、Fingerbank）。**默认：False（安全默认值）**。UI 和软件层面添加软限制。
- **示例**:
  ```bash
  FEATURE_EXTERNAL_LOOKUP=true  # 启用外部查询
  FEATURE_EXTERNAL_LOOKUP=false  # 禁用（隐私安全默认值）
  ```

#### `EXTERNAL_LOOKUP_OUI_ONLY`
- **类型**: 布尔值
- **默认值**: `true`
- **说明**: 仅 OUI 模式：仅发送 OUI 前缀（前 3 个字节），不发送完整 MAC。隐私保护（默认：True）。
- **示例**:
  ```bash
  EXTERNAL_LOOKUP_OUI_ONLY=true  # 隐私模式（推荐）
  EXTERNAL_LOOKUP_OUI_ONLY=false  # 发送完整 MAC（隐私性较低）
  ```

#### `FINGERBANK_API_KEY`
- **类型**: 字符串
- **默认值**: `None`
- **说明**: Fingerbank API 密钥（Fingerbank 提供商必需）。从 [Fingerbank](https://www.fingerbank.org/) 获取密钥。
- **示例**:
  ```bash
  FINGERBANK_API_KEY=your-fingerbank-api-key-here
  ```

---

## `.env` 文件示例

在 `backend/.env` 中创建您的配置：

```bash
# 应用配置
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=debug

# 安全配置
SECRET_KEY=your-super-secret-key-here-min-32-chars
ACTIVE_DEFENSE_ENABLED=false
ACTIVE_DEFENSE_READONLY=false
CORS_ALLOW_ORIGINS=http://localhost:5173

# 数据库（可选，默认使用 SQLite）
# DATABASE_URL=postgresql://user:password@localhost:5432/zenethunter

# 扫描配置
SCAN_MODE=hybrid
SCAN_ALLOW_FULL_SUBNET=false
SCAN_RANGE=192.168.31.0/24

# 功能开关
FEATURE_MDNS=true
FEATURE_SSDP=true
FEATURE_ACTIVE_PROBE=true
FEATURE_EXTERNAL_LOOKUP=false
EXTERNAL_LOOKUP_OUI_ONLY=true

# 外部识别（可选）
# FINGERBANK_API_KEY=your-api-key-here
```

---

## 生产环境检查清单

部署到生产环境前，请确保：

- [ ] `APP_ENV=production`
- [ ] `SECRET_KEY` 设置为安全的随机值
- [ ] `CORS_ALLOW_ORIGINS` 显式设置为您的前端域名
- [ ] `LOG_LEVEL=warning` 或 `error`
- [ ] `ACTIVE_DEFENSE_ENABLED` 适当设置
- [ ] `DATABASE_URL` 已配置（如果不使用 SQLite）
- [ ] 所有敏感值（密码、API 密钥）安全存储

---

## 故障排除

### 变量未加载

1. **检查文件位置**: 确保 `.env` 在 `backend/` 目录中
2. **检查语法**: `=` 号周围不要有空格：`KEY=value`（不是 `KEY = value`）
3. **检查引号**: 仅在值包含空格时使用引号：`KEY="value with spaces"`
4. **重启服务器**: 对 `.env` 的更改需要重启服务器

### 环境特定默认值

某些变量根据 `APP_ENV` 有不同的默认值：
- **开发环境**: `LOG_LEVEL` 默认为 `debug`，CORS 允许 `localhost:5173`
- **生产环境**: `LOG_LEVEL` 默认为 `warning`，CORS 必须显式设置

### 验证

检查当前配置：
```bash
cd backend
python -m app.core.config
```

这将打印当前设置（敏感值会被屏蔽）。

---

## 参考

- [12-Factor App: Config](https://12factor.net/config)
- [Pydantic Settings 文档](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [FastAPI Settings](https://fastapi.tiangolo.com/advanced/settings/)
