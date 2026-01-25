# 系统级环境变量说明

## 概述

本文档说明 ZenetHunter 使用的**系统级环境变量**。这些变量通常由操作系统、Python 运行时或 shell 环境设置，而不是应用程序特定的配置变量。

> **注意**：关于应用程序配置变量（如 `APP_ENV`、`DATABASE_URL` 等），请参阅 [ENVIRONMENT.zh-CN.md](ENVIRONMENT.zh-CN.md)。

---

## Python 环境变量

### `VIRTUAL_ENV`

- **类型**: 字符串（路径）
- **设置者**: Python `venv` 模块（激活虚拟环境时）
- **用途**: 指示当前激活的 Python 虚拟环境的路径
- **使用位置**: `start-local.sh` 用于环境检测
- **示例**:
  ```bash
  # 当 venv 被激活时
  echo $VIRTUAL_ENV
  # 输出: /path/to/project/backend/.venv
  ```
- **检测**:
  ```bash
  if [ -z "$VIRTUAL_ENV" ]; then
      echo "不在虚拟环境中"
  fi
  ```

### `CONDA_DEFAULT_ENV`

- **类型**: 字符串
- **设置者**: Conda（激活 conda 环境时）
- **用途**: 当前激活的 conda 环境的名称
- **使用位置**: `start-local.sh` 用于 conda 环境检测
- **示例**:
  ```bash
  # 当 conda 环境被激活时
  conda activate zenethunter
  echo $CONDA_DEFAULT_ENV
  # 输出: zenethunter
  ```
- **检测**:
  ```bash
  if [ ! -z "$CONDA_DEFAULT_ENV" ] && [ "$CONDA_DEFAULT_ENV" != "base" ]; then
      echo "在 conda 环境中: $CONDA_DEFAULT_ENV"
  fi
  ```
- **⚠️ 注意**: 脚本将 `base` 环境视为"无环境"，以防止污染。

### `PYTHONPATH`

- **类型**: 字符串（Unix 上为冒号分隔，Windows 上为分号分隔）
- **设置者**: 用户或系统
- **用途**: 搜索 Python 模块的额外目录
- **使用位置**: Python 导入解析
- **示例**:
  ```bash
  export PYTHONPATH="/custom/path:$PYTHONPATH"
  python -c "import mymodule"  # 将在 /custom/path 中搜索
  ```
- **⚠️ 注意**: 如果使用正确的包安装方式（`pip install -e .`），通常不需要设置。

---

## 操作系统变量

### `EUID` / `$(id -u)`

- **类型**: 整数
- **设置者**: Shell（有效用户 ID）
- **用途**: 检测脚本是否以 root/管理员权限运行
- **使用位置**: `start-local.sh` 用于 root 检测
- **示例**:
  ```bash
  if [ "$EUID" -eq 0 ] || [ "$(id -u)" -eq 0 ]; then
      echo "以 root 权限运行"
  fi
  ```
- **取值**:
  - `0`: Root 用户（Unix/Linux）或管理员（Windows）
  - `> 0`: 普通用户
- **影响**: Root 权限启用完整的网络扫描功能（ARP 扫描、原始套接字等）

### `PATH`

- **类型**: 字符串（冒号分隔的路径）
- **设置者**: 系统/shell
- **用途**: 搜索可执行命令的目录
- **使用位置**: 命令检测（`command -v python3`、`command -v node` 等）
- **示例**:
  ```bash
  # 检查命令是否存在
  if ! command -v python3 &> /dev/null; then
      echo "PATH 中未找到 python3"
  fi
  ```
- **项目中常见检查**:
  - `python3`: Python 解释器
  - `node`: Node.js 运行时
  - `npm`: Node.js 包管理器
  - `conda`: Conda 包管理器
  - `lsof`: 列出打开的文件（用于端口检查）
  - `netstat`: 网络统计（用于端口检查）

### `DOCKER_CONTAINER` / `container`

- **类型**: 字符串（通常为 "1" 或空）
- **设置者**: Docker 运行时
- **用途**: 指示代码是否在 Docker 容器内运行
- **使用位置**: `backend/app/core/platform/detect.py` 用于平台检测
- **示例**:
  ```python
  if os.getenv("DOCKER_CONTAINER") or os.getenv("container"):
      # 在 Docker 中运行
      platform_type = "docker"
  ```
- **检测**:
  ```python
  is_docker = bool(os.getenv("DOCKER_CONTAINER") or os.getenv("container"))
  ```

### `uname -s`（通过命令）

