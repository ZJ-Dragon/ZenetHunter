# Active Defense Module Documentation

⚠️ **AUTHORIZED USE ONLY** ⚠️  
This module contains active defense implementations for authorized security research and testing. Unauthorized use may violate laws and regulations.

---

## Overview

The Active Defense module provides a comprehensive framework for network security research in controlled environments. It implements various active defense techniques across different network layers, from WiFi to application protocols.

### Key Features

- **Multi-layer Defense**: WiFi, Network, Protocol, and Bridge layers
- **Cross-platform Support**: Linux, macOS, and Windows
- **Real-time Monitoring**: WebSocket-based operation tracking
- **Safety Controls**: Built-in timeouts, intensity controls, and emergency stops
- **Comprehensive Logging**: Detailed operation logs and audit trails

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Frontend Interface                     │
│            (React Dashboard + WebSocket)                 │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────┐
│                  API Layer (FastAPI)                     │
│  - /api/active-defense/types (List operations)          │
│  - /api/active-defense/{mac}/start (Start operation)    │
│  - /api/active-defense/{mac}/stop (Stop operation)      │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────┐
│            Active Defense Service Layer                  │
│  - Operation lifecycle management                        │
│  - Task scheduling and cancellation                      │
│  - Status tracking and broadcasting                      │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────┐
│              Attack Engine (Scapy-based)                 │
│  - Raw packet manipulation                               │
│  - Platform-specific implementations                     │
│  - Permission and capability checks                      │
└─────────────────────────────────────────────────────────┘
```

---

## Active Defense Types

### WiFi Layer

#### 1. WiFi Deauthentication (KICK)
Sends 802.11 deauthentication frames to disconnect devices from wireless networks.

**Use Cases**:
- Wireless network resilience testing
- Access control mechanism evaluation
- Client reconnection behavior analysis

**Parameters**:
- `duration`: Operation duration in seconds (1-3600)
- `intensity`: Deauth frame rate (1=low, 10=high)

**Implementation**: `_run_kick_attack()` in `scapy.py`

#### 2. Beacon Flooding (BEACON_FLOOD)
Floods the area with fake AP beacon frames to confuse wireless clients.

**Use Cases**:
- AP selection algorithm testing
- Wireless interference resistance evaluation
- SSID-based filtering mechanism testing

**Parameters**:
- `duration`: Operation duration in seconds
- `intensity`: Beacon transmission rate

**Implementation**: `_run_beacon_flood_attack()` in `scapy.py`

---

### Network Layer

#### 3. ARP Spoofing (BLOCK)
Manipulates ARP cache entries to redirect or block network traffic.

**Use Cases**:
- Man-in-the-Middle attack simulation
- Network isolation testing
- Traffic redirection scenarios

**Technical Details**:
- Sends crafted ARP replies with spoofed sender MAC
- Maintains continuous cache poisoning during operation
- Automatic restoration upon completion

**Implementation**: `_run_block_attack()` in `scapy.py`

#### 4. ARP Flooding (ARP_FLOOD)
Floods the network with ARP requests to stress test ARP tables.

**Use Cases**:
- Network capacity testing
- ARP table overflow scenarios
- Switch performance evaluation

**Parameters**:
- `duration`: Flood duration
- `intensity`: Packet transmission rate

**Implementation**: `_run_arp_flood_attack()` in `scapy.py`

#### 5. ICMP Redirect (ICMP_REDIRECT)
Sends ICMP redirect messages to manipulate routing tables.

**Use Cases**:
- Routing security testing
- ICMP filtering mechanism evaluation
- Network path manipulation research

**Technical Details**:
- Type 5 ICMP redirect messages
- Targets specific host routes
- Tests router security configurations

**Implementation**: `_run_icmp_redirect_attack()` in `scapy.py`

---

### Protocol Layer

#### 6. DHCP Spoofing (DHCP_SPOOF)
Responds to DHCP requests with malicious DHCP offers.

**Use Cases**:
- DHCP security mechanism testing
- Network configuration control research
- Rogue DHCP server detection evaluation

**Technical Details**:
- Listens for DHCP DISCOVER packets
- Sends crafted DHCP OFFER responses
- Can specify custom gateway and DNS

**Implementation**: `_run_dhcp_spoof_attack()` in `scapy.py`

#### 7. DNS Spoofing (DNS_SPOOF)
Intercepts DNS queries and provides malicious responses.

**Use Cases**:
- DNS security testing
- Name resolution manipulation
- DNS filtering bypass research

**Technical Details**:
- Monitors UDP port 53 traffic
- Crafts DNS response packets
- Supports A, AAAA, and other record types

**Implementation**: `_run_dns_spoof_attack()` in `scapy.py`

---

### Switch/Bridge Layer

#### 8. MAC Flooding (MAC_FLOOD)
Floods switch CAM tables with fake MAC addresses.

**Use Cases**:
- Switch security testing
- CAM table overflow scenarios
- Port security mechanism evaluation

**Technical Details**:
- Generates random source MAC addresses
- High-rate packet transmission
- Tests switch failover behavior

**Implementation**: `_run_mac_flood_attack()` in `scapy.py`

#### 9. VLAN Hopping (VLAN_HOP)
Attempts to bypass VLAN segmentation.

**Use Cases**:
- VLAN security testing
- Network segmentation evaluation
- Double-tagging attack simulation

**Parameters**:
- `target_vlan`: VLAN ID to access
- `duration`: Test duration

**Implementation**: `_run_vlan_hop_attack()` in `scapy.py`

---

### Advanced Techniques

#### 10. Port Scanning (PORT_SCAN)
Active TCP/UDP port scanning for service discovery.

**Use Cases**:
- Attack surface analysis
- Service enumeration
- Firewall rule testing

**Technical Details**:
- SYN scan implementation
- Configurable port ranges
- Stealth scan options

**Implementation**: `_run_port_scan_attack()` in `scapy.py`

#### 11. Traffic Shaping (TRAFFIC_SHAPE)
Bandwidth limiting and QoS testing.

**Use Cases**:
- QoS mechanism testing
- Bandwidth control evaluation
- Traffic prioritization research

**Technical Details**:
- Uses OS-level traffic control (tc/iptables)
- Configurable bandwidth limits
- Per-device rate limiting

**Implementation**: `_run_traffic_shape_attack()` in `scapy.py`

---

## Usage Examples

### Starting an Operation

```python
# Python SDK Example
from zenethunter import ActiveDefenseClient

