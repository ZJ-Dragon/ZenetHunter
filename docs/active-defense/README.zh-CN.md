# 主动防御模块文档

⚠️ **仅限授权使用** ⚠️  
本模块包含用于授权安全研究和测试的主动防御实现。未经授权使用可能违反法律法规。

---

## 概述

主动防御模块为受控环境中的网络安全研究提供了全面的框架。它在不同的网络层实现各种主动防御技术，从WiFi到应用协议。

### 核心特性

- **多层防御**：WiFi、网络、协议和网桥层
- **跨平台支持**：Linux、macOS和Windows
- **实时监控**：基于WebSocket的操作跟踪
- **安全控制**：内置超时、强度控制和紧急停止
- **全面日志**：详细的操作日志和审计追踪

---

## 架构

```
┌─────────────────────────────────────────────────────────┐
│                   前端界面                               │
│            (React仪表板 + WebSocket)                     │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────┐
│                  API层 (FastAPI)                         │
│  - /api/active-defense/types (列出操作类型)             │
│  - /api/active-defense/{mac}/start (启动操作)           │
│  - /api/active-defense/{mac}/stop (停止操作)            │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────┐
│            主动防御服务层                                │
│  - 操作生命周期管理                                      │
│  - 任务调度和取消                                        │
│  - 状态跟踪和广播                                        │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────┐
│              攻击引擎 (基于Scapy)                        │
│  - 原始数据包操作                                        │
│  - 平台特定实现                                          │
│  - 权限和能力检查                                        │
└─────────────────────────────────────────────────────────┘
```

---

## 主动防御类型

### WiFi层

#### 1. WiFi 去认证 (KICK)
发送802.11去认证帧以断开设备与无线网络的连接。

**使用场景**：
- 无线网络弹性测试
- 访问控制机制评估
- 客户端重连行为分析

**参数**：
- `duration`: 操作持续时间（秒，1-3600）
- `intensity`: 去认证帧速率（1=低，10=高）

**实现**: `scapy.py`中的`_run_kick_attack()`

#### 2. 信标泛洪 (BEACON_FLOOD)
用伪造的AP信标帧淹没区域以混淆无线客户端。

**使用场景**：
- AP选择算法测试
- 无线干扰抵抗评估
- 基于SSID的过滤机制测试

**参数**：
- `duration`: 操作持续时间（秒）
- `intensity`: 信标传输速率

**实现**: `scapy.py`中的`_run_beacon_flood_attack()`

---

### 网络层

#### 3. ARP欺骗 (BLOCK)
操纵ARP缓存条目以重定向或阻止网络流量。

**使用场景**：
- 中间人攻击模拟
- 网络隔离测试
- 流量重定向场景

**技术细节**：
- 发送伪造发送者MAC的精心制作的ARP回复
- 在操作期间维持持续的缓存中毒
- 完成后自动恢复

**实现**: `scapy.py`中的`_run_block_attack()`

#### 4. ARP泛洪 (ARP_FLOOD)
用ARP请求淹没网络以压力测试ARP表。

**使用场景**：
- 网络容量测试
- ARP表溢出场景
- 交换机性能评估

**参数**：
- `duration`: 泛洪持续时间
- `intensity`: 数据包传输速率

**实现**: `scapy.py`中的`_run_arp_flood_attack()`

#### 5. ICMP重定向 (ICMP_REDIRECT)
发送ICMP重定向消息以操纵路由表。

**使用场景**：
- 路由安全测试
- ICMP过滤机制评估
- 网络路径操纵研究

**技术细节**：
- 类型5的ICMP重定向消息
- 针对特定主机路由
- 测试路由器安全配置

**实现**: `scapy.py`中的`_run_icmp_redirect_attack()`

---

### 协议层

#### 6. DHCP欺骗 (DHCP_SPOOF)
用恶意DHCP提供响应DHCP请求。

**使用场景**：
- DHCP安全机制测试
- 网络配置控制研究
- 流氓DHCP服务器检测评估

**技术细节**：
- 监听DHCP DISCOVER数据包
- 发送精心制作的DHCP OFFER响应
- 可指定自定义网关和DNS

**实现**: `scapy.py`中的`_run_dhcp_spoof_attack()`

#### 7. DNS欺骗 (DNS_SPOOF)
拦截DNS查询并提供恶意响应。

**使用场景**：
- DNS安全测试
- 名称解析操纵
- DNS过滤绕过研究

**技术细节**：
- 监控UDP 53端口流量
- 制作DNS响应数据包
- 支持A、AAAA和其他记录类型

**实现**: `scapy.py`中的`_run_dns_spoof_attack()`

