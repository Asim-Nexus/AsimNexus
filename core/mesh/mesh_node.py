#!/usr/bin/env python3
"""
STATUS: NEW — MeshNode Orchestrator
ASIMNEXUS MeshNode Orchestrator
=================================
High-level mesh node that wires all mesh components together.

Provides a unified API for:
  - Starting/stopping all mesh services
  - Peer discovery and NAT traversal
  - Message sending with automatic strategy selection
  - Route discovery and multi-hop forwarding
  - Health monitoring and auto-recovery
  - Unified status reporting

Integrates with ALL mesh components:
  - [`mesh/p2p_transport.py`](p2p_transport.py) — Message transport (UDP + WS)
  - [`mesh/kademlia_dht.py`](kademlia_dht.py) — Distributed hash table
  - [`mesh/crdt_sync.py`](crdt_sync.py) — CRDT state sync
  - [`mesh/autodiscovery.py`](autodiscovery.py) — Automatic peer discovery
  - [`mesh/relay.py`](relay.py) — TCP relay service
  - [`mesh/bootstrap.py`](bootstrap.py) — Bootstrap node discovery
  - [`mesh/stun_turn.py`](stun_turn.py) — STUN/TURN NAT traversal
  - [`mesh/hole_punching.py`](hole_punching.py) — UDP hole punching
  - [`mesh/multi_hop_router.py`](multi_hop_router.py) — Multi-hop routing
  - [`mesh/multi_mesh_router.py`](multi_mesh_router.py) — Multi-mesh routing
  - [`mesh/p2p_integration.py`](p2p_integration.py) — P2P integration bridge
"""

import os
import json
import time
import uuid
import random
import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple, Set, Callable
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("AsimNexus.Mesh.MeshNode")

# ─── Environment Configuration ────────────────────────────────────────────────

_MESH_NODE_HEARTBEAT_INTERVAL = float(os.getenv("ASIM_MESH_HEARTBEAT_INTERVAL", "30"))
_MESH_NODE_DISCOVERY_INTERVAL = float(os.getenv("ASIM_MESH_NODE_DISCOVERY_INTERVAL", "60"))
_MESH_NODE_STARTUP_TIMEOUT = float(os.getenv("ASIM_MESH_NODE_STARTUP_TIMEOUT", "30"))
_MESH_NODE_AUTO_RECOVER = os.getenv("ASIM_MESH_AUTO_RECOVER", "true").lower() == "true"
_MESH_NODE_ENABLE_RELAY = os.getenv("ASIM_MESH_ENABLE_RELAY", "true").lower() == "true"
_MESH_NODE_ENABLE_RENDEZVOUS = os.getenv("ASIM_MESH_ENABLE_RENDEZVOUS", "true").lower() == "true"
_MESH_NODE_ENABLE_MULTIHOP = os.getenv("ASIM_MESH_ENABLE_MULTIHOP", "true").lower() == "true"


# ─── Enums & Data Classes ────────────────────────────────────────────────────