- **类型**: 字符串
- **设置者**: 系统（`uname` 命令）
- **用途**: 操作系统类型检测
- **使用位置**: `start-local.sh` 用于特定于操作系统的配置
- **示例**:
  ```bash
  OS_TYPE=$(uname -s)
  case "$OS_TYPE" in
      "Darwin")
          echo "检测到 macOS"
          ;;
      "Linux")
          echo "检测到 Linux"
          ;;
      *)
          echo "其他操作系统: $OS_TYPE"
          ;;
  esac
  ```
- **常见取值**:
  - `Darwin`: macOS
  - `Linux`: Linux
  - `CYGWIN*`, `MINGW*`, `MSYS*`: Windows（通过 Cygwin/Git Bash）

---

## 网络检测变量

### 本地 IP 地址检测

- **方法**: 不是单个变量，而是通过系统命令检测
- **使用位置**: `start-local.sh` 用于 CORS 配置
- **检测方法**:
  ```bash
  # 方法 1: 使用 `ip` 命令（Linux）
  ip route get 8.8.8.8 2>/dev/null | awk '{print $7; exit}'
  
  # 方法 2: 使用 `ifconfig`（macOS/Linux）
  ifconfig | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | \
      grep -v '127.0.0.1' | awk '{print $2}' | head -1
  ```
- **用途**: 自动将本地网络 IP 添加到 CORS 允许源
- **示例**:
  ```bash
  LOCAL_IP=$(get_local_ip)
  if [ -n "$LOCAL_IP" ]; then
      export CORS_ALLOW_ORIGINS="$CORS_ALLOW_ORIGINS,http://$LOCAL_IP:5173"
  fi
  ```

---

## Shell 环境变量

### `SCRIPT_DIR`

- **类型**: 字符串（路径）
- **设置者**: `start-local.sh` 脚本自身
- **用途**: 存储脚本所在的目录
- **使用位置**: 相对操作的路径解析
- **示例**:
  ```bash
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  cd "$SCRIPT_DIR"
  ```

### `PWD` / `$(pwd)`

- **类型**: 字符串（路径）
- **设置者**: Shell
- **用途**: 当前工作目录
- **使用位置**: 导航和路径解析
- **示例**:
  ```bash
  cd backend
  echo "当前目录: $(pwd)"
  # 输出: /path/to/project/backend
  ```

---

## 进程管理变量

### 进程 ID (PIDs)

- **类型**: 整数
- **设置者**: 脚本（`start-local.sh`）
- **用途**: 跟踪运行中的进程以便清理
- **变量**:
  - `BACKEND_PID`: Uvicorn 服务器进程 ID
  - `FRONTEND_PID`: Vite 开发服务器进程 ID
- **示例**:
  ```bash
  uvicorn app.main:app --host 0.0.0.0 --port 8000 &
  BACKEND_PID=$!
  echo "后端 PID: $BACKEND_PID"
  
  # 稍后，清理
  if kill -0 $BACKEND_PID 2>/dev/null; then
      kill -TERM $BACKEND_PID
  fi
  ```

---

## 环境检测优先级

`start-local.sh` 脚本使用以下优先级进行环境检测：

```
1. Conda 环境 (CONDA_DEFAULT_ENV)
   └─ 如果已设置且不是 "base" → 使用 conda 环境
   
2. 虚拟环境 (VIRTUAL_ENV)
   └─ 如果已设置 → 使用 venv 环境
   
3. 本地 .venv 目录
   └─ 如果存在 → 激活并使用
   
4. 系统环境
   └─ 警告用户并要求确认
```

---

## 如何设置系统变量

### 临时（当前会话）

```bash
# Linux/macOS
export VIRTUAL_ENV=/path/to/venv
export CONDA_DEFAULT_ENV=zenethunter
export PYTHONPATH=/custom/path:$PYTHONPATH

# Windows (PowerShell)
$env:VIRTUAL_ENV="C:\path\to\venv"
$env:CONDA_DEFAULT_ENV="zenethunter"
```

### 持久（用户配置文件）

**Linux/macOS** (`~/.bashrc` 或 `~/.zshrc`):
```bash
export PYTHONPATH="$HOME/custom/path:$PYTHONPATH"
```

**Windows**（系统属性 → 环境变量）:
- 通过 GUI 添加或使用 setx 命令

### 在脚本中

```bash
#!/bin/bash
# 在脚本顶部设置变量
export APP_ENV=development
export DATABASE_URL="sqlite+aiosqlite:///./data/zenethunter.db"
```

---

## 验证命令

### 检查当前环境

