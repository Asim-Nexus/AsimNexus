#!/usr/bin/env python3
"""
STATUS: REAL — P2P Integration Bridge
ASIMNEXUS P2P Transport ↔ MultiMeshRouter Integration
=====================================================
Bridges P2PTransport with MultiMeshRouter so that route_through_mesh()
actually sends data via the P2P transport layer. Also provides:
- Health checker registration for all 4 mesh types
- Automatic peer discovery via NodeRegistry
- Kademlia DHT integration for distributed routing
- CRDT sync for conflict-free data replication
- Bootstrap service integration for peer discovery
- WebRTC transport support (optional, via aiortc)
- Mesh-level metrics aggregation
"""

import os
import time
import json
import logging
import asyncio
import socket
import hashlib
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum

from mesh.multi_mesh_router import (
    MeshType,
    MeshProfile,
    MultiMeshRouter,
    get_multi_mesh_router,
)
from mesh.p2p_transport import (
    P2PTransport,
    P2PMessage,
    PeerInfo,
    get_p2p_transport,
)
from mesh.node_registry import NodeRegistry, TrustLevel, NodeStatus, get_node_registry
from mesh.kademlia_dht import KademliaDHT, get_kademlia_dht
from mesh.crdt_sync import CRDTStore, get_crdt_store
from mesh.bootstrap import BootstrapService, get_bootstrap_service
from core.event_bus import event_bus, ASIMEvent, EventType

logger = logging.getLogger("AsimNexus.Mesh.P2PIntegration")

# ─── Environment Configuration ────────────────────────────────────────────────
_PEER_DISCOVERY_INTERVAL = int(os.getenv("ASIM_P2P_PEER_DISCOVERY_INTERVAL", "60"))
_HEALTH_PING_INTERVAL = int(os.getenv("ASIM_P2P_HEALTH_PING_INTERVAL", "30"))
_MAX_PEERS_PER_MESH = int(os.getenv("ASIM_P2P_MAX_PEERS_PER_MESH", "50"))


# ─── WebRTC Transport (Optional) ──────────────────────────────────────────────

try:
    from aiortc import RTCPeerConnection, RTCSessionDescription, RTCDataChannel
    AIORTC_AVAILABLE = True
except ImportError:
    AIORTC_AVAILABLE = False


@dataclass
class WebRTCPeerConnection:
    """Manages a WebRTC peer connection for mesh transport."""
    peer_id: str
    connection: Optional[Any] = None  # RTCPeerConnection
    data_channel: Optional[Any] = None  # RTCDataChannel
    mesh_type: MeshType = MeshType.PUBLIC
    connected: bool = False
    created_at: float = field(default_factory=time.time)
    bytes_sent: int = 0
    bytes_received: int = 0


