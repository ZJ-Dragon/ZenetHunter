# macOS 支持说明

ZenetHunter 现已全面支持 macOS 平台运行。系统会自动检测 macOS 并选择相应的实现。

## 特性

### ✅ 已支持的功能

1. **网络扫描**
   - ARP 表扫描（使用 `arp -an` 命令）
   - 主动 ARP 扫描（使用 Scapy，需要 root 权限）
   - 自动检测网络接口和网关

2. **防御功能**
   - macOS 使用 `pfctl` (Packet Filter) 进行防火墙管理
   - 支持 BLOCK_WAN（阻断外网访问）
   - 支持 QUARANTINE（完全隔离）
   - 需要 root 权限

3. **攻击功能**
   - WiFi Deauthentication（需要 root 权限）
   - ARP Spoofing（需要 root 权限）
   - 使用 Scapy 进行数据包注入

4. **平台检测**
   - 自动检测 macOS 平台
   - 检测可用工具（arp, pfctl, networksetup 等）
   - 检测 root 权限

## 使用方法

### 1. 本地运行（推荐）

```bash
# 启动后端
./start-local.sh

# 或手动启动
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. 权限要求

某些功能需要管理员权限：

```bash
# 使用 sudo 运行（需要 root 权限的功能）
sudo python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**需要 root 权限的功能：**
- 主动网络扫描（Scapy ARP 扫描）
- 防御策略应用（pfctl 防火墙规则）
- 网络攻击功能（数据包注入）

**不需要 root 权限的功能：**
- 被动 ARP 表扫描
- 设备列表查看
- 网络拓扑查看
- 系统日志查看

### 3. 系统要求

- macOS 10.14+ (Mojave 或更高版本)
- Python 3.11+
- 网络工具：`arp`, `ifconfig`, `route`（系统自带）
- 防火墙工具：`pfctl`（系统自带，需要 root）

### 4. 依赖安装

```bash
cd backend
pip install -e .
```

主要依赖：
- `scapy>=2.5.0` - 网络数据包操作（需要 root）
- `fastapi` - Web 框架
- `uvicorn` - ASGI 服务器

## 平台特定功能

### macOS 网络工具

系统会自动检测并使用以下工具：

- **arp**: ARP 表查询
- **ifconfig**: 网络接口配置
- **route**: 路由表查询
- **pfctl**: 防火墙管理（需要 root）
- **networksetup**: 网络配置（需要 root）

### macOS 防御引擎

macOS 使用 `pfctl` (Packet Filter) 而不是 Linux 的 `iptables`：

- 规则文件：`/tmp/zenethunter_pf_rules.conf`
- 需要 root 权限来加载规则
- 支持基于 MAC 地址的流量过滤

## 故障排除

### 问题：扫描功能不可用

**解决方案：**
1. 检查是否有 `arp` 命令：`which arp`
2. 检查网络接口：`ifconfig -l`
3. 尝试手动运行：`arp -an`

### 问题：防御功能不可用

**解决方案：**
1. 确保以 root 权限运行：`sudo python ...`
2. 检查 `pfctl` 是否可用：`which pfctl`
3. 检查防火墙状态：`sudo pfctl -s info`

### 问题：攻击功能不可用

**解决方案：**
1. 确保以 root 权限运行
2. 检查 Scapy 是否安装：`python -c "import scapy; print(scapy.__version__)"`
3. 检查网络接口权限

## 技术细节

### 平台检测

系统使用 `app.core.platform.detect` 模块自动检测：
- 操作系统类型
- 可用工具
- 权限级别
- Docker 环境

### macOS 特定实现

- **扫描器**: `app.services.scanner` - 使用 `arp -an` 解析
- **防御引擎**: `app.core.engine.macos_defense` - 使用 `pfctl`
- **网络功能**: `app.core.engine.features_macos` - macOS 网络工具封装

### 代码结构

```
backend/
├── app/
│   ├── core/
│   │   ├── platform/
│   │   │   ├── detect.py          # 平台检测
│   │   │   └── __init__.py
│   │   └── engine/
│   │       ├── features_macos.py  # macOS 网络功能
│   │       ├── macos_defense.py    # macOS 防御引擎
│   │       └── defense_factory.py # 自动选择引擎
```

## 与 Linux 的差异

| 功能 | Linux | macOS |
|------|-------|-------|
| 防火墙 | iptables/nftables | pfctl |
| ARP 表 | `/proc/net/arp` 或 `ip neigh` | `arp -an` |
| 网络接口 | `ip link` | `ifconfig` |
| 路由表 | `ip route` | `route get` |
| 权限检查 | `/proc/self/status` | `os.geteuid()` |

## 开发说明

所有平台特定代码都通过工厂模式自动选择：
- `defense_factory.py` - 自动选择防御引擎
- `factory.py` - 自动选择攻击引擎
- `scanner.py` - 自动选择扫描方法

无需手动配置，系统会自动检测并选择正确的实现。
