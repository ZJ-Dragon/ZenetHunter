# ZenetHunter 项目完整性核查清单

生成时间：2026-01-17  
核查范围：A) 扫描与识别、B) 主动防御、C) API对齐、D) 数据层、E) 错误处理、F) 运行发布、G) 工程质量

---

## A) 扫描与识别（Active Probe + Fingerprinting）

### ✅ 已完成

1. **主动扫描引擎**
   - ✅ 使用 Scapy 进行 ARP sweep 主动发包
   - ✅ 位置：`backend/app/core/engine/scapy.py:scan_network()`
   - ✅ 扫描器集成：`backend/app/services/scanner_service.py`

2. **指纹采集**
   - ✅ 指纹采集器：`backend/app/services/fingerprint_collector.py`
   - ✅ DHCP 指纹：`backend/app/services/scanner/enrich/`（pipeline支持）
   - ✅ mDNS：`backend/app/services/scanner/enrich/mdns.py`
   - ✅ SSDP/UPnP：`backend/app/services/scanner/enrich/ssdp.py`

3. **识别引擎**
   - ✅ 识别引擎：`backend/app/services/recognition_engine.py`
   - ✅ 输出包含：vendor_guess, model_guess, recognition_confidence, recognition_evidence
   - ✅ 设备模型：`backend/app/models/device.py` 包含所有识别字段

4. **WebSocket 事件**
   - ✅ scanStarted: `scanner_service.py:78`
   - ✅ scanCompleted: `scanner_service.py:224`
   - ✅ deviceDiscovered: `scanner_service.py:173`
   - ✅ deviceUpdated: `scanner_service.py:186`

### ⚠️ 待完成

1. **管理员手动确认/覆盖功能**
   - ❌ **缺失**: 没有 `/devices/{mac}/recognition/override` API端点
   - 📍 **位置**: 需要在 `backend/app/routes/devices.py` 添加
   - 🔧 **修复**: 添加 PATCH 端点允许管理员覆盖自动识别结果
   - 💾 **持久化**: 需要在数据库标记为"手动确认"（添加字段 `recognition_manual_override: bool`）

---

## B) 主动防御（Defender-first / Active Defense）

### ✅ 已完成

1. **统一抽象**
   - ✅ Service: `backend/app/services/attack.py:ActiveDefenseService`
   - ✅ API: `/active-defense/{mac}/start`, `/active-defense/{mac}/stop`
   - ✅ Policies: `/active-defense/types` 列出所有可用策略

2. **实现的攻击类型**
   - ✅ KICK (WiFi Deauth): `scapy.py:_run_kick_attack()`
   - ✅ BLOCK (ARP Spoof): `scapy.py:_run_block_attack()`
   - ✅ ARP_FLOOD: `scapy.py` 中实现
   - ✅ DHCP_SPOOF: `scapy.py:_run_dhcp_spoof_attack()`
   - ✅ DNS_SPOOF: `scapy.py:_run_dns_spoof_attack()`
   - ✅ MAC_FLOOD: `scapy.py:_run_mac_flood_attack()`
   - ✅ BEACON_FLOOD: `scapy.py:_run_beacon_flood_attack()`

3. **WebSocket 事件**
   - ✅ activeDefenseStarted: `attack.py:91`
   - ✅ activeDefenseLog: `attack.py:105`
   - ✅ activeDefenseStopped: `attack.py:178`

### ⚠️ 待完成

1. **能力探测与降级**
   - ⚠️ **部分完成**: `scapy.py:check_permissions()` 检查权限
   - ❌ **缺失**: 没有返回 `pending`/`unsupported` 状态
   - 📍 **位置**: `backend/app/services/attack.py:start_operation()`
   - 🔧 **修复**: 当权限不足时，返回 `status='unsupported'` 而不是失败