```bash
# 检查 Python 环境
echo "VIRTUAL_ENV: $VIRTUAL_ENV"
echo "CONDA_DEFAULT_ENV: $CONDA_DEFAULT_ENV"
echo "Python: $(which python3)"
echo "Python 版本: $(python3 --version)"

# 检查系统信息
echo "操作系统: $(uname -s)"
echo "用户: $(whoami)"
echo "EUID: $EUID"
echo "是否为 root: $([ "$EUID" -eq 0 ] && echo "是" || echo "否")"

# 检查 PATH
echo "PATH: $PATH"
echo "PATH 中的 Python: $(command -v python3)"
```

### 检查 Docker 环境

```bash
# 检查是否在 Docker 中
if [ -n "$DOCKER_CONTAINER" ] || [ -n "$container" ]; then
    echo "在 Docker 中运行"
else
    echo "不在 Docker 中"
fi
```

---

## 故障排除

### 虚拟环境未检测到

**问题**: 脚本未检测到虚拟环境

**解决方案**:
1. **显式激活 venv**:
   ```bash
   source .venv/bin/activate
   ./start-local.sh
   ```

2. **检查 VIRTUAL_ENV 变量**:
   ```bash
   echo $VIRTUAL_ENV
   # 应显示 venv 的路径
   ```

3. **创建并激活 venv**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

### Conda 环境未检测到

**问题**: 脚本未检测到 conda 环境

**解决方案**:
1. **激活 conda 环境**:
   ```bash
   conda activate zenethunter
   ./start-local.sh
   ```

2. **检查 CONDA_DEFAULT_ENV**:
   ```bash
   echo $CONDA_DEFAULT_ENV
   # 应显示环境名称（不是 "base"）
   ```

3. **创建 conda 环境**:
   ```bash
   conda env create -f environment.yml
   conda activate zenethunter
   ```

### Root 权限未检测到

**问题**: 网络扫描功能不工作

**解决方案**:
1. **检查当前用户**:
   ```bash
   echo "EUID: $EUID"
   echo "用户: $(whoami)"
   ```

2. **使用 sudo 运行**:
   ```bash
   sudo ./start-local.sh
   ```

3. **授予能力**（Linux）:
   ```bash
   sudo setcap cap_net_raw,cap_net_admin+eip $(which python3)
   ```

### 命令未找到

**问题**: `command -v python3` 返回空

**解决方案**:
1. **检查 PATH**:
   ```bash
   echo $PATH
   which python3
   ```

2. **添加到 PATH**:
   ```bash
   export PATH="/usr/local/bin:$PATH"
   ```

3. **安装缺失的工具**:
   ```bash
   # macOS
   brew install python3 node
   
   # Linux (Debian/Ubuntu)
   sudo apt-get install python3 python3-pip nodejs npm
   ```

---

## 最佳实践

### 1. 始终使用虚拟环境

```bash
# 推荐: 使用 conda 或 venv
conda env create -f environment.yml
conda activate zenethunter
# 或
python3 -m venv .venv
source .venv/bin/activate
```

### 2. 不要不必要地修改系统 PATH

- 使用虚拟环境而不是修改全局 PATH
- 让包管理器处理 Python/Node.js 安装

### 3. 运行前检查环境

```bash
# 验证环境
python3 --version
node --version
npm --version
```

### 4. 使用特定于环境的配置

- **开发环境**: 使用 `.env` 文件或本地环境变量
- **生产环境**: 使用系统环境变量或密钥管理
- **Docker**: 使用 Docker 环境变量或 `.env` 文件

---

## 相关文档

- **[ENVIRONMENT.zh-CN.md](ENVIRONMENT.zh-CN.md)**: 应用程序配置变量
- **[环境设置指南](guides/ENVIRONMENT_SETUP.md)**: 详细的环境设置说明
- **[Conda 设置指南](guides/CONDA_SETUP.md)**: Conda 特定设置

---

## 总结表

| 变量 | 设置者 | 用途 | 使用位置 |
|------|--------|------|----------|
| `VIRTUAL_ENV` | Python venv | 虚拟环境路径 | `start-local.sh` |
| `CONDA_DEFAULT_ENV` | Conda | Conda 环境名称 | `start-local.sh` |
| `PYTHONPATH` | 用户/系统 | Python 模块搜索路径 | Python 导入 |
| `EUID` | Shell | 有效用户 ID | Root 检测 |
| `PATH` | 系统 | 命令搜索路径 | 命令检测 |
| `DOCKER_CONTAINER` | Docker | 容器检测 | 平台检测 |
| `uname -s` | 系统 | 操作系统类型 | 特定于操作系统的配置 |

---

**最后更新**: 2026-01-24  
**文档版本**: 1.0
