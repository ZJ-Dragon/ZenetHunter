# 平台检测模块

此模块提供平台检测和平台特定功能可用性检查。

## 功能

- **自动平台检测**：检测 Linux、macOS、Windows 和其他平台
- **Windows 支持**：完全支持 Windows Server 和 Windows 10/11，集成 Windows 防火墙
- **功能可用性**：检查平台特定的工具和功能
- **Root/Admin 检测**：检测是否以提升的权限运行
- **Docker 检测**：检测是否在 Docker 容器内运行

## 使用方法

```python
from app.core.platform.detect import get_platform_features, is_macos, is_linux, is_windows

# 获取平台功能
features = get_platform_features()
print(f"平台: {features.platform.value}")
print(f"是否 root: {features.is_root}")
print(f"是否有 Scapy: {features.has_scapy}")

# 快速检查
if is_macos():
    # macOS 特定代码
    pass
elif is_linux():
    # Linux 特定代码
    pass
```

## 平台特定功能

### macOS
- `pfctl`：数据包过滤器防火墙
- `networksetup`：网络配置
- `arp`：ARP 表访问
- `ifconfig`：接口配置

### Linux
- `iptables`：防火墙规则
- `ip`：现代网络配置
- `arp`：ARP 表访问
- `/proc/net/arp`：ARP 表文件

### Windows
- `netsh`：网络外壳和 Windows 防火墙管理
- `arp`：ARP 表访问（通过 `arp -a`）
- `ipconfig`：网络配置
- Windows 防火墙：高级防火墙，带规则管理

## 集成

平台检测自动用于：
- 防御引擎工厂 (`defense_factory.py`)
- 扫描器服务 (`scanner.py`)
- 系统信息端点 (`routes/logs.py`)