2. **全局Kill-Switch / Readonly模式**
   - ❌ **缺失**: 没有全局开关配置
   - 📍 **位置**: 需要在 `backend/app/core/config.py` 添加配置项
   - 🔧 **修复**: 添加 `ACTIVE_DEFENSE_ENABLED` 环境变量，默认 `False`
   - 🔧 **修复**: 在 `start_operation()` 中检查此开关

3. **审计日志**
   - ⚠️ **部分完成**: WebSocket 日志事件存在
   - ❌ **缺失**: 没有写入数据库 `event_log` 表
   - 📍 **位置**: `backend/app/services/attack.py`
   - 🔧 **修复**: 在操作启动/停止时写入审计日志

4. **缺失的攻击类型实现**
   - ❌ **SYN Flood**: 未实现
   - ❌ **UDP Flood**: 未实现
   - ❌ **DNS 污染/劫持**: 部分实现（DNS_SPOOF存在但功能可能不完整）
   - ❌ **TCP RST 策略拒绝**: 未实现
   - 📍 **位置**: `backend/app/core/engine/scapy.py`
   - 🔧 **修复**: 添加这些攻击类型的实现方法

---

## C) API 对齐（REST + WebSocket）

### ✅ 已完成

1. **REST API**
   - ✅ 设备列表: `GET /api/devices`
   - ✅ 设备详情: `GET /api/devices/{mac}`
   - ✅ 扫描触发: `POST /api/scan/start`
   - ✅ 策略应用: `POST /api/active-defense/{mac}/start`
   - ✅ 策略停止: `POST /api/active-defense/{mac}/stop`
   - ✅ 策略枚举: `GET /api/active-defense/types`
   - ✅ 日志查询: `GET /api/logs`

2. **WebSocket**
   - ✅ 事件统一命名: camelCase 格式
   - ✅ 连接管理: `backend/app/services/websocket.py`
   - ✅ 实时推送: 扫描、设备、主动防御事件

3. **鉴权**
   - ✅ JWT 认证: `backend/app/core/security.py`
   - ✅ 写操作鉴权: 使用 `get_current_user` dependency

### ⚠️ 待完成

1. **API 端点缺失**
   - ❌ **扫描状态查询**: 缺少 `GET /api/scan/status`
   - ❌ **设备更新**: 缺少 `PATCH /api/devices/{mac}`（用于别名、标签等）
   - 📍 **位置**: `backend/app/routes/scan.py`, `devices.py`

---

## D) 数据层（DB 模型与迁移）

### ✅ 已完成

1. **数据库模型**
   - ✅ 设备表: `backend/app/models/db/device.py`
   - ✅ 信任列表: `backend/app/models/db/trust_list.py`
   - ✅ 事件日志: `backend/app/models/db/event_log.py`
   - ✅ 指纹表: `backend/app/models/db/device_fingerprint.py`

2. **Repository 层**
   - ✅ DeviceRepository: `backend/app/repositories/device.py`
   - ✅ TrustListRepository: 存在
   - ✅ EventLogRepository: 存在

### ❌ 严重缺失

1. **数据库迁移**
   - ❌ **Alembic 配置不存在**
   - ❌ **没有 `alembic.ini`**
   - ❌ **没有 `alembic/` 目录**
   - ❌ **没有初始迁移脚本**
   - 📍 **位置**: 需要在 `backend/` 创建
   - 🔧 **修复**: 初始化 Alembic，创建初始迁移

2. **数据库初始化**
   - ⚠️ **部分完成**: `backend/app/core/database.py:init_db()` 存在
   - ❌ **缺失**: 没有使用 Alembic 进行版本化迁移
   - 🔧 **修复**: 集成 Alembic 迁移到启动流程

3. **索引和优化**
   - ⚠️ **需要验证**: MAC 地址索引是否存在
   - ⚠️ **需要验证**: last_seen 时间戳索引
   - 🔧 **修复**: 在迁移脚本中添加必要的索引

---

## E) 错误与异常处理规范

### ✅ 已完成

