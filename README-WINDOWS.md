# ZenetHunter - Windows 支持指南

本文档说明如何在 Windows 服务器上运行和维护 ZenetHunter。

## 系统要求

- **操作系统**: Windows Server 2016+ 或 Windows 10/11
- **Python**: 3.11 或更高版本
- **权限**: 管理员权限（用于网络扫描和防火墙管理）
- **网络**: 需要访问本地网络和 ARP 表

## 快速开始

### 1. 安装 Python

从 [python.org](https://www.python.org/downloads/) 下载并安装 Python 3.11+。

**重要**: 安装时勾选 "Add Python to PATH"。

### 2. 克隆或下载项目

```powershell
git clone <repository-url>
cd ZenetHunter
```

### 3. 启动后端服务

**方法 1: 使用批处理脚本（推荐）**

```cmd
start-local.bat
```

**方法 2: 手动启动**

```cmd
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e .
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. 访问前端

在浏览器中打开 `html/index.html` 或访问 `http://localhost:8000/docs` 查看 API 文档。

## Windows 特定功能

### 网络扫描

Windows 版本使用 `arp -a` 命令扫描 ARP 表，自动识别网络设备。

**要求**: 
- 普通用户权限即可进行 ARP 表扫描
- 管理员权限用于主动扫描（Scapy）

### 防御功能

Windows 版本使用 **Windows Firewall with Advanced Security** (netsh advfirewall) 进行网络防御。

**要求**: 
- **必须**以管理员身份运行后端服务
- Windows Firewall 服务必须运行

**启动方式**:
1. 右键点击命令提示符
2. 选择"以管理员身份运行"
3. 运行 `start-local.bat`

### 攻击功能

Scapy 在 Windows 上需要：
- 管理员权限
- Npcap 或 WinPcap 驱动程序（用于原始套接字支持）

**安装 Npcap**:
1. 下载: https://npcap.com/
2. 安装时选择 "Install Npcap in WinPcap API-compatible Mode"

## 权限说明

### 管理员权限

以下功能需要管理员权限：

- ✅ **防御功能** (Windows Firewall 规则管理)
- ✅ **主动网络扫描** (Scapy 原始套接字)
- ⚠️ **ARP 表扫描** (普通用户权限即可)

### 以管理员身份运行

**方法 1: 右键运行**
1. 右键点击 `start-local.bat`
2. 选择"以管理员身份运行"

**方法 2: PowerShell**
```powershell
Start-Process powershell -Verb RunAs -ArgumentList "-File", "start-local.bat"
```

## 网络配置

### Windows Firewall

ZenetHunter 会自动管理 Windows Firewall 规则：

- **规则前缀**: `ZenetHunter_`
- **规则类型**: 出站和入站规则
- **管理方式**: 通过 `netsh advfirewall` 命令

**查看规则**:
```cmd
netsh advfirewall firewall show rule name=all | findstr ZenetHunter
```

**手动删除规则** (如果需要):
```cmd
netsh advfirewall firewall delete rule name=ZenetHunter_BlockWAN_XX-XX-XX-XX-XX-XX
```

### 端口配置

默认端口：
- **后端 API**: 8000
- **前端**: 通过 `html/index.html` 本地访问

如需修改，编辑 `start-local.bat` 中的环境变量。

## 故障排除

### 问题 1: ARP 扫描找不到设备

**解决方案**:
1. 检查是否以管理员身份运行
2. 确认网络适配器已启用
3. 运行 `arp -a` 手动检查 ARP 表

### 问题 2: 防御功能无法使用

**解决方案**:
1. 确认以管理员身份运行
2. 检查 Windows Firewall 服务是否运行:
   ```cmd
   sc query MpsSvc
   ```
3. 确认 netsh 命令可用:
   ```cmd
   netsh advfirewall show allprofiles
   ```

### 问题 3: Scapy 无法发送数据包

**解决方案**:
1. 安装 Npcap: https://npcap.com/
2. 安装时选择 "Install Npcap in WinPcap API-compatible Mode"
3. 重启后端服务

### 问题 4: 数据库初始化失败

**解决方案**:
1. 检查 `backend/data/` 目录是否存在且可写
2. 确认 SQLite 数据库路径正确
3. 检查文件权限

## Docker 支持

Windows 上可以使用 Docker Desktop 运行 ZenetHunter：

```cmd
docker compose up -d
```

**注意**: 
- Windows 容器模式需要 Windows Server 2016+ 或 Windows 10/11 Pro/Enterprise
- Linux 容器模式（推荐）需要启用 WSL2

## 安全注意事项

1. **管理员权限**: 仅在需要网络防御功能时使用管理员权限
2. **防火墙规则**: ZenetHunter 创建的防火墙规则会持续存在，重启后仍有效
3. **网络隔离**: Windows Firewall 规则会影响所有网络流量，请谨慎使用
4. **日志记录**: 所有操作都会记录在系统日志中

## 与 Linux/macOS 的差异

| 功能 | Linux | macOS | Windows |
|------|-------|-------|---------|
| ARP 扫描 | ✅ `/proc/net/arp` 或 `ip neigh` | ✅ `arp -an` | ✅ `arp -a` |
| 防火墙 | ✅ iptables | ✅ pfctl | ✅ netsh advfirewall |
| 原始套接字 | ✅ 需要 root | ✅ 需要 root | ✅ 需要管理员 + Npcap |
| MAC 过滤 | ✅ 支持 | ✅ 支持 | ⚠️ 有限支持（需 IP） |

## 技术支持

如遇到问题，请检查：
1. 后端日志: 查看控制台输出
2. 系统日志: Windows 事件查看器
3. API 文档: http://localhost:8000/docs

## 相关文档

- [主 README](README.md)
- [macOS 支持指南](README-MACOS.md) (如果存在)
- [后端文档](backend/README.md)
