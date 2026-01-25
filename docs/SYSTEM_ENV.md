# System-Level Environment Variables

## Overview

This document describes **system-level environment variables** used by ZenetHunter. These are variables that are typically set by the operating system, Python runtime, or shell environment, rather than application-specific configuration variables.

> **Note**: For application configuration variables (like `APP_ENV`, `DATABASE_URL`, etc.), see [ENVIRONMENT.md](ENVIRONMENT.md).

---

## Python Environment Variables

### `VIRTUAL_ENV`

- **Type**: String (path)
- **Set by**: Python `venv` module when virtual environment is activated
- **Purpose**: Indicates the path to the active Python virtual environment
- **Used in**: `start-local.sh` for environment detection
- **Example**:
  ```bash
  # When venv is activated
  echo $VIRTUAL_ENV
  # Output: /path/to/project/backend/.venv
  ```
- **Detection**:
  ```bash
  if [ -z "$VIRTUAL_ENV" ]; then
      echo "Not in virtual environment"
  fi
  ```

### `CONDA_DEFAULT_ENV`

- **Type**: String
- **Set by**: Conda when a conda environment is activated
- **Purpose**: Name of the currently active conda environment
- **Used in**: `start-local.sh` for conda environment detection
- **Example**:
  ```bash
  # When conda environment is activated
  conda activate zenethunter
  echo $CONDA_DEFAULT_ENV
  # Output: zenethunter
  ```
- **Detection**:
  ```bash
  if [ ! -z "$CONDA_DEFAULT_ENV" ] && [ "$CONDA_DEFAULT_ENV" != "base" ]; then
      echo "In conda environment: $CONDA_DEFAULT_ENV"
  fi
  ```
- **⚠️ Note**: The script treats `base` environment as "no environment" to prevent pollution.

### `PYTHONPATH`

- **Type**: String (colon-separated paths on Unix, semicolon-separated on Windows)
- **Set by**: User or system
- **Purpose**: Additional directories to search for Python modules
- **Used in**: Python import resolution
- **Example**:
  ```bash
  export PYTHONPATH="/custom/path:$PYTHONPATH"
  python -c "import mymodule"  # Will search in /custom/path
  ```
- **⚠️ Note**: Usually not needed if using proper package installation (`pip install -e .`).

---

## Operating System Variables

### `EUID` / `$(id -u)`

- **Type**: Integer
- **Set by**: Shell (effective user ID)
- **Purpose**: Detects if the script is running with root/administrator privileges
- **Used in**: `start-local.sh` for root detection
- **Example**:
  ```bash
  if [ "$EUID" -eq 0 ] || [ "$(id -u)" -eq 0 ]; then
      echo "Running as root"
  fi
  ```
- **Values**:
  - `0`: Root user (Unix/Linux) or Administrator (Windows)
  - `> 0`: Regular user
- **Impact**: Root privileges enable full network scanning capabilities (ARP sweep, raw sockets, etc.)

### `PATH`

- **Type**: String (colon-separated paths)
- **Set by**: System/shell
- **Purpose**: Directories to search for executable commands
- **Used in**: Command detection (`command -v python3`, `command -v node`, etc.)
- **Example**:
  ```bash
  # Check if command exists
  if ! command -v python3 &> /dev/null; then
      echo "python3 not found in PATH"
  fi
  ```
- **Common checks in project**:
  - `python3`: Python interpreter
  - `node`: Node.js runtime
  - `npm`: Node.js package manager
  - `conda`: Conda package manager
  - `lsof`: List open files (for port checking)
  - `netstat`: Network statistics (for port checking)

### `DOCKER_CONTAINER` / `container`

- **Type**: String (usually "1" or empty)
- **Set by**: Docker runtime
- **Purpose**: Indicates if code is running inside a Docker container
- **Used in**: `backend/app/core/platform/detect.py` for platform detection
- **Example**:
  ```python
  if os.getenv("DOCKER_CONTAINER") or os.getenv("container"):
      # Running in Docker
      platform_type = "docker"
  ```
- **Detection**:
  ```python
  is_docker = bool(os.getenv("DOCKER_CONTAINER") or os.getenv("container"))
  ```

### `uname -s` (via command)