class WebRTCTransport:
    """
    WebRTC data channel transport for mesh networking.
    Falls back gracefully if aiortc is not installed.

    Uses browser-compatible WebRTC for P2P data channels.
    Best suited for PUBLIC mesh where nodes may be in browsers.
    """

    def __init__(self, node_id: str):
        self.node_id = node_id
        self._connections: Dict[str, WebRTCPeerConnection] = {}
        self._available = AIORTC_AVAILABLE

        if not self._available:
            logger.info(
                "📡 WebRTC transport unavailable (install aiortc for WebRTC support)"
            )

    @property
    def is_available(self) -> bool:
        return self._available

    async def connect(
        self,
        peer_id: str,
        peer_host: str,
        peer_port: int,
        mesh_type: MeshType = MeshType.PUBLIC,
    ) -> bool:
        """
        Establish a WebRTC data channel connection to a peer.
        Falls back to a simulated connection if aiortc is unavailable.
        """
        if not self._available:
            logger.debug(
                f"WebRTC connect to {peer_id} skipped (aiortc not available)"
            )
            # Register as simulated connection for stats
            wc = WebRTCPeerConnection(
                peer_id=peer_id,
                mesh_type=mesh_type,
                connected=False,
            )
            self._connections[peer_id] = wc
            return False

        try:
            pc = RTCPeerConnection()
            dc = pc.createDataChannel("asim-mesh")

            wc = WebRTCPeerConnection(
                peer_id=peer_id,
                connection=pc,
                data_channel=dc,
                mesh_type=mesh_type,
            )

            @dc.on("open")
            def on_open():
                wc.connected = True
                logger.info(f"📡 WebRTC data channel open to {peer_id}")

            @dc.on("message")
            def on_message(message):
                wc.bytes_received += len(message)

            @dc.on("close")
            def on_close():
                wc.connected = False
                logger.info(f"📡 WebRTC data channel closed to {peer_id}")

            # Create offer
            offer = await pc.createOffer()
            await pc.setLocalDescription(offer)

            # In production, this would be exchanged via signaling server
            self._connections[peer_id] = wc
            logger.info(f"📡 WebRTC connecting to {peer_id} at {peer_host}:{peer_port}")
            return True

        except Exception as e:
            logger.warning(f"WebRTC connect to {peer_id} failed: {e}")
            return False

    async def send(self, peer_id: str, data: bytes) -> bool:
        """Send data over a WebRTC data channel."""
        wc = self._connections.get(peer_id)
        if not wc or not wc.connected or not wc.data_channel:
            return False

        try:
            wc.data_channel.send(data)
            wc.bytes_sent += len(data)
            return True
        except Exception as e:
            logger.debug(f"WebRTC send to {peer_id} failed: {e}")
            return False

    async def disconnect(self, peer_id: str) -> None:
        """Close a WebRTC connection."""
        wc = self._connections.pop(peer_id, None)
        if wc and wc.connection:
            try:
                await wc.connection.close()
            except Exception:
                pass

    def get_connected_peers(self) -> List[str]:
        """Get list of peer IDs with active WebRTC connections."""
        return [
            pid for pid, wc in self._connections.items()
            if wc.connected
        ]

    def get_stats(self) -> Dict[str, Any]:
        """Get WebRTC transport statistics."""
        connected = len(self.get_connected_peers())
        total_bytes_sent = sum(wc.bytes_sent for wc in self._connections.values())
        total_bytes_recv = sum(wc.bytes_received for wc in self._connections.values())
        return {
            "available": self._available,
            "connections_total": len(self._connections),
            "connections_active": connected,
            "bytes_sent": total_bytes_sent,
            "bytes_received": total_bytes_recv,
        }


# ─── P2P Integration Bridge ───────────────────────────────────────────────────

