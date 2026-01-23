"""Candidate refresh prober - validates candidate device online status.

Performs targeted probes on candidate devices to confirm they are still
online and update their last_seen timestamp.
"""

import asyncio
import logging
from datetime import UTC, datetime
from typing import NamedTuple

logger = logging.getLogger(__name__)


class RefreshResult(NamedTuple):
    """Result of refreshing a candidate device."""

    ip: str
    mac: str
    online: bool
    rtt: float | None  # Round-trip time in ms (if successful)
    method: str  # "icmp-ping" or "arp-probe"
    last_seen: datetime


async def refresh_candidates(
    candidates: list[tuple[str, str]],  # (ip, mac) pairs
    timeout: float = 1.0,
    concurrency: int = 10,
) -> list[RefreshResult]:
    """Refresh candidate devices to confirm online status.

    Performs lightweight probes on candidate devices from cache/leases
    to validate they are still accessible. This is much faster than
    full subnet scanning.

    Args:
        candidates: List of (IP, MAC) tuples to refresh
        timeout: Probe timeout per device in seconds
        concurrency: Maximum concurrent probes

    Returns:
        List of RefreshResult with online status and RTT
    """
    logger.info(
        f"Starting candidate refresh: {len(candidates)} candidates, "
        f"timeout={timeout}s, concurrency={concurrency}"
    )

    if not candidates:
        logger.warning("No candidates to refresh")
        return []

    # Limit concurrency with semaphore
    semaphore = asyncio.Semaphore(concurrency)

    async def probe_candidate(ip: str, mac: str) -> RefreshResult:
        async with semaphore:
            try:
                # Try ICMP ping first (faster)
                online, rtt, method = await _ping_device(ip, timeout)

                return RefreshResult(
                    ip=ip,
                    mac=mac,
                    online=online,
                    rtt=rtt,
                    method=method,
                    last_seen=datetime.now(UTC) if online else datetime.now(UTC),
                )
            except Exception as e:
                logger.debug(f"Refresh probe failed for {ip}: {e}")
                return RefreshResult(
                    ip=ip,
                    mac=mac,
                    online=False,
                    rtt=None,
                    method="failed",
                    last_seen=datetime.now(UTC),
                )

    # Probe all candidates concurrently
    tasks = [probe_candidate(ip, mac) for ip, mac in candidates]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Filter out exceptions
    valid_results = []
    for result in results:
        if isinstance(result, RefreshResult):
            valid_results.append(result)
        elif isinstance(result, Exception):
            logger.warning(f"Refresh task exception: {result}")

    # Statistics
    online_count = sum(1 for r in valid_results if r.online)
    logger.info(
        f"Candidate refresh completed: {online_count}/{len(valid_results)} online"
    )

    return valid_results


async def _ping_device(ip: str, timeout: float) -> tuple[bool, float | None, str]:
    """Ping a device using ICMP.

    Args:
        ip: Target IP address
        timeout: Timeout in seconds

    Returns:
        (online, rtt_ms, method)
    """
    import platform
    import subprocess

    try:
        # Platform-specific ping command
        if platform.system().lower() == "windows":
            ping_cmd = ["ping", "-n", "1", "-w", str(int(timeout * 1000)), ip]
        else:
            # macOS/Linux
            ping_cmd = ["ping", "-c", "1", "-W", str(int(timeout)), ip]

        start_time = datetime.now()

        proc = await asyncio.create_subprocess_exec(
            *ping_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout + 1)
            end_time = datetime.now()

            if proc.returncode == 0:
                # Calculate RTT
                rtt = (end_time - start_time).total_seconds() * 1000  # ms

                # Try to extract actual RTT from output
                output = stdout.decode("utf-8", errors="ignore")
                time_match = re.search(r"time[=<]([0-9.]+)\s*ms", output, re.I)
                if time_match:
                    rtt = float(time_match.group(1))

                return (True, rtt, "icmp-ping")
            else:
                return (False, None, "icmp-ping")

        except asyncio.TimeoutError:
            # Timeout means device is offline or unreachable
            return (False, None, "icmp-ping-timeout")

    except Exception as e:
        logger.debug(f"Ping failed for {ip}: {e}")
        return (False, None, "ping-error")
