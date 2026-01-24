# 🚀 启动检查清单（必读）

## ⚠️ 重要：数据库Schema已更新

如果遇到以下任何错误，**必须删除旧数据库**：
```
❌ no such column: devices.active_defense_status
❌ no such column: devices.discovery_source
❌ NOT NULL constraint failed: devices.attack_status
```

---

## ✅ 正确启动步骤

### 第1步：清理环境

```bash
cd /Volumes/MobileWorkstation/Projects/ZenetHunter

# 清理所有残留进程和端口
./cleanup.sh
```

### 第2步：删除旧数据库（重要！）

```bash
# 删除旧数据库及其锁文件
rm -rf backend/data/*.db*

# 数据库将在启动时自动创建新schema
```

### 第3步：启动服务

```bash
./start-local.sh

# 预期输出：
# ✅ 无残留进程
# ✅ 端口空闲
# ✅ 数据库将自动创建
# ✅ 后端服务器已启动
```

---

## 🔍 验证启动成功

### 检查后端

```bash
# 1. 检查进程
ps aux | grep uvicorn | grep -v grep

# 2. 检查端口
lsof -i:8000

# 3. 测试API
curl http://localhost:8000/healthz
# 应返回: {"status":"ok"}
```

### 检查数据库

```bash
sqlite3 backend/data/zenethunter.db "PRAGMA table_info(devices);" | wc -l
# 应该是 19 列（不是更多）

sqlite3 backend/data/zenethunter.db "SELECT name FROM sqlite_master WHERE type='table';"
# 应该有: devices, device_fingerprints, event_logs, trust_lists
```

---

## 📊 测试扫描功能

### 1. 打开前端

```
http://localhost:8000/docs  (API文档)
或访问前端UI
```

### 2. 执行扫描

点击 "扫描" 按钮

### 3. 观察日志

**预期日志流程**：
```
Scan started in mode: hybrid | succeed=true
ARP cache: X candidates | succeed=true
DHCP leases: Y candidates | succeed=true  
Stage 1: Generated N candidates | succeed=true
Stage 2: M/N confirmed | succeed=true
Enrichment stage completed: M devices | succeed=true
Scan completed: M devices | succeed=true
```

**时间预期**：
- 候选集：<1秒
- 刷新：2-3秒
- Enrichment：10-30秒
- **总计：15-35秒**

---

## ⚠️ 常见问题

### Q1: 端口被占用

**解决**：
```bash
./cleanup.sh  # 自动清理
# 或手动
sudo lsof -ti:8000 | xargs kill -9
```

### Q2: 数据库错误

**解决**：
```bash
rm -rf backend/data/*.db*  # 删除重建
./start-local.sh
```

### Q3: 扫描卡住

**原因**：Enrichment阶段可能需要30秒

**解决**：等待或重启服务

### Q4: 无设备显示

**原因**：可能是网络问题或权限不足

**检查**：
```bash
# 查看后端日志
tail -f backend/.log  # 如果有日志文件

# 或查看终端输出
# 寻找 "succeed=true" 确认各阶段完成
```

---

## 🎯 Schema版本对照

| 版本 | attack_status | defense_status | active_defense_status | discovery_source | freshness_score |
|------|---------------|----------------|----------------------|-----------------|----------------|
| v1.0 | ✅ | ✅ | ❌ | ❌ | ❌ |
| v2.0 | ✅ | ✅ | ✅ | ❌ | ❌ |
| v2.1 | ❌ | ❌ | ✅ | ✅ | ✅ |

**当前版本**: v2.1

**如果数据库是v1.0/v2.0**: 必须删除重建

---

## 📝 快速命令

```bash
# 完整重启流程（推荐）
./cleanup.sh && rm -rf backend/data/*.db* && ./start-local.sh

# 仅重启后端
./cleanup.sh && ./start-local.sh

# 查看进程
ps aux | grep uvicorn

# 查看端口
lsof -i:8000
lsof -i:5173

# 测试健康检查
curl http://localhost:8000/healthz
```

---

## ✅ 成功标志

- ✅ 无 "no such column" 错误
- ✅ 无 "NOT NULL constraint" 错误
- ✅ 无 "NameError: asyncio" 错误
- ✅ 扫描日志包含 "succeed=true"
- ✅ 设备列表能正常显示

---

**重要**: 删除旧数据库是必须的！  
**命令**: `rm -rf backend/data/*.db*`
