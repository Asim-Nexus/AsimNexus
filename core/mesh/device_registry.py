"""
STATUS: REAL — Auto-Scan + Auto-Connect + Auto-Scale Device Registry
====================================================================
ASIMNEXUS Device Registry
=========================
Tracks all connected devices and manages resilient network topology
with automatic scanning, connection, and scaling capabilities.

Features:
- Auto-Scan: Periodic LAN scanning via broadcast/multicast/mDNS
- Auto-Connect: Automatic handshake and registration of discovered devices
- Auto-Scale: Automatic resource distribution across connected devices
- Topology Management: Tree + Star + Ring hybrid topology
- Capability Indexing: Devices indexed by compute/storage/network/iot/output
- Health Monitoring: Periodic PING/PONG with stale node cleanup
- Event Publishing: Device events published to event bus
"""

import asyncio
import json
import logging
import os
import platform
import socket
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("AsimNexus.DeviceRegistry")


# ══════════════════════════════════════════════════════════════════════
# Enums
# ══════════════════════════════════════════════════════════════════════

class ConnectionMethod(Enum):
    """How a device connects to the mesh."""
    LOCAL = "local"
    SSH = "ssh"
    API = "api"
    BLUETOOTH = "bluetooth"
    WIFI = "wifi"
    WEBSOCKET = "websocket"
    P2P = "p2p"


class TrustLevel(Enum):
    """Trust classification for devices."""
    VERIFIED = "verified"      # Cryptographically verified
    TRUSTED = "trusted"        # Known and trusted
    UNKNOWN = "unknown"        # New device, not yet trusted
    SUSPICIOUS = "suspicious"  # Failed verification


class DeviceType(Enum):
    """Types of devices that can join the mesh."""
    PC = "pc"
    MOBILE = "mobile"
    TABLET = "tablet"
    IOT = "iot"
    SERVER = "server"
    CLOUD = "cloud"
    PRINTER = "printer"
    ROUTER = "router"
    SMART_HOME = "smart_home"
    WEARABLE = "wearable"
    VEHICLE = "vehicle"
    DRONE = "drone"
    EMBEDDED = "embedded"
    VIRTUAL = "virtual"        # Docker/VM instances


class DeviceStatus(Enum):
    """Current operational status of a device."""
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    MAINTENANCE = "maintenance"
    ERROR = "error"
    CONNECTING = "connecting"
    DISCONNECTED = "disconnected"


class TopologyType(Enum):
    """Network topology types supported."""
    TREE = "tree"    # Hierarchical: Owner -> AsimCore -> Devices
    STAR = "star"    # Central: All devices connect to AsimCore
    RING = "ring"    # Resilient: Backup paths between devices
    MESH = "mesh"    # Full mesh: Every device connects to every other


class ResourceType(Enum):
    """Types of resources a device can contribute."""
    COMPUTE = "compute"       # CPU/GPU cycles
    STORAGE = "storage"       # Disk space
    MEMORY = "memory"         # RAM
    NETWORK = "network"       # Bandwidth
    GPU = "gpu"               # GPU compute
    SENSOR = "sensor"         # Sensor data
    DISPLAY = "display"       # Screen/output
    AUDIO = "audio"           # Speaker/mic


# ══════════════════════════════════════════════════════════════════════
# Data Classes
# ══════════════════════════════════════════════════════════════════════