- **Type**: String
- **Set by**: System (`uname` command)
- **Purpose**: Operating system type detection
- **Used in**: `start-local.sh` for OS-specific configuration
- **Example**:
  ```bash
  OS_TYPE=$(uname -s)
  case "$OS_TYPE" in
      "Darwin")
          echo "macOS detected"
          ;;
      "Linux")
          echo "Linux detected"
          ;;
      *)
          echo "Other OS: $OS_TYPE"
          ;;
  esac
  ```
- **Common values**:
  - `Darwin`: macOS
  - `Linux`: Linux
  - `CYGWIN*`, `MINGW*`, `MSYS*`: Windows (via Cygwin/Git Bash)

---

## Network Detection Variables

### Local IP Address Detection

- **Method**: Not a single variable, but detected via system commands
- **Used in**: `start-local.sh` for CORS configuration
- **Detection methods**:
  ```bash
  # Method 1: Using `ip` command (Linux)
  ip route get 8.8.8.8 2>/dev/null | awk '{print $7; exit}'
  
  # Method 2: Using `ifconfig` (macOS/Linux)
  ifconfig | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | \
      grep -v '127.0.0.1' | awk '{print $2}' | head -1
  ```
- **Purpose**: Automatically add local network IP to CORS allowed origins
- **Example**:
  ```bash
  LOCAL_IP=$(get_local_ip)
  if [ -n "$LOCAL_IP" ]; then
      export CORS_ALLOW_ORIGINS="$CORS_ALLOW_ORIGINS,http://$LOCAL_IP:5173"
  fi
  ```

---

## Shell Environment Variables

### `SCRIPT_DIR`

- **Type**: String (path)
- **Set by**: `start-local.sh` script itself
- **Purpose**: Stores the directory where the script is located
- **Used in**: Path resolution for relative operations
- **Example**:
  ```bash
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  cd "$SCRIPT_DIR"
  ```

### `PWD` / `$(pwd)`

- **Type**: String (path)
- **Set by**: Shell
- **Purpose**: Current working directory
- **Used in**: Navigation and path resolution
- **Example**:
  ```bash
  cd backend
  echo "Current directory: $(pwd)"
  # Output: /path/to/project/backend
  ```

---

## Process Management Variables

### Process IDs (PIDs)

- **Type**: Integer
- **Set by**: Script (`start-local.sh`)
- **Purpose**: Track running processes for cleanup
- **Variables**:
  - `BACKEND_PID`: Uvicorn server process ID
  - `FRONTEND_PID`: Vite dev server process ID
- **Example**:
  ```bash
  uvicorn app.main:app --host 0.0.0.0 --port 8000 &
  BACKEND_PID=$!
  echo "Backend PID: $BACKEND_PID"
  
  # Later, cleanup
  if kill -0 $BACKEND_PID 2>/dev/null; then
      kill -TERM $BACKEND_PID
  fi
  ```

---

## Environment Detection Priority

The `start-local.sh` script uses the following priority for environment detection:

```
1. Conda Environment (CONDA_DEFAULT_ENV)
   └─ If set and not "base" → Use conda environment
   
2. Virtual Environment (VIRTUAL_ENV)
   └─ If set → Use venv environment
   
3. Local .venv Directory
   └─ If exists → Activate and use
   
4. System Environment
   └─ Warn user and ask for confirmation
```

---

## How to Set System Variables

### Temporary (Current Session)

```bash
# Linux/macOS
export VIRTUAL_ENV=/path/to/venv
export CONDA_DEFAULT_ENV=zenethunter
export PYTHONPATH=/custom/path:$PYTHONPATH

# Windows (PowerShell)
$env:VIRTUAL_ENV="C:\path\to\venv"
$env:CONDA_DEFAULT_ENV="zenethunter"
```

### Persistent (User Profile)

**Linux/macOS** (`~/.bashrc` or `~/.zshrc`):
```bash
export PYTHONPATH="$HOME/custom/path:$PYTHONPATH"
```

**Windows** (System Properties → Environment Variables):
- Add via GUI or setx command

### In Scripts

```bash
#!/bin/bash
# Set variables at the top of the script
export APP_ENV=development
export DATABASE_URL="sqlite+aiosqlite:///./data/zenethunter.db"
```

---

## Verification Commands

### Check Current Environment

