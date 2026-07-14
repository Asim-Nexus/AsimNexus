#!/usr/bin/env python3
"""
STATUS: REAL — Production-grade LAN device discovery with DeviceRegistry integration
ASIMNEXUS Auto Discovery
========================
LAN device discovery for mesh network.
Supports broadcast, multicast, and mDNS-based discovery.
Integrates with DeviceRegistry for auto-connect on discovery.
"""

import os
import socket
import json
import logging
import threading
import time
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import hashlib
import secrets

logger = logging.getLogger("AsimNexus.Mesh.AutoDiscovery")


class DiscoveryMethod(Enum):
    """Discovery methods."""
    BROADCAST = "broadcast"       # UDP broadcast
    MULTICAST = "multicast"       # UDP multicast
    MDNS = "mdns"                 # mDNS/Bonjour
    CONFIG = "config"             # Config-based (ASIM_SINGLE_MACHINE_PEERS)


@dataclass
class NodeInfo:
    """Information about a discovered node."""
    node_id: str
    hostname: str
    ip_address: str
    port: int
    capabilities: List[str] = field(default_factory=list)
    version: str = "1.0.0"
    last_seen: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


class AutoDiscovery:
    """
    LAN device discovery for mesh network.
    Discovers other AsimNexus nodes on the local network.
    Automatically registers discovered nodes with DeviceRegistry.
    """
    
    # Env var configurable defaults
    DISCOVERY_PORT = int(os.getenv("ASIM_MESH_DISCOVERY_PORT", "7331"))
    DISCOVERY_INTERVAL = int(os.getenv("ASIM_MESH_DISCOVERY_INTERVAL", "30"))  # seconds
    BEACON_INTERVAL = int(os.getenv("ASIM_MESH_BEACON_INTERVAL", "60"))  # seconds
    # Phase 1C: Single-machine config-based peer list
    # Format: "node_a:host:port_udp:port_ws,node_b:host:port_udp:port_ws"
    SINGLE_MACHINE_PEERS = os.getenv("ASIM_SINGLE_MACHINE_PEERS", "")
    
    def __init__(self, node_id: Optional[str] = None, port: int = 8000,
                 device_registry: Optional[Any] = None):
        self.node_id = node_id or self._generate_node_id()
        self.port = port
        self.hostname = socket.gethostname()
        self.ip_address = self._get_local_ip()
        
        self.discovered_nodes: Dict[str, NodeInfo] = {}
        self.discovery_callbacks: List[Callable[[NodeInfo], None]] = []
        self._device_registry = device_registry
        self._running = False
        self._socket: Optional[socket.socket] = None
        self._beacon_thread: Optional[threading.Thread] = None
        self._listener_thread: Optional[threading.Thread] = None
        
        logger.info(f"🔍 AutoDiscovery initialized - Node: {self.node_id}, IP: {self.ip_address}")
    
    def set_device_registry(self, registry: Any):
        """Set the DeviceRegistry instance for auto-connect integration."""
        self._device_registry = registry
        logger.info("🔗 AutoDiscovery linked to DeviceRegistry")
    
    def _generate_node_id(self) -> str:
        """Generate unique node ID."""
        mac = hashlib.sha256(socket.gethostname().encode()).hexdigest()[:16]
        return f"node_{mac}"
    
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
    
    def get_node_info(self) -> NodeInfo:
        """Get current node information."""
        return NodeInfo(
            node_id=self.node_id,
            hostname=self.hostname,
            ip_address=self.ip_address,
            port=self.port,
            capabilities=["chat", "memory", "clones", "mesh", "compute", "storage"],
            version="2.0.0"
        )
    
    def _is_localhost(self) -> bool:
        """Check if we are running on localhost (single-machine mode)."""
        return self.ip_address in ("127.0.0.1", "::1", "localhost", "0.0.0.0")

    def _discover_from_env(self) -> List[NodeInfo]:
        """
        Parse ASIM_SINGLE_MACHINE_PEERS env var and return discovered NodeInfo list.
        Format: "node_a:127.0.0.1:17332:17333,node_b:127.0.0.1:17334:17335"
        """
        peer_spec = self.SINGLE_MACHINE_PEERS
        if not peer_spec:
            return []
        
        discovered: List[NodeInfo] = []
        for entry in peer_spec.split(","):
            entry = entry.strip()
            if not entry:
                continue
            parts = entry.split(":")
            if len(parts) < 4:
                logger.warning(f"Malformed peer entry in ASIM_SINGLE_MACHINE_PEERS: {entry}")
                continue
            node_id = parts[0].strip()
            host = parts[1].strip()
            try:
                port_udp = int(parts[2])
                port_ws = int(parts[3])
            except ValueError:
                logger.warning(f"Invalid port in ASIM_SINGLE_MACHINE_PEERS entry: {entry}")
                continue
            
            node_info = NodeInfo(
                node_id=node_id,
                hostname=node_id,
                ip_address=host,
                port=port_udp,
                capabilities=["chat", "memory", "clones", "mesh", "compute", "storage"],
                version="2.0.0",
                metadata={"port_ws": port_ws, "source": "ASIM_SINGLE_MACHINE_PEERS"}
            )
            discovered.append(node_info)
            # Immediately trigger discovery callback
            self._on_node_discovered(node_info)
        
        if discovered:
            logger.info(f"📋 Discovered {len(discovered)} peer(s) from ASIM_SINGLE_MACHINE_PEERS")
        return discovered

    def start(self, method: DiscoveryMethod = DiscoveryMethod.BROADCAST):
        """Start discovery service."""
        if self._running:
            logger.warning("AutoDiscovery already running")
            return
        
        self._running = True
        
        # Phase 1C: On localhost, short-circuit broadcast/multicast/mDNS
        # Windows loopback doesn't support broadcast discovery
        if self._is_localhost() and method in (DiscoveryMethod.BROADCAST,
                                                 DiscoveryMethod.MULTICAST,
                                                 DiscoveryMethod.MDNS):
            logger.info(
                f"🔍 Localhost detected ({self.ip_address}) — "
                f"short-circuiting {method.value} discovery, using CONFIG instead"
            )
            # Still try env-based discovery first
            self._discover_from_env()
            logger.info(
                f"🔍 AutoDiscovery started (method: {DiscoveryMethod.CONFIG.value}, "
                f"localhost shortcut)"
            )
            return
        
        # Try env-based discovery regardless of method (adds configured peers)
        self._discover_from_env()
        
        if method == DiscoveryMethod.BROADCAST:
            self._start_broadcast_discovery()
        elif method == DiscoveryMethod.MULTICAST:
            self._start_multicast_discovery()
        elif method == DiscoveryMethod.MDNS:
            self._start_mdns_discovery()
        elif method == DiscoveryMethod.CONFIG:
            logger.info("🔍 Config-based discovery — no broadcast threads needed")
        
        logger.info(f"🔍 AutoDiscovery started (method: {method.value})")
    
    def stop(self):
        """Stop discovery service."""
        self._running = False
        
        if self._socket:
            try:
                self._socket.close()
            except Exception:
                pass
        
        if self._beacon_thread:
            self._beacon_thread.join(timeout=2)
        
        if self._listener_thread:
            self._listener_thread.join(timeout=2)
        
        logger.info("🔍 AutoDiscovery stopped")
    
    def _start_broadcast_discovery(self):
        """Start UDP broadcast discovery."""
        if self._is_localhost():
            logger.warning("Broadcast discovery skipped — localhost detected")
            return
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind(("", self.DISCOVERY_PORT))
        
        # Start listener thread
        self._listener_thread = threading.Thread(target=self._broadcast_listener, daemon=True)
        self._listener_thread.start()
        
        # Start beacon thread
        self._beacon_thread = threading.Thread(target=self._broadcast_beacon, daemon=True)
        self._beacon_thread.start()
    
    def _broadcast_listener(self):
        """Listen for broadcast discovery messages."""
        while self._running:
            try:
                self._socket.settimeout(1.0)
                data, addr = self._socket.recvfrom(4096)
                
                try:
                    message = json.loads(data.decode())
                    
                    # Ignore messages from self
                    if message.get("node_id") == self.node_id:
                        continue
                    
                    # Process discovered node
                    node_info = NodeInfo(
                        node_id=message["node_id"],
                        hostname=message["hostname"],
                        ip_address=message["ip_address"],
                        port=message["port"],
                        capabilities=message.get("capabilities", []),
                        version=message.get("version", "1.0.0"),
                        metadata=message.get("metadata", {})
                    )
                    
                    self._on_node_discovered(node_info)
                    
                except json.JSONDecodeError:
                    logger.warning(f"Invalid discovery message from {addr}")
                except Exception as e:
                    logger.error(f"Error processing discovery message: {e}")
                    
            except socket.timeout:
                continue
            except Exception as e:
                if self._running:
                    logger.error(f"Broadcast listener error: {e}")
                break
    
    def _broadcast_beacon(self):
        """Send periodic broadcast beacons."""
        while self._running:
            try:
                node_info = self.get_node_info()
                message = asdict(node_info)
                
                self._socket.sendto(
                    json.dumps(message).encode(),
                    ("<broadcast>", self.DISCOVERY_PORT)
                )
                
                logger.debug(f"📡 Sent beacon to <broadcast>")
                
            except Exception as e:
                if self._running:
                    logger.error(f"Broadcast beacon error: {e}")
            
            time.sleep(self.BEACON_INTERVAL)
    
    def _start_multicast_discovery(self):
        """Start UDP multicast discovery."""
        MULTICAST_GROUP = "239.255.255.250"
        
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind(("", self.DISCOVERY_PORT))
        
        # Join multicast group
        mreq = socket.inet_aton(MULTICAST_GROUP) + socket.inet_aton(self.ip_address)
        self._socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        
        # Start listener thread
        self._listener_thread = threading.Thread(target=self._multicast_listener, daemon=True)
        self._listener_thread.start()
        
        # Start beacon thread
        self._beacon_thread = threading.Thread(target=self._multicast_beacon, daemon=True, args=(MULTICAST_GROUP,))
        self._beacon_thread.start()
    
    def _multicast_listener(self):
        """Listen for multicast discovery messages."""
        while self._running:
            try:
                self._socket.settimeout(1.0)
                data, addr = self._socket.recvfrom(4096)
                
                try:
                    message = json.loads(data.decode())
                    
                    # Ignore messages from self
                    if message.get("node_id") == self.node_id:
                        continue
                    
                    node_info = NodeInfo(
                        node_id=message["node_id"],
                        hostname=message["hostname"],
                        ip_address=message["ip_address"],
                        port=message["port"],
                        capabilities=message.get("capabilities", []),
                        version=message.get("version", "1.0.0"),
                        metadata=message.get("metadata", {})
                    )
                    
                    self._on_node_discovered(node_info)
                    
                except json.JSONDecodeError:
                    logger.warning(f"Invalid discovery message from {addr}")
                except Exception as e:
                    logger.error(f"Error processing discovery message: {e}")
                    
            except socket.timeout:
                continue
            except Exception as e:
                if self._running:
                    logger.error(f"Multicast listener error: {e}")
                break
    
    def _multicast_beacon(self, multicast_group: str):
        """Send periodic multicast beacons."""
        while self._running:
            try:
                node_info = self.get_node_info()
                message = asdict(node_info)
                
                self._socket.sendto(
                    json.dumps(message).encode(),
                    (multicast_group, self.DISCOVERY_PORT)
                )
                
                logger.debug(f"📡 Sent beacon to {multicast_group}")
                
            except Exception as e:
                if self._running:
                    logger.error(f"Multicast beacon error: {e}")
            
            time.sleep(self.BEACON_INTERVAL)
    
    def _start_mdns_discovery(self):
        """Start mDNS/Bonjour discovery."""
        if self._is_localhost():
            logger.warning("mDNS discovery skipped — localhost detected")
            return
        try:
            from zeroconf import ServiceBrowser, Zeroconf
            from zeroconf import ServiceListener
            
            class AsimNexusListener(ServiceListener):
                def __init__(self, discovery):
                    self.discovery = discovery
                
                def add_service(self, zc, type_, name):
                    info = zc.get_service_info(type_, name)
                    if info:
                        node_info = NodeInfo(
                            node_id=name.split('.')[0],
                            hostname=info.server,
                            ip_address=socket.inet_ntoa(info.addresses[0]),
                            port=info.port,
                            capabilities=["mdns"],
                            version="2.0.0"
                        )
                        self.discovery._on_node_discovered(node_info)
                
                def remove_service(self, zc, type_, name):
                    pass
                
                def update_service(self, zc, type_, name):
                    pass
            
            self._zeroconf = Zeroconf()
            listener = AsimNexusListener(self)
            
            # Register our own service
            node_info = self.get_node_info()
            from zeroconf import ServiceInfo
            info = ServiceInfo(
                "_asimnexus._tcp.local.",
                f"{self.node_id}._asimnexus._tcp.local.",
                addresses=[socket.inet_aton(self.ip_address)],
                port=self.port,
                properties=json.dumps(asdict(node_info))
            )
            self._zeroconf.register_service(info)
            
            # Browse for other services
            browser = ServiceBrowser(self._zeroconf, "_asimnexus._tcp.local.", listener)
            
            logger.info("🔍 mDNS discovery started")
            
        except ImportError:
            logger.warning("⚠️  zeroconf not installed, falling back to broadcast")
            self._start_broadcast_discovery()
        except Exception as e:
            logger.error(f"mDNS discovery error: {e}, falling back to broadcast")
            self._start_broadcast_discovery()
    
    def _on_node_discovered(self, node_info: NodeInfo):
        """Handle discovered node — updates local cache and triggers auto-connect."""
        # Update last seen
        node_info.last_seen = datetime.utcnow().isoformat()
        
        # Check if new or updated
        existing = self.discovered_nodes.get(node_info.node_id)
        if existing:
            existing.last_seen = node_info.last_seen
            existing.ip_address = node_info.ip_address
            existing.port = node_info.port
            logger.debug(f"🔄 Updated node: {node_info.node_id}")
        else:
            self.discovered_nodes[node_info.node_id] = node_info
            logger.info(f"✅ Discovered new node: {node_info.node_id} ({node_info.ip_address}:{node_info.port})")
            
            # Auto-register with DeviceRegistry if available
            if self._device_registry is not None:
                try:
                    from core.mesh.device_registry import (
                        DeviceInfo, DeviceType, ConnectionMethod,
                        TrustLevel, DeviceStatus
                    )
                    device_info = DeviceInfo(
                        id=node_info.node_id,
                        name=node_info.hostname,
                        device_type=DeviceType.PC,
                        connection=ConnectionMethod.WIFI,
                        trust_level=TrustLevel.UNKNOWN,
                        status=DeviceStatus.ONLINE,
                        ip_address=node_info.ip_address,
                        port=node_info.port,
                        hostname=node_info.hostname,
                        version=node_info.version,
                        capabilities=node_info.capabilities,
                        last_seen=time.time(),
                    )
                    self._device_registry.connect_device_manual(device_info)
                    logger.info(f"🔗 Auto-registered {node_info.node_id} with DeviceRegistry")
                except Exception as e:
                    logger.error(f"Failed to auto-register with DeviceRegistry: {e}")
            
            # Notify callbacks
            for callback in self.discovery_callbacks:
                try:
                    callback(node_info)
                except Exception as e:
                    logger.error(f"Discovery callback error: {e}")
    
    def on_discovery(self, callback: Callable[[NodeInfo], None]):
        """Register callback for node discovery events."""
        self.discovery_callbacks.append(callback)
    
    def get_discovered_nodes(self) -> List[NodeInfo]:
        """Get all discovered nodes."""
        return list(self.discovered_nodes.values())
    
    def discover_once(self, timeout: Optional[int] = None) -> List[NodeInfo]:
        """Perform one-time discovery scan."""
        timeout = timeout if timeout is not None else int(os.getenv("ASIM_MESH_DISCOVERY_TIMEOUT", "5"))
        # Send discovery ping
        node_info = self.get_node_info()
        message = asdict(node_info)
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(timeout)
            
            sock.sendto(
                json.dumps(message).encode(),
                ("<broadcast>", self.DISCOVERY_PORT)
            )
            
            # Listen for responses
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    data, addr = sock.recvfrom(4096)
                    
                    try:
                        response = json.loads(data.decode())
                        
                        if response.get("node_id") != self.node_id:
                            node_info = NodeInfo(
                                node_id=response["node_id"],
                                hostname=response["hostname"],
                                ip_address=response["ip_address"],
                                port=response["port"],
                                capabilities=response.get("capabilities", []),
                                version=response.get("version", "1.0.0"),
                                metadata=response.get("metadata", {})
                            )
                            self._on_node_discovered(node_info)
                            
                    except json.JSONDecodeError:
                        pass
                        
                except socket.timeout:
                    break
            
            sock.close()
            
        except Exception as e:
            logger.error(f"One-time discovery error: {e}")
        
        return self.get_discovered_nodes()
    
    def cleanup_stale_nodes(self, max_age_seconds: Optional[int] = None):
        """Remove nodes not seen recently."""
        max_age = max_age_seconds if max_age_seconds is not None else int(os.getenv("ASIM_MESH_STALE_NODE_AGE", "300"))
        cutoff = (datetime.utcnow().timestamp() - max_age)
        stale_nodes = []
        
        for node_id, node in list(self.discovered_nodes.items()):
            try:
                last_seen = datetime.fromisoformat(node.last_seen).timestamp()
                if last_seen < cutoff:
                    stale_nodes.append(node_id)
                    del self.discovered_nodes[node_id]
                    logger.info(f"🗑️  Removed stale node: {node_id}")
                    
                    # Also disconnect from DeviceRegistry
                    if self._device_registry is not None:
                        try:
                            self._device_registry.disconnect_device(node_id)
                        except Exception:
                            pass
            except Exception:
                pass
        
        return stale_nodes

    def get_single_machine_peers(self) -> List[NodeInfo]:
        """
        Parse and return peers from ASIM_SINGLE_MACHINE_PEERS env var.
        Convenience wrapper around _discover_from_env() for external callers.
        
        Returns:
            List of NodeInfo for peers defined in the environment variable.
        """
        return self._discover_from_env()


# Global auto discovery instance
_auto_discovery: Optional[AutoDiscovery] = None


def get_auto_discovery(node_id: Optional[str] = None, port: int = 8000,
                       device_registry: Optional[Any] = None) -> AutoDiscovery:
    """Get or create global auto discovery instance."""
    global _auto_discovery
    if _auto_discovery is None:
        _auto_discovery = AutoDiscovery(node_id, port, device_registry)
    elif device_registry is not None:
        _auto_discovery.set_device_registry(device_registry)
    return _auto_discovery


def reset_auto_discovery():
    """Reset global auto discovery instance (for testing)."""
    global _auto_discovery
    if _auto_discovery:
        _auto_discovery.stop()
    _auto_discovery = None