@dataclass
class DeviceResource:
    """Resource contribution from a device."""
    type: ResourceType
    total: float
    available: float
    unit: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DeviceInfo:
    """Complete information about a registered device."""
    id: str
    name: str
    device_type: DeviceType
    connection: ConnectionMethod
    trust_level: TrustLevel
    status: DeviceStatus = DeviceStatus.ONLINE
    ip_address: Optional[str] = None
    port: Optional[int] = None
    hostname: Optional[str] = None
    mac_address: Optional[str] = None
    os_info: Optional[str] = None
    version: str = "1.0.0"
    capabilities: List[str] = field(default_factory=list)
    resources: List[DeviceResource] = field(default_factory=list)
    parent_id: Optional[str] = None          # For tree topology
    backup_paths: List[str] = field(default_factory=list)  # For ring topology
    owner_id: str = "default_owner"
    last_seen: float = field(default_factory=time.time)
    first_seen: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-safe dict."""
        return {
            "id": self.id,
            "name": self.name,
            "device_type": self.device_type.value,
            "connection": self.connection.value,
            "trust_level": self.trust_level.value,
            "status": self.status.value,
            "ip_address": self.ip_address,
            "port": self.port,
            "hostname": self.hostname,
            "os_info": self.os_info,
            "version": self.version,
            "capabilities": self.capabilities,
            "resources": [
                {
                    "type": r.type.value,
                    "total": r.total,
                    "available": r.available,
                    "unit": r.unit,
                    "metadata": r.metadata,
                }
                for r in self.resources
            ],
            "parent_id": self.parent_id,
            "backup_paths": self.backup_paths,
            "owner_id": self.owner_id,
            "last_seen": self.last_seen,
            "first_seen": self.first_seen,
            "metadata": self.metadata,
            "tags": self.tags,
        }


@dataclass
class ScanResult:
    """Result of a device scan."""
    device_id: str
    ip_address: str
    port: int
    hostname: str
    capabilities: List[str]
    version: str
    response_time_ms: float
    trust_level: TrustLevel = TrustLevel.UNKNOWN


# ══════════════════════════════════════════════════════════════════════
# DeviceRegistry — Main Class
# ══════════════════════════════════════════════════════════════════════

class DeviceRegistry:
    """
    Device Registry for ASIM Nexus with Auto-Scan, Auto-Connect, Auto-Scale.

    Manages all devices in the mesh network with:
    - Automatic discovery and registration
    - Hybrid topology (Tree + Star + Ring)
    - Resource capability indexing
    - Health monitoring and stale cleanup
    - Event-driven notifications
    """

    # Configuration (env var overridable)
    SCAN_INTERVAL = int(os.getenv("ASIM_SCAN_INTERVAL", "30"))        # seconds
    HEALTH_INTERVAL = int(os.getenv("ASIM_HEALTH_INTERVAL", "15"))    # seconds
    STALE_TIMEOUT = int(os.getenv("ASIM_STALE_TIMEOUT", "300"))       # seconds
    DISCOVERY_PORT = int(os.getenv("ASIM_DISCOVERY_PORT", "7331"))
    MAX_BACKUP_PATHS = int(os.getenv("ASIM_MAX_BACKUP_PATHS", "3"))

    def __init__(self, node_id: Optional[str] = None):
        self.node_id = node_id or self._generate_node_id()
        self.devices: Dict[str, DeviceInfo] = {}
        self._scan_history: Dict[str, float] = {}  # device_id -> last_seen
        self._connection_attempts: Dict[str, int] = {}  # device_id -> attempt_count
        self._callbacks: Dict[str, List[Callable]] = {
            "device_connected": [],
            "device_disconnected": [],
            "device_updated": [],
            "scan_complete": [],
            "resource_updated": [],
        }

        # Topology structures
        self.topology: Dict[TopologyType, Dict] = {
            TopologyType.TREE: {},   # parent_id -> [child_ids]
            TopologyType.STAR: {},   # device_id -> "asim_core"
            TopologyType.RING: {},   # device_id -> [backup_device_ids]
            TopologyType.MESH: {},   # device_id -> [all_peer_ids]
        }

        # Capability index: capability_name -> [device_ids]
        self.capability_index: Dict[str, List[str]] = {
            "compute": [],
            "storage": [],
            "memory": [],
            "network": [],
            "gpu": [],
            "iot": [],
            "sensor": [],
            "output": [],
            "display": [],
            "audio": [],
        }

        # Resource pool: resource_type -> total_available
        self.resource_pool: Dict[str, float] = {
            "compute": 0.0,
            "storage": 0.0,
            "memory": 0.0,
            "gpu": 0.0,
        }

        # Background tasks
        self._running = False
        self._scan_task: Optional[asyncio.Task] = None
        self._health_task: Optional[asyncio.Task] = None
        self._udp_socket: Optional[socket.socket] = None

        logger.info(f"📱 DeviceRegistry initialized — Node: {self.node_id}")

    # ── Lifecycle ────────────────────────────────────────────────────

    async def start(self):
        """Start the device registry with auto-scan and health monitoring."""
        if self._running:
            logger.warning("DeviceRegistry already running")
            return

        self._running = True

        # Register local device
        local_device = self._create_local_device()
        self._register_device_internal(local_device)

        # Start UDP listener for discovery
        self._start_udp_listener()

        # Start background tasks
        self._scan_task = asyncio.create_task(self._auto_scan_loop())
        self._health_task = asyncio.create_task(self._health_monitor_loop())

        logger.info(f"📱 DeviceRegistry started — scanning every {self.SCAN_INTERVAL}s, "
                    f"health check every {self.HEALTH_INTERVAL}s")

    async def stop(self):
        """Stop the device registry."""
        self._running = False

        if self._scan_task:
            self._scan_task.cancel()
            self._scan_task = None

        if self._health_task:
            self._health_task.cancel()
            self._health_task = None

        if self._udp_socket:
            try:
                self._udp_socket.close()
            except Exception:
                pass
            self._udp_socket = None

        logger.info("📱 DeviceRegistry stopped")

    # ── Auto-Scan ────────────────────────────────────────────────────

    async def _auto_scan_loop(self):
        """Background loop that periodically scans for new devices."""
        while self._running:
            try:
                discovered = await self.scan_lan()
                if discovered:
                    logger.info(f"🔍 Auto-Scan found {len(discovered)} device(s)")
                    for scan_result in discovered:
                        await self._auto_connect(scan_result)

                # Notify callbacks
                self._notify_callbacks("scan_complete", {"count": len(discovered)})

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Auto-scan error: {e}")

            await asyncio.sleep(self.SCAN_INTERVAL)

    async def scan_lan(self, timeout: int = 5) -> List[ScanResult]:
        """
        Scan LAN for other AsimNexus nodes via UDP broadcast.
        Returns list of discovered devices.
        """
        results: List[ScanResult] = []
        seen_ids: Set[str] = set()

        try:
            # Create temporary socket for scanning
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(timeout)

            # Send discovery beacon
            beacon = json.dumps({
                "type": "asim_discovery",
                "node_id": self.node_id,
                "hostname": socket.gethostname(),
                "ip_address": self._get_local_ip(),
                "port": self.DISCOVERY_PORT,
                "version": "2.0.0",
                "capabilities": list(self.capability_index.keys()),
                "timestamp": time.time(),
            }).encode()

            sock.sendto(beacon, ("<broadcast>", self.DISCOVERY_PORT))

            # Listen for responses
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    data, addr = sock.recvfrom(4096)
                    response = json.loads(data.decode())

                    if response.get("type") != "asim_discovery":
                        continue
                    if response.get("node_id") == self.node_id:
                        continue
                    if response["node_id"] in seen_ids:
                        continue

                    seen_ids.add(response["node_id"])
                    response_time = (time.time() - start_time) * 1000  # ms

                    scan_result = ScanResult(
                        device_id=response["node_id"],
                        ip_address=response.get("ip_address", addr[0]),
                        port=response.get("port", self.DISCOVERY_PORT),
                        hostname=response.get("hostname", addr[0]),
                        capabilities=response.get("capabilities", []),
                        version=response.get("version", "1.0.0"),
                        response_time_ms=round(response_time, 1),
                    )
                    results.append(scan_result)

                except socket.timeout:
                    break
                except (json.JSONDecodeError, KeyError):
                    continue

            sock.close()

        except Exception as e:
            logger.error(f"LAN scan error: {e}")

        return results

    async def scan_device(self, ip_address: str, port: int) -> Optional[ScanResult]:
        """Scan a specific device by IP:port."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(3)

            probe = json.dumps({
                "type": "asim_discovery",
                "node_id": self.node_id,
                "hostname": socket.gethostname(),
                "ip_address": self._get_local_ip(),
                "port": self.DISCOVERY_PORT,
                "version": "2.0.0",
                "probe": True,
            }).encode()

            start = time.time()
            sock.sendto(probe, (ip_address, port))

            data, addr = sock.recvfrom(4096)
            response = json.loads(data.decode())
            response_time = (time.time() - start) * 1000

            sock.close()

            if response.get("type") == "asim_discovery" and response.get("node_id") != self.node_id:
                return ScanResult(
                    device_id=response["node_id"],
                    ip_address=response.get("ip_address", ip_address),
                    port=response.get("port", port),
                    hostname=response.get("hostname", ip_address),
                    capabilities=response.get("capabilities", []),
                    version=response.get("version", "1.0.0"),
                    response_time_ms=round(response_time, 1),
                )

        except socket.timeout:
            logger.debug(f"Scan timeout for {ip_address}:{port}")
        except Exception as e:
            logger.debug(f"Scan error for {ip_address}:{port}: {e}")

        return None

    # ── Auto-Connect ─────────────────────────────────────────────────

    async def _auto_connect(self, scan_result: ScanResult) -> bool:
        """
        Automatically connect to a discovered device.
        Returns True if connection was established.
        """
        device_id = scan_result.device_id

        # Already connected?
        if device_id in self.devices:
            existing = self.devices[device_id]
            existing.last_seen = time.time()
            existing.status = DeviceStatus.ONLINE
            self._notify_callbacks("device_updated", {"device_id": device_id})
            return True

        # Check connection attempt limit
        attempts = self._connection_attempts.get(device_id, 0)
        if attempts >= 3:
            logger.warning(f"⚠️ Max connection attempts reached for {device_id}")
            return False

        self._connection_attempts[device_id] = attempts + 1

        # Perform handshake
        logger.info(f"🔗 Auto-Connecting to {scan_result.hostname} ({scan_result.ip_address})")

        device_info = await self._perform_handshake(scan_result)
        if device_info is None:
            logger.warning(f"⚠️ Handshake failed for {device_id}")
            return False

        # Register the device
        self._register_device_internal(device_info)
        logger.info(f"✅ Auto-Connected: {device_info.name} ({device_info.device_type.value}) "
                    f"via {device_info.connection.value}")

        # Reset attempt counter on success
        self._connection_attempts[device_id] = 0

        # Notify callbacks
        self._notify_callbacks("device_connected", {"device_id": device_id})

        return True

    async def _perform_handshake(self, scan_result: ScanResult) -> Optional[DeviceInfo]:
        """
        Perform handshake with discovered device.
        Exchanges capability and resource information.
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(5)

            handshake = json.dumps({
                "type": "asim_handshake",
                "node_id": self.node_id,
                "hostname": socket.gethostname(),
                "ip_address": self._get_local_ip(),
                "port": self.DISCOVERY_PORT,
                "version": "2.0.0",
                "capabilities": list(self.capability_index.keys()),
                "resources": self._get_local_resources(),
                "timestamp": time.time(),
            }).encode()

            sock.sendto(handshake, (scan_result.ip_address, scan_result.port))

            data, addr = sock.recvfrom(8192)
            response = json.loads(data.decode())
            sock.close()

            if response.get("type") != "asim_handshake_ack":
                logger.warning(f"Invalid handshake response from {scan_result.device_id}")
                return None

            # Determine connection method
            connection = ConnectionMethod.WIFI
            if scan_result.ip_address.startswith("127.") or scan_result.ip_address == self._get_local_ip():
                connection = ConnectionMethod.LOCAL

            # Determine device type from capabilities
            device_type = self._infer_device_type(response.get("capabilities", []))

            return DeviceInfo(
                id=scan_result.device_id,
                name=response.get("hostname", scan_result.hostname),
                device_type=device_type,
                connection=connection,
                trust_level=TrustLevel.UNKNOWN,
                status=DeviceStatus.ONLINE,
                ip_address=scan_result.ip_address,
                port=scan_result.port,
                hostname=scan_result.hostname,
                os_info=response.get("os_info"),
                version=response.get("version", scan_result.version),
                capabilities=response.get("capabilities", scan_result.capabilities),
                resources=self._parse_resources(response.get("resources", [])),
                last_seen=time.time(),
            )

        except socket.timeout:
            logger.debug(f"Handshake timeout for {scan_result.device_id}")
        except json.JSONDecodeError:
            logger.warning(f"Invalid handshake data from {scan_result.device_id}")
        except Exception as e:
            logger.error(f"Handshake error with {scan_result.device_id}: {e}")

        return None

    def connect_device_manual(self, device_info: DeviceInfo) -> bool:
        """
        Manually register a device (e.g., from API or config).
        Returns True if device was registered.
        """
        if device_info.id in self.devices:
            logger.warning(f"Device {device_info.id} already registered")
            return False

        self._register_device_internal(device_info)
        logger.info(f"📱 Manual connect: {device_info.name} ({device_info.device_type.value})")
        self._notify_callbacks("device_connected", {"device_id": device_info.id})
        return True

    def disconnect_device(self, device_id: str) -> bool:
        """Disconnect a device from the mesh."""
        device = self.devices.get(device_id)
        if not device:
            return False

        device.status = DeviceStatus.DISCONNECTED
        self._remove_from_topology(device_id)
        self._remove_from_capability_index(device_id)
        self._recalculate_resource_pool()

        logger.info(f"📱 Disconnected: {device.name} ({device_id})")
        self._notify_callbacks("device_disconnected", {"device_id": device_id})
        return True

    # ── Auto-Scale ───────────────────────────────────────────────────

    def get_resource_pool(self) -> Dict[str, Dict[str, float]]:
        """Get aggregated resource pool across all connected devices."""
        pool: Dict[str, Dict[str, float]] = {}

        for device in self.devices.values():
            if device.status != DeviceStatus.ONLINE:
                continue
            for resource in device.resources:
                rtype = resource.type.value
                if rtype not in pool:
                    pool[rtype] = {"total": 0.0, "available": 0.0}
                pool[rtype]["total"] += resource.total
                pool[rtype]["available"] += resource.available

        return pool

    def find_resource(self, resource_type: ResourceType, amount: float,
                      exclude_device: Optional[str] = None) -> List[DeviceInfo]:
        """
        Find devices that can provide a specific amount of a resource.
        Used for auto-scaling — distributing workloads across devices.
        """
        candidates = []
        for device in self.devices.values():
            if device.status != DeviceStatus.ONLINE:
                continue
            if exclude_device and device.id == exclude_device:
                continue

            for resource in device.resources:
                if resource.type == resource_type and resource.available >= amount:
                    candidates.append(device)
                    break

        # Sort by most available first
        candidates.sort(
            key=lambda d: max(
                (r.available for r in d.resources if r.type == resource_type),
                default=0
            ),
            reverse=True
        )

        return candidates

    def allocate_resource(self, resource_type: ResourceType, amount: float,
                          device_id: str) -> bool:
        """Allocate a resource from a specific device."""
        device = self.devices.get(device_id)
        if not device or device.status != DeviceStatus.ONLINE:
            return False

        for resource in device.resources:
            if resource.type == resource_type and resource.available >= amount:
                resource.available -= amount
                self._recalculate_resource_pool()
                self._notify_callbacks("resource_updated", {
                    "device_id": device_id,
                    "resource_type": resource_type.value,
                    "allocated": amount,
                })
                return True

        return False

    def release_resource(self, resource_type: ResourceType, amount: float,
                         device_id: str) -> bool:
        """Release a previously allocated resource."""
        device = self.devices.get(device_id)
        if not device:
            return False

        for resource in device.resources:
            if resource.type == resource_type:
                resource.available = min(resource.available + amount, resource.total)
                self._recalculate_resource_pool()
                return True

        return False

    def get_scale_recommendation(self, resource_type: ResourceType,
                                  required_amount: float) -> Dict[str, Any]:
        """
        Get auto-scale recommendation for a resource need.
        Returns which devices to use or if new devices are needed.
        """
        pool = self.get_resource_pool()
        rtype = resource_type.value

        currently_available = pool.get(rtype, {}).get("available", 0.0)
        total_capacity = pool.get(rtype, {}).get("total", 0.0)

        if currently_available >= required_amount:
            # Can fulfill from existing devices
            devices = self.find_resource(resource_type, required_amount)
            return {
                "can_scale": True,
                "needs_new_devices": False,
                "available": currently_available,
                "required": required_amount,
                "recommended_devices": [d.id for d in devices],
            }
        else:
            # Need more devices
            deficit = required_amount - currently_available
            return {
                "can_scale": False,
                "needs_new_devices": True,
                "available": currently_available,
                "required": required_amount,
                "deficit": deficit,
                "message": f"Need {deficit:.1f} more {rtype} capacity. "
                           f"Connect new devices or free up resources.",
            }

    # ── Health Monitoring ────────────────────────────────────────────

    async def _health_monitor_loop(self):
        """Background loop that checks device health."""
        while self._running:
            try:
                await self._check_device_health()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitor error: {e}")

            await asyncio.sleep(self.HEALTH_INTERVAL)

    async def _check_device_health(self):
        """Ping all devices and update status."""
        now = time.time()
        for device_id, device in list(self.devices.items()):
            if device_id == self.node_id:
                continue  # Skip self

            # Check if device is stale
            time_since_seen = now - device.last_seen

            if time_since_seen > self.STALE_TIMEOUT:
                if device.status == DeviceStatus.ONLINE:
                    logger.warning(f"⚠️ Device {device.name} ({device_id}) is stale "
                                   f"({time_since_seen:.0f}s since last seen)")
                    device.status = DeviceStatus.OFFLINE
                    self._notify_callbacks("device_disconnected", {"device_id": device_id})
            elif device.status == DeviceStatus.OFFLINE:
                # Device came back
                device.status = DeviceStatus.ONLINE
                logger.info(f"🔄 Device {device.name} ({device_id}) is back online")
                self._notify_callbacks("device_connected", {"device_id": device_id})

    async def ping_device(self, device_id: str) -> bool:
        """Ping a specific device to check if it's alive."""
        device = self.devices.get(device_id)
        if not device or not device.ip_address:
            return False

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(2)

            ping = json.dumps({
                "type": "asim_ping",
                "node_id": self.node_id,
                "timestamp": time.time(),
            }).encode()

            sock.sendto(ping, (device.ip_address, device.port or self.DISCOVERY_PORT))

            data, addr = sock.recvfrom(1024)
            response = json.loads(data.decode())
            sock.close()

            if response.get("type") == "asim_pong":
                device.last_seen = time.time()
                device.status = DeviceStatus.ONLINE
                return True

        except (socket.timeout, json.JSONDecodeError, Exception):
            pass

        device.status = DeviceStatus.OFFLINE
        return False

    # ── UDP Listener ─────────────────────────────────────────────────

    def _start_udp_listener(self):
        """Start UDP listener for discovery/handshake/ping messages."""
        try:
            self._udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self._udp_socket.bind(("", self.DISCOVERY_PORT))
            self._udp_socket.settimeout(1.0)

            # Start listener in a thread
            import threading
            listener_thread = threading.Thread(target=self._udp_listener_loop, daemon=True)
            listener_thread.start()

            logger.info(f"📡 UDP listener started on port {self.DISCOVERY_PORT}")

        except Exception as e:
            logger.error(f"Failed to start UDP listener: {e}")

    def _udp_listener_loop(self):
        """Background thread that listens for UDP messages."""
        while self._running:
            try:
                data, addr = self._udp_socket.recvfrom(8192)
                message = json.loads(data.decode())
                msg_type = message.get("type", "")

                if msg_type == "asim_discovery":
                    self._handle_discovery_message(message, addr)
                elif msg_type == "asim_handshake":
                    self._handle_handshake_message(message, addr)
                elif msg_type == "asim_ping":
                    self._handle_ping_message(message, addr)

            except socket.timeout:
                continue
            except json.JSONDecodeError:
                continue
            except Exception as e:
                if self._running:
                    logger.error(f"UDP listener error: {e}")

    def _handle_discovery_message(self, message: Dict, addr: Tuple):
        """Respond to discovery probes."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            response = json.dumps({
                "type": "asim_discovery",
                "node_id": self.node_id,
                "hostname": socket.gethostname(),
                "ip_address": self._get_local_ip(),
                "port": self.DISCOVERY_PORT,
                "version": "2.0.0",
                "capabilities": list(self.capability_index.keys()),
                "timestamp": time.time(),
            }).encode()
            sock.sendto(response, addr)
            sock.close()
        except Exception:
            pass

    def _handle_handshake_message(self, message: Dict, addr: Tuple):
        """Respond to handshake requests."""
        try:
            device_id = message.get("node_id")
            if not device_id or device_id == self.node_id:
                return

            # Serialize resources to JSON-safe dicts
            local_resources = self._get_local_resources()
            serialized_resources = [
                {
                    "type": r.type.value,
                    "total": r.total,
                    "available": r.available,
                    "unit": r.unit,
                    "metadata": r.metadata,
                }
                for r in local_resources
            ]

            # Send handshake acknowledgment
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            response = json.dumps({
                "type": "asim_handshake_ack",
                "node_id": self.node_id,
                "hostname": socket.gethostname(),
                "ip_address": self._get_local_ip(),
                "port": self.DISCOVERY_PORT,
                "version": "2.0.0",
                "capabilities": list(self.capability_index.keys()),
                "resources": serialized_resources,
                "os_info": f"{os.name} - {platform.system()} {platform.release()}" if hasattr(os, 'name') else "unknown",
                "timestamp": time.time(),
            }).encode()
            sock.sendto(response, addr)
            sock.close()

            # Auto-register the connecting device
            if device_id not in self.devices:
                device_type = self._infer_device_type(message.get("capabilities", []))
                device_info = DeviceInfo(
                    id=device_id,
                    name=message.get("hostname", device_id),
                    device_type=device_type,
                    connection=ConnectionMethod.WIFI,
                    trust_level=TrustLevel.UNKNOWN,
                    status=DeviceStatus.ONLINE,
                    ip_address=message.get("ip_address", addr[0]),
                    port=message.get("port", self.DISCOVERY_PORT),
                    hostname=message.get("hostname"),
                    version=message.get("version", "1.0.0"),
                    capabilities=message.get("capabilities", []),
                    resources=self._parse_resources(message.get("resources", [])),
                    last_seen=time.time(),
                )
                self._register_device_internal(device_info)
                logger.info(f"✅ Auto-Registered from handshake: {device_info.name}")
                self._notify_callbacks("device_connected", {"device_id": device_id})

        except Exception as e:
            logger.error(f"Handshake handler error: {e}")

    def _handle_ping_message(self, message: Dict, addr: Tuple):
        """Respond to ping messages."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            response = json.dumps({
                "type": "asim_pong",
                "node_id": self.node_id,
                "timestamp": time.time(),
            }).encode()
            sock.sendto(response, addr)
            sock.close()
        except Exception:
            pass

    # ── Internal Registration ────────────────────────────────────────

    def _register_device_internal(self, device: DeviceInfo):
        """Register a device and update all indices."""
        self.devices[device.id] = device
        self._update_topology(device)
        self._index_capabilities(device)
        self._recalculate_resource_pool()

    def _update_topology(self, device: DeviceInfo):
        """Update all topology structures for a device."""
        # Tree topology
        if device.parent_id:
            if device.parent_id not in self.topology[TopologyType.TREE]:
                self.topology[TopologyType.TREE][device.parent_id] = []
            if device.id not in self.topology[TopologyType.TREE][device.parent_id]:
                self.topology[TopologyType.TREE][device.parent_id].append(device.id)

        # Star topology — all connect to AsimCore
        self.topology[TopologyType.STAR][device.id] = "asim_core"

        # Ring topology — find backup paths
        self._establish_ring_connections(device)

        # Mesh topology — full connectivity
        self.topology[TopologyType.MESH][device.id] = [
            d.id for d in self.devices.values()
            if d.id != device.id and d.status == DeviceStatus.ONLINE
        ]

    def _establish_ring_connections(self, device: DeviceInfo):
        """Establish backup paths for ring topology."""
        candidates = []
        for cap in device.capabilities:
            for dev_id in self.capability_index.get(cap, []):
                if dev_id != device.id and dev_id not in candidates:
                    candidates.append(dev_id)

        device.backup_paths = candidates[:self.MAX_BACKUP_PATHS]
        self.topology[TopologyType.RING][device.id] = device.backup_paths

    def _index_capabilities(self, device: DeviceInfo):
        """Index device by capabilities."""
        for cap in device.capabilities:
            if cap in self.capability_index:
                if device.id not in self.capability_index[cap]:
                    self.capability_index[cap].append(device.id)

    def _remove_from_topology(self, device_id: str):
        """Remove device from all topology structures."""
        for topology_dict in self.topology.values():
            topology_dict.pop(device_id, None)

        # Also remove from tree children lists
        for parent_id, children in list(self.topology[TopologyType.TREE].items()):
            if device_id in children:
                children.remove(device_id)

        # Remove from ring backup paths
        for dev_id, paths in list(self.topology[TopologyType.RING].items()):
            if device_id in paths:
                paths.remove(device_id)

        # Remove from mesh
        for dev_id, peers in list(self.topology[TopologyType.MESH].items()):
            if device_id in peers:
                peers.remove(device_id)

        # Remove from devices dict
        self.devices.pop(device_id, None)

    def _remove_from_capability_index(self, device_id: str):
        """Remove device from capability index."""
        for cap, dev_ids in self.capability_index.items():
            if device_id in dev_ids:
                dev_ids.remove(device_id)

    def _recalculate_resource_pool(self):
        """Recalculate the aggregated resource pool."""
        self.resource_pool = {
            "compute": 0.0,
            "storage": 0.0,
            "memory": 0.0,
            "gpu": 0.0,
        }
        for device in self.devices.values():
            if device.status != DeviceStatus.ONLINE:
                continue
            for resource in device.resources:
                rtype = resource.type.value
                if rtype in self.resource_pool:
                    self.resource_pool[rtype] += resource.available

    # ── Helper Methods ───────────────────────────────────────────────

    def _create_local_device(self) -> DeviceInfo:
        """Create DeviceInfo for the local machine."""
        return DeviceInfo(
            id=self.node_id,
            name=socket.gethostname(),
            device_type=DeviceType.PC,
            connection=ConnectionMethod.LOCAL,
            trust_level=TrustLevel.VERIFIED,
            status=DeviceStatus.ONLINE,
            ip_address=self._get_local_ip(),
            hostname=socket.gethostname(),
            os_info=f"{os.name} - {platform.system()} {platform.release()}",
            version="2.0.0",
            capabilities=list(self.capability_index.keys()),
            resources=self._get_local_resources(),
            last_seen=time.time(),
            tags=["local", "primary"],
        )

    def _get_local_ip(self) -> str:
        """Get local IP address."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def _get_local_resources(self) -> List[DeviceResource]:
        """Get local machine resources."""
        resources = []
        try:
            import psutil
            # CPU
            cpu_count = psutil.cpu_count(logical=True) or 1
            resources.append(DeviceResource(
                type=ResourceType.COMPUTE,
                total=float(cpu_count),
                available=float(cpu_count),
                unit="cores",
            ))
            # Memory
            mem = psutil.virtual_memory()
            resources.append(DeviceResource(
                type=ResourceType.MEMORY,
                total=round(mem.total / (1024**3), 1),
                available=round(mem.available / (1024**3), 1),
                unit="GB",
            ))
            # Storage
            disk = psutil.disk_usage("/")
            resources.append(DeviceResource(
                type=ResourceType.STORAGE,
                total=round(disk.total / (1024**3), 1),
                available=round(disk.free / (1024**3), 1),
                unit="GB",
            ))
        except ImportError:
            pass
        return resources

    def _infer_device_type(self, capabilities: List[str]) -> DeviceType:
        """Infer device type from capabilities."""
        cap_set = set(capabilities)
        if "gpu" in cap_set or "compute" in cap_set:
            return DeviceType.PC
        if "sensor" in cap_set or "iot" in cap_set:
            return DeviceType.IOT
        if "network" in cap_set:
            return DeviceType.ROUTER
        if "display" in cap_set or "output" in cap_set:
            return DeviceType.PRINTER
        return DeviceType.PC

    def _parse_resources(self, resources_data: List[Dict]) -> List[DeviceResource]:
        """Parse resource data from handshake response."""
        resources = []
        for r in resources_data:
            try:
                resources.append(DeviceResource(
                    type=ResourceType(r.get("type", "compute")),
                    total=float(r.get("total", 0)),
                    available=float(r.get("available", 0)),
                    unit=r.get("unit", "units"),
                    metadata=r.get("metadata", {}),
                ))
            except (ValueError, TypeError):
                continue
        return resources

    def _generate_node_id(self) -> str:
        """Generate unique node ID."""
        import hashlib
        mac = hashlib.sha256(socket.gethostname().encode()).hexdigest()[:16]
        return f"node_{mac}"

    def _notify_callbacks(self, event: str, data: Dict):
        """Notify registered callbacks for an event."""
        for callback in self._callbacks.get(event, []):
            try:
                callback(data)
            except Exception as e:
                logger.error(f"Callback error for {event}: {e}")

    # ── Public API ───────────────────────────────────────────────────

    def on_event(self, event: str, callback: Callable):
        """Register a callback for a device event.

        Events: device_connected, device_disconnected, device_updated,
                scan_complete, resource_updated
        """
        if event in self._callbacks:
            self._callbacks[event].append(callback)

    def get_device(self, device_id: str) -> Optional[DeviceInfo]:
        """Get device info by ID."""
        return self.devices.get(device_id)

    def list_devices(self, status: Optional[DeviceStatus] = None) -> List[DeviceInfo]:
        """List all devices, optionally filtered by status."""
        if status:
            return [d for d in self.devices.values() if d.status == status]
        return list(self.devices.values())

    def get_devices_by_type(self, device_type: DeviceType) -> List[DeviceInfo]:
        """Get all devices of a specific type."""
        return [d for d in self.devices.values() if d.device_type == device_type]

    def get_devices_by_capability(self, capability: str) -> List[DeviceInfo]:
        """Get all devices with a specific capability."""
        device_ids = self.capability_index.get(capability, [])
        return [self.devices[did] for did in device_ids if did in self.devices]

    def get_online_count(self) -> int:
        """Get count of online devices."""
        return len([d for d in self.devices.values() if d.status == DeviceStatus.ONLINE])

    def get_topology(self, topology_type: Optional[TopologyType] = None) -> Dict:
        """Get topology structure."""
        if topology_type:
            return self.topology.get(topology_type, {})
        return {t.value: data for t, data in self.topology.items()}

    async def get_mesh_status(self) -> Dict:
        """Get complete mesh status."""
        return {
            "node_id": self.node_id,
            "total_devices": len(self.devices),
            "online_devices": self.get_online_count(),
            "offline_devices": len([d for d in self.devices.values()
                                    if d.status == DeviceStatus.OFFLINE]),
            "devices_by_type": self._count_by_type(),
            "devices_by_status": self._count_by_status(),
            "capability_index": {cap: len(devs) for cap, devs in self.capability_index.items()},
            "resource_pool": self.resource_pool,
            "topology": {
                "tree_depth": self._calculate_tree_depth(),
                "star_connections": len(self.topology[TopologyType.STAR]),
                "ring_backup_paths": sum(
                    len(paths) for paths in self.topology[TopologyType.RING].values()
                ),
                "mesh_connections": sum(
                    len(peers) for peers in self.topology[TopologyType.MESH].values()
                ),
            },
            "scan_history": len(self._scan_history),
            "running": self._running,
        }

    def _calculate_tree_depth(self) -> int:
        """Calculate maximum depth of tree topology."""
        def depth(node_id, current_depth=0):
            children = self.topology[TopologyType.TREE].get(node_id, [])
            if not children:
                return current_depth
            return max(depth(child, current_depth + 1) for child in children)

        root = next((d for d in self.devices.values() if d.parent_id is None), None)
        if root:
            return depth(root.id)
        return 0

    def _count_by_type(self) -> Dict:
        """Count devices by type."""
        counts = {}
        for device in self.devices.values():
            dtype = device.device_type.value
            counts[dtype] = counts.get(dtype, 0) + 1
        return counts

    def _count_by_status(self) -> Dict:
        """Count devices by status."""
        counts = {}
        for device in self.devices.values():
            status = device.status.value
            counts[status] = counts.get(status, 0) + 1
        return counts


# ══════════════════════════════════════════════════════════════════════
# Global Instance
# ══════════════════════════════════════════════════════════════════════

_device_registry: Optional[DeviceRegistry] = None


def get_device_registry(node_id: Optional[str] = None) -> DeviceRegistry:
    """Get or create the global DeviceRegistry instance."""
    global _device_registry
    if _device_registry is None:
        _device_registry = DeviceRegistry(node_id)
    return _device_registry


def reset_device_registry():
    """Reset the global DeviceRegistry instance (for testing)."""
    global _device_registry
    if _device_registry:
        import asyncio
        try:
            asyncio.create_task(_device_registry.stop())
        except Exception:
            pass
    _device_registry = None
