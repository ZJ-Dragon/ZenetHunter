# ZenetHunter - macOS 支持

ZenetHunter 在 macOS 上提供完整的网络扫描和主动防御功能。

## 平台支持

ZenetHunter 自动检测 macOS 平台并使用 macOS 特定的网络功能：

- **网络扫描**：使用 ARP 表和系统命令
- **防火墙控制**：使用 `pfctl` (Packet Filter)
- **网络配置**：使用 `networksetup` 和 `ifconfig`

## 系统要求

- macOS 10.15 (Catalina) 或更高版本
- Python 3.11+
- 管理员权限（用于网络扫描和防火墙控制）

## 安装

### 1. 安装 Python 依赖

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 2. 安装 Scapy（可选，用于高级网络功能）

```bash
pip install scapy
```

**注意**：在 macOS 上，Scapy 需要管理员权限才能创建原始套接字。如果没有管理员权限，部分功能可能会受限。

## 权限设置

### 网络扫描权限

网络扫描功能需要以下权限：

1. **网络访问权限**：
   - 系统设置 → 隐私与安全性 → 网络访问
   - 允许终端/Python 访问网络

2. **管理员权限**：
   - 某些网络操作需要管理员权限
   - 使用 `sudo` 运行后端服务（如果需要）

### 防火墙控制权限

防火墙控制需要管理员权限。可以使用以下方式运行：

```bash
# 使用 sudo 运行（如果需要防火墙控制）
sudo -E uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**安全提示**：仅在受信任的环境中运行。

## 功能特性

### 支持的攻击类型

在 macOS 上，以下攻击类型可用：

1. **KICK** - WiFi 去认证（需要 WiFi 接口）
2. **BLOCK** - ARP 欺骗/中间人攻击
3. **DHCP_SPOOF** - DHCP 欺骗
4. **DNS_SPOOF** - DNS 欺骗
5. **ICMP_REDIRECT** - ICMP 重定向
6. **PORT_SCAN** - 端口扫描
7. **TRAFFIC_SHAPE** - 流量整形
8. **MAC_FLOOD** - MAC 洪水攻击
9. **BEACON_FLOOD** - WiFi Beacon 洪水

### 网络扫描

macOS 网络扫描使用以下方法：

- ARP 表查询（`arp -a`）
- 网络接口检测（`ifconfig`）
- 系统网络配置（`networksetup`）

## 故障排除

### 问题：无法进行网络扫描

**解决方案**：
1. 检查网络访问权限
2. 确认有网络接口可用：`ifconfig`
3. 检查 ARP 表：`arp -a`
4. 尝试使用 `sudo` 运行

### 问题：防火墙控制失败

**解决方案**：
1. 确认有管理员权限
2. 检查 `pfctl` 是否可用：`which pfctl`
3. 查看系统日志：`log show --predicate 'process == "pfctl"' --last 1m`

### 问题：Scapy 功能受限

**原因**：macOS 对原始套接字的限制

**解决方案**：
1. 使用管理员权限运行
2. 某些功能可能需要禁用 SIP（System Integrity Protection），**不推荐**
3. 使用虚拟网络接口进行测试

## 平台特定注意事项

1. **系统完整性保护 (SIP)**：
   - macOS 的系统完整性保护可能限制某些低级网络操作
   - 大多数功能可以在启用 SIP 的情况下正常工作

2. **防火墙 (pfctl)**：
   - macOS 使用 `pfctl` 作为防火墙后端
   - 规则语法与 Linux `iptables` 不同

3. **网络接口命名**：
   - macOS 使用 BSD 风格的接口命名（如 `en0`, `en1`）
   - 与 Linux 的命名约定不同

## 相关文档

- [主 README](../../README.zh-CN.md) - 项目总览
- [后端 README](../../backend/README.zh-CN.md) - 后端开发指南
- [部署说明](../../README.zh-CN.md) - Docker/一键启动
