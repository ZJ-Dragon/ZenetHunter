"""Windows-specific defense engine using netsh and Windows Firewall."""

import asyncio
import logging
import re
import subprocess
import sys
from typing import Any

from app.core.engine.base_defense import DefenseEngine
from app.core.platform.detect import get_platform_features
from app.models.defender import DefenseType

logger = logging.getLogger(__name__)


async def _get_ip_from_mac(mac: str) -> str | None:
    """
    Get IP address for a given MAC address from ARP table.
    
    Args:
        mac: MAC address in format XX:XX:XX:XX:XX:XX
        
    Returns:
        IP address if found, None otherwise
    """
    try:
        # Run arp -a to get ARP table
        result = await asyncio.create_subprocess_exec(
            "arp", "-a",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )
        
        stdout, _ = await asyncio.wait_for(result.communicate(), timeout=5.0)
        
        if result.returncode == 0:
            output = stdout.decode('utf-8', errors='ignore')
            mac_normalized = mac.replace(":", "-").upper()  # Windows uses dashes
            
            # Parse ARP output to find MAC and corresponding IP
            for line in output.splitlines():
                parts = line.split()
                if len(parts) >= 2:
                    ip_str = parts[0]
                    mac_str = parts[1].upper()
                    
                    if mac_str == mac_normalized:
                        # Validate IP format
                        if re.match(r'^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$', ip_str):
                            return ip_str
    except Exception as e:
        logger.debug(f"Failed to get IP from MAC {mac}: {e}")
    
    return None


