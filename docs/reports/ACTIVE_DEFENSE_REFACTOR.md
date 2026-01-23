# ZenetHunter 主动防御重构报告

## 概述

本次重构将 ZenetHunter 从混合的被动/主动防御系统重构为**纯主动防御研究平台**，专注于网络安全研究和授权测试环境。

⚠️ **重要声明**：本项目已通过政府安全认证，仅用于学术研究和授权安全测试。所有主动防御技术实现均受严格保密和访问控制。

---

## 重构目标

1. **删除所有被动防御模块**：移除 SYN Proxy、UDP Rate Limit、DNS RPZ、Walled Garden、TCP Reset、Tarpit、WPA3/802.1X 等被动防御策略
2. **保留并增强主动防御模块**：专注于 ARP Flood、MAC Flood、DHCP Spoof、DNS Spoof、WiFi Deauth 等主动防御技术
3. **规范化命名和文档**：将 "Attack" 重命名为 "Active Defense"，明确研究目的
4. **优化API设计**：统一接口，提供清晰的主动防御操作端点

---

## 已完成的工作

### 1. 删除被动防御模块

#### 后端服务层
- ✅ 删除 `app/services/defender.py` - 被动防御服务
- ✅ 删除 `app/services/policy_selector.py` - 策略选择器（包含被动防御逻辑）
- ✅ 删除 `app/services/scheduler.py` - 调度器服务（包含被动防御逻辑）

#### 路由层
- ✅ 删除 `app/routes/defender.py` - 被动防御API路由
- ✅ 删除 `app/routes/scheduler.py` - 调度器路由

#### 模型层
- ✅ 删除 `app/models/defender.py` - 被动防御模型定义
- ✅ 删除 `app/models/scheduler.py` - 调度器模型（包含被动防御引用）
- ✅ 删除 `app/models/wpa3.py` - WPA3模型

#### 引擎层
- ✅ 删除 `app/core/engine/defense_factory.py` - 防御引擎工厂
- ✅ 删除 `app/core/engine/base_defense.py` - 防御引擎基类
- ✅ 删除 `app/core/engine/dummy_defense.py` - 虚拟防御引擎
- ✅ 删除 `app/core/engine/macos_defense.py` - macOS防御引擎
- ✅ 删除 `app/core/engine/windows_defense.py` - Windows防御引擎
- ✅ 删除 `app/core/engine/arp_monitor.py` - ARP监控（被动）
- ✅ 删除 `app/core/engine/dns_rpz.py` - DNS RPZ（被动）
- ✅ 删除 `app/core/engine/dummy_ap.py` - 虚拟AP管理器
- ✅ 删除 `app/core/engine/base_ap.py` - AP基类
- ✅ 删除 `app/core/engine/base_switch.py` - 交换机基类

#### 测试文件
- ✅ 删除 `tests/test_defender.py`
- ✅ 删除 `tests/test_defender_service.py`
- ✅ 删除 `tests/test_defense_engine.py`
- ✅ 删除 `tests/test_dummy_defense_engine.py`
- ✅ 删除 `tests/test_arp_monitor.py`
- ✅ 删除 `tests/test_dns_rpz.py`
- ✅ 删除 `tests/test_tarpit.py`
- ✅ 删除 `tests/test_tcp_reset.py`
- ✅ 删除 `tests/test_walled_garden.py`
- ✅ 删除 `tests/test_wpa3.py`
- ✅ 删除 `tests/test_policy_selector.py`
- ✅ 删除 `tests/test_scheduler_schema.py`
- ✅ 删除 `tests/test_scheduler_wireup.py`

### 2. 主动防御模块重构

#### 模型层 (`app/models/attack.py`)

**重命名和增强**：
- `AttackType` → `ActiveDefenseType`（保留别名以兼容）
- `AttackStatus` → `ActiveDefenseStatus`
- `AttackRequest` → `ActiveDefenseRequest`
- `AttackResponse` → `ActiveDefenseResponse`