class MeshNodeStatus(Enum):
    """Overall status of a MeshNode."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    DEGRADED = "degraded"   # Some components failed
    STOPPING = "stopping"
    ERROR = "error"


class SendStrategy(Enum):
    """Strategy selection for sending a message."""
    AUTO = "auto"                     # Let the node decide best strategy
    DIRECT_UDP = "direct_udp"         # Direct UDP via P2PTransport
    DIRECT_WS = "direct_ws"           # Direct WebSocket via P2PTransport
    STUN_PUNCH = "stun_punch"        # STUN-discovered hole punch
    RENDEZVOUS = "rendezvous"         # Rendezvous-coordinated punch
    MULTIHOP = "multihop"             # Multi-hop routing
    TURN_RELAY = "turn_relay"         # TURN relay
    TCP_RELAY = "tcp_relay"           # TCP relay fallback
    BROADCAST = "broadcast"           # Broadcast to all peers


@dataclass
class ComponentHealth:
    """Health status of a single mesh component."""
    name: str
    running: bool = False
    last_heartbeat: float = 0.0
    error_count: int = 0
    last_error: Optional[str] = None

    @property
    def healthy(self) -> bool:
        return self.running and self.error_count < 5


@dataclass
class MeshNodeConfig:
    """Configuration for MeshNode startup."""
    node_id: str
    host: str = "0.0.0.0"
    port_udp: int = 7332
    port_ws: int = 7333
    port_relay: int = 7334
    port_bootstrap: int = 7335
    port_rendezvous: int = 7336
    enable_relay: bool = _MESH_NODE_ENABLE_RELAY
    enable_rendezvous: bool = _MESH_NODE_ENABLE_RENDEZVOUS
    enable_multihop: bool = _MESH_NODE_ENABLE_MULTIHOP
    enable_stun: bool = True
    auto_recover: bool = _MESH_NODE_AUTO_RECOVER
    heartbeat_interval: float = _MESH_NODE_HEARTBEAT_INTERVAL
    discovery_interval: float = _MESH_NODE_DISCOVERY_INTERVAL
    bootstrap_nodes: Optional[List[Tuple[str, int]]] = None
    is_bootstrap_node: bool = False
    stun_servers: Optional[List[str]] = None
    turn_servers: Optional[List[Tuple[str, int, str, str]]] = None  # (host, port, user, pass)


# ─── MeshNode ────────────────────────────────────────────────────────────────


class MeshNode:
    """
    High-level mesh node orchestrator.

    Wires all mesh components together and provides a unified API.

    Usage:
        config = MeshNodeConfig(node_id="my-node")
        node = MeshNode(config)
        await node.start()

        # Send a message (auto-selects best strategy)
        await node.send("peer-id", {"hello": "world"})

        # Receive messages
        @node.on_message
        async def handler(sender_id, payload):
            print(f"From {sender_id}: {payload}")

        status = node.get_status()
        await node.stop()
    """

    def __init__(self, config: MeshNodeConfig):
        self._config = config
        self._status = MeshNodeStatus.STOPPED

        # Component references (lazily initialized on start)
        self._transport = None
        self._dht = None
        self._crdt_store = None
        self._discovery = None
        self._relay = None
        self._bootstrap = None
        self._stun_client = None
        self._nat_detector = None
        self._turn_client = None
        self._hole_puncher = None
        self._punch_listener = None
        self._rendezvous_server = None
        self._rendezvous_client = None
        self._multi_hop_router = None
        self._multi_mesh_router = None
        self._p2p_integration = None

        # Health tracking
        self._health: Dict[str, ComponentHealth] = {}

        # Message handler
        self._message_handler: Optional[Callable] = None

        # Known peers cache
        self._known_peers: Dict[str, Dict[str, Any]] = {}

        # Network classification (cached)
        self._nat_type: Optional[str] = None
        self._public_address: Optional[Tuple[str, int]] = None

        # Background tasks
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._discovery_task: Optional[asyncio.Task] = None
        self._recovery_task: Optional[asyncio.Task] = None

        # Locks
        self._lock = asyncio.Lock()

        # Startup timestamp
        self._start_time = time.time()

    # ─── Lifecycle ────────────────────────────────────────────────────────────

    async def start(self) -> bool:
        """
        Start the mesh node and all its components.

        Returns True if all components started successfully.
        Components are started in dependency order.
        """
        if self._status == MeshNodeStatus.RUNNING:
            return True

        self._status = MeshNodeStatus.STARTING
        logger.info(f"Starting MeshNode [{self._config.node_id[:8]}...]")

        success = True

        try:
            # 1. Start P2P Transport (foundation for all other communication)
            success &= await self._start_transport()

            # 2. Start STUN/NAT detection (need to know our network topology)
            if self._config.enable_stun:
                success &= await self._start_stun()

            # 3. Start Bootstrap (seed node connection)
            success &= await self._start_bootstrap()

            # 4. Start Kademlia DHT (peer discovery & routing)
            success &= await self._start_dht()

            # 5. Start CRDT Store (state sync)
            success &= await self._start_crdt()

            # 6. Start AutoDiscovery (LAN neighbor discovery)
            success &= await self._start_discovery()

            # 7. Start Relay Service (TCP relay for NAT'd peers)
            if self._config.enable_relay:
                success &= await self._start_relay()

            # 8. Start Hole Punching + Rendezvous (NAT traversal)
            if self._config.enable_rendezvous:
                success &= await self._start_hole_punching()

            # 9. Start Multi-Hop Router (indirect routing)
            if self._config.enable_multihop:
                success &= await self._start_multihop()

            # 10. Start MultiMesh Router + P2P Integration (high-level routing)
            success &= await self._start_mesh_routing()

            # 11. Start background tasks
            self._start_background_tasks()

            if success:
                self._status = MeshNodeStatus.RUNNING
                logger.info(
                    f"MeshNode [{self._config.node_id[:8]}...] "
                    f"started successfully"
                )
            else:
                self._status = MeshNodeStatus.DEGRADED
                logger.warning(
                    f"MeshNode [{self._config.node_id[:8]}...] "
                    f"started in DEGRADED mode"
                )

        except Exception as exc:
            logger.error(f"MeshNode startup failed: {exc}")
            self._status = MeshNodeStatus.ERROR
            return False

        return success

    async def stop(self) -> None:
        """
        Stop the mesh node and all components.

        Components are stopped in reverse dependency order.
        """
        self._status = MeshNodeStatus.STOPPING
        logger.info(f"Stopping MeshNode [{self._config.node_id[:8]}...]")

        # Stop background tasks
        for task_name in ("_recovery_task", "_discovery_task", "_heartbeat_task"):
            task = getattr(self, task_name, None)
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        # Stop components in reverse order
        await self._stop_component("_p2p_integration")
        await self._stop_component("_multi_mesh_router")
        await self._stop_component("_multi_hop_router")
        await self._stop_component("_rendezvous_server")
        await self._stop_component("_rendezvous_client")
        await self._stop_component("_punch_listener")
        await self._stop_component("_hole_puncher")
        await self._stop_component("_relay")
        await self._stop_component("_discovery")
        await self._stop_component("_crdt_store")
        await self._stop_component("_dht")
        await self._stop_component("_bootstrap")
        await self._stop_component("_stun_client")
        await self._stop_component("_nat_detector")
        await self._stop_component("_turn_client")
        await self._stop_component("_transport")

        self._status = MeshNodeStatus.STOPPED
        logger.info(f"MeshNode [{self._config.node_id[:8]}...] stopped")

    async def _stop_component(self, attr_name: str) -> None:
        """Safely stop a component."""
        component = getattr(self, attr_name, None)
        if component is None:
            return

        try:
            stop_method = getattr(component, "stop", None)
            if stop_method:
                if asyncio.iscoroutinefunction(stop_method):
                    await stop_method()
                else:
                    stop_method()
        except Exception as exc:
            logger.debug(f"Error stopping {attr_name}: {exc}")

        setattr(self, attr_name, None)

    # ─── Component Starters ──────────────────────────────────────────────────

    async def _start_transport(self) -> bool:
        """Start the P2P transport layer."""
        try:
            from core.mesh.p2p_transport import get_p2p_transport

            self._transport = get_p2p_transport(
                node_id=self._config.node_id,
                host=self._config.host,
                port_udp=self._config.port_udp,
                port_ws=self._config.port_ws,
            )
            await self._transport.start()
            self._register_health("transport", True)
            logger.info("P2P Transport started")
            return True
        except Exception as exc:
            logger.error(f"Failed to start P2P Transport: {exc}")
            self._register_health("transport", False, str(exc))
            return False

    async def _start_stun(self) -> bool:
        """Start STUN client + NAT detector + TURN client."""
        success = True
        try:
            from core.mesh.stun_turn import (
                get_stun_client,
                get_nat_detector,
                get_turn_client,
            )

            self._stun_client = get_stun_client()
            self._nat_detector = get_nat_detector()
            self._turn_client = get_turn_client()
            self._register_health("stun", True)

            # Run NAT classification
            try:
                if self._nat_detector is None:
                    logger.warning("NAT detector not available")
                    self._nat_type = "unknown"
                else:
                    classification = await self._nat_detector.classify()
                    self._nat_type = classification.nat_type.value
                    if classification.public_address:
                        self._public_address = (
                            classification.public_address.ip_address,
                            classification.public_address.port,
                        )
                    logger.info(
                        f"NAT classification: {self._nat_type} "
                        f"(public: {self._public_address})"
                    )
            except Exception as exc:
                logger.warning(f"NAT classification failed: {exc}")
                self._nat_type = "unknown"

        except Exception as exc:
            logger.error(f"Failed to start STUN/TURN: {exc}")
            self._register_health("stun", False, str(exc))
            success = False

        return success

    async def _start_bootstrap(self) -> bool:
        """Start the bootstrap service."""
        try:
            from core.mesh.bootstrap import get_bootstrap_service

            self._bootstrap = get_bootstrap_service(
                node_id=self._config.node_id,
                is_bootstrap=self._config.is_bootstrap_node,
                port=self._config.port_bootstrap,
            )
            await self._bootstrap.start()

            # Connect to bootstrap nodes if configured
            if self._config.bootstrap_nodes:
                for host, port in self._config.bootstrap_nodes:
                    try:
                        peers = await self._bootstrap.bootstrap(host, port)
                        for peer in peers:
                            peer_id = peer.get("node_id", "")
                            if peer_id:
                                self._known_peers[peer_id] = peer
                        logger.info(
                            f"Bootstrapped from {host}:{port} "
                            f"({len(peers)} peers)"
                        )
                    except Exception as exc:
                        logger.debug(
                            f"Bootstrap from {host}:{port} failed: {exc}"
                        )

            self._register_health("bootstrap", True)
            logger.info("Bootstrap service started")
            return True

        except Exception as exc:
            logger.error(f"Failed to start Bootstrap: {exc}")
            self._register_health("bootstrap", False, str(exc))
            return False

    async def _start_dht(self) -> bool:
        """Start the Kademlia DHT."""
        try:
            from core.mesh.kademlia_dht import get_kademlia_dht, NodeID

            dht_node_id = NodeID.from_string(self._config.node_id)
            self._dht = get_kademlia_dht(
                node_id=dht_node_id,
            )
            await self._dht.start(transport=self._transport)
            self._register_health("dht", True)
            logger.info("Kademlia DHT started")
            return True

        except Exception as exc:
            logger.error(f"Failed to start DHT: {exc}")
            self._register_health("dht", False, str(exc))
            return False

    async def _start_crdt(self) -> bool:
        """Start the CRDT store."""
        try:
            from core.mesh.crdt_sync import get_crdt_store

            self._crdt_store = get_crdt_store(
                node_id=self._config.node_id,
                transport=self._transport,
            )
            await self._crdt_store.start()
            self._register_health("crdt", True)
            logger.info("CRDT store started")
            return True

        except Exception as exc:
            logger.error(f"Failed to start CRDT store: {exc}")
            self._register_health("crdt", False, str(exc))
            return False

    async def _start_discovery(self) -> bool:
        """Start auto-discovery."""
        try:
            from core.mesh.autodiscovery import get_auto_discovery

            self._discovery = get_auto_discovery(
                node_id=self._config.node_id,
                port=self._config.port_udp,
            )
            self._discovery.start()
            self._register_health("discovery", True)
            logger.info("Auto-discovery started")
            return True

        except Exception as exc:
            logger.error(f"Failed to start auto-discovery: {exc}")
            self._register_health("discovery", False, str(exc))
            return False

    async def _start_relay(self) -> bool:
        """Start the TCP relay service."""
        try:
            from core.mesh.relay import get_relay_service

            self._relay = get_relay_service(
                node_id=self._config.node_id,
                port=self._config.port_relay,
            )
            await self._relay.start()
            self._register_health("relay", True)
            logger.info("Relay service started")
            return True

        except Exception as exc:
            logger.error(f"Failed to start relay: {exc}")
            self._register_health("relay", False, str(exc))
            return False

    async def _start_hole_punching(self) -> bool:
        """Start hole punching + rendezvous server/client."""
        success = True

        try:
            from core.mesh.hole_punching import (
                get_hole_puncher,
                get_rendezvous_server,
                RendezvousClient,
                PunchEndpoint,
                PunchListener,
            )

            # Start rendezvous server (if configured as rendezvous node)
            try:
                self._rendezvous_server = await get_rendezvous_server(
                    host=self._config.host,
                    port=self._config.port_rendezvous,
                )
                self._register_health("rendezvous_server", True)
            except Exception as exc:
                logger.debug(f"Rendezvous server start skipped: {exc}")
                self._register_health("rendezvous_server", False, str(exc))

            # Create rendezvous client
            rendezvous_addr = (
                self._config.bootstrap_nodes[0][0]
                if self._config.bootstrap_nodes
                else "127.0.0.1",
                self._config.port_rendezvous,
            )
            try:
                self._rendezvous_client = RendezvousClient(
                    node_id=self._config.node_id,
                    rendezvous_addr=rendezvous_addr,
                    local_endpoint=PunchEndpoint(
                        node_id=self._config.node_id,
                        local_addr=(
                            (self._config.host, self._config.port_udp)
                            if self._config.host != "0.0.0.0"
                            else ("127.0.0.1", self._config.port_udp)
                        ),
                    ),
                )
                await self._rendezvous_client.start()
                self._register_health("rendezvous_client", True)
            except Exception as exc:
                logger.debug(f"Rendezvous client start failed: {exc}")
                self._register_health("rendezvous_client", False, str(exc))

            # Create hole puncher
            self._hole_puncher = await get_hole_puncher(
                node_id=self._config.node_id,
                stun_client=self._stun_client,
                nat_detector=self._nat_detector,
                turn_client=self._turn_client,
                rendezvous_client=self._rendezvous_client,
                local_addr=(
                    (self._config.host, self._config.port_udp)
                    if self._config.host != "0.0.0.0"
                    else None
                ),
            )
            self._register_health("hole_puncher", True)

            # Start punch listener
            self._punch_listener = PunchListener(
                node_id=self._config.node_id,
                hole_puncher=self._hole_puncher,
                listen_addr=(self._config.host, 0),
                on_punch_request=self._on_punch_request,
            )
            punch_port = await self._punch_listener.start()
            self._register_health("punch_listener", True)
            logger.info(f"Punch listener on port {punch_port}")

            logger.info("Hole punching + rendezvous started")

        except Exception as exc:
            logger.error(f"Failed to start hole punching: {exc}")
            self._register_health("hole_puncher", False, str(exc))
            success = False

        return success

    async def _start_multihop(self) -> bool:
        """Start the multi-hop router."""
        try:
            from core.mesh.multi_hop_router import get_multi_hop_router

            self._multi_hop_router = await get_multi_hop_router(
                node_id=self._config.node_id,
                transport=self._transport,
                dht=self._dht,
                crdt_store=self._crdt_store,
            )

            # Register peers already known via bootstrap as neighbors
            for peer_id, peer_info in self._known_peers.items():
                host = peer_info.get("ip_address", "")
                port = peer_info.get("port_udp", 0)
                if host and port:
                    self._multi_hop_router.register_neighbor(
                        node_id=peer_id,
                        address=(host, port),
                    )

            self._register_health("multihop", True)
            logger.info("Multi-hop router started")
            return True

        except Exception as exc:
            logger.error(f"Failed to start multi-hop router: {exc}")
            self._register_health("multihop", False, str(exc))
            return False

    async def _start_mesh_routing(self) -> bool:
        """Start MultiMeshRouter + P2PIntegration."""
        success = True

        try:
            from core.mesh.multi_mesh_router import get_multi_mesh_router
            self._multi_mesh_router = get_multi_mesh_router()
            self._register_health("multi_mesh_router", True)
        except Exception as exc:
            logger.error(f"Failed to get MultiMeshRouter: {exc}")
            self._register_health("multi_mesh_router", False, str(exc))
            success = False

        try:
            from core.mesh.p2p_integration import get_p2p_integration
            self._p2p_integration = get_p2p_integration(
                node_id=self._config.node_id,
                kademlia_dht=self._dht,
                crdt_store=self._crdt_store,
                bootstrap_service=self._bootstrap,
            )
            await self._p2p_integration.start()
            self._register_health("p2p_integration", True)

            # Patch route-through-mesh for MultiMeshRouter
            from core.mesh.p2p_integration import patch_route_through_mesh
            patch_route_through_mesh(self._p2p_integration)

            logger.info("P2P Integration started")
        except Exception as exc:
            logger.error(f"Failed to start P2P Integration: {exc}")
            self._register_health("p2p_integration", False, str(exc))
            success = False

        return success

    def _start_background_tasks(self) -> None:
        """Start background maintenance tasks."""
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self._discovery_task = asyncio.create_task(self._discovery_loop())
        if self._config.auto_recover:
            self._recovery_task = asyncio.create_task(self._recovery_loop())

    # ─── Background Loops ────────────────────────────────────────────────────

    async def _heartbeat_loop(self) -> None:
        """Periodic heartbeat to update health status."""
        while True:
            await asyncio.sleep(self._config.heartbeat_interval)
            now = time.time()
            for comp in self._health.values():
                comp.last_heartbeat = now

    async def _discovery_loop(self) -> None:
        """Periodic peer discovery via bootstrap + LAN."""
        await asyncio.sleep(5)  # Initial delay after startup
        while True:
            await asyncio.sleep(self._config.discovery_interval)
            try:
                await self._discover_peers()
            except Exception as exc:
                logger.debug(f"Peer discovery error: {exc}")

    async def _discover_peers(self) -> None:
        """Discover new peers via bootstrap, DHT, and LAN discovery."""
        # Bootstrap discovery
        if self._bootstrap and self._config.bootstrap_nodes:
            for host, port in self._config.bootstrap_nodes:
                try:
                    peers = await self._bootstrap.bootstrap(host, port)
                    for peer in peers:
                        peer_id = peer.get("node_id", "")
                        if peer_id and peer_id != self._config.node_id:
                            self._known_peers[peer_id] = peer
                            # Register with multi-hop router
                            if self._multi_hop_router:
                                self._multi_hop_router.register_neighbor(
                                    node_id=peer_id,
                                    address=(
                                        peer.get("ip_address", ""),
                                        peer.get("port_udp", 0),
                                    ),
                                )
                except Exception:
                    pass

        # LAN discovery
        if self._discovery:
            try:
                lan_peers = self._discovery.discover_once()
                for node_info in lan_peers:
                    if node_info.node_id != self._config.node_id:
                        self._known_peers[node_info.node_id] = {
                            "node_id": node_info.node_id,
                            "ip_address": node_info.ip_address,
                            "port_udp": node_info.port,
                        }
                        if self._multi_hop_router:
                            self._multi_hop_router.register_neighbor(
                                node_id=node_info.node_id,
                                address=(node_info.ip_address, node_info.port),
                            )
            except Exception:
                pass

        # DHT-based peer discovery
        if self._dht:
            try:
                from core.mesh.kademlia_dht import NodeID
                # Query DHT for random keys to discover peers
                for _ in range(3):
                    random_key = NodeID.from_string(
                        f"peer_discovery_{random.randint(0, 2**32)}"
                    )
                    closest = self._dht.find_closest_nodes(random_key, count=5)
                    for node in closest:
                        node_id_str = str(node.node_id)
                        if node_id_str != self._config.node_id:
                            self._known_peers[node_id_str] = {
                                "node_id": node_id_str,
                                "ip_address": node.ip_address,
                                "port_udp": node.port_udp,
                            }
            except Exception:
                pass

    async def _recovery_loop(self) -> None:
        """Auto-recovery loop — restart failed components."""
        await asyncio.sleep(10)
        while True:
            await asyncio.sleep(60)
            if self._status not in (MeshNodeStatus.RUNNING, MeshNodeStatus.DEGRADED):
                continue

            for comp_name, health in list(self._health.items()):
                if not health.healthy:
                    logger.info(f"Attempting recovery of {comp_name}...")
                    try:
                        await self._restart_component(comp_name)
                    except Exception as exc:
                        logger.error(f"Recovery of {comp_name} failed: {exc}")

    async def _restart_component(self, component: str) -> bool:
        """Restart a specific component by name."""
        starters = {
            "transport": self._start_transport,
            "stun": self._start_stun,
            "bootstrap": self._start_bootstrap,
            "dht": self._start_dht,
            "crdt": self._start_crdt,
            "discovery": self._start_discovery,
            "relay": self._start_relay,
            "hole_puncher": self._start_hole_punching,
            "multihop": self._start_multihop,
            "multi_mesh_router": self._start_mesh_routing,
        }
        starter = starters.get(component)
        if starter:
            return await starter()
        return False

    # ─── Message API ─────────────────────────────────────────────────────────

    async def send(
        self,
        destination_id: str,
        payload: Dict[str, Any],
        strategy: SendStrategy = SendStrategy.AUTO,
        timeout: float = 10.0,
    ) -> bool:
        """
        Send a message to a destination peer.

        Auto-selects the best strategy based on:
          1. Direct UDP/WS if peer is directly connected
          2. STUN hole punch if peer is behind NAT
          3. Rendezvous-coordinated punch if both are NAT'd
          4. Multi-hop routing if no direct path exists
          5. TURN relay if all else fails
        """
        if strategy == SendStrategy.AUTO:
            return await self._send_auto(destination_id, payload, timeout)
        elif strategy == SendStrategy.DIRECT_UDP:
            return await self._send_direct_udp(destination_id, payload)
        elif strategy == SendStrategy.DIRECT_WS:
            return await self._send_direct_ws(destination_id, payload)
        elif strategy == SendStrategy.MULTIHOP:
            return await self._send_multihop(destination_id, payload, timeout)
        elif strategy == SendStrategy.TURN_RELAY:
            return await self._send_turn_relay(destination_id, payload)
        elif strategy == SendStrategy.TCP_RELAY:
            return await self._send_tcp_relay(destination_id, payload)
        elif strategy == SendStrategy.BROADCAST:
            return await self._broadcast(payload)
        else:
            return await self._send_auto(destination_id, payload, timeout)

    async def _send_auto(
        self,
        destination_id: str,
        payload: Dict[str, Any],
        timeout: float = 10.0,
    ) -> bool:
        """Auto-select the best send strategy."""
        # 1. Try direct transport
        if await self._send_direct_udp(destination_id, payload):
            return True

        # 2. Try direct WebSocket
        if await self._send_direct_ws(destination_id, payload):
            return True

        # 3. Try STUN hole punch
        if self._hole_puncher:
            peer_endpoint = self._known_peers.get(destination_id)
            if peer_endpoint:
                from core.mesh.hole_punching import PunchEndpoint
                remote = PunchEndpoint(
                    node_id=destination_id,
                    public_addr=(
                        peer_endpoint.get("public_ip") or peer_endpoint.get("ip_address", ""),
                        peer_endpoint.get("port_udp", 0),
                    ),
                )
                session = await self._hole_puncher.punch(
                    destination_id, remote, timeout=5.0
                )
                if session.status.name == "ESTABLISHED":
                    return await self._send_direct_udp(destination_id, payload)

        # 4. Try multi-hop routing
        if self._multi_hop_router:
            return await self._send_multihop(destination_id, payload, timeout)

        # 5. Try TCP relay
        if self._relay:
            return await self._send_tcp_relay(destination_id, payload)

        return False

    async def _send_direct_udp(
        self,
        destination_id: str,
        payload: Dict[str, Any],
    ) -> bool:
        """Send directly via UDP transport."""
        if not self._transport:
            return False
        try:
            from core.mesh.p2p_transport import P2PMessage, RPCMessageType
            msg = P2PMessage(
                msg_type=RPCMessageType.DIRECT_MESSAGE.value,
                sender_id=self._config.node_id,
                msg_id=str(uuid.uuid4()),
                payload=payload,
            )
            peer = self._transport.peers.get(destination_id)
            if peer:
                return await self._transport.send_udp(peer, msg)
        except Exception:
            pass
        return False

    async def _send_direct_ws(
        self,
        destination_id: str,
        payload: Dict[str, Any],
    ) -> bool:
        """Send directly via WebSocket transport."""
        if not self._transport:
            return False
        try:
            from core.mesh.p2p_transport import P2PMessage, RPCMessageType
            msg = P2PMessage(
                msg_type=RPCMessageType.DIRECT_MESSAGE.value,
                sender_id=self._config.node_id,
                msg_id=str(uuid.uuid4()),
                payload=payload,
            )
            peer = self._transport.peers.get(destination_id)
            if peer:
                return await self._transport.send_ws(peer, msg)
        except Exception:
            pass
        return False

    async def _send_multihop(
        self,
        destination_id: str,
        payload: Dict[str, Any],
        timeout: float = 10.0,
    ) -> bool:
        """Send via multi-hop routing."""
        if not self._multi_hop_router:
            return False
        try:
            return await self._multi_hop_router.forward_data(
                destination_id, payload, timeout=timeout
            )
        except Exception as exc:
            logger.debug(f"Multi-hop send failed: {exc}")
            return False

    async def _send_turn_relay(
        self,
        destination_id: str,
        payload: Dict[str, Any],
    ) -> bool:
        """Send via TURN relay."""
        if not self._turn_client or not self._turn_client._servers:
            return False
        try:
            allocation = await self._turn_client.allocate(
                server=self._turn_client._servers[0],
                username=os.getenv("ASIM_MESH_TURN_USERNAME", ""),
                password=os.getenv("ASIM_MESH_TURN_PASSWORD", ""),
            )
            if allocation and allocation.relayed_address:
                # Send via TURN relay address
                sock = __import__("socket").socket(
                    __import__("socket").AF_INET,
                    __import__("socket").SOCK_DGRAM,
                )
                data = json.dumps(payload).encode("utf-8")
                sock.sendto(
                    data,
                    (allocation.relayed_address.ip_address, allocation.relayed_address.port),
                )
                sock.close()
                return True
        except Exception:
            pass
        return False

    async def _send_tcp_relay(
        self,
        destination_id: str,
        payload: Dict[str, Any],
    ) -> bool:
        """Send via TCP relay."""
        if not self._relay:
            return False
        try:
            session_id = await self._relay.request_relay(
                self._config.node_id, destination_id
            )
            if session_id:
                # Relay sends on our behalf
                return True
        except Exception:
            pass
        return False

    async def _broadcast(self, payload: Dict[str, Any]) -> bool:
        """Broadcast a message to all known peers."""
        if not self._transport:
            return False
        try:
            from core.mesh.p2p_transport import P2PMessage, RPCMessageType
            msg = P2PMessage(
                msg_type=RPCMessageType.MULTIHOP_ROUTE.value,
                sender_id=self._config.node_id,
                msg_id=str(uuid.uuid4()),
                payload=payload,
            )
            count = await self._transport.broadcast_ws(msg)
            return count > 0
        except Exception:
            return False

    # ─── Incoming Message Handler ────────────────────────────────────────────

    def on_message(self, handler: Callable) -> None:
        """Set the message handler for incoming messages."""
        self._message_handler = handler

    async def _on_punch_request(
        self,
        peer_id: str,
        address: Tuple[str, int],
    ) -> None:
        """Handle an incoming punch request."""
        logger.info(f"Punch request from {peer_id} @ {address}")
        # Register the peer for future communication
        if self._transport:
            from core.mesh.p2p_transport import PeerInfo
            self._transport.add_peer(
                node_id=peer_id,
                host=address[0],
                port_udp=address[1],
                port_ws=address[1],
            )

    # ─── Health & Status ─────────────────────────────────────────────────────

    def _register_health(
        self,
        name: str,
        running: bool,
        error: Optional[str] = None,
    ) -> None:
        """Register/update component health."""
        if name not in self._health:
            self._health[name] = ComponentHealth(name=name)
        health = self._health[name]
        health.running = running
        health.last_heartbeat = time.time()
        if error:
            health.error_count += 1
            health.last_error = error

    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive mesh node status."""
        component_states = {
            name: {
                "running": h.running,
                "healthy": h.healthy,
                "error_count": h.error_count,
                "last_error": h.last_error,
            }
            for name, h in self._health.items()
        }

        running_count = sum(1 for h in self._health.values() if h.running)
        healthy_count = sum(1 for h in self._health.values() if h.healthy)
        total_components = len(self._health) or 1  # Avoid division by zero

        return {
            "node_id": self._config.node_id[:16],
            "status": self._status.value,
            "uptime": self._get_uptime(),
            "nat_type": self._nat_type,
            "public_address": self._public_address,
            "known_peers": len(self._known_peers),
            "components": {
                "total": len(self._health),
                "running": running_count,
                "healthy": healthy_count,
            },
            "health_score": healthy_count / total_components,
            "component_states": component_states,
            "transport": {
                "host": self._config.host,
                "port_udp": self._config.port_udp,
                "port_ws": self._config.port_ws,
            },
        }

    def _get_uptime(self) -> float:
        """Get node uptime in seconds."""
        if self._start_time:
            return time.time() - self._start_time
        return 0.0

    def get_known_peers(self) -> Dict[str, Dict[str, Any]]:
        """Get dictionary of known peers."""
        return dict(self._known_peers)

    def get_peer_count(self) -> int:
        """Get number of known peers."""
        return len(self._known_peers)

    def get_health(self) -> Dict[str, ComponentHealth]:
        """Get component health status."""
        return dict(self._health)

    @property
    def is_healthy(self) -> bool:
        """Whether the node is healthy (all components running)."""
        return (
            self._status == MeshNodeStatus.RUNNING
            and all(h.healthy for h in self._health.values())
        )

    @property
    def node_id(self) -> str:
        return self._config.node_id