---

### 交换机/网桥层

#### 8. MAC泛洪 (MAC_FLOOD)
用伪造的MAC地址淹没交换机CAM表。

**使用场景**：
- 交换机安全测试
- CAM表溢出场景
- 端口安全机制评估

**技术细节**：
- 生成随机源MAC地址
- 高速率数据包传输
- 测试交换机故障转移行为

**实现**: `scapy.py`中的`_run_mac_flood_attack()`

#### 9. VLAN跳跃 (VLAN_HOP)
尝试绕过VLAN分段。

**使用场景**：
- VLAN安全测试
- 网络分段评估
- 双标签攻击模拟

**参数**：
- `target_vlan`: 要访问的VLAN ID
- `duration`: 测试持续时间

**实现**: `scapy.py`中的`_run_vlan_hop_attack()`

---

### 高级技术

#### 10. 端口扫描 (PORT_SCAN)
主动TCP/UDP端口扫描用于服务发现。

**使用场景**：
- 攻击面分析
- 服务枚举
- 防火墙规则测试

**技术细节**：
- SYN扫描实现
- 可配置端口范围
- 隐蔽扫描选项

**实现**: `scapy.py`中的`_run_port_scan_attack()`

#### 11. 流量整形 (TRAFFIC_SHAPE)
带宽限制和QoS测试。

**使用场景**：
- QoS机制测试
- 带宽控制评估
- 流量优先级研究

**技术细节**：
- 使用操作系统级流量控制(tc/iptables)
- 可配置带宽限制
- 按设备速率限制

**实现**: `scapy.py`中的`_run_traffic_shape_attack()`

---

## 使用示例

### 启动操作

```python
# Python SDK示例
from zenethunter import ActiveDefenseClient

client = ActiveDefenseClient("http://localhost:8000", token="your-jwt-token")

# 启动ARP欺骗操作
response = client.start_operation(
    mac="aa:bb:cc:dd:ee:ff",
    operation_type="block",
    duration=300,  # 5分钟
    intensity=5    # 中等强度
)

print(f"操作已启动: {response.status}")
```

### 使用REST API

```bash
# 获取可用的操作类型
curl -X GET "http://localhost:8000/api/active-defense/types" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 启动操作
curl -X POST "http://localhost:8000/api/active-defense/aa:bb:cc:dd:ee:ff/start" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "arp_flood",
    "duration": 120,
    "intensity": 7
  }'

# 停止操作
curl -X POST "http://localhost:8000/api/active-defense/aa:bb:cc:dd:ee:ff/stop" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### WebSocket监控

```javascript
// JavaScript WebSocket示例
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch(data.event) {
    case 'activeDefenseStarted':
      console.log('操作已启动:', data.data);
      break;
    case 'activeDefenseLog':
      console.log('日志:', data.data.message);
      break;
    case 'activeDefenseStopped':
      console.log('操作已停止:', data.data);
      break;
  }
};
```

---

## 安全性和最佳实践

### 权限要求

所有操作需要：
- **Root/管理员权限**用于原始数据包操作
- **NET_RAW能力**在Linux上（最低要求）
- 通过JWT令牌的**显式用户认证**

### 安全控制

1. **最大持续时间**：操作上限为3600秒（1小时）
2. **自动超时**：所有操作都有10秒安全超时
3. **紧急停止**：操作可随时取消
4. **强度限制**：可配置的强度级别（1-10）

### 操作指南

✅ **应该**：
- 测试前获得书面授权
- 在隔离的实验室环境中测试
- 通过WebSocket日志监控操作
- 记录所有测试活动
- 使用适当的强度级别

❌ **不应该**：
- 未经授权在生产网络上测试
- 无理由以最大强度运行操作
- 无人看管地运行操作
- 共享访问凭据
- 绕过安全控制

### 法律合规

⚠️ **警告**：未经授权使用这些技术可能违反：
- 美国的《计算机欺诈和滥用法》(CFAA)
- 英国的《计算机滥用法》
- 其他司法管辖区的类似法律

**始终确保**：
- 您拥有明确的书面许可
- 您正在测试自己的系统或授权的系统
- 您的活动符合当地法律法规
- 您维护适当的文档和审计追踪

---

## 实现细节

### 引擎架构

主动防御模块使用模块化引擎架构：

```python
class ScapyAttackEngine(AttackEngine):
    """基于Scapy的主动防御操作实现。"""
    
    def check_permissions(self) -> bool:
        """验证原始数据包操作所需的权限。"""
        
    async def start_attack(self, target_mac: str, 
                          attack_type: ActiveDefenseType,
                          duration: int) -> None:
        """执行主动防御操作。"""
        
    async def stop_attack(self, target_mac: str) -> None:
        """紧急停止活动操作。"""
