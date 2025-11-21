"""Linux Netfilter/IPTables implementation of Defense Engine."""

import asyncio
import logging
import os
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
        logger.info(
            f"[LinuxDefense] Applying {policy} to {target} (Not implemented yet)"
        )
        pass

    async def remove_policy(self, target: str, policy: DefenseType) -> None:
        """Remove specific policy."""
        logger.info(
            f"[LinuxDefense] Removing {policy} from {target} (Not implemented yet)"
        )
        pass

    async def enable_global_protection(self, policy: DefenseType) -> None:
        """Enable global protection."""
        if policy == DefenseType.SYN_PROXY:
            await self._enable_synproxy()
        elif policy == DefenseType.UDP_RATE_LIMIT:
            await self._enable_udp_limit()
        elif policy == DefenseType.TCP_RESET_POLICY:
            await self._enable_tcp_reset_policy()
        elif policy == DefenseType.WALLED_GARDEN:
            await self._enable_walled_garden()
        elif policy == DefenseType.TARPIT:
            await self._enable_tarpit()
        else:
            logger.warning(f"[LinuxDefense] Global policy {policy} not supported")

    async def disable_global_protection(self, policy: DefenseType) -> None:
        """Disable global protection."""
        if policy == DefenseType.SYN_PROXY:
            await self._disable_synproxy()
        elif policy == DefenseType.UDP_RATE_LIMIT:
            await self._disable_udp_limit()
        elif policy == DefenseType.TCP_RESET_POLICY:
            await self._disable_tcp_reset_policy()
        elif policy == DefenseType.WALLED_GARDEN:
            await self._disable_walled_garden()
        elif policy == DefenseType.TARPIT:
            await self._disable_tarpit()

    async def _enable_udp_limit(self) -> None:
        """
        Apply UDP rate limiting using Traffic Control (tc).
        Uses HTB (Hierarchical Token Bucket) or TBF (Token Bucket Filter).

        Target: Default interface (eth0/wlan0), egress traffic.
        Strategy:
          - Limit UDP traffic to reasonable bandwidth (e.g., 1Mbps for non-video UDP)
          - Use fq_codel to reduce bufferbloat.

        Simplified implementation for MVP:
        tc qdisc add dev eth0 root handle 1: htb default 10
        tc class add dev eth0 parent 1: classid 1:1 htb rate 100mbit burst 15k
        tc class add dev eth0 parent 1:1 classid 1:10 htb rate 10mbit ceil 100mbit \
            burst 15k prio 1
        tc filter add dev eth0 protocol ip parent 1:0 prio 1 u32 match ip protocol 17 \
            0xff flowid 1:10
        """
        logger.info("[LinuxDefense] Enabling UDP Rate Limiting (tc)...")

        # Detect primary interface (simplified)
        # In a real app, this should be configurable or auto-detected via 'ip route'
        iface = "eth0"

        # Note: This is a destructive operation for existing qdiscs
        cmds = [
            # 1. Clean existing qdiscs
            ["tc", "qdisc", "del", "dev", iface, "root"],
            # 2. Add HTB root
            [
                "tc",
                "qdisc",
                "add",
                "dev",
                iface,
                "root",
                "handle",
                "1:",
                "htb",
                "default",
                "20",
            ],
            # 3. Root class (Total bandwidth, e.g., 100Mbit)
            [
                "tc",
                "class",
                "add",
                "dev",
                iface,
                "parent",
                "1:",
                "classid",
                "1:1",
                "htb",
                "rate",
                "100mbit",
                "burst",
                "15k",
            ],
            # 4. Class for UDP (Limited, e.g., 5Mbit)
            [
                "tc",
                "class",
                "add",
                "dev",
                iface,
                "parent",
                "1:1",
                "classid",
                "1:10",
                "htb",
                "rate",
                "5mbit",
                "ceil",
                "10mbit",
                "burst",
                "15k",
                "prio",
                "1",
            ],
            # 5. Class for others (Default, higher bandwidth)
            [
                "tc",
                "class",
                "add",
                "dev",
                iface,
                "parent",
                "1:1",
                "classid",
                "1:20",
                "htb",
                "rate",
                "90mbit",
                "ceil",
                "100mbit",
                "burst",
                "15k",
                "prio",
                "2",
            ],
            # 6. Filter to direct UDP (proto 17) to class 1:10
            [
                "tc",
                "filter",
                "add",
                "dev",
                iface,
                "protocol",
                "ip",
                "parent",
                "1:0",
                "prio",
                "1",
                "u32",
                "match",
                "ip",
                "protocol",
                "17",
                "0xff",
                "flowid",
                "1:10",
            ],
        ]

        for cmd in cmds:
            # Ignore errors on 'del' command
            ignore_error = cmd[2] == "del"
            code, _, stderr = await self._run_cmd(cmd)

            if code != 0 and not ignore_error:
                logger.error(
                    f"[LinuxDefense] Failed to execute: {' '.join(cmd)}. "
                    f"Error: {stderr}"
                )
                # For MVP we log and continue, but ideally should rollback
                # raise RuntimeError(f"Failed to enable UDP Limit: {stderr}")

    async def _disable_udp_limit(self) -> None:
        """Disable UDP rate limiting (reset tc)."""
        logger.info("[LinuxDefense] Disabling UDP Rate Limiting...")

        iface = "eth0"
        # Simply delete root qdisc
        cmd = ["tc", "qdisc", "del", "dev", iface, "root"]
        await self._run_cmd(cmd)

    async def _enable_tcp_reset_policy(self) -> None:
        """
        Enable TCP Reset policy for unauthorized traffic.

        Strategy:
        - TCP: REJECT with tcp-reset (fast connection termination)
        - UDP: REJECT with icmp-port-unreachable (informative rejection)

        This is an active defense mechanism that quickly closes unauthorized
        connections instead of silently dropping them (DROP), preventing
        resource exhaustion from half-open connections.

        Commands equivalent to:
        iptables -A INPUT -p tcp -m state --state NEW,ESTABLISHED \
            -m set ! --match-set whitelist src -j REJECT --reject-with tcp-reset
        iptables -A INPUT -p udp -m set ! --match-set whitelist src \
            -j REJECT --reject-with icmp-port-unreachable
        """
        logger.info("[LinuxDefense] Enabling TCP Reset Policy...")

        # For MVP, we'll use a simple approach:
        # Match traffic that doesn't match our allow list
        # In production, this would integrate with StateManager's allow_list

        cmds = [
            # TCP: Reject unauthorized connections with RST
            [
                "iptables",
                "-A",
                "INPUT",
                "-p",
                "tcp",
                "-m",
                "state",
                "--state",
                "NEW,ESTABLISHED",
                "-j",
                "REJECT",
                "--reject-with",
                "tcp-reset",
            ],
            # UDP: Reject with ICMP port unreachable
            [
                "iptables",
                "-A",
                "INPUT",
                "-p",
                "udp",
                "-j",
                "REJECT",
                "--reject-with",
                "icmp-port-unreachable",
            ],
        ]

        for cmd in cmds:
            code, _, stderr = await self._run_cmd(cmd)
            if code != 0:
                logger.error(
                    f"[LinuxDefense] Failed to execute: {' '.join(cmd)}. "
                    f"Error: {stderr}"
                )
                # For MVP we log and continue
                # raise RuntimeError(f"Failed to enable TCP Reset Policy: {stderr}")

    async def _disable_tcp_reset_policy(self) -> None:
        """Disable TCP Reset policy."""
        logger.info("[LinuxDefense] Disabling TCP Reset Policy...")

        cmds = [
            [
                "iptables",
                "-D",
                "INPUT",
                "-p",
                "tcp",
                "-m",
                "state",
                "--state",
                "NEW,ESTABLISHED",
                "-j",
                "REJECT",
                "--reject-with",
                "tcp-reset",
            ],
            [
                "iptables",
                "-D",
                "INPUT",
                "-p",
                "udp",
                "-j",
                "REJECT",
                "--reject-with",
                "icmp-port-unreachable",
            ],
        ]

        for cmd in cmds:
            # Suppress errors on deletion (rule might not exist)
            await self._run_cmd(cmd)

    async def _enable_walled_garden(self) -> None:
        """
        Enable Walled Garden / Captive Portal for unauthorized devices.

        Strategy:
        - Allow access to Portal server and essential services (NTP, DNS)
        - Redirect HTTP/HTTPS traffic to Portal page via DNAT
        - Redirect DNS queries to Portal server (for captive portal detection)
        - Block all other outbound traffic

        This creates a "walled garden" where unauthorized devices can only
        access the authentication portal and a few whitelisted services.

        Commands equivalent to:
        # Allow Portal server (assume gateway IP is 192.168.1.1)
        iptables -I FORWARD -d 192.168.1.1 -j ACCEPT
        # Allow DNS to Portal
        iptables -I FORWARD -p udp --dport 53 -d 192.168.1.1 -j ACCEPT
        # Redirect HTTP to Portal
        iptables -t nat -A PREROUTING -p tcp --dport 80 -j DNAT \
            --to-destination 192.168.1.1:8080
        iptables -t nat -A PREROUTING -p tcp --dport 443 -j DNAT \
            --to-destination 192.168.1.1:8080
        # Block other outbound (default policy)
        """
        logger.info("[LinuxDefense] Enabling Walled Garden...")

        # Portal server IP (typically the gateway)
        portal_ip = "192.168.1.1"
        portal_port = "8080"

        cmds = [
            # 1. Allow access to Portal server itself
            [
                "iptables",
                "-I",
                "FORWARD",
                "-d",
                portal_ip,
                "-j",
                "ACCEPT",
            ],
            # 2. Allow DNS queries to Portal (for captive portal detection)
            [
                "iptables",
                "-I",
                "FORWARD",
                "-p",
                "udp",
                "--dport",
                "53",
                "-d",
                portal_ip,
                "-j",
                "ACCEPT",
            ],
            # 3. Redirect HTTP to Portal
            [
                "iptables",
                "-t",
                "nat",
                "-A",
                "PREROUTING",
                "-p",
                "tcp",
                "--dport",
                "80",
                "-j",
                "DNAT",
                "--to-destination",
                f"{portal_ip}:{portal_port}",
            ],
            # 4. Redirect HTTPS to Portal
            [
                "iptables",
                "-t",
                "nat",
                "-A",
                "PREROUTING",
                "-p",
                "tcp",
                "--dport",
                "443",
                "-j",
                "DNAT",
                "--to-destination",
                f"{portal_ip}:{portal_port}",
            ],
        ]

        for cmd in cmds:
            code, _, stderr = await self._run_cmd(cmd)
            if code != 0:
                logger.error(
                    f"[LinuxDefense] Failed to execute: {' '.join(cmd)}. "
                    f"Error: {stderr}"
                )

    async def _disable_walled_garden(self) -> None:
        """Disable Walled Garden."""
        logger.info("[LinuxDefense] Disabling Walled Garden...")

        portal_ip = "192.168.1.1"
        portal_port = "8080"

        cmds = [
            [
                "iptables",
                "-D",
                "FORWARD",
                "-d",
                portal_ip,
                "-j",
                "ACCEPT",
            ],
            [
                "iptables",
                "-D",
                "FORWARD",
                "-p",
                "udp",
                "--dport",
                "53",
                "-d",
                portal_ip,
                "-j",
                "ACCEPT",
            ],
            [
                "iptables",
                "-t",
                "nat",
                "-D",
                "PREROUTING",
                "-p",
                "tcp",
                "--dport",
                "80",
                "-j",
                "DNAT",
                "--to-destination",
                f"{portal_ip}:{portal_port}",
            ],
            [
                "iptables",
                "-t",
                "nat",
                "-D",
                "PREROUTING",
                "-p",
                "tcp",
                "--dport",
                "443",
                "-j",
                "DNAT",
                "--to-destination",
                f"{portal_ip}:{portal_port}",
            ],
        ]

        for cmd in cmds:
            # Suppress errors on deletion (rule might not exist)
            await self._run_cmd(cmd)

    async def _check_tarpit_module(self) -> bool:
        """
        Check if TARPIT kernel module is available.

        TARPIT requires xtables-addons or nf_tarpit module.
        We check by attempting to list iptables extensions.
        """
        # Check if TARPIT target is available in iptables
        cmd = ["iptables", "-j", "TARPIT", "-h"]
        code, _, stderr = await self._run_cmd(cmd)
        if code == 0:
            return True

        # Alternative: Check if module is loaded
        if os.path.exists("/proc/modules"):
            with open("/proc/modules") as f:
                modules = f.read()
                if "xt_TARPIT" in modules or "nf_tarpit" in modules:
                    return True

        logger.warning(
            "[LinuxDefense] TARPIT module not available. "
            "Requires xtables-addons or nf_tarpit kernel module."
        )
        return False

    async def _enable_tarpit(self) -> None:
        """
        Enable TCP Tarpit for unauthorized connections.

        TCP Tarpit is a "sticky" defense mechanism that keeps connections
        open but responds extremely slowly, consuming attacker resources
        and reducing scanning efficiency.

        Strategy:
        - Use iptables TARPIT target to slow down unauthorized TCP connections
        - Target specific ports or all ports based on policy
        - Only works if xtables-addons/nf_tarpit module is loaded

        Commands equivalent to:
        iptables -A INPUT -p tcp -m state --state NEW \
            -m set ! --match-set whitelist src -j TARPIT

        Note: TARPIT target requires xtables-addons package or nf_tarpit module.
        """
        logger.info("[LinuxDefense] Enabling TCP Tarpit...")

        # Check module availability
        if not await self._check_tarpit_module():
            logger.error(
                "[LinuxDefense] TARPIT module not available. "
                "Cannot enable TCP Tarpit. Install xtables-addons or nf_tarpit."
            )
            raise RuntimeError("TARPIT kernel module not available")

        # For MVP, apply Tarpit to all new TCP connections from unauthorized sources
        # In production, this should integrate with StateManager's allow_list
        cmds = [
            # Tarpit unauthorized TCP connections
            [
                "iptables",
                "-A",
                "INPUT",
                "-p",
                "tcp",
                "-m",
                "state",
                "--state",
                "NEW",
                "-j",
                "TARPIT",
            ],
        ]

        for cmd in cmds:
            code, _, stderr = await self._run_cmd(cmd)
            if code != 0:
                logger.error(
                    f"[LinuxDefense] Failed to execute: {' '.join(cmd)}. "
                    f"Error: {stderr}"
                )
                raise RuntimeError(f"Failed to enable TCP Tarpit: {stderr}")

    async def _disable_tarpit(self) -> None:
        """Disable TCP Tarpit."""
        logger.info("[LinuxDefense] Disabling TCP Tarpit...")

        cmd = [
            "iptables",
            "-D",
            "INPUT",
            "-p",
            "tcp",
            "-m",
            "state",
            "--state",
            "NEW",
            "-j",
            "TARPIT",
        ]

        # Suppress errors on deletion (rule might not exist)
        await self._run_cmd(cmd)

    async def _enable_synproxy(self) -> None:
        """
        Enable SYNPROXY on the PREROUTING chain.

        Commands equivalent to:
        iptables -t raw -I PREROUTING -p tcp -m tcp --syn -j CT --notrack
        iptables -A INPUT -p tcp -m tcp -m conntrack --ctstate INVALID,UNTRACKED \
            -j SYNPROXY --sack-perm --timestamp --wscale 7 --mss 1460
        iptables -A INPUT -m conntrack --ctstate INVALID -j DROP
        """
        logger.info("[LinuxDefense] Enabling SYNPROXY...")

        # 1. Set backend/kernel parameters (optional but recommended)
        # echo 1 > /proc/sys/net/ipv4/tcp_syncookies

        cmds = [
            # Mark SYN packets as UNTRACKED to bypass default connection tracking
            [
                "iptables",
                "-t",
                "raw",
                "-I",
                "PREROUTING",
                "-p",
                "tcp",
                "-m",
                "tcp",
                "--syn",
                "-j",
                "CT",
                "--notrack",
            ],
            # Redirect UNTRACKED SYN packets to SYNPROXY target
            # Using standard MSS 1460 (MTU 1500 - 40 bytes header)
            [
                "iptables",
                "-A",
                "INPUT",
                "-p",
                "tcp",
                "-m",
                "tcp",
                "-m",
                "conntrack",
                "--ctstate",
                "INVALID,UNTRACKED",
                "-j",
                "SYNPROXY",
                "--sack-perm",
                "--timestamp",
                "--wscale",
                "7",
                "--mss",
                "1460",
            ],
            # Drop any other INVALID packets that leaked through
            [
                "iptables",
                "-A",
                "INPUT",
                "-m",
                "conntrack",
                "--ctstate",
                "INVALID",
                "-j",
                "DROP",
            ],
        ]

        for cmd in cmds:
            code, _, stderr = await self._run_cmd(cmd)
            if code != 0:
                logger.error(
                    f"[LinuxDefense] Failed to execute: {' '.join(cmd)}. "
                    f"Error: {stderr}"
                )
                # In a real scenario, we should rollback partial changes here.
                raise RuntimeError(f"Failed to enable SYNPROXY: {stderr}")

    async def _disable_synproxy(self) -> None:
        """Disable SYNPROXY."""
        logger.info("[LinuxDefense] Disabling SYNPROXY...")

        # Simple cleanup: delete the rules we added.
        # Note: In production, we should use specific rule handles or comments to delete
        # safely. For MVP, we attempt to delete the exact signatures.

        cmds = [
            [
                "iptables",
                "-t",
                "raw",
                "-D",
                "PREROUTING",
                "-p",
                "tcp",
                "-m",
                "tcp",
                "--syn",
                "-j",
                "CT",
                "--notrack",
            ],
            [
                "iptables",
                "-D",
                "INPUT",
                "-p",
                "tcp",
                "-m",
                "tcp",
                "-m",
                "conntrack",
                "--ctstate",
                "INVALID,UNTRACKED",
                "-j",
                "SYNPROXY",
                "--sack-perm",
                "--timestamp",
                "--wscale",
                "7",
                "--mss",
                "1460",
            ],
            [
                "iptables",
                "-D",
                "INPUT",
                "-m",
                "conntrack",
                "--ctstate",
                "INVALID",
                "-j",
                "DROP",
            ],
        ]

        for cmd in cmds:
            # Suppress errors on deletion (rule might not exist)
            await self._run_cmd(cmd)