1. **REST 错误**
   - ✅ Problem Details 格式: `backend/app/core/exceptions.py:AppError`
   - ✅ 稳定错误码: `ErrorCode` enum
   - ✅ Correlation ID: `backend/app/core/middleware.py`

2. **结构化日志**
   - ✅ logging 配置: `backend/app/core/logging.py`
   - ✅ Correlation ID 传播: middleware 实现

### ⚠️ 待完成

1. **WebSocket 错误格式**
   - ❌ **缺失**: 没有统一的 `event=error` 格式
   - 📍 **位置**: `backend/app/services/websocket.py`
   - 🔧 **修复**: 添加 `broadcast_error()` 方法

---

## F) 运行与发布

### ✅ 已完成

1. **启动脚本**
   - ✅ macOS/Linux: `start-local.sh`
   - ✅ Windows: `start-local.bat`

2. **12-Factor 配置**
   - ✅ 环境变量: `backend/app/core/config.py`
   - ✅ `.env.example`: 存在

### ⚠️ 待完成

1. **README Quickstart**
   - ⚠️ **需要验证**: 命令是否与实际一致
   - 📍 **位置**: `README.zh-CN.md`

---

## G) 工程质量门槛

### ⚠️ 待完成

1. **TODO/FIXME 清理**
   - ❌ **发现 8 处残留**:
     - `backend/app/core/engine/scapy.py`: 1处
     - `backend/app/routes/config.py`: 1处
     - `backend/app/core/engine/base_router.py`: 6处
   - 🔧 **修复**: 逐一清理或转换为规范的 Feature Flag

2. **Pre-commit 检查**
   - ⚠️ **需要运行**: `pre-commit run --all-files`

3. **测试运行**
   - ⚠️ **需要运行**: `pytest backend/tests/`

4. **CI 状态**
   - ⚠️ **需要检查**: GitHub Actions 是否全绿

---

## 优先级修复顺序

### 🔴 P0 - 阻塞性（必须完成）

1. **创建 Alembic 迁移系统**
   - 初始化 Alembic
   - 创建初始迁移脚本
   - 集成到启动流程

2. **清理 TODO/FIXME**
   - 清理或规范化所有残留

3. **添加全局 Kill-Switch**
   - 配置项：`ACTIVE_DEFENSE_ENABLED`
   - 运行时检查

### 🟡 P1 - 重要（应该完成）

4. **添加管理员覆盖功能**
   - API: `PATCH /devices/{mac}/recognition/override`
   - 数据库字段：`recognition_manual_override`

5. **完善主动防御能力探测**
   - 返回 `unsupported` 状态
   - 审计日志写入数据库

6. **添加缺失的 API 端点**
   - `GET /scan/status`
   - `PATCH /devices/{mac}`

### 🟢 P2 - 增强（可选）

7. **实现缺失的攻击类型**
   - SYN Flood
   - UDP Flood
   - TCP RST

8. **WebSocket 错误格式统一**
   - `event=error` 格式
   - 错误广播方法

---

## 文件修改位置总结

### 需要创建的文件
- `backend/alembic.ini`
- `backend/alembic/env.py`
- `backend/alembic/versions/001_initial.py`

### 需要修改的文件
1. `backend/app/core/config.py` - 添加全局开关
2. `backend/app/services/attack.py` - 能力探测、审计日志
3. `backend/app/routes/devices.py` - 管理员覆盖 API
4. `backend/app/routes/scan.py` - 扫描状态 API
5. `backend/app/core/engine/scapy.py` - 清理 TODO
6. `backend/app/routes/config.py` - 清理 TODO
7. `backend/app/core/engine/base_router.py` - 清理 TODO
8. `backend/app/models/db/device.py` - 添加 `recognition_manual_override` 字段

---

**核查结论**: 项目整体架构良好，但存在 **3 个阻塞性问题** 和 **5 个重要问题** 需要修复才能达到生产可用状态。