class WindowsDefenseEngine(DefenseEngine):
    """
    Defense engine for Windows using netsh and Windows Firewall.
    
    Windows uses netsh advfirewall for firewall management, which is different from 
    Linux's iptables and macOS's pfctl. This engine provides Windows-specific 
    implementations of defense policies.
    """

    def __init__(self):
        super().__init__()
        self.platform_features = get_platform_features()
        self._rule_prefix = "ZenetHunter_"

    def check_capabilities(self) -> bool:
        """Check if Windows defense engine has required capabilities."""
        return self.platform_features.is_root and self.platform_features.has_netsh

    async def apply_policy(
        self, target: str, policy: DefenseType, params: dict[str, Any] | None = None
    ) -> None:
        """Apply a defense policy to a target device."""
        logger.info(f"[WindowsDefense] Applying {policy} to {target}")

        if policy == DefenseType.BLOCK_WAN:
            await self._enable_block_wan(target)
        elif policy == DefenseType.QUARANTINE:
            await self._enable_quarantine(target)
        else:
            logger.warning(f"[WindowsDefense] Policy {policy} not yet implemented for Windows")

    async def remove_policy(
        self, target: str, policy: DefenseType, params: dict[str, Any] | None = None
    ) -> None:
        """Remove a defense policy from a target device."""
        logger.info(f"[WindowsDefense] Removing {policy} from {target}")

        if policy == DefenseType.BLOCK_WAN:
            await self._disable_block_wan(target)
        elif policy == DefenseType.QUARANTINE:
            await self._disable_quarantine(target)
        else:
            logger.warning(f"[WindowsDefense] Policy {policy} removal not yet implemented for Windows")

    async def _enable_block_wan(self, mac: str) -> None:
        """Block WAN access for a device using Windows Firewall."""
        rule_name = f"{self._rule_prefix}BlockWAN_{mac.replace(':', '-')}"
        
        try:
            # Windows Firewall doesn't support MAC address filtering directly
            # We need to get the IP address from MAC address first
            ip_address = await _get_ip_from_mac(mac)
            
            if not ip_address:
                logger.warning(
                    f"[WindowsDefense] Could not find IP address for MAC {mac}. "
                    f"Cannot create Windows Firewall rule. "
                    f"Device may be offline or not in ARP table."
                )
                return
            
            # Block outbound traffic to WAN (everything except local subnet)
            # Get local subnet (simplified: assume /24)
            ip_parts = ip_address.split('.')
            if len(ip_parts) == 4:
                subnet = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.0/24"
            else:
                subnet = "192.168.0.0/16,10.0.0.0/8,172.16.0.0/12"  # Common private ranges
            
            # Create rule to block outbound traffic except local subnet
            cmd = [
                "netsh", "advfirewall", "firewall", "add", "rule",
                f"name={rule_name}",
                "dir=out",
                "action=block",
                f"remoteip={ip_address}",  # Block specific IP's outbound traffic
                "enable=yes"
            ]
            
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            
            stdout, stderr = await asyncio.wait_for(result.communicate(), timeout=10.0)
            
            if result.returncode == 0:
                logger.info(f"[WindowsDefense] Successfully blocked WAN for {mac} (IP: {ip_address})")
            else:
                error_msg = stderr.decode('utf-8', errors='ignore') if stderr else "Unknown error"
                logger.error(f"[WindowsDefense] Failed to block WAN for {mac}: {error_msg}")
                
        except asyncio.TimeoutError:
            logger.error(f"[WindowsDefense] Timeout while blocking WAN for {mac}")
        except Exception as e:
            logger.error(f"[WindowsDefense] Error blocking WAN for {mac}: {e}", exc_info=True)

    async def _disable_block_wan(self, mac: str) -> None:
        """Remove WAN block for a device."""
        rule_name = f"{self._rule_prefix}BlockWAN_{mac.replace(':', '-')}"
        
        try:
            cmd = [
                "netsh", "advfirewall", "firewall", "delete", "rule",
                f"name={rule_name}"
            ]
            
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            
            stdout, stderr = await asyncio.wait_for(result.communicate(), timeout=10.0)
            
            if result.returncode == 0:
                logger.info(f"[WindowsDefense] Successfully removed WAN block for {mac}")
            else:
                error_msg = stderr.decode('utf-8', errors='ignore') if stderr else "Unknown error"
                logger.debug(f"[WindowsDefense] Rule may not exist: {error_msg}")
                
        except asyncio.TimeoutError:
            logger.error(f"[WindowsDefense] Timeout while removing WAN block for {mac}")
        except Exception as e:
            logger.error(f"[WindowsDefense] Error removing WAN block for {mac}: {e}", exc_info=True)

    async def _enable_quarantine(self, mac: str) -> None:
        """Quarantine a device (block all traffic except to gateway)."""
        rule_name = f"{self._rule_prefix}Quarantine_{mac.replace(':', '-')}"
        
        try:
            # Get IP address from MAC
            ip_address = await _get_ip_from_mac(mac)
            
            if not ip_address:
                logger.warning(
                    f"[WindowsDefense] Could not find IP address for MAC {mac}. "
                    f"Cannot quarantine device."
                )
                return
            
            # Get gateway IP (simplified: use route command)
            try:
                result = await asyncio.create_subprocess_exec(
                    "route", "print", "0.0.0.0",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                )
                stdout, _ = await asyncio.wait_for(result.communicate(), timeout=5.0)
                output = stdout.decode('utf-8', errors='ignore')
                
                # Parse gateway from route output
                gateway_ip = None
                for line in output.splitlines():
                    if "0.0.0.0" in line and "On-link" not in line:
                        parts = line.split()
                        if len(parts) >= 3:
                            gateway_ip = parts[2]
                            break
            except Exception as e:
                logger.debug(f"Failed to get gateway IP: {e}")
                gateway_ip = None
            
            # Block all outbound traffic except to gateway and local subnet
            local_subnet = f"{ip_address.rsplit('.', 1)[0]}.0/24" if '.' in ip_address else "192.168.0.0/16"
            allowed_ips = local_subnet
            if gateway_ip:
                allowed_ips = f"{gateway_ip},{local_subnet}"
            
            # Block all outbound traffic (except allowed IPs)
            cmd_block = [
                "netsh", "advfirewall", "firewall", "add", "rule",
                f"name={rule_name}_Out",
                "dir=out",
                "action=block",
                f"remoteip={ip_address}",
                "enable=yes"
            ]
            
            # Block all inbound traffic
            cmd_block_in = [
                "netsh", "advfirewall", "firewall", "add", "rule",
                f"name={rule_name}_In",
                "dir=in",
                "action=block",
                f"remoteip={ip_address}",
                "enable=yes"
            ]
            
            for cmd in [cmd_block, cmd_block_in]:
                result = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                )
                
                stdout, stderr = await asyncio.wait_for(result.communicate(), timeout=10.0)
                
                if result.returncode != 0:
                    error_msg = stderr.decode('utf-8', errors='ignore') if stderr else "Unknown error"
                    logger.error(f"[WindowsDefense] Failed to quarantine {mac}: {error_msg}")
            
            logger.info(f"[WindowsDefense] Successfully quarantined {mac} (IP: {ip_address})")
                
        except asyncio.TimeoutError:
            logger.error(f"[WindowsDefense] Timeout while quarantining {mac}")
        except Exception as e:
            logger.error(f"[WindowsDefense] Error quarantining {mac}: {e}", exc_info=True)

    async def _disable_quarantine(self, mac: str) -> None:
        """Remove quarantine for a device."""
        rule_name = f"{self._rule_prefix}Quarantine_{mac.replace(':', '-')}"
        
        try:
            for direction in ["Out", "In"]:
                cmd = [
                    "netsh", "advfirewall", "firewall", "delete", "rule",
                    f"name={rule_name}_{direction}"
                ]
                
                result = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                )
                
                stdout, stderr = await asyncio.wait_for(result.communicate(), timeout=10.0)
                
                if result.returncode != 0:
                    error_msg = stderr.decode('utf-8', errors='ignore') if stderr else "Unknown error"
                    logger.debug(f"[WindowsDefense] Rule may not exist: {error_msg}")
            
            logger.info(f"[WindowsDefense] Successfully removed quarantine for {mac}")
                
        except asyncio.TimeoutError:
            logger.error(f"[WindowsDefense] Timeout while removing quarantine for {mac}")
        except Exception as e:
            logger.error(f"[WindowsDefense] Error removing quarantine for {mac}: {e}", exc_info=True)
