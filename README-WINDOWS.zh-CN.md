# ZenetHunter - Windows 支持

ZenetHunter 在 Windows 上提供完整的网络扫描和主动防御功能。

## 平台支持

ZenetHunter 自动检测 Windows 平台并使用 Windows 特定的网络功能：

- **网络扫描**：使用 ARP 表和系统命令
- **防火墙控制**：使用 Windows Firewall (netsh)
- **网络配置**：使用 `ipconfig` 和 `netsh`

## 系统要求

- Windows Server 2016/2019/2022 或 Windows 10/11
- Python 3.11+
- 管理员权限（用于网络扫描和防火墙控制）
- Npcap 或 WinPcap（用于 Scapy 高级网络功能）

## 安装

### 1. 安装 Python

从 [python.org](https://www.python.org/downloads/) 下载并安装 Python 3.11 或更高版本。

### 2. 安装 Npcap（推荐）

Scapy 在 Windows 上需要 Npcap 或 WinPcap：

1. 下载 Npcap：https://npcap.com/
2. 安装 Npcap（推荐使用安装程序的默认选项）
3. 重启计算机（如果提示）

**注意**：Npcap 是 WinPcap 的现代替代品，推荐使用。

### 3. 安装 Python 依赖

```cmd
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e .
```

### 4. 安装 Scapy（可选，用于高级网络功能）

```cmd
pip install scapy
```

## 权限设置

### 管理员权限

Windows 上的网络扫描和防火墙控制需要管理员权限。

**运行方式**：

1. **以管理员身份运行 PowerShell/CMD**：
   - 右键点击 PowerShell 或 CMD
   - 选择"以管理员身份运行"

2. **在管理员 PowerShell 中运行**：
   ```powershell
   cd backend
   .venv\Scripts\activate
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

### 防火墙权限

Windows Firewall 控制需要：

1. **管理员权限**
2. **防火墙管理权限**（通常与管理员权限相同）

## 功能特性

### 支持的攻击类型

在 Windows 上，以下攻击类型可用：

1. **KICK** - WiFi 去认证（需要 WiFi 接口和支持的网卡）
2. **BLOCK** - ARP 欺骗/中间人攻击
3. **DHCP_SPOOF** - DHCP 欺骗
4. **DNS_SPOOF** - DNS 欺骗
5. **ICMP_REDIRECT** - ICMP 重定向
6. **PORT_SCAN** - 端口扫描
7. **TRAFFIC_SHAPE** - 流量整形（通过 Windows QoS）
8. **MAC_FLOOD** - MAC 洪水攻击

### 网络扫描

Windows 网络扫描使用以下方法：

- ARP 表查询（`arp -a`）
- 网络接口检测（`ipconfig`）
- 网络配置（`netsh`）

### 防火墙控制

Windows Firewall 通过 `netsh` 命令管理：

```cmd
# 查看防火墙状态
netsh advfirewall show allprofiles

# 添加防火墙规则（示例）
netsh advfirewall firewall add rule name="Allow Port 8000" dir=in action=allow protocol=TCP localport=8000
```

## 故障排除

### 问题：无法进行网络扫描

**解决方案**：
1. 确认以管理员身份运行
2. 检查网络接口：`ipconfig /all`
3. 检查 ARP 表：`arp -a`
4. 确认 Npcap 已正确安装

### 问题：Scapy 无法工作

**常见原因和解决方案**：

1. **未安装 Npcap/WinPcap**：
   ```cmd
   # 检查 Npcap 是否安装
   # 查看控制面板 → 程序和功能
   # 或运行：sc query npcap
   ```

2. **Npcap 版本不兼容**：
   - 卸载旧版本
   - 安装最新版本的 Npcap

3. **权限不足**：
   - 确保以管理员身份运行
   - 某些操作需要提升的权限

### 问题：防火墙控制失败

**解决方案**：
1. 确认以管理员身份运行 PowerShell/CMD
2. 检查 `netsh` 是否可用：`where netsh`
3. 测试防火墙命令：`netsh advfirewall show allprofiles`
4. 检查 Windows Firewall 服务是否运行：
   ```cmd
   sc query MpsSvc
   ```

### 问题：端口被占用

**解决方案**：
```cmd
# 查看端口占用
netstat -ano | findstr :8000

# 结束占用进程（替换 PID）
taskkill /PID <PID> /F
```

## 平台特定注意事项

1. **Windows Firewall**：
   - Windows 使用高级防火墙 (Advanced Firewall)
   - 规则通过 `netsh advfirewall` 管理
   - 语法与 Linux `iptables` 完全不同

2. **网络接口**：
   - Windows 使用友好的接口名称
   - 可以通过 `netsh interface show interface` 查看

3. **原始套接字限制**：
   - Windows 对原始套接字有更严格的限制
   - 某些功能可能需要 Npcap 的特殊权限

4. **用户账户控制 (UAC)**：
   - UAC 可能阻止某些操作
   - 需要确认提升权限提示

## 安全注意事项

1. **管理员权限**：
   - 仅在受信任的环境中运行
   - 不要在生产环境中长期以管理员身份运行

2. **Windows Defender**：
   - Windows Defender 可能将某些网络工具标记为威胁
   - 可能需要添加例外

3. **企业环境**：
   - 企业网络策略可能限制网络扫描
   - 联系 IT 管理员获取权限

## 相关文档

- [主 README](README.md) - 完整的项目文档
- [后端 README](backend/README.md) - 后端开发指南
- [部署文档](deploy/README.md) - 部署说明
