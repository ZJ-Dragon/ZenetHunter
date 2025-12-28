"""macOS-specific defense engine using pfctl (Packet Filter)."""

import asyncio
import logging
from typing import Any

from app.core.engine.base_defense import DefenseEngine
from app.core.engine.features_macos import MacOSNetworkFeatures
from app.core.platform.detect import get_platform_features
from app.models.defender import DefenseType

logger = logging.getLogger(__name__)


class MacOSDefenseEngine(DefenseEngine):
    """
    Defense engine for macOS using pfctl (Packet Filter).

    macOS uses pfctl for firewall management, which is different from Linux's iptables.
    This engine provides macOS-specific implementations of defense policies.
    """

    def __init__(self):
        super().__init__()
        self.platform_features = get_platform_features()
        self.macos_features = MacOSNetworkFeatures()
        self._pf_rules_file = "/tmp/zenethunter_pf_rules.conf"

    def check_capabilities(self) -> bool:
        """Check if macOS defense engine has required capabilities."""
        return self.platform_features.is_root and self.platform_features.has_pfctl

    async def apply_policy(
        self, target: str, policy: DefenseType, params: dict[str, Any] | None = None
    ) -> None:
        """Apply a defense policy to a target device."""
        logger.info(f"[MacOSDefense] Applying {policy} to {target}")

        if policy == DefenseType.BLOCK_WAN:
            await self._enable_block_wan(target)
        elif policy == DefenseType.QUARANTINE:
            await self._enable_quarantine(target)
        else:
            logger.warning(
                f"[MacOSDefense] Policy {policy} not yet implemented for macOS"
            )

    async def remove_policy(
        self, target: str, policy: DefenseType, params: dict[str, Any] | None = None
    ) -> None:
        """Remove a defense policy from a target device."""
        logger.info(f"[MacOSDefense] Removing {policy} from {target}")

        if policy == DefenseType.BLOCK_WAN:
            await self._disable_block_wan(target)
        elif policy == DefenseType.QUARANTINE:
            await self._disable_quarantine(target)
        else:
            logger.warning(
                f"[MacOSDefense] Policy {policy} removal not yet implemented for macOS"
            )

    async def _enable_block_wan(self, mac: str) -> None:
        """Block WAN access for a device using pfctl."""
        if not self.platform_features.has_pfctl:
            logger.error("[MacOSDefense] pfctl not available. Cannot block WAN.")
            return

        try:
            # Create pfctl rule to block outbound traffic from MAC
            rule = f"block out quick on any from any to any mac {mac}\n"

            # Append to rules file
            with open(self._pf_rules_file, "a") as f:
                f.write(rule)

            # Reload pfctl rules
            await self._reload_pfctl()
            logger.info(f"[MacOSDefense] Blocked WAN access for {mac}")
        except Exception as e:
            logger.error(f"[MacOSDefense] Failed to block WAN for {mac}: {e}")

    async def _disable_block_wan(self, mac: str) -> None:
        """Remove WAN block for a device."""
        try:
            # Read current rules
            try:
                with open(self._pf_rules_file) as f:
                    lines = f.readlines()
            except FileNotFoundError:
                return

            # Remove rules for this MAC
            new_lines = [line for line in lines if mac not in line]

            # Write back
            with open(self._pf_rules_file, "w") as f:
                f.writelines(new_lines)

            # Reload pfctl rules
            await self._reload_pfctl()
            logger.info(f"[MacOSDefense] Removed WAN block for {mac}")
        except Exception as e:
            logger.error(f"[MacOSDefense] Failed to remove WAN block for {mac}: {e}")

    async def _enable_quarantine(self, mac: str) -> None:
        """Quarantine a device (block all network access)."""
        if not self.platform_features.has_pfctl:
            logger.error(
                "[MacOSDefense] pfctl not available. Cannot quarantine device."
            )
            return

        try:
            # Block all traffic from/to this MAC
            rule = f"block quick from any to any mac {mac}\n"
            rule += f"block quick from any mac {mac} to any\n"

            # Append to rules file
            with open(self._pf_rules_file, "a") as f:
                f.write(rule)

            # Reload pfctl rules
            await self._reload_pfctl()
            logger.info(f"[MacOSDefense] Quarantined {mac}")
        except Exception as e:
            logger.error(f"[MacOSDefense] Failed to quarantine {mac}: {e}")

    async def _disable_quarantine(self, mac: str) -> None:
        """Remove quarantine for a device."""
        await self._disable_block_wan(mac)  # Same logic

    async def _reload_pfctl(self) -> None:
        """Reload pfctl rules."""
        try:
            # Enable pfctl if not enabled
            result = await asyncio.create_subprocess_exec(
                "pfctl",
                "-f",
                self._pf_rules_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await result.communicate()

            if result.returncode != 0:
                logger.warning(
                    "[MacOSDefense] pfctl reload failed. May need root privileges."
                )
        except Exception as e:
            logger.error(f"[MacOSDefense] Failed to reload pfctl: {e}")

    async def enable_global_protection(self, policy: DefenseType) -> None:
        """Enable a global protection mechanism."""
        logger.warning(
            f"[MacOSDefense] Global protection {policy} not yet implemented for macOS"
        )

    async def disable_global_protection(self, policy: DefenseType) -> None:
        """Disable a global protection mechanism."""
        logger.warning(
            "[MacOSDefense] Global protection removal not yet implemented for macOS"
        )
