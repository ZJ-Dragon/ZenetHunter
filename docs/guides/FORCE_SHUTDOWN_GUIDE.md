# 强制关闭功能使用指南

## 功能概述

针对后端服务器难以关闭的问题，新增**强制关闭**功能，使用 SIGKILL 信号立即终止进程。

---

## 🎯 两种关闭模式

### 1. 优雅关闭 (Graceful Shutdown)

**特点**:
- ✅ 取消所有后台任务
- ✅ 关闭WebSocket连接
- ✅ 关闭数据库连接
- ✅ 刷新日志缓冲
- ⏱️ 最多5秒超时

**适用场景**: 正常关闭，保证资源清理

**方式**:
- Ctrl+C（终端）
- UI "优雅关闭服务器"按钮
- API: `POST /shutdown`

### 2. 强制关闭 (Force Shutdown) ⚡ NEW

**特点**:
- ⚡ 立即取消所有任务
- ⚡ 发送 SIGKILL 信号
- ⚡ 100ms内完成
- ⚠️ 可能丢失未保存数据
- ⚠️ 数据库连接可能未正确关闭

**适用场景**:
- 优雅关闭失败/卡住
- 紧急终止
- 系统无响应

**方式**:
- UI "强制关闭"按钮
- API: `POST /force-shutdown`

---

## 🎨 UI使用指南

### 位置
**Settings（设置）→ 系统信息 → 危险区域**

### 交互流程

#### 场景1: 正常优雅关闭

```
1. 点击 "优雅关闭服务器"
   ↓
2. 显示确认对话框："确定要关闭服务器吗？"
   ├─ 点击"确认关闭" → 执行优雅关闭
   └─ 点击"取消" → 返回
   ↓
3. Toast提示:
   🔄 正在优雅关闭服务器...
   ✅ 服务器已关闭
   ❌ 与服务器的连接已断开
```

#### 场景2: 优雅关闭失败 → 强制关闭

```
1. 优雅关闭失败
   ↓
2. Toast显示: "优雅关闭失败，请尝试强制关闭"
   ↓
3. UI自动显示"强制关闭"按钮
   ⚠️ 优雅关闭失败？使用强制关闭
   [⚡ 强制关闭服务器]
   ↓
4. 点击"强制关闭服务器"
   ↓
5. Toast提示:
   ❌ 正在强制关闭服务器...
   ✅ 服务器已强制关闭
   ⏰ 连接已断开，页面将在2秒后关闭
   ↓
6. 2.5秒后自动关闭浏览器标签页
```

#### 场景3: 确认对话框中直接强制关闭

```
1. 点击"优雅关闭服务器" → 确认对话框
   ↓
2. 对话框中看到两个选项:
   [确认关闭] (优雅)
   [⚡ 强制关闭] (下方，深红色)
   ↓
3. 如果优雅关闭可能卡住，直接点击"强制关闭"
   ↓
4. 立即执行SIGKILL，页面自动关闭
```

---

## 🔧 技术实现

### 后端API

#### 优雅关闭
```http
POST /shutdown
Authorization: Bearer {admin_token}
```

**流程**:
1. 广播 systemShutdown 事件
2. 延迟 500ms
3. 发送 SIGTERM 信号
4. 执行 lifespan shutdown（5秒超时）

#### 强制关闭 ⚡
```http
POST /force-shutdown
Authorization: Bearer {admin_token}
```

**流程**:
1. 广播 systemForceShutdown 事件
2. 取消所有 asyncio 任务
3. 延迟 100ms
4. 发送 SIGKILL 信号
5. 立即终止，无清理

**代码**:
```python
async def immediate_force_shutdown():
    # Cancel ALL tasks
    for task in asyncio.all_tasks():
        if task is not asyncio.current_task():
            task.cancel()

    await asyncio.sleep(0.1)  # Brief delay for response

    # SIGKILL - immediate kill
    os.kill(os.getpid(), signal.SIGKILL)
```

### 前端实现