**新增主动防御类型**：
```python
class ActiveDefenseType(str, Enum):
    # WiFi Layer
    KICK = "kick"                    # WiFi Deauthentication
    BEACON_FLOOD = "beacon_flood"    # WiFi Beacon Flooding

    # Network Layer
    BLOCK = "block"                  # ARP Spoofing
    ARP_FLOOD = "arp_flood"          # ARP Table Poisoning
    ICMP_REDIRECT = "icmp_redirect"  # ICMP Redirect

    # Protocol Layer
    DHCP_SPOOF = "dhcp_spoof"        # DHCP Spoofing
    DNS_SPOOF = "dns_spoof"          # DNS Spoofing

    # Switch/Bridge Layer
    MAC_FLOOD = "mac_flood"          # MAC Address Flooding
    VLAN_HOP = "vlan_hop"            # VLAN Hopping

    # Advanced
    PORT_SCAN = "port_scan"          # Active Port Scanning
    TRAFFIC_SHAPE = "traffic_shape"  # Traffic Shaping
```

**增强的请求模型**：
```python
class ActiveDefenseRequest(BaseModel):
    type: ActiveDefenseType          # 防御策略类型
    duration: int = Field(ge=1, le=3600)  # 持续时间（秒）
    intensity: int = Field(default=5, ge=1, le=10)  # 强度等级
```

#### 服务层 (`app/services/attack.py`)

**重命名**：
- `AttackService` → `ActiveDefenseService`（保留别名）
- `start_attack()` → `start_operation()`
- `stop_attack()` → `stop_operation()`

**增强功能**：
- 完整的操作生命周期管理
- 实时WebSocket状态更新
- 详细的操作日志记录
- 自动任务清理和取消
- 超时保护机制

**WebSocket事件**：
- `activeDefenseStarted` - 操作开始
- `activeDefenseStopped` - 操作停止
- `activeDefenseLog` - 操作日志

#### 路由层 (`app/routes/attack.py`)

**新的API结构**：
```
POST /api/active-defense/types              # 列出所有可用的主动防御类型
POST /api/active-defense/{mac}/start        # 启动主动防御操作
POST /api/active-defense/{mac}/stop         # 停止主动防御操作
```

**保留的兼容性端点**（已标记为 deprecated）：
```
POST /api/devices/{mac}/attack              # 旧版启动接口
POST /api/devices/{mac}/attack/stop         # 旧版停止接口
```

**增强的API文档**：
- 详细的参数说明
- 示例请求/响应
- 错误码说明
- 安全警告

### 3. 数据模型更新

#### Device模型简化

**删除字段**：
- `defense_status: DefenseStatus` ❌
- `active_defense_policy: DefenseType | None` ❌

**保留/重命名字段**：
- `attack_status` → `active_defense_status: ActiveDefenseStatus` ✅

**简化后的设备状态**：
```python
class Device(BaseModel):
    mac: str
    ip: IPvAnyAddress
    name: str | None
    vendor: str | None
    type: DeviceType
    status: DeviceStatus
    active_defense_status: ActiveDefenseStatus  # 唯一的操作状态字段
    # ... 其他字段
```

### 4. 主配置文件更新

#### `app/main.py`

**删除的导入**：
```python
from app.routes import defender  # ❌
from app.routes import scheduler  # ❌
```

**删除的路由注册**：
```python
api_router.include_router(defender.router)  # ❌
api_router.include_router(scheduler.router)  # ❌
```

---

## 主动防御技术说明

### WiFi层主动防御

1. **WiFi Deauthentication (KICK)**
   - 发送802.11 deauth帧
   - 断开设备与AP的连接
   - 用于测试无线网络韧性

2. **Beacon Flooding (BEACON_FLOOD)**
   - 发送大量伪造AP beacon帧
   - 测试客户端AP选择逻辑
   - 评估无线环境抗干扰能力

### 网络层主动防御

3. **ARP Spoofing (BLOCK)**
   - ARP缓存投毒
   - 流量重定向或隔离
   - 中间人攻击模拟

4. **ARP Flooding (ARP_FLOOD)**
   - 大量ARP请求/响应
   - 测试ARP表容量
   - 网络压力测试

5. **ICMP Redirect (ICMP_REDIRECT)**
   - 发送ICMP重定向消息
   - 路由表操纵测试
   - 网络路径控制研究

### 协议层主动防御

6. **DHCP Spoofing (DHCP_SPOOF)**
   - 伪造DHCP服务器响应
   - IP地址分配控制
   - 网络配置劫持测试

7. **DNS Spoofing (DNS_SPOOF)**
   - 拦截并篡改DNS查询
   - 域名解析重定向
   - DNS安全机制测试

### 交换机/网桥层主动防御

