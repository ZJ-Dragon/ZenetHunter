"""Linux Netfilter/IPTables implementation of Defense Engine."""

import asyncio
import logging
import shutil
from typing import Any

from app.core.engine.base_defense import DefenseEngine
from app.models.defender import DefenseType

logger = logging.getLogger(__name__)


class LinuxDefenseEngine(DefenseEngine):
    """
    Defense engine using Linux iptables/nftables and kernel modules.
    Requires root privileges.
    """

    def check_capabilities(self) -> bool:
        """Check for root and iptables availability."""
        # 1. Check for iptables command
        if not shutil.which("iptables"):
            return False
            
        # 2. Check if we can list rules (implies root/sudo)
        # This is a bit aggressive for a check, but effective.
        # We'll assume the caller handles the permission check via `os.geteuid()`
        # in the factory or service layer, similar to AttackEngine.
        return True

    async def _run_cmd(self, args: list[str]) -> tuple[int, str, str]:
        """Run a shell command asynchronously."""
        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        return process.returncode or 0, stdout.decode(), stderr.decode()

    async def apply_policy(
        self, target: str, policy: DefenseType, params: dict[str, Any] | None = None
    ) -> None:
        """Apply specific policy."""
        # Implementation deferred for QUARANTINE/BLOCK_WAN
        logger.info(f"[LinuxDefense] Applying {policy} to {target} (Not implemented yet)")
        pass

    async def remove_policy(self, target: str, policy: DefenseType) -> None:
        """Remove specific policy."""
        logger.info(f"[LinuxDefense] Removing {policy} from {target} (Not implemented yet)")
        pass

    async def enable_global_protection(self, policy: DefenseType) -> None:
        """Enable global protection."""
        if policy == DefenseType.SYN_PROXY:
            await self._enable_synproxy()
        else:
            logger.warning(f"[LinuxDefense] Global policy {policy} not supported")

    async def disable_global_protection(self, policy: DefenseType) -> None:
        """Disable global protection."""
        if policy == DefenseType.SYN_PROXY:
            await self._disable_synproxy()

    async def _enable_synproxy(self) -> None:
        """
        Enable SYNPROXY on the PREROUTING chain.
        
        Commands equivalent to:
        iptables -t raw -I PREROUTING -p tcp -m tcp --syn -j CT --notrack
        iptables -A INPUT -p tcp -m tcp -m conntrack --ctstate INVALID,UNTRACKED -j SYNPROXY --sack-perm --timestamp --wscale 7 --mss 1460
        iptables -A INPUT -m conntrack --ctstate INVALID -j DROP
        """
        logger.info("[LinuxDefense] Enabling SYNPROXY...")
        
        # 1. Set backend/kernel parameters (optional but recommended)
        # echo 1 > /proc/sys/net/ipv4/tcp_syncookies
        
        cmds = [
            # Mark SYN packets as UNTRACKED to bypass default connection tracking
            ["iptables", "-t", "raw", "-I", "PREROUTING", "-p", "tcp", "-m", "tcp", "--syn", "-j", "CT", "--notrack"],
            
            # Redirect UNTRACKED SYN packets to SYNPROXY target
            # Using standard MSS 1460 (MTU 1500 - 40 bytes header)
            ["iptables", "-A", "INPUT", "-p", "tcp", "-m", "tcp", "-m", "conntrack", "--ctstate", "INVALID,UNTRACKED", "-j", "SYNPROXY", "--sack-perm", "--timestamp", "--wscale", "7", "--mss", "1460"],
            
            # Drop any other INVALID packets that leaked through
            ["iptables", "-A", "INPUT", "-m", "conntrack", "--ctstate", "INVALID", "-j", "DROP"],
        ]

        for cmd in cmds:
            code, _, stderr = await self._run_cmd(cmd)
            if code != 0:
                logger.error(f"[LinuxDefense] Failed to execute: {' '.join(cmd)}. Error: {stderr}")
                # In a real scenario, we should rollback partial changes here.
                raise RuntimeError(f"Failed to enable SYNPROXY: {stderr}")

    async def _disable_synproxy(self) -> None:
        """Disable SYNPROXY."""
        logger.info("[LinuxDefense] Disabling SYNPROXY...")
        
        # Simple cleanup: delete the rules we added.
        # Note: In production, we should use specific rule handles or comments to delete safely.
        # For MVP, we attempt to delete the exact signatures.
        
        cmds = [
             ["iptables", "-t", "raw", "-D", "PREROUTING", "-p", "tcp", "-m", "tcp", "--syn", "-j", "CT", "--notrack"],
             ["iptables", "-D", "INPUT", "-p", "tcp", "-m", "tcp", "-m", "conntrack", "--ctstate", "INVALID,UNTRACKED", "-j", "SYNPROXY", "--sack-perm", "--timestamp", "--wscale", "7", "--mss", "1460"],
             ["iptables", "-D", "INPUT", "-m", "conntrack", "--ctstate", "INVALID", "-j", "DROP"],
        ]
        
        for cmd in cmds:
            # Suppress errors on deletion (rule might not exist)
            await self._run_cmd(cmd)