client = ActiveDefenseClient("http://localhost:8000", token="your-jwt-token")

# Start ARP spoofing operation
response = client.start_operation(
    mac="aa:bb:cc:dd:ee:ff",
    operation_type="block",
    duration=300,  # 5 minutes
    intensity=5    # Medium intensity
)

print(f"Operation started: {response.status}")
```

### Using REST API

```bash
# Get available operation types
curl -X GET "http://localhost:8000/api/active-defense/types" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Start operation
curl -X POST "http://localhost:8000/api/active-defense/aa:bb:cc:dd:ee:ff/start" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "arp_flood",
    "duration": 120,
    "intensity": 7
  }'

# Stop operation
curl -X POST "http://localhost:8000/api/active-defense/aa:bb:cc:dd:ee:ff/stop" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### WebSocket Monitoring

```javascript
// JavaScript WebSocket Example
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch(data.event) {
    case 'activeDefenseStarted':
      console.log('Operation started:', data.data);
      break;
    case 'activeDefenseLog':
      console.log('Log:', data.data.message);
      break;
    case 'activeDefenseStopped':
      console.log('Operation stopped:', data.data);
      break;
  }
};
```

---

## Safety and Best Practices

### Permission Requirements

All operations require:
- **Root/Administrator privileges** for raw packet operations
- **NET_RAW capability** on Linux (minimum requirement)
- **Explicit user authentication** via JWT tokens

### Safety Controls

1. **Maximum Duration**: Operations are capped at 3600 seconds (1 hour)
2. **Automatic Timeouts**: All operations have 10-second safety timeouts
3. **Emergency Stop**: Operations can be cancelled at any time
4. **Intensity Limiting**: Configurable intensity levels (1-10)

### Operational Guidelines

✅ **DO**:
- Obtain written authorization before testing
- Test in isolated lab environments
- Monitor operations via WebSocket logs
- Document all testing activities
- Use appropriate intensity levels

❌ **DON'T**:
- Test on production networks without authorization
- Run operations at maximum intensity without cause
- Leave operations running unattended
- Share access credentials
- Bypass safety controls

### Legal Compliance

⚠️ **Warning**: Unauthorized use of these techniques may violate:
- Computer Fraud and Abuse Act (CFAA) in the United States
- Computer Misuse Act in the United Kingdom
- Similar laws in other jurisdictions

**Always ensure**:
- You have explicit written permission
- You are testing your own systems or authorized systems
- Your activities comply with local laws and regulations
- You maintain proper documentation and audit trails

---

## Implementation Details

### Engine Architecture

The Active Defense module uses a modular engine architecture:

```python
class ScapyAttackEngine(AttackEngine):
    """Scapy-based implementation of active defense operations."""

    def check_permissions(self) -> bool:
        """Verify required permissions for raw packet operations."""

    async def start_attack(self, target_mac: str,
                          attack_type: ActiveDefenseType,
                          duration: int) -> None:
        """Execute active defense operation."""

    async def stop_attack(self, target_mac: str) -> None:
        """Emergency stop for active operations."""
```

### Platform Support

| Platform | Raw Sockets | Permissions Required | Notes |
|----------|-------------|---------------------|-------|
| Linux | ✅ Full | root or CAP_NET_RAW | Recommended platform |
| macOS | ✅ Full | root | Requires sudo/root |
| Windows | ⚠️ Limited | Administrator | Some operations may fail |

### Packet Crafting

Operations use Scapy for packet manipulation:

```python
from scapy.all import ARP, Ether, sendp

# Example: ARP spoofing packet
packet = Ether(dst=target_mac, src=my_mac) / \
         ARP(op=2,                    # ARP reply
             pdst=gateway_ip,         # Target IP
             psrc=gateway_ip,         # Spoofed source
             hwdst=target_mac,        # Target MAC
             hwsrc=my_mac)            # Our MAC

sendp(packet, iface=interface, verbose=False)
```

---

## Troubleshooting

### Common Issues

#### 1. Permission Denied

**Symptom**: Operations fail with "Permission denied" or "Root required"

**Solutions**:
- Run backend with root/administrator privileges
- On Linux: Add CAP_NET_RAW capability
- Check process UID: `id` should show `uid=0(root)`

#### 2. Network Interface Not Found

**Symptom**: "Interface not found" or "No default interface"

**Solutions**:
- Check available interfaces: `ip link` (Linux) or `ifconfig` (macOS)
- Set default interface in configuration
- Verify network adapter is enabled

#### 3. Operation Timeouts

**Symptom**: Operations complete immediately or timeout

**Solutions**:
- Check target device is online
- Verify network connectivity
- Increase timeout values in configuration
- Check firewall rules

#### 4. WebSocket Disconnects

**Symptom**: Real-time updates stop working

**Solutions**:
- Check WebSocket connection in browser DevTools
- Verify backend WebSocket endpoint is accessible
- Check for proxy/firewall blocking WebSocket connections

---

## Testing and Validation

### Unit Tests

```bash
# Run active defense module tests
cd backend
pytest tests/test_attack.py -v
pytest tests/test_scapy_engine.py -v
```

### Integration Tests

```bash
# Test full operation lifecycle
pytest tests/test_integration_attack.py -v --run-integration
```

### Manual Testing Checklist

- [ ] Authentication and authorization
- [ ] Operation start/stop functionality
- [ ] WebSocket real-time updates
- [ ] Safety timeout mechanisms
- [ ] Emergency stop functionality
- [ ] Operation logging and audit trail
- [ ] Multiple concurrent operations
- [ ] Error handling and recovery

---

## References

### Technical Documentation

- [Scapy Documentation](https://scapy.readthedocs.io/)
- [IEEE 802.11 Specification](https://standards.ieee.org/standard/802_11-2020.html)
- [RFC 826 - ARP](https://tools.ietf.org/html/rfc826)
- [RFC 2131 - DHCP](https://tools.ietf.org/html/rfc2131)
- [RFC 1035 - DNS](https://tools.ietf.org/html/rfc1035)

### Security Research

- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [SANS Security Research](https://www.sans.org/security-resources/)

### Legal and Ethical Guidelines

- [EC-Council Code of Ethics](https://www.eccouncil.org/code-of-ethics/)
- [ISC2 Code of Ethics](https://www.isc2.org/Ethics)
- [Computer Fraud and Abuse Act](https://www.justice.gov/jm/criminal-resource-manual-1030-computer-fraud-and-abuse-act)

---

## Contributing

For security reasons, contributions to the Active Defense module require:

1. **Security Clearance**: Background check and approval
2. **Code Review**: Mandatory security review by senior engineers
3. **Documentation**: Complete technical documentation
4. **Testing**: Comprehensive unit and integration tests
5. **Legal Review**: Compliance verification

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for general contribution guidelines.

---

## License

This module is part of ZenetHunter and is licensed under MIT License with additional security restrictions. See [LICENSE](../../LICENSE) for details.

**Additional Restrictions**:
- Authorized use only
- No malicious use
- Compliance with local laws required
- Written authorization mandatory

---

## Contact

For questions, security concerns, or authorization requests, contact the project maintainers through official channels.

⚠️ **Do not use this module without proper authorization and understanding of legal implications.**