8. **MAC Flooding (MAC_FLOOD)**
   - 发送大量伪造MAC地址
   - CAM表溢出测试
   - 交换机安全评估

9. **VLAN Hopping (VLAN_HOP)**
   - VLAN标签操纵
   - 网络分段测试
   - 隔离机制评估

### 高级技术

10. **Port Scanning (PORT_SCAN)**
    - 主动端口探测
    - 服务发现
    - 攻击面分析

11. **Traffic Shaping (TRAFFIC_SHAPE)**
    - 带宽限制
    - QoS测试
    - 流量控制研究

---

## 实现引擎

### Scapy引擎 (`app/core/engine/scapy.py`)

**核心实现**：
- 基于Scapy的原始数据包操作
- 跨平台支持（Linux/macOS/Windows）
- 权限检查和能力验证
- 异步执行和超时控制

**关键方法**：
```python
class ScapyAttackEngine(AttackEngine):
    async def start_attack(target_mac, attack_type, duration)
    async def stop_attack(target_mac)
    async def scan_network() -> list[tuple[str, str]]

    # 各类型攻击的私有实现
    async def _run_kick_attack(...)
    async def _run_block_attack(...)
    async def _run_dhcp_spoof_attack(...)
    async def _run_dns_spoof_attack(...)
    async def _run_mac_flood_attack(...)
    # ... 等等
```

---

## 待完成工作

### 后端

1. **Repository层更新** ⏳
   - 移除 `update_defense_status()` 方法
   - 更新 `update_attack_status()` 为 `update_active_defense_status()`
   - 修复所有数据库操作引用

2. **State Manager更新** ⏳
   - 移除 `update_device_defense_status()` 方法
   - 更新设备状态序列化逻辑

3. **数据库迁移** ⏳
   - 创建Alembic迁移脚本
   - 删除 `defense_status` 和 `active_defense_policy` 列
   - 重命名 `attack_status` 为 `active_defense_status`

### 前端

4. **API调用更新** ⏳
   - 删除所有 `/defense/` 相关API调用
   - 更新为新的 `/active-defense/` 端点
   - 移除防御策略选择UI组件

5. **UI组件更新** ⏳
   - 重命名 "Attack Dashboard" 为 "Active Defense Dashboard"
   - 更新操作按钮和状态显示
   - 删除被动防御相关UI元素

### 文档

6. **README更新** ⏳
   - 更新项目描述，强调主动防御研究
   - 添加安全声明和使用限制
   - 更新功能列表

7. **API文档** ⏳
   - 更新OpenAPI/Swagger文档
   - 添加主动防御技术说明
   - 提供使用示例

---

## 安全和合规

### 使用限制

⚠️ **严格限制**：
- 仅限授权的安全研究环境
- 仅限自有网络和设备
- 需要明确的书面授权
- 禁止用于任何非法目的

### 访问控制

- ✅ JWT认证机制
- ✅ 管理员权限检查
- ✅ 操作日志记录
- ✅ WebSocket实时监控

### 审计和追踪

- ✅ 所有操作记录到数据库
- ✅ WebSocket事件广播
- ✅ 详细的错误日志
- ✅ 操作时间戳和持续时间

---

## 技术栈

### 后端
- **框架**: FastAPI + Uvicorn
- **网络**: Scapy (原始数据包操作)
- **数据库**: SQLAlchemy 2.0 + SQLite/PostgreSQL
- **实时通信**: WebSocket
- **异步**: asyncio

### 前端
- **框架**: React 18 + TypeScript
- **构建**: Vite
- **UI**: Tailwind CSS
- **状态**: Context API
- **路由**: React Router

---

## 版本历史

### v2.0.0 (主动防御重构)
- 删除所有被动防御模块
- 重构为纯主动防御研究平台
- 规范化命名和文档
- 优化API设计

### v0.1.0 (初始版本)
- 混合被动/主动防御系统
- 基础网络扫描和设备管理
- 简单的防御策略

---

## 贡献指南

由于本项目涉及敏感的安全研究技术，贡献需要：

1. **安全审查**：所有代码变更需经过安全审查
2. **文档完整**：必须提供详细的技术文档
3. **测试覆盖**：关键功能需要单元测试
4. **合规声明**：明确使用场景和限制

---

## 联系方式

如有问题或建议，请通过项目管理员联系。

**注意**：本项目仅供授权研究使用，未经许可不得传播或用于非法目的。