```bash
# Check Python environment
echo "VIRTUAL_ENV: $VIRTUAL_ENV"
echo "CONDA_DEFAULT_ENV: $CONDA_DEFAULT_ENV"
echo "Python: $(which python3)"
echo "Python version: $(python3 --version)"

# Check system info
echo "OS: $(uname -s)"
echo "User: $(whoami)"
echo "EUID: $EUID"
echo "Is root: $([ "$EUID" -eq 0 ] && echo "yes" || echo "no")"

# Check PATH
echo "PATH: $PATH"
echo "Python in PATH: $(command -v python3)"
```

### Check Docker Environment

```bash
# Check if in Docker
if [ -n "$DOCKER_CONTAINER" ] || [ -n "$container" ]; then
    echo "Running in Docker"
else
    echo "Not in Docker"
fi
```

---

## Troubleshooting

### Virtual Environment Not Detected

**Problem**: Script doesn't detect virtual environment

**Solutions**:
1. **Activate venv explicitly**:
   ```bash
   source .venv/bin/activate
   ./start-local.sh
   ```

2. **Check VIRTUAL_ENV variable**:
   ```bash
   echo $VIRTUAL_ENV
   # Should show path to venv
   ```

3. **Create and activate venv**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

### Conda Environment Not Detected

**Problem**: Script doesn't detect conda environment

**Solutions**:
1. **Activate conda environment**:
   ```bash
   conda activate zenethunter
   ./start-local.sh
   ```

2. **Check CONDA_DEFAULT_ENV**:
   ```bash
   echo $CONDA_DEFAULT_ENV
   # Should show environment name (not "base")
   ```

3. **Create conda environment**:
   ```bash
   conda env create -f environment.yml
   conda activate zenethunter
   ```

### Root Privileges Not Detected

**Problem**: Network scanning features don't work

**Solutions**:
1. **Check current user**:
   ```bash
   echo "EUID: $EUID"
   echo "User: $(whoami)"
   ```

2. **Run with sudo**:
   ```bash
   sudo ./start-local.sh
   ```

3. **Grant capabilities** (Linux):
   ```bash
   sudo setcap cap_net_raw,cap_net_admin+eip $(which python3)
   ```

### Command Not Found

**Problem**: `command -v python3` returns nothing

**Solutions**:
1. **Check PATH**:
   ```bash
   echo $PATH
   which python3
   ```

2. **Add to PATH**:
   ```bash
   export PATH="/usr/local/bin:$PATH"
   ```

3. **Install missing tools**:
   ```bash
   # macOS
   brew install python3 node
   
   # Linux (Debian/Ubuntu)
   sudo apt-get install python3 python3-pip nodejs npm
   ```

---

## Best Practices

### 1. Always Use Virtual Environments

```bash
# Recommended: Use conda or venv
conda env create -f environment.yml
conda activate zenethunter
# OR
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Don't Modify System PATH Unnecessarily

- Use virtual environments instead of modifying global PATH
- Let package managers handle Python/Node.js installation

### 3. Check Environment Before Running

```bash
# Verify environment
python3 --version
node --version
npm --version
```

### 4. Use Environment-Specific Configuration

- Development: Use `.env` file or local environment variables
- Production: Use system environment variables or secrets management
- Docker: Use Docker environment variables or `.env` files

---

## Related Documentation

- **[ENVIRONMENT.md](ENVIRONMENT.md)**: Application configuration variables
- **[Environment Setup Guide](guides/ENVIRONMENT_SETUP.md)**: Detailed environment setup instructions
- **[Conda Setup Guide](guides/CONDA_SETUP.md)**: Conda-specific setup

---

## Summary Table

| Variable | Set By | Purpose | Used In |
|----------|--------|---------|---------|
| `VIRTUAL_ENV` | Python venv | Virtual environment path | `start-local.sh` |
| `CONDA_DEFAULT_ENV` | Conda | Conda environment name | `start-local.sh` |
| `PYTHONPATH` | User/System | Python module search path | Python imports |
| `EUID` | Shell | Effective user ID | Root detection |
| `PATH` | System | Command search path | Command detection |
| `DOCKER_CONTAINER` | Docker | Container detection | Platform detection |
| `uname -s` | System | OS type | OS-specific config |

---

**Last Updated**: 2026-01-24  
**Documentation Version**: 1.0