```

### 平台支持

| 平台 | 原始套接字 | 所需权限 | 备注 |
|----------|-------------|---------------------|-------|
| Linux | ✅ 完全支持 | root或CAP_NET_RAW | 推荐平台 |
| macOS | ✅ 完全支持 | root | 需要sudo/root |
| Windows | ⚠️ 有限支持 | 管理员 | 某些操作可能失败 |

### 数据包制作

操作使用Scapy进行数据包操作：

```python
from scapy.all import ARP, Ether, sendp

# 示例：ARP欺骗数据包
packet = Ether(dst=target_mac, src=my_mac) / \
         ARP(op=2,                    # ARP回复
             pdst=gateway_ip,         # 目标IP
             psrc=gateway_ip,         # 伪造源
             hwdst=target_mac,        # 目标MAC
             hwsrc=my_mac)            # 我们的MAC

sendp(packet, iface=interface, verbose=False)
```

---

## 故障排除

### 常见问题

#### 1. 权限被拒绝

**症状**：操作失败，提示"权限被拒绝"或"需要Root权限"

**解决方案**：
- 以root/管理员权限运行后端
- 在Linux上：添加CAP_NET_RAW能力
- 检查进程UID：`id`应显示`uid=0(root)`

#### 2. 找不到网络接口

**症状**："找不到接口"或"无默认接口"

**解决方案**：
- 检查可用接口：`ip link`(Linux)或`ifconfig`(macOS)
- 在配置中设置默认接口
- 验证网络适配器已启用

#### 3. 操作超时

**症状**：操作立即完成或超时

**解决方案**：
- 检查目标设备是否在线
- 验证网络连接
- 在配置中增加超时值
- 检查防火墙规则

#### 4. WebSocket断开

**症状**：实时更新停止工作

**解决方案**：
- 在浏览器DevTools中检查WebSocket连接
- 验证后端WebSocket端点可访问
- 检查代理/防火墙是否阻止WebSocket连接

---

## 测试和验证

### 单元测试

```bash
# 运行主动防御模块测试
cd backend
pytest tests/test_attack.py -v
pytest tests/test_scapy_engine.py -v
```

### 集成测试

```bash
# 测试完整操作生命周期
pytest tests/test_integration_attack.py -v --run-integration
```

### 手动测试检查清单

- [ ] 认证和授权
- [ ] 操作启动/停止功能
- [ ] WebSocket实时更新
- [ ] 安全超时机制
- [ ] 紧急停止功能
- [ ] 操作日志和审计追踪
- [ ] 多个并发操作
- [ ] 错误处理和恢复

---

## 参考资料

### 技术文档

- [Scapy文档](https://scapy.readthedocs.io/)
- [IEEE 802.11规范](https://standards.ieee.org/standard/802_11-2020.html)
- [RFC 826 - ARP](https://tools.ietf.org/html/rfc826)
- [RFC 2131 - DHCP](https://tools.ietf.org/html/rfc2131)
- [RFC 1035 - DNS](https://tools.ietf.org/html/rfc1035)

### 安全研究

- [OWASP测试指南](https://owasp.org/www-project-web-security-testing-guide/)
- [NIST网络安全框架](https://www.nist.gov/cyberframework)
- [SANS安全研究](https://www.sans.org/security-resources/)

### 法律和道德指南

- [EC-Council道德准则](https://www.eccouncil.org/code-of-ethics/)
- [ISC2道德准则](https://www.isc2.org/Ethics)
- [计算机欺诈和滥用法](https://www.justice.gov/jm/criminal-resource-manual-1030-computer-fraud-and-abuse-act)

---

## 贡献

出于安全原因，对主动防御模块的贡献需要：

1. **安全审查**：背景调查和批准
2. **代码审查**：高级工程师强制性安全审查
3. **文档**：完整的技术文档
4. **测试**：全面的单元和集成测试
5. **法律审查**：合规性验证

一般贡献指南请参见[CONTRIBUTING.md](../../CONTRIBUTING.md)。

---

## 许可证

本模块是ZenetHunter的一部分，根据MIT许可证授权，并附加安全限制。详见[LICENSE](../../LICENSE)。

**附加限制**：
- 仅限授权使用
- 禁止恶意使用
- 需遵守当地法律
- 强制书面授权

---

## 联系方式

如有问题、安全疑虑或授权请求，请通过官方渠道联系项目维护者。

⚠️ **未经适当授权和了解法律影响，请勿使用本模块。**