#### forceShutdownServer方法
```typescript
const handleForceShutdown = async () => {
  setIsShuttingDown(true);
  try {
    await logsService.forceShutdownServer();

    toast.success('服务器已强制关闭');

    // Close page after 2.5 seconds
    setTimeout(() => {
      window.close();
      // Fallback: redirect to blank page
      setTimeout(() => {
        window.location.href = 'about:blank';
      }, 500);
    }, 2500);

  } catch (error) {
    // Expected - server killed before response
    toast.error('服务器已强制终止，页面即将关闭');

    setTimeout(() => {
      window.close();
      window.location.href = 'about:blank';
    }, 2000);
  }
};
```

#### 自动关闭页面
1. 2.5秒后调用 `window.close()`
2. 如果失败（浏览器安全限制），重定向到 `about:blank`

---

## ⚠️ 注意事项

### 强制关闭的风险

1. **数据丢失**
   - 正在进行的扫描结果可能丢失
   - 主动防御操作可能未正确停止
   - 审计日志可能不完整

2. **资源残留**
   - 数据库连接可能未关闭
   - 临时文件可能未清理
   - 网络数据包可能仍在发送

3. **需要手动清理**
   - 可能需要清理残留进程
   - 可能需要重启数据库
   - 可能需要检查网络状态

### 何时使用强制关闭

✅ **应该使用**:
- 优雅关闭超过10秒仍未完成
- 服务器完全无响应
- 紧急情况需要立即终止

❌ **不应该使用**:
- 正常关闭场景
- 有重要数据正在保存
- 可以等待优雅关闭完成

---

## 📋 使用步骤

### Step 1: 尝试优雅关闭

```
Settings → 优雅关闭服务器 → 确认
```

等待最多 **5-10秒**

### Step 2: 如果卡住，使用强制关闭

```
Settings → 强制关闭服务器 → 立即执行
```

**预期**: **<1秒** 完成

### Step 3: 页面自动关闭

- 2.5秒后自动关闭浏览器标签
- 或重定向到空白页

---

## 🧪 测试验证

### 测试强制关闭

1. **启动服务器**:
   ```bash
   ./start-local.sh
   ```

2. **启动一些任务** (可选):
   - 执行网络扫描
   - 启动主动防御操作

3. **尝试优雅关闭**:
   - Settings → 优雅关闭
   - 观察是否卡住

4. **执行强制关闭**:
   - 点击"强制关闭"按钮
   - 应该立即终止

5. **验证结果**:
   ```bash
   ps aux | grep uvicorn
   # 应该没有进程了
   ```

---

## 🔍 故障排除

### 如果强制关闭后进程仍在

```bash
# 查找进程
ps aux | grep -E "uvicorn|python.*app.main"

# 手动kill
kill -9 <PID>
```

### 如果页面未自动关闭

**原因**: 浏览器安全策略限制 `window.close()`

**解决**:
- 已自动重定向到 `about:blank`
- 或手动关闭标签页

### 如果数据库锁定

```bash
# SQLite - 删除锁文件
rm backend/data/*.db-shm backend/data/*.db-wal

# PostgreSQL - 终止连接
psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='zenethunter';"
```

---

## 📊 对比表

| 特性 | 优雅关闭 | 强制关闭 |
|------|---------|---------|
| 信号 | SIGTERM | SIGKILL |
| 耗时 | <5秒 | <1秒 ⚡ |
| 资源清理 | ✅ 完整 | ❌ 跳过 |
| 数据安全 | ✅ 安全 | ⚠️ 可能丢失 |
| 日志完整 | ✅ 完整 | ⚠️ 可能不完整 |
| 使用场景 | 正常关闭 | 紧急/卡住 |
| 页面行为 | 保持打开 | 自动关闭 |

---

## 🎉 功能亮点

1. **双重保险**: 优雅关闭 + 强制关闭
2. **智能降级**: 优雅失败自动显示强制选项
3. **自动清理**: 强制关闭后自动关闭网页
4. **Toast反馈**: 清晰的操作状态提示
5. **安全防护**: 双重确认 + 管理员权限

---

## Git提交

```bash
bb4aebf feat: add force shutdown API with SIGKILL
a5d9301 feat: add force shutdown UI with auto page close
```

---

**状态**: ✅ **功能完整，可立即使用**  
**安全级别**: 🔴 **高危操作，仅管理员可用**  
**建议**: 优先使用优雅关闭，仅在必要时使用强制关闭
