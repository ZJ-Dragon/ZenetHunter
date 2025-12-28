# Platform Detection Module

This module provides platform detection and platform-specific feature availability checking.

## Features

- **Automatic Platform Detection**: Detects Linux, macOS, Windows, and other platforms
- **Windows Support**: Full support for Windows Server and Windows 10/11 with Windows Firewall integration
- **Feature Availability**: Checks for platform-specific tools and capabilities
- **Root/Admin Detection**: Detects if running with elevated privileges
- **Docker Detection**: Detects if running inside a Docker container

## Usage

```python
from app.core.platform.detect import get_platform_features, is_macos, is_linux, is_windows

# Get platform features
features = get_platform_features()
print(f"Platform: {features.platform.value}")
print(f"Is root: {features.is_root}")
print(f"Has Scapy: {features.has_scapy}")

# Quick checks
if is_macos():
    # macOS-specific code
    pass
elif is_linux():
    # Linux-specific code
    pass
```

## Platform-Specific Features

### macOS
- `pfctl`: Packet Filter firewall
- `networksetup`: Network configuration
- `arp`: ARP table access
- `ifconfig`: Interface configuration

### Linux
- `iptables`: Firewall rules
- `ip`: Modern network configuration
- `arp`: ARP table access
- `/proc/net/arp`: ARP table file

### Windows
- `netsh`: Network shell and Windows Firewall management
- `arp`: ARP table access (via `arp -a`)
- `ipconfig`: Network configuration
- Windows Firewall: Advanced firewall with rules management

## Integration

The platform detection is automatically used by:
- Defense engine factory (`defense_factory.py`)
- Scanner service (`scanner.py`)
- System info endpoint (`routes/logs.py`)
