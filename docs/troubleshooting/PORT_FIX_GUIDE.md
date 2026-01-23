# 端口占用问题完全解决方案

## 问题

```
ERROR: [Errno 48] Address already in use
```

## 根本原因

1. **残留的uvicorn进程**: 上次启动未正常关闭，进程仍在后台
2. **端口未释放**: 8000/5173端口被占用
3. **检测时机错误**: 端口检测在启动后才执行

---

## ✅ 完整解决方案

### 方案1: 使用cleanup.sh脚本（推荐）

**新增独立清理脚本**:
```bash
./cleanup.sh
```

**功能**:
- ✅ 清理所有uvicorn进程
- ✅ 清理所有vite进程
- ✅ 释放端口8000
- ✅ 释放端口5173
- ✅ 清理数据库锁文件

**使用流程**:
```bash
# 1. 清理环境
./cleanup.sh

# 2. 启动服务
./start-local.sh
```

### 方案2: start-local.sh自动清理

**已集成到启动脚本**:
```bash
./start-local.sh
# ✅ 自动运行预检查
# ✅ 自动清理残留进程
# ✅ 自动释放占用端口
# ✅ 然后启动服务
```

**启动输出**:
```
=== ZenetHunter 本地启动 ===

=== 预检查：清理残留资源 ===
检查是否有残留的后端进程...
⚠️  发现残留的后端进程:
  root  70665  ... uvicorn app.main:app --port 8000
正在清理残留进程...
✅ 残留进程已清理

检查端口占用...
✅ 后端端口 8000 空闲
✅ 前端端口 5173 空闲
✅ 预检查完成

... (继续正常启动)
```

### 方案3: 手动清理

**如果脚本失败，手动执行**:
```bash
# 查找并kill uvicorn进程
ps aux | grep uvicorn
sudo kill -9 <PID>

# 或使用pkill
sudo pkill -9 -f "uvicorn app.main"

# 清理端口
sudo lsof -ti:8000 | xargs kill -9
sudo lsof -ti:5173 | xargs kill -9

# 然后启动
./start-local.sh
```

---

## 🔧 技术实现

### cleanup_old_processes()

```bash
cleanup_old_processes() {
    # 查找所有uvicorn进程
    local uvicorn_pids=$(ps aux | grep -E "uvicorn app.main" | grep -v grep | awk '{print $2}')

    if [ ! -z "$uvicorn_pids" ]; then
        echo "⚠️  发现残留进程，清理中..."

        for pid in $uvicorn_pids; do
            # 优先尝试普通kill，失败则使用sudo
            kill -KILL $pid 2>/dev/null || sudo kill -KILL $pid 2>/dev/null
        done

        sleep 2
        echo "✅ 进程已清理"
    fi
}
```

### check_and_free_port()

```bash
check_and_free_port() {
    local port=$1
    local port_name=$2

    # 使用lsof检查端口
    local pids=$(lsof -ti:$port 2>/dev/null)

    if [ ! -z "$pids" ]; then
        echo "⚠️  $port_name 端口 $port 被占用 (PID: $pids)"
        kill -KILL $pids 2>/dev/null || sudo kill -KILL $pids 2>/dev/null
        sleep 1
        echo "✅ 端口 $port 已释放"
    fi
}
```

### 执行顺序

```
1. 启动脚本
   ↓
2. cleanup_old_processes()  ← 清理所有uvicorn进程
   ↓
3. check_and_free_port(8000) ← 清理后端端口
   ↓
4. check_and_free_port(5173) ← 清理前端端口
   ↓
5. 安装依赖
   ↓
6. 启动uvicorn
```

---

## 🎯 完整的清理流程

### cleanup.sh内容

1. **清理uvicorn进程** (支持sudo)
2. **清理vite进程**
3. **释放端口8000** (lsof + kill)
4. **释放端口5173**
5. **清理数据库锁文件**

### start-local.sh增强

1. **预检查阶段** (启动前)
   - cleanup_old_processes()
   - check_and_free_port()

2. **trap处理器** (关闭时)
   - Kill BACKEND_PID
   - Kill FRONTEND_PID
   - pkill uvicorn/vite

---

## 📋 使用指南

### 正常流程

```bash
# 方式1: 直接启动（自动清理）
./start-local.sh

# 方式2: 先手动清理
./cleanup.sh
./start-local.sh

# 方式3: 强制清理后启动
sudo ./cleanup.sh  # 确保所有进程被kill
./start-local.sh
```

### 故障排除

#### 问题: 仍然提示端口占用

**检查**:
```bash
# 查看端口占用情况
lsof -i:8000
lsof -i:5173

# 查看进程
ps aux | grep uvicorn
```

**解决**:
```bash
# 强制清理
sudo ./cleanup.sh

# 或手动kill
sudo pkill -9 -f uvicorn
sudo lsof -ti:8000 | xargs sudo kill -9
```

#### 问题: 权限不足

**症状**: `kill: Operation not permitted`

**解决**:
```bash
# 使用sudo运行清理
sudo ./cleanup.sh

# 或单独kill进程
sudo kill -9 <PID>
```

---

## Git提交

```bash
61f404e fix: improve port detection and auto-kill old uvicorn processes
4a5fd77 fix: ensure cleanup functions are called before uvicorn starts
[new]   feat: add cleanup.sh script and ensure pre-check runs first
```

---

## ✅ 验证步骤

### 1. 清理环境

```bash
./cleanup.sh
# 应该看到所有进程被清理，所有端口被释放
```

### 2. 启动服务

```bash
./start-local.sh
# 应该看到:
# === 预检查：清理残留资源 ===
# ✅ 无残留进程
# ✅ 端口空闲
#
# 然后正常启动，无Address already in use错误
```

### 3. 验证端口

```bash
lsof -i:8000
# 应该显示uvicorn进程正在监听
```

---

**状态**: ✅ **完全修复**  
**工具**: cleanup.sh + 改进的start-local.sh  
**建议**: 每次启动前运行 `./cleanup.sh` 确保环境干净
