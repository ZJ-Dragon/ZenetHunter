"""Platform detection and feature availability checking."""

import logging
import os
import platform
import shutil
import sys
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class Platform(str, Enum):
    """Supported platforms."""
    LINUX = "linux"
    MACOS = "darwin"
    WINDOWS = "windows"
    UNKNOWN = "unknown"


class PlatformFeatures:
    """Platform-specific feature availability."""

    def __init__(self):
        self.platform = self._detect_platform()
        self.is_root = self._check_root()
        self.has_scapy = self._check_scapy()
        self.has_network_tools = self._check_network_tools()
        self.has_pfctl = self._check_pfctl()  # macOS firewall
        self.has_ipfw = self._check_ipfw()  # macOS legacy firewall
        self.has_networksetup = self._check_networksetup()  # macOS network config
        self.has_arp = self._check_arp()
        self.has_ip = self._check_ip()  # Linux
        self.has_iptables = self._check_iptables()  # Linux
        self.has_netsh = self._check_netsh()  # Windows
        self.has_windows_firewall = self._check_windows_firewall()  # Windows
        self.is_docker = self._check_docker()

    def _detect_platform(self) -> Platform:
        """Detect the current platform."""
        system = platform.system().lower()
        if system == "darwin":
            return Platform.MACOS
        elif system == "linux":
            return Platform.LINUX
        elif system == "windows":
            return Platform.WINDOWS
        else:
            return Platform.UNKNOWN

    def _check_root(self) -> bool:
        """Check if running as root/admin."""
        try:
            return os.geteuid() == 0
        except AttributeError:
            # Windows - check for admin
            try:
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            except Exception:
                return False

    def _check_scapy(self) -> bool:
        """Check if Scapy is available."""
        try:
            import scapy.all  # noqa: F401
            return True
        except ImportError:
            return False

    def _check_network_tools(self) -> bool:
        """Check if basic network tools are available."""
        tools = []
        if self.platform == Platform.MACOS:
            tools = ["arp", "netstat", "ifconfig"]
        elif self.platform == Platform.LINUX:
            tools = ["ip", "arp", "ifconfig", "netstat"]
        elif self.platform == Platform.WINDOWS:
            tools = ["arp", "netsh", "ipconfig"]
        else:
            return False

        for tool in tools:
            if shutil.which(tool):
                return True
        return False

    def _check_pfctl(self) -> bool:
        """Check if pfctl (macOS firewall) is available."""
        return self.platform == Platform.MACOS and shutil.which("pfctl") is not None

    def _check_ipfw(self) -> bool:
        """Check if ipfw (macOS legacy firewall) is available."""
        return self.platform == Platform.MACOS and shutil.which("ipfw") is not None

    def _check_networksetup(self) -> bool:
        """Check if networksetup (macOS network config) is available."""
        return self.platform == Platform.MACOS and shutil.which("networksetup") is not None

    def _check_arp(self) -> bool:
        """Check if arp command is available."""
        return shutil.which("arp") is not None

    def _check_ip(self) -> bool:
        """Check if ip command (Linux) is available."""
        return self.platform == Platform.LINUX and shutil.which("ip") is not None

    def _check_iptables(self) -> bool:
        """Check if iptables (Linux) is available."""
        return self.platform == Platform.LINUX and shutil.which("iptables") is not None

    def _check_netsh(self) -> bool:
        """Check if netsh (Windows) is available."""
        return self.platform == Platform.WINDOWS and shutil.which("netsh") is not None

    def _check_windows_firewall(self) -> bool:
        """Check if Windows Firewall is available."""
        if self.platform != Platform.WINDOWS:
            return False
        # Check if netsh advfirewall is available (Windows Firewall with Advanced Security)
        try:
            import subprocess
            result = subprocess.run(
                ["netsh", "advfirewall", "show", "allprofiles"],
                capture_output=True,
                timeout=2,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            return result.returncode == 0
        except Exception:
            return False

    def _check_docker(self) -> bool:
        """Check if running in Docker container."""
        # Docker detection works on Linux and macOS
        if self.platform in (Platform.LINUX, Platform.MACOS):
            try:
                with open("/proc/self/cgroup", "r") as f:
                    content = f.read()
                    return "docker" in content or "containerd" in content
            except (FileNotFoundError, PermissionError):
                pass
        # Windows: Check for Docker environment variables or container indicators
        elif self.platform == Platform.WINDOWS:
            import os
            # Check common Docker environment variables
            if os.getenv("DOCKER_CONTAINER") or os.getenv("container"):
                return True
            # Check if running in WSL (Windows Subsystem for Linux)
            try:
                with open("/proc/version", "r") as f:
                    if "microsoft" in f.read().lower():
                        return False  # WSL is not Docker
            except (FileNotFoundError, PermissionError):
                pass
        return False

    def get_summary(self) -> dict:
        """Get a summary of platform features."""
        return {
            "platform": self.platform.value,
            "platform_name": platform.system(),
            "platform_version": platform.version(),
            "is_root": self.is_root,
            "is_docker": self.is_docker,
            "capabilities": {
                "scapy": self.has_scapy,
                "network_tools": self.has_network_tools,
                "arp": self.has_arp,
                "ip": self.has_ip,
                "iptables": self.has_iptables,
                "netsh": self.has_netsh,
                "windows_firewall": self.has_windows_firewall,
                "pfctl": self.has_pfctl,
                "ipfw": self.has_ipfw,
                "networksetup": self.has_networksetup,
            },
        }


# Global platform features instance
_platform_features: Optional[PlatformFeatures] = None


def get_platform_features() -> PlatformFeatures:
    """Get or create platform features instance."""
    global _platform_features
    if _platform_features is None:
        _platform_features = PlatformFeatures()
    return _platform_features


def is_macos() -> bool:
    """Check if running on macOS."""
    return get_platform_features().platform == Platform.MACOS


def is_linux() -> bool:
    """Check if running on Linux."""
    return get_platform_features().platform == Platform.LINUX


def is_windows() -> bool:
    """Check if running on Windows."""
    return get_platform_features().platform == Platform.WINDOWS