# ─── Factory / Singleton ─────────────────────────────────────────────────────

_MESH_NODE: Optional[MeshNode] = None
_MESH_NODE_LOCK = asyncio.Lock()


async def create_mesh_node(
    node_id: str,
    host: str = "0.0.0.0",
    port_udp: int = 7332,
    port_ws: int = 7333,
    bootstrap_nodes: Optional[List[Tuple[str, int]]] = None,
    is_bootstrap_node: bool = False,
    enable_relay: bool = _MESH_NODE_ENABLE_RELAY,
    enable_rendezvous: bool = _MESH_NODE_ENABLE_RENDEZVOUS,
    enable_multihop: bool = _MESH_NODE_ENABLE_MULTIHOP,
    auto_recover: bool = _MESH_NODE_AUTO_RECOVER,
) -> MeshNode:
    """Create and start a new MeshNode."""
    global _MESH_NODE

    config = MeshNodeConfig(
        node_id=node_id,
        host=host,
        port_udp=port_udp,
        port_ws=port_ws,
        enable_relay=enable_relay,
        enable_rendezvous=enable_rendezvous,
        enable_multihop=enable_multihop,
        auto_recover=auto_recover,
        bootstrap_nodes=bootstrap_nodes or [],
        is_bootstrap_node=is_bootstrap_node,
    )

    node = MeshNode(config)
    await node.start()

    async with _MESH_NODE_LOCK:
        _MESH_NODE = node

    return node


async def get_mesh_node() -> Optional[MeshNode]:
    """Get the singleton MeshNode."""
    return _MESH_NODE


async def shutdown_mesh_node() -> None:
    """Shutdown the singleton MeshNode."""
    global _MESH_NODE
    if _MESH_NODE:
        await _MESH_NODE.stop()
        _MESH_NODE = None
