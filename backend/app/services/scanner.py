import asyncio
import logging
import re
import sys
from datetime import UTC, datetime
from uuid import uuid4

from app.models.scan import ScanRequest, ScanResult, ScanStatus
from app.models.device import Device, DeviceType, DeviceStatus
from app.services.websocket import get_connection_manager
from app.services.state import get_state_manager
from app.services.device_model_lookup import get_device_model_lookup
from app.repositories.device import DeviceRepository
from app.core.database import get_session_factory

logger = logging.getLogger(__name__)


class ScannerService:
    """
    Service to handle network scanning operations.
    Implements real ARP table scanning for device discovery.
    """

    def __init__(self):
        self.ws_manager = get_connection_manager()
        self.state_manager = get_state_manager()
        self.active_tasks: dict[str, asyncio.Task] = {}  # Track active scan tasks
        self.model_lookup = get_device_model_lookup()  # Device model lookup service
        try:
            from app.core.engine.factory import get_attack_engine
            self.scapy_engine = get_attack_engine()  # Use for active scanning if available
            from app.core.platform.detect import get_platform_features
            platform_info = get_platform_features()
            logger.info(
                f"ScannerService initialized with engine: {self.scapy_engine.__class__.__name__} "
                f"(Platform: {platform_info.platform.value})"
            )
        except Exception as e:
            logger.error(f"Failed to initialize attack engine for scanner: {e}", exc_info=True)
            # Create a dummy engine as fallback
            from app.core.engine.dummy import DummyAttackEngine
            self.scapy_engine = DummyAttackEngine()

    async def start_scan(self, request: ScanRequest) -> ScanResult:
        """
        Start a scan asynchronously.
        Returns a ScanResult immediately with status=RUNNING.
        This method should return quickly without blocking.
        
        Before starting a new scan, automatically clears old device list
        to ensure fresh scan results.
        """
        logger.info(f"Starting scan: type={request.type}, target_subnets={request.target_subnets}")
        
        # Clear old devices before starting new scan
        await self._clear_device_cache()
        
        # Broadcast scan started event
        await self.ws_manager.broadcast(
            {
                "event": "scanStarted",
                "data": {
                    "type": request.type,
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            }
        )
        
        # Create initial result
        scan_id = uuid4()
        
        # Start the background task immediately without waiting
        # Use create_task to ensure it runs in background
        task = asyncio.create_task(self._run_scan_task(scan_id, request))
        
        # Store task reference for cancellation
        self.active_tasks[str(scan_id)] = task
        
        # Add cleanup callback to remove task when done
        def cleanup_task(t):
            self.active_tasks.pop(str(scan_id), None)
        task.add_done_callback(cleanup_task)
        
        # Don't await the task - let it run in background
        # Log task creation but don't wait for it
        logger.info(f"Scan task {scan_id} queued in background (task: {id(task)})")
        
        # Return immediately
        return ScanResult(
            id=scan_id,
            status=ScanStatus.RUNNING,
            started_at=datetime.now(UTC),
        )

    async def _clear_device_cache(self):
        """
        Clear all devices from database before starting a new scan.
        This ensures that each scan starts with a fresh device list.
        """
        logger.info("Clearing old device list before starting new scan...")
        try:
            session_factory = get_session_factory()
            async with session_factory() as session:
                repo = DeviceRepository(session)
                deleted_count = await repo.clear_all()
                await session.commit()
                logger.info(f"Cleared {deleted_count} old devices from database")
                
                # Clear in-memory state as well
                self.state_manager.clear_devices()
                
                # Broadcast device list cleared event
                await self.ws_manager.broadcast(
                    {
                        "event": "deviceListCleared",
                        "data": {
                            "deleted_count": deleted_count,
                            "timestamp": datetime.now(UTC).isoformat(),
                        },
                    }
                )
        except Exception as e:
            logger.error(f"Failed to clear device cache: {e}", exc_info=True)
            # Don't fail the scan if cache clearing fails, just log the error
            # This allows the scan to proceed even if clearing fails

    async def _run_scan_task(self, scan_id, request: ScanRequest):
        """Background task to perform actual network scanning."""
        logger.info(f"Scan {scan_id} started. Type: {request.type}")
        
        # Add timeout to prevent infinite scanning (max 5 minutes)
        try:
            await asyncio.wait_for(self._do_scan(scan_id, request), timeout=300.0)
        except asyncio.TimeoutError:
            logger.error(f"Scan {scan_id} timed out after 5 minutes")
            await self.ws_manager.broadcast(
                {
                    "event": "scanCompleted",
                    "data": {
                        "id": str(scan_id),
                        "status": "failed",
                        "error": "Scan timed out after 5 minutes",
                        "timestamp": datetime.now(UTC).isoformat(),
                    },
                }
            )
    
    async def _do_scan(self, scan_id, request: ScanRequest):
        """Actual scan implementation."""
        # Check if task was cancelled (this check happens at start)
        # We'll also check periodically during scan
        
        # Notify via WebSocket
        await self.ws_manager.broadcast(
            {
                "event": "scanStarted",
                "data": {
                    "id": str(scan_id),
                    "type": request.type,
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            }
        )

        try:
            devices_found = 0
            discovered_devices = []

            # 1. Active Scan (if engine supports it)
            # This populates the kernel ARP table
            if hasattr(self.scapy_engine, "scan_network"):
                try:
                    # Check permissions before attempting scan
                    # In Docker with privileged mode and host network, permissions should be available
                    if hasattr(self.scapy_engine, "check_permissions"):
                        has_permissions = self.scapy_engine.check_permissions()
                        if not has_permissions:
                            logger.warning(
                                "Active scan requires root privileges or NET_RAW capability. "
                                "Falling back to passive ARP table scan. "
                                "To enable active scanning, ensure container has NET_RAW capability "
                                "or runs as root with privileged mode (see docker-compose.yml)."
                            )
                        else:
                            logger.info("Permissions verified. Performing active Scapy ARP scan...")
                            scan_results = await self.scapy_engine.scan_network()
                            if scan_results:
                                logger.info(f"Active scan found {len(scan_results)} devices")
                            else:
                                logger.debug("Active scan completed but found no new devices")
                    else:
                        logger.info("Performing active Scapy ARP scan (no permission check available)...")
                        scan_results = await self.scapy_engine.scan_network()
                        if scan_results:
                            logger.info(f"Active scan found {len(scan_results)} devices")
                        else:
                            logger.debug("Active scan completed but found no new devices")
                except Exception as e:
                    error_msg = str(e)
                    error_type = type(e).__name__
                    logger.warning(
                        f"Active scan failed (this is non-fatal): {error_type}: {error_msg}. "
                        f"Falling back to passive ARP table scan.",
                        exc_info=True
                    )
            else:
                logger.debug("Scapy engine does not support scan_network, skipping active scan")

            # 2. Passive Scan (Read ARP table)
            # Perform ARP table scan (works without root)
            # Check if cancelled before starting ARP scan
            if str(scan_id) not in self.active_tasks:
                logger.info(f"Scan {scan_id} was cancelled, aborting ARP scan")
                return
            arp_devices = await self._scan_arp_table()
            
            # If QUICK scan, just use ARP table
            # If FULL scan, we could also do ping sweep (requires root/caps)
            if request.type == "full":
                # For now, FULL scan also just uses ARP table
                # In future, could add ping sweep or port scanning
                logger.info("FULL scan requested, using ARP table for now")
            
            # Convert ARP entries to Device objects
            session_factory = get_session_factory()
            async with session_factory() as session:
                try:
                    repo = DeviceRepository(session)
                    
                    for ip, mac, interface in arp_devices:
                        # Check if device already exists
                        existing_device = await repo.get_by_mac(mac)
                        
                        now = datetime.now(UTC)
                        if existing_device:
                            # Update last_seen
                            existing_device.last_seen = now
                            # If vendor is not set, try to identify it
                            if not existing_device.vendor:
                                vendor = self._guess_vendor(mac)
                                if vendor:
                                    existing_device.vendor = vendor
                                    logger.debug(f"Identified vendor for existing device {mac}: {vendor}")
                            # If model is not set, try to identify it
                            if not existing_device.model:
                                model = self.model_lookup.lookup_model(mac, existing_device.vendor)
                                if model:
                                    existing_device.model = model
                                    logger.debug(f"Identified model for existing device {mac}: {model}")
                            # Update device type if still UNKNOWN, using vendor and model
                            if existing_device.type == DeviceType.UNKNOWN:
                                device_type = self._guess_device_type(
                                    mac, 
                                    ip=str(ip), 
                                    vendor=existing_device.vendor, 
                                    model=existing_device.model
                                )
                                if device_type != DeviceType.UNKNOWN:
                                    existing_device.type = device_type
                                    logger.debug(f"Updated device type for {mac}: {device_type}")
                            device = await repo.upsert(existing_device)
                            logger.debug(f"Updated existing device: {mac} ({ip})")
                        else:
                            # Create new device
                            # First identify vendor
                            vendor = self._guess_vendor(mac)
                            # Then identify model using vendor information
                            model = self.model_lookup.lookup_model(mac, vendor) if vendor else self.model_lookup.lookup_model(mac)
                            
                            # Guess device type using all available information
                            device_type = self._guess_device_type(mac, ip=str(ip), vendor=vendor, model=model)
                            
                            device = Device(
                                mac=mac,
                                ip=str(ip),
                                name=None,  # Don't set name, focus on type
                                vendor=vendor,
                                model=model,
                                type=device_type,
                                status=DeviceStatus.ONLINE,
                                first_seen=now,
                                last_seen=now,
                            )
                            device = await repo.upsert(device)
                            
                            logger.info(f"Discovered new device: {mac} ({ip})")
                            discovered_devices.append(device)
                        
                        # Also update in-memory state for immediate UI updates
                        self.state_manager.update_device(device)
                        
                        devices_found += 1
                    
                    await session.commit()
                except Exception as e:
                    await session.rollback()
                    logger.error(f"Error saving devices to database: {e}", exc_info=True)
                    raise

            logger.info(f"Scan {scan_id} completed. Found {devices_found} devices.")

            # Send deviceAdded events for newly discovered devices
            for device in discovered_devices:
                await self.ws_manager.broadcast(
                    {
                        "event": "deviceAdded",
                        "data": device.model_dump(mode="json"),
                    }
                )
                # Also send scan log for each device
                # Use vendor/model for log display
                device_display = device.vendor or device.model or "未知设备"
                
                await self.ws_manager.broadcast(
                    {
                        "event": "scanLog",
                        "data": {
                            "level": "info",
                            "message": f"发现设备: {device.ip} ({device.mac}) - {device_display}",
                            "timestamp": datetime.now(UTC).isoformat(),
                        },
                    }
                )

            # Notify scan completion via WebSocket
            await self.ws_manager.broadcast(
                {
                    "event": "scanCompleted",
                    "data": {
                        "id": str(scan_id),
                        "status": "completed",
                        "devices_found": devices_found,
                        "timestamp": datetime.now(UTC).isoformat(),
                    },
                }
            )

        except Exception as e:
            error_msg = str(e)
            error_type = type(e).__name__
            logger.error(
                f"Scan {scan_id} failed: {error_type}: {error_msg}",
                exc_info=True
            )
            
            # Log to state manager for UI display
            from app.models.log import SystemLog
            from uuid import uuid4
            error_log = SystemLog(
                id=uuid4(),
                level="error",
                module="scanner",
                message=f"Scan {scan_id} failed: {error_msg}",
                context={"scan_id": str(scan_id), "error_type": error_type, "error": error_msg},
            )
            self.state_manager.add_log(error_log)
            
            await self.ws_manager.broadcast(
                {
                    "event": "scanCompleted",
                    "data": {
                        "id": str(scan_id),
                        "status": "failed",
                        "error": error_msg,
                        "error_type": error_type,
                        "timestamp": datetime.now(UTC).isoformat(),
                    },
                }
            )

    async def _scan_arp_table(self) -> list[tuple[str, str, str]]:
        """
        Scan ARP table to discover devices.
        Returns list of (IP, MAC, interface) tuples.
        Works cross-platform (Linux/macOS/Windows/Docker).
        """
        devices = []
        platform = sys.platform
        
        # Detect if running in Docker container
        is_docker = False
        try:
            with open("/proc/self/cgroup", "r") as f:
                if "docker" in f.read() or "containerd" in f.read():
                    is_docker = True
        except (FileNotFoundError, PermissionError):
            pass
        
        logger.info(f"Starting ARP table scan on platform: {platform}, Docker: {is_docker}")
        
        # Broadcast scan progress
        await self.ws_manager.broadcast(
            {
                "event": "scanProgress",
                "data": {
                    "message": f"开始扫描 ARP 表 (平台: {platform})",
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            }
        )
        
        # macOS Implementation
        if platform == "darwin":
            try:
                # arp -an lists all entries without DNS resolution
                result = await asyncio.create_subprocess_exec(
                    "arp", "-an",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                # Add timeout to prevent hanging (5 seconds should be enough for arp command)
                try:
                    stdout, stderr = await asyncio.wait_for(result.communicate(), timeout=5.0)
                except asyncio.TimeoutError:
                    logger.error("ARP command timed out after 5 seconds")
                    result.kill()
                    await result.wait()
                    return []
                
                if result.returncode == 0:
                    output = stdout.decode()
                    logger.debug(f"macOS arp -an output: {output[:200]}...")  # Log first 200 chars
                    
                    for line in output.splitlines():
                        if not line.strip():
                            continue
                            
                        # Format: ? (IP) at MAC on IFACE ...
                        # e.g. ? (192.168.1.1) at 00:11:22:33:44:55 on en0 ifscope [ethernet]
                        # or: (192.168.1.1) at 00:11:22:33:44:55 on en0
                        try:
                            # Try to extract IP from parentheses
                            ip_match = re.search(r'\(([0-9.]+)\)', line)
                            if not ip_match:
                                continue
                            ip_str = ip_match.group(1)
                            
                            # Extract MAC address (after "at")
                            at_match = re.search(r'\bat\s+([0-9a-fA-F:]+)', line)
                            if not at_match:
                                continue
                            mac_str = at_match.group(1)
                            
                            # Extract interface (after "on")
                            on_match = re.search(r'\bon\s+(\w+)', line)
                            interface = on_match.group(1) if on_match else "unknown"
                            
                            # Normalize MAC (macOS can omit leading zeros)
                            # e.g. 0:1:2... -> 00:01:02...
                            mac_parts = mac_str.split(":")
                            if len(mac_parts) == 6:
                                mac_clean = ":".join(p.zfill(2) for p in mac_parts).upper()
                                
                                # Filter out multicast/broadcast/incomplete
                                if (self._is_valid_mac(mac_clean) and 
                                    mac_clean != "00:00:00:00:00:00" and 
                                    mac_clean != "FF:FF:FF:FF:FF:FF"):
                                    devices.append((ip_str, mac_clean, interface))
                                    logger.debug(f"Found device via macOS arp: {ip_str} -> {mac_clean} on {interface}")
                        except Exception as e:
                            logger.debug(f"Failed to parse macOS arp line '{line}': {e}")
                            continue
                else:
                    error_msg = stderr.decode() if stderr else "Unknown error"
                    logger.warning(f"macOS arp command failed (code {result.returncode}): {error_msg}")
                            
            except FileNotFoundError:
                logger.warning("'arp' command not found on macOS. ARP scanning unavailable.")
            except Exception as e:
                logger.error(f"macOS ARP scan failed: {e}", exc_info=True)
            
            if not devices and is_docker:
                logger.warning(
                    "No devices found in Docker container. "
                    "This may be normal if the network is empty or if host network mode is not enabled. "
                    "If using host network mode with privileged mode, ARP scanning should work. "
                    "Check docker-compose.yml for network_mode: 'host' and privileged: true."
                )
            else:
                logger.info(f"macOS ARP scan completed. Found {len(devices)} devices.")
            return devices

        # Linux Implementation (also handles Docker containers)
        if platform.startswith("linux"):
            try:
                # Try using 'ip neigh' command (modern, works on most Linux)
                result = await asyncio.create_subprocess_exec(
                    "ip", "neigh", "show",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                # Add timeout to prevent hanging (5 seconds should be enough for ip command)
                try:
                    stdout, stderr = await asyncio.wait_for(result.communicate(), timeout=5.0)
                except asyncio.TimeoutError:
                    logger.error("ip neigh command timed out after 5 seconds")
                    result.kill()
                    await result.wait()
                    return []
                
                if result.returncode == 0:
                    output = stdout.decode()
                    logger.debug(f"Linux ip neigh output: {output[:200]}...")  # Log first 200 chars
                    
                    # Parse ip neigh output
                    # Format: IP dev INTERFACE lladdr MAC ADDR STALE|REACHABLE
                    for line in output.splitlines():
                        if not line.strip():
                            continue
                        parts = line.strip().split()
                        if len(parts) >= 5:
                            ip_str = parts[0]
                            interface = parts[2]
                            mac_str = parts[4]
                            
                            # Validate MAC address format
                            if self._is_valid_mac(mac_str):
                                devices.append((ip_str, mac_str.upper(), interface))
                                logger.debug(f"Found device via ip neigh: {ip_str} -> {mac_str} on {interface}")
                else:
                    error_msg = stderr.decode() if stderr else "Unknown error"
                    logger.debug(f"ip neigh command failed (code {result.returncode}): {error_msg}")
                
                # Fallback: try /proc/net/arp if ip command failed or found no devices
                if not devices:
                    try:
                        with open("/proc/net/arp", "r") as f:
                            lines = f.readlines()[1:]  # Skip header
                            for line in lines:
                                if not line.strip():
                                    continue
                                parts = line.split()
                                if len(parts) >= 6:
                                    ip_str = parts[0]
                                    mac_str = parts[3]
                                    interface = parts[5]
                                    
                                    # Skip incomplete entries (MAC is 00:00:00:00:00:00)
                                    if mac_str != "00:00:00:00:00:00" and self._is_valid_mac(mac_str):
                                        devices.append((ip_str, mac_str.upper(), interface))
                                        logger.debug(f"Found device via /proc/net/arp: {ip_str} -> {mac_str} on {interface}")
                    except (FileNotFoundError, PermissionError) as e:
                        logger.warning(f"Could not read /proc/net/arp: {e}")
                    except Exception as e:
                        logger.warning(f"Error reading /proc/net/arp: {e}")
                
            except FileNotFoundError:
                logger.warning("'ip' command not found, trying /proc/net/arp")
                # Fallback to /proc/net/arp handled above
                try:
                    with open("/proc/net/arp", "r") as f:
                        lines = f.readlines()[1:]  # Skip header
                        for line in lines:
                            if not line.strip():
                                continue
                            parts = line.split()
                            if len(parts) >= 6:
                                ip_str = parts[0]
                                mac_str = parts[3]
                                interface = parts[5]
                                
                                if mac_str != "00:00:00:00:00:00" and self._is_valid_mac(mac_str):
                                    devices.append((ip_str, mac_str.upper(), interface))
                                    logger.debug(f"Found device via /proc/net/arp: {ip_str} -> {mac_str}")
                except (FileNotFoundError, PermissionError) as e:
                    logger.warning(f"Could not read /proc/net/arp: {e}")
            except Exception as e:
                logger.error(f"Error during Linux ARP table scan: {e}", exc_info=True)
            
            if not devices and is_docker:
                logger.warning(
                    "No devices found in Docker container. "
                    "Docker containers typically cannot access host ARP table. "
                    "Consider using host network mode (--network=host) or mounting /proc/net/arp."
                )
            else:
                logger.info(f"Linux ARP scan completed. Found {len(devices)} devices.")
            return devices
        
        # Windows Implementation
        if platform == "win32":
            try:
                # Windows uses 'arp -a' to list ARP table
                result = await asyncio.create_subprocess_exec(
                    "arp", "-a",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    creationflags=0x08000000 if sys.platform == "win32" else 0  # CREATE_NO_WINDOW on Windows
                )
                # Add timeout to prevent hanging (5 seconds should be enough for arp command)
                try:
                    stdout, stderr = await asyncio.wait_for(result.communicate(), timeout=5.0)
                except asyncio.TimeoutError:
                    logger.error("ARP command timed out after 5 seconds")
                    result.kill()
                    await result.wait()
                    return []
                
                if result.returncode == 0:
                    output = stdout.decode('utf-8', errors='ignore')
                    logger.debug(f"Windows arp -a output: {output[:200]}...")  # Log first 200 chars
                    
                    # Windows ARP output format:
                    # Interface: 192.168.1.100 --- 0xa
                    #   Internet Address      Physical Address      Type
                    #   192.168.1.1          00-11-22-33-44-55     dynamic
                    #   192.168.1.2          aa-bb-cc-dd-ee-ff     static
                    current_interface = "unknown"
                    for line in output.splitlines():
                        line = line.strip()
                        if not line:
                            continue
                        
                        # Check for interface line: "Interface: IP --- 0xN"
                        interface_match = re.search(r'Interface:\s+([0-9.]+)', line, re.IGNORECASE)
                        if interface_match:
                            current_interface = interface_match.group(1)
                            continue
                        
                        # Skip header line
                        if "Internet Address" in line or "Physical Address" in line or "Type" in line:
                            continue
                        
                        # Parse ARP entry: "IP          MAC-ADDRESS      TYPE"
                        # Format: IP address, MAC address (with dashes), Type
                        parts = line.split()
                        if len(parts) >= 2:
                            ip_str = parts[0]
                            mac_str = parts[1].replace("-", ":")  # Convert Windows format to standard
                            
                            # Validate IP and MAC
                            if re.match(r'^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$', ip_str):
                                # Normalize MAC address
                                mac_parts = mac_str.split(":")
                                if len(mac_parts) == 6:
                                    mac_clean = ":".join(p.zfill(2) for p in mac_parts).upper()
                                    
                                    # Filter out multicast/broadcast/incomplete
                                    if (self._is_valid_mac(mac_clean) and 
                                        mac_clean != "00:00:00:00:00:00" and 
                                        mac_clean != "FF:FF:FF:FF:FF:FF"):
                                        devices.append((ip_str, mac_clean, current_interface))
                                        logger.debug(f"Found device via Windows arp: {ip_str} -> {mac_clean} on {current_interface}")
                else:
                    error_msg = stderr.decode('utf-8', errors='ignore') if stderr else "Unknown error"
                    logger.warning(f"Windows arp command failed (code {result.returncode}): {error_msg}")
                            
            except FileNotFoundError:
                logger.warning("'arp' command not found on Windows. ARP scanning unavailable.")
            except Exception as e:
                logger.error(f"Windows ARP scan failed: {e}", exc_info=True)
            
            logger.info(f"Windows ARP scan completed. Found {len(devices)} devices.")
            return devices
        
        # Unknown platform - log warning and return empty
        logger.warning(f"Unsupported platform for ARP scanning: {platform}. Returning empty device list.")
        return devices
        
        # Remove duplicates (same MAC)
        seen_macs = set()
        unique_devices = []
        for ip, mac, interface in devices:
            if mac not in seen_macs:
                seen_macs.add(mac)
                unique_devices.append((ip, mac, interface))
        
        logger.info(f"ARP table scan found {len(unique_devices)} unique devices")
        
        # Broadcast scan progress
        await self.ws_manager.broadcast(
            {
                "event": "scanProgress",
                "data": {
                    "message": f"扫描完成，发现 {len(unique_devices)} 个设备",
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            }
        )
        return unique_devices

    def _is_valid_mac(self, mac_str: str) -> bool:
        """Check if a string is a valid MAC address."""
        # Accept formats: XX:XX:XX:XX:XX:XX or XX-XX-XX-XX-XX-XX
        mac_pattern = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
        return bool(mac_pattern.match(mac_str))

    def _guess_vendor(self, mac: str) -> str | None:
        """
        Guess vendor from MAC address OUI (first 3 octets).
        Uses Scapy's built-in manufacturer database.
        """
        try:
            # Try to use Scapy's built-in manufacturer database
            from scapy.data import get_manuf
            
            # Normalize MAC address format (remove separators for lookup)
            # get_manuf accepts formats like "00:11:22:33:44:55" or "00-11-22-33-44-55"
            # But it's more lenient, so we can pass the MAC as-is if it's already normalized
            mac_normalized = mac.upper().replace("-", ":")
            
            # get_manuf returns the vendor name or None if not found
            vendor = get_manuf(mac_normalized)
            
            if vendor and vendor.strip():
                # get_manuf might return empty string or whitespace, filter those out
                return vendor.strip()
            return None
        except ImportError:
            # Scapy not available, return None
            logger.debug(f"Scapy not available for vendor lookup of {mac}")
            return None
        except Exception as e:
            # Log but don't fail - vendor lookup is non-critical
            logger.debug(f"Failed to lookup vendor for MAC {mac}: {e}")
            return None

    def _guess_device_type(self, mac: str, ip: str = None, vendor: str = None, model: str = None) -> DeviceType:
        """
        Guess device type from MAC address, IP, vendor, and model.
        Uses heuristics based on vendor/model names and IP address.
        """
        # Try to detect gateway (router)
        try:
            from scapy.all import conf
            # conf.route.route("0.0.0.0")[2] returns default gateway IP
            gateway_ip = conf.route.route("0.0.0.0")[2]
            if ip and ip == gateway_ip:
                return DeviceType.ROUTER
        except Exception:
            pass

        # Use vendor and model information to infer device type
        # Priority: model > vendor (model is more specific)
        vendor_lower = (vendor or "").lower()
        model_lower = (model or "").lower()
        combined = f"{vendor_lower} {model_lower}".lower()

        # Router detection keywords (more specific, check model first)
        # Only match if model/vendor explicitly contains router-related terms
        router_keywords = ["router", "modem", "gateway", "access point", "ap", "switch", "hub", "wifi router", "wireless router", "tplink router", "d-link router", "netgear router", "asus router", "cisco router", "huawei router", "xiaomi router", "mi router"]
        # Check model first (more specific)
        if model_lower and any(keyword in model_lower for keyword in router_keywords):
            return DeviceType.ROUTER
        # Then check vendor only if it's a known router manufacturer AND model suggests router
        router_vendors = ["tplink", "d-link", "netgear", "cisco"]
        if vendor_lower in router_vendors and ("router" in model_lower or "modem" in model_lower or "ap" in model_lower):
            return DeviceType.ROUTER

        # Mobile device detection keywords (check model first)
        mobile_keywords = ["iphone", "ipad", "ipod", "galaxy", "redmi", "honor", "phone", "tablet", "mobile", "smartphone", "mate", "p series", "nova", "reno", "find", "x series"]
        if model_lower and any(keyword in model_lower for keyword in mobile_keywords):
            return DeviceType.MOBILE
        # Check vendor for mobile manufacturers
        mobile_vendors = ["apple", "samsung", "xiaomi", "redmi", "huawei", "honor", "oppo", "vivo", "oneplus", "lg", "meizu"]
        if vendor_lower in mobile_vendors and not any(router_word in combined for router_word in ["router", "modem", "gateway", "switch"]):
            return DeviceType.MOBILE

        # PC/Laptop detection keywords
        pc_keywords = ["laptop", "notebook", "desktop", "pc", "computer", "macbook", "thinkpad", "ideapad", "zenbook", "vivobook", "rog", "alienware", "optiplex", "precision", "elitebook", "probook", "pavilion", "envy", "omen", "spectre", "zbook", "workstation", "imac", "mac pro", "mac mini"]
        if any(keyword in combined for keyword in pc_keywords):
            return DeviceType.PC

        # IoT device detection keywords
        iot_keywords = ["iot", "homepod", "airpods", "watch", "band", "camera", "sensor", "scale", "lock", "purifier", "vacuum", "tv", "monitor", "printer", "scanner"]
        if any(keyword in combined for keyword in iot_keywords):
            return DeviceType.IOT

        # Default to UNKNOWN if no match
        return DeviceType.UNKNOWN


# Global accessor
def get_scanner_service() -> ScannerService:
    return ScannerService()