class P2PIntegration:
    """
    Bridges P2PTransport with MultiMeshRouter.

    Responsibilities:
    1. Register health checkers for each mesh type
    2. Discover peers via NodeRegistry per mesh type
    3. Wire route_through_mesh() to actual P2PTransport send methods
    4. Aggregate peer connectivity stats into mesh profiles
    5. Provide optional WebRTC transport alongside UDP/WS
    """

    def __init__(
        self,
        node_id: Optional[str] = None,
        enable_webrtc: bool = False,
        kademlia_dht: Optional['KademliaDHT'] = None,
        crdt_store: Optional['CRDTStore'] = None,
        bootstrap_service: Optional['BootstrapService'] = None,
    ):
        self.node_id = node_id or f"p2p_node_{os.urandom(4).hex()}"

        # Core components
        self._p2p: P2PTransport = get_p2p_transport(self.node_id)
        self._router: MultiMeshRouter = get_multi_mesh_router()
        self._registry: NodeRegistry = get_node_registry()

        # Optional mesh components
        self._dht: Optional[KademliaDHT] = kademlia_dht
        self._crdt: Optional[CRDTStore] = crdt_store
        self._bootstrap: Optional[BootstrapService] = bootstrap_service

        # WebRTC transport (optional)
        self._webrtc: Optional[WebRTCTransport] = None
        if enable_webrtc:
            self._webrtc = WebRTCTransport(self.node_id)

        # Peer-to-mesh mapping
        self._peer_mesh_map: Dict[str, MeshType] = {}

        # Mesh-specific peer caches
        self._mesh_peers: Dict[MeshType, List[str]] = {
            mt: [] for mt in MeshType
        }

        # Background tasks
        self._running = False
        self._discovery_task: Optional[asyncio.Task] = None
        self._health_task: Optional[asyncio.Task] = None

        # Health checkers registered flag
        self._health_checkers_registered = False

        logger.info(
            f"🔌 P2PIntegration initialized — Node: {self.node_id}, "
            f"WebRTC: {'enabled' if enable_webrtc else 'disabled'}, "
            f"DHT: {'yes' if kademlia_dht else 'no'}, "
            f"CRDT: {'yes' if crdt_store else 'no'}, "
            f"Bootstrap: {'yes' if bootstrap_service else 'no'}"
        )

    # ─── Lifecycle ────────────────────────────────────────────────────────────

    async def start(self) -> None:
        """Start the P2P integration layer."""
        if self._running:
            return
        self._running = True

        # Start P2P transport
        await self._p2p.start()

        # Start Kademlia DHT on the same transport
        if self._dht is not None:
            await self._dht.start(self._p2p)
            logger.info("🔗 Kademlia DHT started on P2P transport")

        # Start CRDT Store on the same transport
        if self._crdt is not None:
            await self._crdt.start(self._p2p)
            logger.info("🔗 CRDT Store started on P2P transport")

        # Bootstrap discovery — feed discovered peers into DHT
        if self._bootstrap is not None:
            await self._bootstrap.discover_and_connect(self._p2p, dht=self._dht)
            logger.info("🔗 Bootstrap discovery complete — peers fed into DHT")

        # Register health checkers with MultiMeshRouter
        self._register_health_checkers()

        # Register with NodeRegistry
        self._registry.register_node(
            node_id=self.node_id,
            hostname=socket.gethostname(),
            ip_address=self._p2p.host,
            port=self._p2p.port_ws,
            capabilities=["p2p_transport", "mesh_relay", "kademlia_dht", "crdt_sync"],
        )

        # Start background tasks
        loop = asyncio.get_event_loop()
        self._discovery_task = loop.create_task(self._peer_discovery_loop())
        self._health_task = loop.create_task(self._health_ping_loop())

        logger.info(f"🔌 P2PIntegration started — Node: {self.node_id}")
        # Subscribe to transport events for mesh health tracking
        event_bus.subscribe(EventType.PEER_CONNECTED, self._on_peer_connected)
        event_bus.subscribe(EventType.PEER_DISCONNECTED, self._on_peer_disconnected)


    async def stop(self) -> None:
        """Stop the P2P integration layer."""
        self._running = False

        if self._discovery_task:
            self._discovery_task.cancel()
            try:
                await self._discovery_task
            except asyncio.CancelledError:
                pass

        if self._health_task:
            self._health_task.cancel()
            try:
                await self._health_task
            except asyncio.CancelledError:
                pass

        # Stop CRDT Store (sync flush)
        if self._crdt is not None:
            await self._crdt.stop()
            logger.info("🔄 CRDT Store stopped")

        # Stop Kademlia DHT
        if self._dht is not None:
            await self._dht.stop()
            logger.info("📡 Kademlia DHT stopped")

        await self._p2p.stop()
        # Unsubscribe from transport events
        event_bus.unsubscribe(EventType.PEER_CONNECTED, self._on_peer_connected)
        event_bus.unsubscribe(EventType.PEER_DISCONNECTED, self._on_peer_disconnected)

        logger.info(f"🔌 P2PIntegration stopped — Node: {self.node_id}")


    # ─── Event Handlers ──────────────────────────────

    async def _on_peer_connected(self, event: ASIMEvent) -> None:
        """Handle peer connected event — update mesh health."""
        peer_id = event.data.get("peer_id", "")
        if peer_id:
            mesh_type = self._peer_mesh_map.get(peer_id, MeshType.PUBLIC)
            self._router.update_mesh_health(
                mesh_type=mesh_type,
                is_connected=True,
                peers=len(self._mesh_peers.get(mesh_type, [])),
            )
            logger.info(f"🔗 Peer {peer_id} connected — mesh {mesh_type.value} health updated")

    async def _on_peer_disconnected(self, event: ASIMEvent) -> None:
        """Handle peer disconnected event — update mesh health."""
        peer_id = event.data.get("peer_id", "")
        if peer_id:
            mesh_type = self._peer_mesh_map.get(peer_id, MeshType.PUBLIC)
            self._router.update_mesh_health(
                mesh_type=mesh_type,
                is_connected=self._check_mesh_health(mesh_type),
                peers=len(self._mesh_peers.get(mesh_type, [])),
            )
            logger.info(f"🔌 Peer {peer_id} disconnected — mesh {mesh_type.value} health updated")
    # ─── Health Checkers ──────────────────────────────────────────────────────

    def _register_health_checkers(self) -> None:
        """Register per-mesh health checkers with MultiMeshRouter."""
        if self._health_checkers_registered:
            return

        def make_checker(mesh_type: MeshType) -> Callable[[], bool]:
            def checker() -> bool:
                return self._check_mesh_health(mesh_type)
            return checker

        for mt in MeshType:
            self._router.register_health_checker(mt, make_checker(mt))

        self._health_checkers_registered = True
        logger.debug("✅ Mesh health checkers registered")

    def _check_mesh_health(self, mesh_type: MeshType) -> bool:
        """
        Check if a specific mesh type is healthy by looking at peer count
        and connection status.
        """
        peers = self._mesh_peers.get(mesh_type, [])
        connected_count = sum(
            1 for pid in peers
            if self._p2p.get_peer(pid) and self._p2p.get_peer(pid).is_connected
        )

        # WebRTC peers
        webrtc_count = 0
        if self._webrtc:
            webrtc_count = len(self._webrtc.get_connected_peers())

        # LOCAL mesh is always healthy
        if mesh_type == MeshType.LOCAL:
            return True

        # Cloud/Public meshes require at least 1 connected peer or WebRTC peer
        if mesh_type in (MeshType.CLOUD, MeshType.PUBLIC):
            return connected_count > 0 or webrtc_count > 0

        # PERSONAL mesh requires local connectivity
        if mesh_type == MeshType.PERSONAL:
            return connected_count > 0

        return False

    # ─── Peer Discovery ───────────────────────────────────────────────────────

    async def _peer_discovery_loop(self) -> None:
        """Periodically discover peers and update mesh peer caches."""
        while self._running:
            try:
                await self._discover_peers()
            except Exception as e:
                logger.error(f"Peer discovery error: {e}")
            await asyncio.sleep(_PEER_DISCOVERY_INTERVAL)

    async def _discover_peers(self) -> None:
        """
        Discover peers from NodeRegistry and classify them by mesh type.
        Also feeds discovered peers into KademliaDHT routing table.

        Classification rules:
        - Same hostname / 127.0.0.1 → LOCAL
        - Private IP range (192.168.x, 10.x, 172.16-31.x) → PERSONAL
        - Public IP, high trust → CLOUD
        - Public IP, low/unknown trust → PUBLIC
        """
        discovered_peers = []  # Collect for DHT feeding

        # Get all known nodes from registry
        for node_id, record in list(self._registry.nodes.items()):
            if node_id == self.node_id:
                continue

            # Classify by IP
            ip = record.ip_address
            mesh_type = self._classify_ip(ip, record.trust_level)

            # Add to P2P transport if not already known
            if node_id not in self._p2p.peers:
                self._p2p.add_peer(
                    node_id=node_id,
                    host=ip,
                    port_udp=record.port,
                    port_ws=record.port + 1,
                )

            # Classify into mesh
            if node_id not in self._peer_mesh_map:
                self._peer_mesh_map[node_id] = mesh_type
                self._mesh_peers[mesh_type].append(node_id)

            # Collect for DHT feeding
            discovered_peers.append({
                "node_id": node_id,
                "host": ip,
                "port_udp": record.port,
            })

        # Feed discovered peers into Kademlia DHT routing table
        if self._dht is not None and discovered_peers:
            added = self._dht.add_nodes_from_bootstrap(discovered_peers)
            if added > 0:
                logger.debug(f"📡 Fed {added} discovered peer(s) into DHT routing table")

        # Update MultiMeshRouter with peer counts
        for mt, peers in self._mesh_peers.items():
            connected = sum(
                1 for pid in peers
                if self._p2p.get_peer(pid) and self._p2p.get_peer(pid).is_connected
            )
            self._router.update_mesh_health(
                mesh_type=mt,
                is_connected=self._check_mesh_health(mt),
                peers=connected,
            )

    def _classify_ip(self, ip: str, trust_level: TrustLevel) -> MeshType:
        """Classify an IP address into a mesh type."""
        import socket as _socket
        # Localhost
        if ip in ("127.0.0.1", "::1", "localhost"):
            return MeshType.LOCAL

        # Private IP ranges
        if ip.startswith("192.168.") or ip.startswith("10."):
            return MeshType.PERSONAL

        # Check for 172.16-31.x.x
        try:
            first_octet = int(ip.split(".")[0])
            if first_octet == 172:
                second = int(ip.split(".")[1])
                if 16 <= second <= 31:
                    return MeshType.PERSONAL
        except (ValueError, IndexError):
            pass

        # Public IPs: classify by trust
        if trust_level in (TrustLevel.HIGH, TrustLevel.TRUSTED):
            return MeshType.CLOUD

        return MeshType.PUBLIC

    # ─── Health Pings ─────────────────────────────────────────────────────────

    async def _health_ping_loop(self) -> None:
        """Periodically ping known peers to update health metrics."""
        while self._running:
            try:
                await self._ping_all_peers()
            except Exception as e:
                logger.error(f"Health ping error: {e}")
            await asyncio.sleep(_HEALTH_PING_INTERVAL)

    async def _ping_all_peers(self) -> None:
        """Ping all known peers and update mesh health metrics."""
        total_latency = 0.0
        ping_count = 0

        for peer_id, peer in list(self._p2p.peers.items()):
            start = time.time()
            response = await self._p2p.rpc_call(
                peer,
                "ping",
                {"ping": int(time.time() * 1000)},
                timeout=5.0,
            )
            if response:
                latency_ms = (time.time() - start) * 1000
                total_latency += latency_ms
                ping_count += 1

        # Update mesh health with aggregated metrics
        if ping_count > 0:
            avg_latency = total_latency / ping_count
            for mt in MeshType:
                peers = self._mesh_peers.get(mt, [])
                self._router.update_mesh_health(
                    mesh_type=mt,
                    is_connected=self._check_mesh_health(mt),
                    latency_ms=avg_latency,
                    peers=len(peers),
                )

    # ─── Data Routing ─────────────────────────────────────────────────────────

    async def route_data(
        self,
        mesh_type: MeshType,
        data: bytes,
        destination: str,
        msg_type: str = "mesh_data",
    ) -> bool:
        """
        Route data through a mesh type using the actual P2P transport.

        This is the integration point called by MultiMeshRouter.route_through_mesh().

        Args:
            mesh_type: Which mesh to route through.
            data: Raw data bytes to send.
            destination: Destination peer/node ID.
            msg_type: Message type for P2P routing.

        Returns:
            True if data was sent successfully.
        """
        # Find peer in this mesh
        peer = self._p2p.get_peer(destination)
        if not peer:
            # Try to find peer in mesh peer list
            peer_ids = self._mesh_peers.get(mesh_type, [])
            if destination in peer_ids:
                # Peer is known but not in transport — try to find it
                record = self._registry.nodes.get(destination)
                if record:
                    peer = self._p2p.add_peer(
                        node_id=destination,
                        host=record.ip_address,
                        port_udp=record.port,
                        port_ws=record.port + 1,
                    )

        if not peer:
            logger.warning(
                f"⛔ Cannot route to {destination}: unknown peer"
            )
            return False

        # Build P2P message
        msg = P2PMessage(
            msg_type=msg_type,
            sender_id=self.node_id,
            msg_id=self._p2p._next_msg_id(),
            payload={"data": data.hex(), "mesh": mesh_type.value},
        )

        # Try UDP first, fall back to WebSocket
        sent = await self._p2p.send_udp(peer, msg)
        if not sent:
            sent = await self._p2p.send_ws(peer, msg)

        # Try WebRTC as third fallback
        if not sent and self._webrtc:
            sent = await self._webrtc.send(destination, data)

        if sent:
            logger.debug(
                f"📡 Routed {len(data)} bytes via {mesh_type.value} → {destination}"
            )
        else:
            logger.warning(
                f"⛔ Failed to route data via {mesh_type.value} → {destination}"
            )

        return sent

    # ─── Peer Management ──────────────────────────────────────────────────────

    def add_peer_to_mesh(
        self,
        node_id: str,
        host: str,
        port_udp: int,
        port_ws: int,
        mesh_type: MeshType,
    ) -> None:
        """Add a peer to a specific mesh."""
        self._p2p.add_peer(node_id, host, port_udp, port_ws)
        self._peer_mesh_map[node_id] = mesh_type
        if node_id not in self._mesh_peers[mesh_type]:
            self._mesh_peers[mesh_type].append(node_id)

        # Register in NodeRegistry
        self._registry.register_node(
            node_id=node_id,
            hostname=host,
            ip_address=host,
            port=port_udp,
        )

    def remove_peer_from_mesh(self, node_id: str) -> None:
        """Remove a peer from its mesh."""
        mesh_type = self._peer_mesh_map.pop(node_id, None)
        if mesh_type:
            peers = self._mesh_peers.get(mesh_type, [])
            if node_id in peers:
                peers.remove(node_id)
        self._p2p.remove_peer(node_id)

    # ─── Stats ────────────────────────────────────────────────────────────────

    def get_p2p_stats(self) -> Dict[str, Any]:
        """Get comprehensive P2P integration statistics."""
        from mesh.multi_mesh_router import get_multi_mesh_router
        router = get_multi_mesh_router()
        mesh_stats = router.get_mesh_stats()
        return {
            "node_id": self.node_id,
            "transport": {
                "udp_port": self._p2p.port_udp,
                "ws_port": self._p2p.port_ws,
                "peers_total": len(self._p2p.peers),
                "peers_connected": len(self._p2p.get_online_peers()),
            },
            "webrtc": self._webrtc.get_stats() if self._webrtc else {"available": False},
            "mesh_peers": {
                mt.value: len(peers)
                for mt, peers in self._mesh_peers.items()
            },
            "mesh_stats": mesh_stats,
        }


