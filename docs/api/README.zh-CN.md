# ZenetHunter API 文档

ZenetHunter 主动防御平台的完整 REST API 参考。

**基础 URL**: `http://localhost:8000/api`  
**API 版本**: v2.0.0  
**认证方式**: JWT Bearer Token

---

## 目录

1. [认证](#认证)
2. [主动防御](#主动防御)
3. [设备管理](#设备管理)
4. [网络扫描](#网络扫描)
5. [拓扑](#拓扑)
6. [日志](#日志)
7. [配置](#配置)
8. [WebSocket](#websocket)
9. [错误处理](#错误处理)

---

## 认证

### 登录

认证并接收 JWT token。

```http
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=admin&password=your_password
```

**响应**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

### 使用 Token

在所有后续请求的 Authorization 头中包含 token：

```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

---

## 主动防御

### 列出操作类型

获取所有可用的主动防御操作类型。

```http
GET /active-defense/types
Authorization: Bearer {token}
```

**响应**:
```json
[
  {
    "id": "kick",
    "name": "KICK",
    "description": "WiFi 去认证 - 断开设备与无线网络的连接"
  },
  {
    "id": "arp_flood",
    "name": "ARP_FLOOD",
    "description": "ARP 泛洪 - 压力测试网络 ARP 表"
  }
]
```

### 启动操作

对目标设备启动主动防御操作。

```http
POST /active-defense/{mac}/start
Authorization: Bearer {token}
Content-Type: application/json

{
  "type": "arp_flood",
  "duration": 120,
  "intensity": 5
}
```

**路径参数**:
- `mac` (字符串，必需): 目标设备 MAC 地址（格式：`aa:bb:cc:dd:ee:ff`）

**请求体**:
- `type` (字符串，必需): 操作类型（见[操作类型](#操作类型)）
- `duration` (整数，必需): 持续时间（秒，1-3600）
- `intensity` (整数，可选): 强度等级 1-10（默认：5）

**响应** (202 Accepted):
```json
{
  "device_mac": "aa:bb:cc:dd:ee:ff",
  "status": "running",
  "message": "主动防御 arp_flood 已在 aa:bb:cc:dd:ee:ff 上启动",
  "start_time": "2026-01-17T10:30:00Z"
}
```

**错误响应** (400 Bad Request):
```json
{
  "type": "validation_error",
  "title": "请求验证失败",
  "status": 400,
  "detail": "无效的强度值",
  "correlation_id": "req-12345"
}
```

### 停止操作

停止目标设备上的任何主动防御操作。

```http
POST /active-defense/{mac}/stop
Authorization: Bearer {token}
```

**响应** (200 OK):
```json
{
  "device_mac": "aa:bb:cc:dd:ee:ff",
  "status": "stopped",
  "message": "用户已停止主动防御操作"
}
```

### 操作类型

| 类型 | 层级 | 描述 |
|------|-------|-------------|
| `kick` | WiFi | WiFi 去认证 |
| `beacon_flood` | WiFi | WiFi 信标泛洪 |
| `block` | 网络层 | ARP 欺骗 |
| `arp_flood` | 网络层 | ARP 泛洪 |
| `icmp_redirect` | 网络层 | ICMP 重定向 |
| `dhcp_spoof` | 协议层 | DHCP 欺骗 |
| `dns_spoof` | 协议层 | DNS 欺骗 |
| `mac_flood` | 桥接层 | MAC 地址泛洪 |
| `vlan_hop` | 桥接层 | VLAN 跳跃 |
| `port_scan` | 高级 | TCP/UDP 端口扫描 |
| `traffic_shape` | 高级 | 流量整形 |

---

## 设备管理

### 列出所有设备

获取所有发现的网络设备。

```http
GET /devices
Authorization: Bearer {token}
```

**查询参数**:
- `status` (字符串，可选): 按状态过滤（`online`、`offline`、`blocked`）
- `type` (字符串，可选): 按类型过滤（`router`、`pc`、`mobile`、`iot`、`unknown`）
- `limit` (整数，可选): 最大结果数（默认：100）
- `offset` (整数，可选): 分页偏移量（默认：0）

**响应**:
```json
{
  "devices": [
    {
      "mac": "aa:bb:cc:dd:ee:ff",
      "ip": "192.168.1.100",
      "name": "iPhone-12",
      "vendor": "Apple Inc.",
      "model": "iPhone 12",
      "type": "mobile",
      "status": "online",
      "active_defense_status": "idle",
      "first_seen": "2026-01-17T08:00:00Z",
      "last_seen": "2026-01-17T10:30:00Z",
      "tags": ["trusted"],
      "alias": "John的iPhone"
    }
  ],
  "total": 15,
  "limit": 100,
  "offset": 0
}
```

### 获取设备详情

获取特定设备的详细信息。

```http
GET /devices/{mac}
Authorization: Bearer {token}
```

### 更新设备

更新设备信息（别名、标签等）。

```http
PATCH /devices/{mac}
Authorization: Bearer {token}
Content-Type: application/json

{
  "alias": "John的iPhone",
  "tags": ["trusted", "personal"]
}
```

### 删除设备

从数据库中删除设备。

```http
DELETE /devices/{mac}
Authorization: Bearer {token}
```

**响应** (204 No Content)

---

## 网络扫描

### 启动网络扫描

启动网络扫描以发现设备。

```http
POST /scan/start
Authorization: Bearer {token}
Content-Type: application/json

{
  "type": "quick",
  "target_subnets": ["192.168.1.0/24"]
}
```

**请求体**:
- `type` (字符串，必需): 扫描类型（`quick`、`deep`、`custom`）
- `target_subnets` (数组，可选): 要扫描的特定子网

**响应** (202 Accepted):
```json
{
  "scan_id": "scan-uuid-12345",
  "status": "running",
  "type": "quick",
  "started_at": "2026-01-17T10:40:00Z"
}
```

### 获取扫描状态

检查正在运行的扫描状态。

```http
GET /scan/status
Authorization: Bearer {token}
```

**响应**:
```json
{
  "scan_id": "scan-uuid-12345",
  "status": "running",
  "progress": 65,
  "devices_found": 12,
  "started_at": "2026-01-17T10:40:00Z",
  "estimated_completion": "2026-01-17T10:42:00Z"
}
```

### 停止扫描

停止正在运行的网络扫描。

```http
POST /scan/stop
Authorization: Bearer {token}
```

---

## 拓扑

### 获取网络拓扑

检索网络拓扑图。

```http
GET /topology
Authorization: Bearer {token}
```

**响应**:
```json
{
  "nodes": [
    {
      "id": "aa:bb:cc:dd:ee:ff",
      "label": "iPhone-12",
      "type": "mobile",
      "ip": "192.168.1.100",
      "status": "online"
    }
  ],
  "edges": [
    {
      "source": "aa:bb:cc:dd:ee:ff",
      "target": "11:22:33:44:55:66",
      "type": "wireless"
    }
  ],
  "metadata": {
    "total_devices": 15,
    "total_connections": 14,
    "last_updated": "2026-01-17T10:45:00Z"
  }
}
```

---

## 日志

### 获取事件日志

检索系统和操作日志。

```http
GET /logs
Authorization: Bearer {token}
```

**查询参数**:
- `level` (字符串，可选): 按日志级别过滤（`debug`、`info`、`warning`、`error`）
- `source` (字符串，可选): 按来源过滤（`scan`、`active_defense`、`auth`等）
- `start_time` (字符串，可选): 开始时间（ISO 8601）
- `end_time` (字符串，可选): 结束时间（ISO 8601）
- `limit` (整数，可选): 最大结果数（默认：100）

**响应**:
```json
{
  "logs": [
    {
      "id": "log-uuid-12345",
      "timestamp": "2026-01-17T10:30:00Z",
      "level": "info",
      "source": "active_defense",
      "message": "主动防御执行中: arp_flood | 目标 aa:bb:cc:dd:ee:ff",
      "metadata": {
        "mac": "aa:bb:cc:dd:ee:ff",
        "operation_type": "arp_flood",
        "duration": 120
      }
    }
  ],
  "total": 450,
  "limit": 100,
  "has_more": true
}
```

---

## 配置

### 获取配置

检索当前系统配置。

```http
GET /config
Authorization: Bearer {token}
```

**响应**:
```json
{
  "scan": {
    "default_timeout": 2,
    "max_concurrency": 50,
    "auto_scan_interval": 300
  },
  "active_defense": {
    "max_duration": 3600,
    "default_intensity": 5,
    "allowed_operations": ["arp_flood", "block", "kick"]
  },
  "security": {
    "require_auth": true,
    "session_timeout": 3600,
    "max_login_attempts": 5
  }
}
```

### 更新配置

更新系统配置。

```http
PATCH /config
Authorization: Bearer {token}
Content-Type: application/json

{
  "scan": {
    "max_concurrency": 100
  }
}
```

---

## WebSocket

### 连接

连接到 WebSocket 端点以获取实时更新。

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
```

### 认证

连接后发送认证消息：

```javascript
ws.send(JSON.stringify({
  type: 'auth',
  token: 'your-jwt-token'
}));
```

### 事件类型

#### 主动防御事件

**操作已启动**:
```json
{
  "event": "activeDefenseStarted",
  "data": {
    "mac": "aa:bb:cc:dd:ee:ff",
    "type": "arp_flood",
    "duration": 120,
    "intensity": 5,
    "start_time": "2026-01-17T10:30:00Z"
  }
}
```

**操作日志**:
```json
{
  "event": "activeDefenseLog",
  "data": {
    "level": "info",
    "message": "主动防御执行中: arp_flood | 目标 aa:bb:cc:dd:ee:ff",
    "mac": "aa:bb:cc:dd:ee:ff",
    "operation_type": "arp_flood",
    "timestamp": "2026-01-17T10:30:05Z"
  }
}
```

**操作已停止**:
```json
{
  "event": "activeDefenseStopped",
  "data": {
    "mac": "aa:bb:cc:dd:ee:ff",
    "timestamp": "2026-01-17T10:32:00Z"
  }
}
```

#### 扫描事件

**扫描已启动**:
```json
{
  "event": "scanStarted",
  "data": {
    "scan_id": "scan-uuid-12345",
    "type": "quick",
    "timestamp": "2026-01-17T10:40:00Z"
  }
}
```

**设备已发现**:
```json
{
  "event": "deviceDiscovered",
  "data": {
    "mac": "aa:bb:cc:dd:ee:ff",
    "ip": "192.168.1.100",
    "vendor": "Apple Inc.",
    "timestamp": "2026-01-17T10:40:15Z"
  }
}
```

**扫描已完成**:
```json
{
  "event": "scanCompleted",
  "data": {
    "scan_id": "scan-uuid-12345",
    "devices_found": 15,
    "duration": 120,
    "timestamp": "2026-01-17T10:42:00Z"
  }
}
```

---

## 错误处理

所有 API 错误遵循 RFC 7807 Problem Details 格式。

### 错误响应格式

```json
{
  "type": "validation_error",
  "title": "请求验证失败",
  "status": 400,
  "detail": "持续时间必须在 1 到 3600 秒之间",
  "correlation_id": "req-12345",
  "errors": [
    {
      "field": "duration",
      "message": "值必须在 1 到 3600 之间"
    }
  ]
}
```

### 常见错误代码

| 状态码 | 类型 | 描述 |
|--------|------|-------------|
| 400 | `validation_error` | 无效的请求参数 |
| 401 | `authentication_error` | 缺失或无效的认证 |
| 403 | `authorization_error` | 权限不足 |
| 404 | `not_found` | 资源未找到 |
| 409 | `conflict` | 资源冲突（例如，操作已在运行） |
| 429 | `rate_limit_exceeded` | 请求过多 |
| 500 | `internal_error` | 服务器内部错误 |
| 503 | `service_unavailable` | 服务暂时不可用 |

### 错误处理最佳实践

1. **检查状态码**：始终检查 HTTP 状态码
2. **使用关联 ID**：记录关联 ID 以便调试
3. **实现重试逻辑**：针对 429 和 503 错误
4. **发送前验证**：客户端验证参数
5. **处理超时**：设置适当的请求超时

---

## 速率限制

API 请求受速率限制以防止滥用：

- **认证**：每分钟 10 个请求
- **主动防御操作**：每用户 5 个并发操作
- **网络扫描**：每用户 1 个并发扫描
- **一般 API**：每用户每分钟 100 个请求

**速率限制头**:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642416000
```

---

## 分页

列表端点支持分页：

```http
GET /devices?limit=20&offset=40
```

**响应头**:
```http
X-Total-Count: 150
X-Limit: 20
X-Offset: 40
Link: </devices?limit=20&offset=60>; rel="next"
```

---

## 版本控制

API 版本控制通过 URL 路径处理：

- **当前**：`/api/v2/...`（默认，可省略版本）
- **旧版**：`/api/v1/...`（已弃用）

---

## SDK 和客户端库

### Python

```python
from zenethunter import ZenetHunterClient

client = ZenetHunterClient(
    base_url="http://localhost:8000",
    username="admin",
    password="your_password"
)

# 启动操作
response = client.active_defense.start(
    mac="aa:bb:cc:dd:ee:ff",
    type="arp_flood",
    duration=120
)

# 列出设备
devices = client.devices.list(status="online")
```

### JavaScript/TypeScript

```typescript
import { ZenetHunterClient } from 'zenethunter-js';

const client = new ZenetHunterClient({
  baseUrl: 'http://localhost:8000',
  token: 'your-jwt-token'
});

// 启动操作
const response = await client.activeDefense.start({
  mac: 'aa:bb:cc:dd:ee:ff',
  type: 'arp_flood',
  duration: 120
});

// WebSocket 连接
client.ws.on('activeDefenseLog', (data) => {
  console.log('日志:', data);
});
```

---

## 交互式 API 文档

访问交互式 API 文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

---

## 支持和资源

- **GitHub**: https://github.com/ZJ-Dragon/ZenetHunter
- **文档**: https://zenethunter.readthedocs.io
- **问题跟踪**: https://github.com/ZJ-Dragon/ZenetHunter/issues

---

**⚠️ 安全提示**：此 API 提供对强大网络安全研究工具的访问。确保对所有操作进行适当的认证、授权和审计日志记录。未经授权使用可能违反法律法规。
