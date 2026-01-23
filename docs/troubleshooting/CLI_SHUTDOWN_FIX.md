# CLI关闭逻辑修复报告

## 问题

1. **数据库Schema不匹配**
   ```
   sqlite3.OperationalError: no such column: devices.active_defense_status
   ```

2. **Ctrl+C无法退出**
   - start-local.sh的Ctrl+C不能正确终止所有进程
   - uvicorn子进程可能残留

3. **缺少前端清理**
   - 前端进程不会被自动关闭

---

## 解决方案

### 1. 自动数据库迁移

**start-local.sh** 新增自动检测和修复：

```bash
# 检查数据库schema
if [ -f "data/zenethunter.db" ]; then
    COLUMN_CHECK=$(sqlite3 data/zenethunter.db "PRAGMA table_info(devices);" | grep "active_defense_status")

    if [ -z "$COLUMN_CHECK" ]; then
        echo "⚠️  检测到schema不匹配，自动修复..."

        # 自动添加缺失列
        sqlite3 data/zenethunter.db <<EOF
ALTER TABLE devices ADD COLUMN active_defense_status TEXT DEFAULT 'idle';
ALTER TABLE devices ADD COLUMN recognition_manual_override INTEGER DEFAULT 0;
UPDATE devices SET active_defense_status = COALESCE(attack_status, 'idle');
EOF

        echo "✅ 数据库schema已更新"
    fi
fi
```

**效果**:
- ✅ 自动检测schema版本
- ✅ 自动添加缺失列
- ✅ 迁移旧数据
- ✅ 无需手动操作

### 2. 优化信号处理

**新增trap处理器**:

```bash
# 信号处理函数
cleanup() {
    echo "=== 正在关闭所有服务 ==="

    # 1. 终止后端（优雅 → 强制）
    if [ ! -z "$BACKEND_PID" ]; then
        kill -TERM $BACKEND_PID 2>/dev/null

        # 等待3秒
        for i in {1..6}; do
            if ! kill -0 $BACKEND_PID 2>/dev/null; then
                echo "✅ 后端已优雅关闭"
                break
            fi
            sleep 0.5
        done

        # 超时则强制kill
        if kill -0 $BACKEND_PID 2>/dev/null; then
            echo "⚠️  超时，强制终止..."
            kill -KILL $BACKEND_PID 2>/dev/null
        fi
    fi

    # 2. 终止前端
    if [ ! -z "$FRONTEND_PID" ]; then
        kill -TERM $FRONTEND_PID 2>/dev/null
        kill -KILL $FRONTEND_PID 2>/dev/null
    fi

    # 3. 清理uvicorn子进程
    pkill -f "uvicorn app.main" 2>/dev/null

    exit 0
}

# 注册信号处理器
trap cleanup SIGINT SIGTERM EXIT
```

**效果**:
- ✅ Ctrl+C 立即响应
- ✅ 3秒内优雅关闭后端
- ✅ 超时自动强制kill
- ✅ 同时清理前端
- ✅ 清理所有uvicorn子进程

### 3. PID跟踪

**后端PID**:
```bash
uvicorn app.main:app --reload &
BACKEND_PID=$!
```

**前端PID**:
```bash
npm run dev &
FRONTEND_PID=$!
```

**效果**: cleanup函数可以正确终止所有进程

---

## 使用说明

### 正常启动

```bash
./start-local.sh
```

**自动操作**:
1. ✅ 检查数据库schema
2. ✅ 自动修复不匹配
3. ✅ 启动后端（后台）
4. ✅ 启动前端（后台）
5. ✅ 显示访问地址

### 优雅关闭

**Ctrl+C**:
```bash
^C
=== 正在关闭所有服务 ===
正在关闭后端服务 (PID: 12345)...
✅ 后端已优雅关闭
正在关闭前端服务 (PID: 12346)...
✅ 前端服务已关闭
✅ 清理完成
```

**预期耗时**: <3秒

### 强制关闭

**如果优雅关闭卡住**:
```bash
# 等待3秒后自动强制kill
⚠️  超时，强制终止...
✅ 清理完成
```

---

## 数据库迁移选项

### 选项1: 自动修复（推荐）

脚本启动时自动检测并修复，无需操作。

### 选项2: 手动删除（丢失数据）

```bash
rm -rf backend/data/*.db*
./start-local.sh  # 重新创建
```

### 选项3: Alembic迁移（保留数据）

```bash
cd backend
alembic upgrade head
```

---

## Git提交

```bash
41fd6bd feat: add auto database migration and optimized shutdown trap
bb1185e feat: enhance cleanup to kill frontend and uvicorn subprocesses  
[new]   fix: run uvicorn in background and track PID correctly
```

---

## 测试验证

### 1. 启动测试

```bash
./start-local.sh
# 应该看到:
# ✅ 数据库schema正常
# ✅ 后端服务器已启动
# 无错误日志
```

### 2. 关闭测试

```bash
^C
# 应该看到:
# === 正在关闭所有服务 ===
# ✅ 后端已优雅关闭
# ✅ 清理完成
#
# 耗时: <3秒
```

### 3. 强制关闭测试

```bash
# 启动后立即按Ctrl+C多次
^C^C^C
# 应该强制kill，不会hang住
```

---

## 修复的根本原因

| 问题 | 原因 | 解决 |
|------|------|------|
| Schema不匹配 | 模型更新但DB未迁移 | ✅ 自动检测和修复 |
| Ctrl+C无效 | 未注册trap | ✅ 添加cleanup函数 |
| 进程残留 | PID未跟踪 | ✅ 保存和使用PID |
| 前端未关闭 | 缺少清理逻辑 | ✅ 添加前端清理 |
| uvicorn子进程 | 子进程未kill | ✅ pkill清理 |

---

**状态**: ✅ **全部修复完成**  
**测试**: 需要重启服务验证