# ─── Wire into MultiMeshRouter ────────────────────────────────────────────────

def patch_route_through_mesh(integration: P2PIntegration) -> None:
    """
    Monkey-patch MultiMeshRouter.route_through_mesh() to use real P2P transport.

    This makes the router's routing decisions actually send data via P2PTransport.
    """
    router = get_multi_mesh_router()
    original_route = router.route_through_mesh

    async def patched_route(mesh: MeshType, data: bytes, destination: str) -> bool:
        # First, validate routing is allowed (original logic)
        if not original_route(mesh, data, destination):
            return False
        # Then, actually send via P2P
        return await integration.route_data(mesh, data, destination)

    router.route_through_mesh = patched_route  # type: ignore
    logger.info("🔄 MultiMeshRouter.route_through_mesh() patched with real P2P transport")


# ─── Singleton ────────────────────────────────────────────────────────────────

_p2p_integration: Optional[P2PIntegration] = None


def get_p2p_integration(
    node_id: Optional[str] = None,
    enable_webrtc: bool = False,
    kademlia_dht: Optional['KademliaDHT'] = None,
    crdt_store: Optional['CRDTStore'] = None,
    bootstrap_service: Optional['BootstrapService'] = None,
) -> P2PIntegration:
    """Get or create the global P2P integration instance."""
    global _p2p_integration
    if _p2p_integration is None:
        _p2p_integration = P2PIntegration(
            node_id=node_id,
            enable_webrtc=enable_webrtc,
            kademlia_dht=kademlia_dht,
            crdt_store=crdt_store,
            bootstrap_service=bootstrap_service,
        )
        patch_route_through_mesh(_p2p_integration)
    return _p2p_integration


def reset_p2p_integration():
    """Reset the global P2P integration (for testing)."""
    global _p2p_integration
    _p2p_integration = None


__all__ = [
    "P2PIntegration",
    "WebRTCTransport",
    "WebRTCPeerConnection",
    "get_p2p_integration",
    "reset_p2p_integration",
    "patch_route_through_mesh",
]
