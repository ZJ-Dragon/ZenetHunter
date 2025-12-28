"""macOS-specific network features and utilities."""

import asyncio
import logging
import re

logger = logging.getLogger(__name__)


class MacOSNetworkFeatures:
    """macOS-specific network operations."""

    @staticmethod
    async def get_default_interface() -> str | None:
        """Get the default network interface on macOS."""
        try:
            result = await asyncio.create_subprocess_exec(
                "route",
                "get",
                "default",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await result.communicate()

            if result.returncode == 0:
                output = stdout.decode()
                # Look for "interface: en0" or similar
                match = re.search(r"interface:\s+(\w+)", output)
                if match:
                    return match.group(1)
        except Exception as e:
            logger.debug(f"Failed to get default interface: {e}")
        return None

    @staticmethod
    async def get_interface_ip(interface: str) -> str | None:
        """Get IP address of a network interface."""
        try:
            result = await asyncio.create_subprocess_exec(
                "ifconfig",
                interface,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await result.communicate()

            if result.returncode == 0:
                output = stdout.decode()
                # Look for "inet 192.168.1.100" or similar
                match = re.search(r"inet\s+(\d+\.\d+\.\d+\.\d+)", output)
                if match:
                    return match.group(1)
        except Exception as e:
            logger.debug(f"Failed to get interface IP: {e}")
        return None

    @staticmethod
    async def get_gateway_ip() -> str | None:
        """Get the default gateway IP address."""
        try:
            result = await asyncio.create_subprocess_exec(
                "route",
                "get",
                "default",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await result.communicate()

            if result.returncode == 0:
                output = stdout.decode()
                # Look for "gateway: 192.168.1.1" or similar
                match = re.search(r"gateway:\s+(\d+\.\d+\.\d+\.\d+)", output)
                if match:
                    return match.group(1)
        except Exception as e:
            logger.debug(f"Failed to get gateway IP: {e}")
        return None

    @staticmethod
    async def get_subnet_mask(interface: str) -> str | None:
        """Get subnet mask for an interface."""
        try:
            result = await asyncio.create_subprocess_exec(
                "ifconfig",
                interface,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await result.communicate()

            if result.returncode == 0:
                output = stdout.decode()
                # Look for "netmask 0xffffff00" or "netmask 255.255.255.0"
                match = re.search(
                    r"netmask\s+(0x[0-9a-fA-F]+|\d+\.\d+\.\d+\.\d+)", output
                )
                if match:
                    mask = match.group(1)
                    # Convert hex to dotted decimal if needed
                    if mask.startswith("0x"):
                        mask_int = int(mask, 16)
                        return (
                            f"{(mask_int >> 24) & 0xFF}."
                            f"{(mask_int >> 16) & 0xFF}."
                            f"{(mask_int >> 8) & 0xFF}.{mask_int & 0xFF}"
                        )
                    return mask
        except Exception as e:
            logger.debug(f"Failed to get subnet mask: {e}")
        return None

    @staticmethod
    async def calculate_subnet(ip: str, mask: str | None = None) -> str | None:
        """Calculate subnet CIDR from IP and mask."""
        if not mask:
            # Default to /24 for common home networks
            return ".".join(ip.split(".")[:3]) + ".0/24"

        # Convert mask to CIDR notation
        try:
            mask_parts = [int(x) for x in mask.split(".")]
            cidr = sum(bin(x).count("1") for x in mask_parts)
            ip_parts = ip.split(".")
            network_parts = [str(int(ip_parts[i]) & mask_parts[i]) for i in range(4)]
            return ".".join(network_parts) + f"/{cidr}"
        except Exception as e:
            logger.debug(f"Failed to calculate subnet: {e}")
            return ".".join(ip.split(".")[:3]) + ".0/24"

    @staticmethod
    async def get_all_interfaces() -> list[str]:
        """Get all network interfaces."""
        interfaces = []
        try:
            result = await asyncio.create_subprocess_exec(
                "ifconfig",
                "-l",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await result.communicate()

            if result.returncode == 0:
                output = stdout.decode().strip()
                interfaces = output.split()
        except Exception as e:
            logger.debug(f"Failed to get interfaces: {e}")
        return interfaces

    @staticmethod
    async def check_interface_up(interface: str) -> bool:
        """Check if an interface is up."""
        try:
            result = await asyncio.create_subprocess_exec(
                "ifconfig",
                interface,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await result.communicate()

            if result.returncode == 0:
                output = stdout.decode()
                # Check for "status: active" or "UP" flag
                return "status: active" in output or "flags=" in output
        except Exception as e:
            logger.debug(f"Failed to check interface status: {e}")
        return False
