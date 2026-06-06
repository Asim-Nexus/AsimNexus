#!/usr/bin/env python3
"""
STATUS: NEW — Multi-Hop Mesh Router
ASIMNEXUS Multi-Hop Mesh Router
=================================
Handles multi-hop routing, path discovery, and store-and-forward relay
for the mesh network layer.

When direct P2P connections are unavailable or unreliable, this router
discovers multi-hop paths through intermediate peers and manages
store-and-forward message delivery.

Integrates with:
  - [`mesh/p2p_transport.py`](p2p_transport.py) — Underlying message transport
  - [`mesh/kademlia_dht.py`](kademlia_dht.py) — DHT for peer discovery & routing info storage
  - [`mesh/crdt_sync.py`](crdt_sync.py) — CRDT store for pending message replication
  - [`mesh/relay.py`](relay.py) — Relay fallback for direct multi-hop
  - [`mesh/hole_punching.py`](hole_punching.py) — NAT traversal status
  - [`mesh/multi_mesh_router.py`](multi_mesh_router.py) — MultiMeshRouter integration
"""

import os
import json
import time
import struct
import random
import heapq
import socket
import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

logger = logging.getLogger("AsimNexus.Mesh.MultiHopRouter")

# ─── Environment Configuration ────────────────────────────────────────────────

_MAX_HOPS = int(os.getenv("ASIM_MESH_MAX_HOPS", "5"))
_PATH_DISCOVERY_TIMEOUT_SEC = float(os.getenv("ASIM_MESH_PATH_DISCOVERY_TIMEOUT", "10"))
_PATH_DISCOVERY_TTL = int(os.getenv("ASIM_MESH_PATH_DISCOVERY_TTL", "5"))
_PATH_REFRESH_INTERVAL_SEC = float(os.getenv("ASIM_MESH_PATH_REFRESH_INTERVAL", "120"))
_STORE_FORWARD_EXPIRY_SEC = float(os.getenv("ASIM_MESH_STORE_FORWARD_EXPIRY", "3600"))
_MULTIHOP_RETRY_INTERVAL_SEC = float(os.getenv("ASIM_MESH_MULTIHOP_RETRY", "30"))
_MAX_PATH_AGE_SEC = float(os.getenv("ASIM_MESH_MAX_PATH_AGE", "300"))
_MAX_STORED_MESSAGES = int(os.getenv("ASIM_MESH_MAX_STORED_MSGS", "1000"))


# ─── Enums & Data Classes ────────────────────────────────────────────────────


class PathStatus(Enum):
    """Status of a multi-hop path."""
    UNKNOWN = "unknown"
    DISCOVERING = "discovering"
    ACTIVE = "active"
    STALE = "stale"
    FAILED = "failed"


class RouteMessageType(Enum):
    """Types of multi-hop routing messages."""
    PATH_DISCOVERY = 0x01        # Broadcast: find path to destination
    PATH_RESPONSE = 0x02         # Unicast: path found
    PATH_ERROR = 0x03            # Unicast: no path available
    DATA_FORWARD = 0x04          # Forward: relay data along path
    DATA_DELIVERY = 0x05         # Unicast: final delivery
    DATA_ACK = 0x06              # Unicast: delivery confirmation
    STORE_REQUEST = 0x07         # Request to store message for offline peer
    STORE_ACK = 0x08             # Store accepted
    STORE_RETRIEVE = 0x09        # Request stored messages
    STORE_RESPONSE = 0x0A        # Deliver stored messages
    HEALTH_CHECK = 0x0B          # Path health probe
    HEALTH_RESPONSE = 0x0C       # Path health response
    PEER_LEAVE = 0x0D            # Peer is leaving, invalidate paths
    PATH_UPDATE = 0x0E           # Path cost/metric update


@dataclass
class HopInfo:
    """Information about a single hop in a path."""
    node_id: str
    address: Optional[Tuple[str, int]] = None
    latency_ms: float = 0.0
    last_seen: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"node_id": self.node_id, "latency_ms": self.latency_ms}
        if self.address:
            d["address"] = {"ip": self.address[0], "port": self.address[1]}
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HopInfo":
        addr = data.get("address")
        return cls(
            node_id=data["node_id"],
            address=(addr["ip"], addr["port"]) if addr else None,
            latency_ms=data.get("latency_ms", 0.0),
        )


@dataclass
class RoutePath:
    """A discovered multi-hop path to a destination."""
    destination_id: str
    hops: List[HopInfo]                # Ordered list of intermediate peers
    total_hops: int = 0
    total_latency_ms: float = 0.0
    discovered_at: float = field(default_factory=time.time)
    last_used: float = field(default_factory=time.time)
    status: PathStatus = PathStatus.ACTIVE
    ttl: int = _PATH_DISCOVERY_TTL
    source_id: str = ""                # Who discovered this path
    via_relay: bool = False            # Whether path uses relay nodes

    def __post_init__(self):
        self.total_hops = len(self.hops)

    @property
    def is_expired(self) -> bool:
        return (time.time() - self.discovered_at) > _MAX_PATH_AGE_SEC

    @property
    def last_hop(self) -> Optional[HopInfo]:
        return self.hops[-1] if self.hops else None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "destination_id": self.destination_id,
            "hops": [h.to_dict() for h in self.hops],
            "total_hops": self.total_hops,
            "total_latency_ms": self.total_latency_ms,
            "discovered_at": self.discovered_at,
            "status": self.status.value,
            "source_id": self.source_id,
            "via_relay": self.via_relay,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RoutePath":
        hops = [HopInfo.from_dict(h) for h in data.get("hops", [])]
        path = cls(
            destination_id=data["destination_id"],
            hops=hops,
            discovered_at=data.get("discovered_at", time.time()),
            status=PathStatus(data.get("status", "active")),
            source_id=data.get("source_id", ""),
            via_relay=data.get("via_relay", False),
        )
        path.total_latency_ms = data.get("total_latency_ms", 0.0)
        return path


@dataclass
class StoredMessage:
    """
    A message stored for store-and-forward delivery.
    Held when destination peer is offline, delivered on reconnection.
    """
    message_id: str
    source_id: str
    destination_id: str
    payload: Dict[str, Any]
    created_at: float = field(default_factory=time.time)
    ttl: float = _STORE_FORWARD_EXPIRY_SEC
    retry_count: int = 0
    last_retry: float = 0.0

    @property
    def is_expired(self) -> bool:
        return (time.time() - self.created_at) > self.ttl

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "source_id": self.source_id,
            "destination_id": self.destination_id,
            "payload": self.payload,
            "created_at": self.created_at,
            "ttl": self.ttl,
            "retry_count": self.retry_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StoredMessage":
        return cls(
            message_id=data["message_id"],
            source_id=data["source_id"],
            destination_id=data["destination_id"],
            payload=data.get("payload", {}),
            created_at=data.get("created_at", time.time()),
            ttl=data.get("ttl", _STORE_FORWARD_EXPIRY_SEC),
            retry_count=data.get("retry_count", 0),
        )


@dataclass
class PathDiscoveryRequest:
    """Tracks a path discovery request."""
    destination_id: str
    request_id: str
    started_at: float = field(default_factory=time.time)
    paths_found: List[RoutePath] = field(default_factory=list)
    pending_responses: int = 0

    @property
    def elapsed(self) -> float:
        return time.time() - self.started_at


# ─── MultiHopRouter ──────────────────────────────────────────────────────────


class MultiHopRouter:
    """
    Multi-hop mesh router with path discovery, store-and-forward,
    and adaptive routing.

    Core capabilities:
      1. Path Discovery  — Find multi-hop paths via controlled flooding
      2. Path Selection  — Pick best path (shortest latency, fewest hops)
      3. Data Forwarding — Relay data along discovered paths
      4. Store & Forward — Buffer messages for offline peers
      5. Path Health     — Monitor and refresh active paths
      6. Path Invalidation — React to peer departures
    """

    def __init__(
        self,
        node_id: str,
        transport=None,  # P2PTransport
        dht=None,        # KademliaDHT
        crdt_store=None, # CRDTStore
    ):
        self._node_id = node_id
        self._transport = transport
        self._dht = dht
        self._crdt_store = crdt_store

        # Routing table: destination_id → list of RoutePath (sorted by quality)
        self._routes: Dict[str, List[RoutePath]] = {}

        # Forwarding table: target_id → next_hop (fast lookup for forwarding)
        self._forwarding_table: Dict[str, HopInfo] = {}

        # Neighbor quality metrics: node_id → (latency, last_seen, reliability)
        self._neighbors: Dict[str, HopInfo] = {}

        # Pending path discoveries
        self._pending_discoveries: Dict[str, PathDiscoveryRequest] = {}

        # Seen discovery requests (dedup TTL-based flood)
        self._seen_discovery_ids: Set[str] = set()

        # Store-and-forward message queue
        self._stored_messages: Dict[str, List[StoredMessage]] = defaultdict(list)

        # Message ID dedup set
        self._seen_message_ids: Set[str] = set()

        # Callback: when a message is received via multi-hop
        self._message_callback: Optional[Callable] = None

        # Locks
        self._lock = asyncio.Lock()
        self._routes_lock = asyncio.Lock()
        self._store_lock = asyncio.Lock()

        # Maintenance tasks
        self._maintenance_task: Optional[asyncio.Task] = None
        self._path_refresh_task: Optional[asyncio.Task] = None
        self._store_retry_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self) -> None:
        """Start the multi-hop router."""
        self._running = True
        self._maintenance_task = asyncio.create_task(self._maintenance_loop())
        self._path_refresh_task = asyncio.create_task(self._path_refresh_loop())
        self._store_retry_task = asyncio.create_task(self._store_retry_loop())
        logger.info(f"MultiHopRouter started for node {self._node_id[:8]}...")

    async def stop(self) -> None:
        """Stop the multi-hop router."""
        self._running = False
        for task in (self._maintenance_task, self._path_refresh_task, self._store_retry_task):
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        logger.info("MultiHopRouter stopped")

    def set_message_callback(self, callback: Callable) -> None:
        """Set callback for received multi-hop messages."""
        self._message_callback = callback

    # ─── Path Discovery ───────────────────────────────────────────────────────

    async def discover_path(
        self,
        destination_id: str,
        timeout: float = _PATH_DISCOVERY_TIMEOUT_SEC,
    ) -> Optional[RoutePath]:
        """
        Discover a multi-hop path to a destination.

        Uses controlled flooding: broadcast PATH_DISCOVERY with TTL.
        Each intermediate peer that has a path to the destination responds.
        Returns the best path found (lowest latency, then fewest hops).
        """
        # Check if we already have a valid route
        existing = await self._get_best_route(destination_id)
        if existing and not existing.is_expired:
            return existing

        # Check DHT for stored paths
        dht_path = await self._query_dht_for_path(destination_id)
        if dht_path:
            async with self._routes_lock:
                self._routes[destination_id] = [dht_path]
                self._update_forwarding_table(destination_id, dht_path)
            return dht_path

        # Start path discovery
        request_id = f"pd_{self._node_id}_{destination_id}_{time.time_ns()}"
        discovery = PathDiscoveryRequest(
            destination_id=destination_id,
            request_id=request_id,
        )

        async with self._lock:
            self._pending_discoveries[request_id] = discovery

        # Broadcast discovery to neighbors
        discovery_msg = {
            "type": RouteMessageType.PATH_DISCOVERY.value,
            "request_id": request_id,
            "source_id": self._node_id,
            "destination_id": destination_id,
            "ttl": _PATH_DISCOVERY_TTL,
            "path_so_far": [HopInfo(node_id=self._node_id).to_dict()],
            "timestamp": time.time(),
        }

        await self._broadcast_to_neighbors(discovery_msg)

        # Wait for responses
        await asyncio.sleep(timeout)

        async with self._lock:
            if request_id in self._pending_discoveries:
                discovery = self._pending_discoveries.pop(request_id, None)
            else:
                discovery = None

        if discovery and discovery.paths_found:
            # Sort by quality (total_latency_ms ascending, then total_hops ascending)
            discovery.paths_found.sort(key=lambda p: (p.total_latency_ms, p.total_hops))
            best = discovery.paths_found[0]

            async with self._routes_lock:
                self._routes[destination_id] = discovery.paths_found
                self._update_forwarding_table(destination_id, best)

            # Optionally publish to DHT for others
            await self._publish_path_to_dht(best)

            logger.info(
                f"Path discovered to {destination_id[:8]}... "
                f"({best.total_hops} hops, {best.total_latency_ms:.1f}ms)"
            )
            return best

        logger.info(f"No path found to {destination_id[:8]}...")
        return None

    async def _query_dht_for_path(self, destination_id: str) -> Optional[RoutePath]:
        """Query the DHT for a stored path to the destination."""
        if not self._dht:
            return None
        try:
            from mesh.kademlia_dht import NodeID
            key = NodeID.from_string(f"route:{destination_id}")
            value = self._dht.get(key)
            if value:
                data = json.loads(value.decode("utf-8"))
                path = RoutePath.from_dict(data)
                if not path.is_expired:
                    return path
        except Exception as exc:
            logger.debug(f"DHT path query failed for {destination_id[:8]}: {exc}")
        return None

    async def _publish_path_to_dht(self, path: RoutePath) -> None:
        """Publish discovered path to DHT for other peers to use."""
        if not self._dht:
            return
        try:
            from mesh.kademlia_dht import NodeID
            key = NodeID.from_string(f"route:{path.destination_id}")
            value = json.dumps(path.to_dict()).encode("utf-8")
            self._dht.store(key, value, ttl=_MAX_PATH_AGE_SEC)
        except Exception as exc:
            logger.debug(f"DHT path publish failed: {exc}")

    async def handle_path_discovery(
        self,
        msg: Dict[str, Any],
        sender_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Handle an incoming PATH_DISCOVERY message.

        If this node knows the destination, respond with the path.
        Otherwise, forward with decremented TTL.
        """
        request_id = msg.get("request_id", "")
        destination_id = msg.get("destination_id", "")
        ttl = msg.get("ttl", 0)
        path_so_far = msg.get("path_so_far", [])

        # Dedup
        if request_id in self._seen_discovery_ids:
            return None
        self._seen_discovery_ids.add(request_id)

        # Am I the destination?
        if destination_id == self._node_id:
            # Build return path
            return_path = [HopInfo.from_dict(h) for h in path_so_far]
            return {
                "type": RouteMessageType.PATH_RESPONSE.value,
                "request_id": request_id,
                "source_id": self._node_id,
                "destination_id": msg.get("source_id", ""),
                "path": [h.to_dict() for h in return_path],
                "latency_ms": 0.0,
                "timestamp": time.time(),
            }

        # Do I have a route to the destination?
        route = await self._get_best_route(destination_id)
        if route and not route.is_expired:
            response_path = path_so_far + [h.to_dict() for h in route.hops]
            return {
                "type": RouteMessageType.PATH_RESPONSE.value,
                "request_id": request_id,
                "source_id": self._node_id,
                "destination_id": msg.get("source_id", ""),
                "path": response_path,
                "latency_ms": route.total_latency_ms,
                "timestamp": time.time(),
            }

        # Forward with decremented TTL
        if ttl > 1 and len(path_so_far) < _MAX_HOPS:
            updated_path = path_so_far + [HopInfo(node_id=self._node_id).to_dict()]
            forward_msg = {
                "type": RouteMessageType.PATH_DISCOVERY.value,
                "request_id": request_id,
                "source_id": msg.get("source_id", ""),
                "destination_id": destination_id,
                "ttl": ttl - 1,
                "path_so_far": updated_path,
                "timestamp": time.time(),
            }
            await self._broadcast_to_neighbors(forward_msg, exclude=sender_id)

        return None

    async def handle_path_response(
        self,
        msg: Dict[str, Any],
    ) -> None:
        """Handle an incoming PATH_RESPONSE message."""
        request_id = msg.get("request_id", "")
        path_data = msg.get("path", [])
        latency = msg.get("latency_ms", 0.0)

        if not path_data:
            return

        # Reconstruct the path
        hops = [HopInfo.from_dict(h) for h in path_data]
        destination_id = msg.get("source_id", "")

        # Find which destination this path leads to
        target_id = ""
        async with self._lock:
            for req_id, discovery in self._pending_discoveries.items():
                # The original source stored in msg.destination_id is the requester
                pass

        # Determine the actual destination from the request context
        # The response path leads from "source_id" (responding node) back to requestor
        # We need to figure out which discovery this belongs to
        for req_id, discovery in list(self._pending_discoveries.items()):
            if discovery.destination_id == destination_id and req_id == request_id:
                target_id = discovery.destination_id
                break

        # Fallback: use the last hop's node_id as destination
        if not target_id and hops:
            target_id = hops[-1].node_id

        if not target_id:
            return

        route_path = RoutePath(
            destination_id=target_id,
            hops=hops,
            source_id=msg.get("source_id", ""),
            total_latency_ms=latency,
        )

        async with self._lock:
            for req_id, discovery in self._pending_discoveries.items():
                if discovery.destination_id == target_id:
                    discovery.paths_found.append(route_path)
                    break

        logger.debug(
            f"Path response for {target_id[:8]}... via {len(hops)} hops"
        )

    # ─── Data Forwarding ──────────────────────────────────────────────────────

    async def forward_data(
        self,
        destination_id: str,
        payload: Dict[str, Any],
        timeout: float = 10.0,
    ) -> bool:
        """
        Forward data to a destination via multi-hop routing.

        Returns True if delivery was acknowledged.
        Falls back to store-and-forward if destination is unreachable.
        """
        # Check forwarding table
        next_hop = await self._get_next_hop(destination_id)

        if next_hop is None:
            # Try path discovery
            path = await self.discover_path(destination_id)
            if path and path.hops:
                next_hop = path.hops[0]
            else:
                # Store for later delivery
                await self._store_message(destination_id, payload)
                logger.info(
                    f"No route to {destination_id[:8]}... message stored"
                )
                return False

        message_id = f"fwd_{self._node_id}_{destination_id}_{time.time_ns()}"

        forward_msg = {
            "type": RouteMessageType.DATA_FORWARD.value,
            "message_id": message_id,
            "source_id": self._node_id,
            "destination_id": destination_id,
            "payload": payload,
            "hops_remaining": _MAX_HOPS,
            "path": [],  # Will be populated by intermediate nodes
            "timestamp": time.time(),
        }

        # Send to next hop
        sent = await self._send_to_peer(next_hop, forward_msg)

        if sent:
            logger.debug(
                f"Forwarded data to {destination_id[:8]}... via {next_hop.node_id[:8]}"
            )
            return True

        # Direct send failed, try path discovery
        path = await self.discover_path(destination_id)
        if path and path.hops:
            next_hop = path.hops[0]
            sent = await self._send_to_peer(next_hop, forward_msg)
            if sent:
                return True

        # Store for later
        await self._store_message(destination_id, payload)
        return False

    async def handle_data_forward(
        self,
        msg: Dict[str, Any],
        sender_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Handle an incoming DATA_FORWARD message.

        If this node is the destination, deliver locally.
        Otherwise, forward to the next hop toward the destination.
        """
        destination_id = msg.get("destination_id", "")
        message_id = msg.get("message_id", "")

        # Dedup
        if message_id in self._seen_message_ids:
            return None
        self._seen_message_ids.add(message_id)

        # Am I the destination?
        if destination_id == self._node_id:
            # Deliver locally
            payload = msg.get("payload", {})
            source_id = msg.get("source_id", "")

            if self._message_callback:
                try:
                    await self._message_callback(source_id, payload)
                except Exception as exc:
                    logger.error(f"Message callback error: {exc}")

            # Send ACK back along the path
            return {
                "type": RouteMessageType.DATA_ACK.value,
                "message_id": message_id,
                "source_id": self._node_id,
                "destination_id": source_id,
                "status": "delivered",
                "timestamp": time.time(),
            }

        # Forward to next hop
        hops_remaining = msg.get("hops_remaining", _MAX_HOPS)
        if hops_remaining <= 0:
            logger.warning(f"Too many hops for msg {message_id[:16]}... dropping")
            return None

        next_hop = await self._get_next_hop(destination_id)

        if next_hop is None:
            # Try path discovery
            path = await self.discover_path(destination_id)
            if path and path.hops:
                next_hop = path.hops[0]

        if next_hop:
            # Update the path trace
            path_trace = msg.get("path", [])
            path_trace.append({
                "node_id": self._node_id,
                "timestamp": time.time(),
            })

            forward_msg = {
                "type": RouteMessageType.DATA_FORWARD.value,
                "message_id": message_id,
                "source_id": msg.get("source_id", ""),
                "destination_id": destination_id,
                "payload": msg.get("payload", {}),
                "hops_remaining": hops_remaining - 1,
                "path": path_trace,
                "timestamp": time.time(),
            }

            await self._send_to_peer(next_hop, forward_msg)

        # If no route, message is dropped (could implement store-and-forward here)
        return None

    async def handle_data_ack(self, msg: Dict[str, Any]) -> None:
        """Handle a DATA_ACK from the destination."""
        message_id = msg.get("message_id", "")
        logger.debug(f"Delivery confirmed for message {message_id[:16]}...")

    # ─── Store and Forward ────────────────────────────────────────────────────

    async def _store_message(
        self,
        destination_id: str,
        payload: Dict[str, Any],
    ) -> str:
        """Store a message for later delivery."""
        message_id = f"sf_{self._node_id}_{destination_id}_{time.time_ns()}"
        stored = StoredMessage(
            message_id=message_id,
            source_id=self._node_id,
            destination_id=destination_id,
            payload=payload,
        )

        async with self._store_lock:
            queue = self._stored_messages[destination_id]
            queue.append(stored)
            # Enforce size limit
            if len(queue) > _MAX_STORED_MESSAGES:
                queue.pop(0)

        logger.info(
            f"Stored message for {destination_id[:8]}... "
            f"(total pending: {len(queue)})"
        )
        return message_id

    async def get_stored_messages(
        self,
        destination_id: Optional[str] = None,
    ) -> List[StoredMessage]:
        """Get stored messages, optionally for a specific destination."""
        async with self._store_lock:
            if destination_id:
                return list(self._stored_messages.get(destination_id, []))
            all_msgs: List[StoredMessage] = []
            for msgs in self._stored_messages.values():
                all_msgs.extend(msgs)
            return all_msgs

    async def deliver_stored_messages(self, destination_id: str) -> int:
        """Attempt to deliver all stored messages for a destination."""
        async with self._store_lock:
            messages = list(self._stored_messages.get(destination_id, []))

        if not messages:
            return 0

        delivered = 0
        for msg in messages:
            if msg.is_expired:
                async with self._store_lock:
                    if destination_id in self._stored_messages:
                        try:
                            self._stored_messages[destination_id].remove(msg)
                        except ValueError:
                            pass
                continue

            success = await self.forward_data(destination_id, msg.payload)
            if success:
                delivered += 1
                async with self._store_lock:
                    if destination_id in self._stored_messages:
                        try:
                            self._stored_messages[destination_id].remove(msg)
                        except ValueError:
                            pass
            else:
                msg.retry_count += 1
                msg.last_retry = time.time()

        if delivered:
            logger.info(
                f"Delivered {delivered}/{len(messages)} stored messages "
                f"to {destination_id[:8]}..."
            )
        return delivered

    # ─── Path Management ──────────────────────────────────────────────────────

    async def _get_best_route(self, destination_id: str) -> Optional[RoutePath]:
        """Get the best known route to a destination."""
        async with self._routes_lock:
            routes = self._routes.get(destination_id, [])
            # Filter expired and failed routes
            valid = [
                r for r in routes
                if r.status != PathStatus.FAILED and not r.is_expired
            ]
            if valid:
                # Sort: active first, then by latency, then by hops
                valid.sort(key=lambda r: (
                    0 if r.status == PathStatus.ACTIVE else 1,
                    r.total_latency_ms,
                    r.total_hops,
                ))
                return valid[0]
        return None

    async def _get_next_hop(self, destination_id: str) -> Optional[HopInfo]:
        """Get the next hop for a destination from the forwarding table."""
        async with self._routes_lock:
            hop = self._forwarding_table.get(destination_id)
            if hop:
                return hop

        # Fallback: compute from route
        route = await self._get_best_route(destination_id)
        if route and route.hops:
            hop = route.hops[0]
            async with self._routes_lock:
                self._forwarding_table[destination_id] = hop
            return hop
        return None

    def _update_forwarding_table(
        self,
        destination_id: str,
        path: RoutePath,
    ) -> None:
        """Update the forwarding table with the first hop of a path."""
        if path.hops:
            self._forwarding_table[destination_id] = path.hops[0]

    async def invalidate_path(self, destination_id: str) -> None:
        """Mark all routes to a destination as failed."""
        async with self._routes_lock:
            if destination_id in self._routes:
                for route in self._routes[destination_id]:
                    route.status = PathStatus.FAILED
                self._forwarding_table.pop(destination_id, None)

    async def handle_peer_leave(self, peer_id: str) -> None:
        """
        Handle a peer leaving the network.
        Invalidate all paths that use this peer as an intermediate hop.
        """
        async with self._routes_lock:
            for dest_id, routes in list(self._routes.items()):
                for route in routes:
                    for hop in route.hops:
                        if hop.node_id == peer_id:
                            route.status = PathStatus.FAILED
                            break

            # Clean up neighbors
            self._neighbors.pop(peer_id, None)

        logger.info(f"Invalidated paths through departed peer {peer_id[:8]}...")

    # ─── Peer Registration ────────────────────────────────────────────────────

    def register_neighbor(
        self,
        node_id: str,
        address: Optional[Tuple[str, int]] = None,
        latency_ms: float = 0.0,
    ) -> None:
        """Register a direct neighbor."""
        self._neighbors[node_id] = HopInfo(
            node_id=node_id,
            address=address,
            latency_ms=latency_ms,
            last_seen=time.time(),
        )

    def remove_neighbor(self, node_id: str) -> None:
        """Remove a neighbor."""
        self._neighbors.pop(node_id, None)

    def get_neighbors(self) -> List[HopInfo]:
        """Get list of direct neighbors."""
        return list(self._neighbors.values())

    def get_known_destinations(self) -> List[str]:
        """Get list of destinations we have routes for."""
        return list(self._routes.keys())

    # ─── Message Sending ──────────────────────────────────────────────────────

    async def _send_to_peer(
        self,
        hop: HopInfo,
        msg: Dict[str, Any],
    ) -> bool:
        """Send a message to a peer, either via transport or raw socket."""
        if self._transport and hop.address:
            try:
                from mesh.p2p_transport import P2PMessage, RPCMessageType
                import uuid as _uuid
                p2p_msg = P2PMessage(
                    msg_type=RPCMessageType.MULTIHOP_ROUTE.value,
                    sender_id=self._node_id,
                    msg_id=str(_uuid.uuid4()),
                    payload={
                        "route_payload": msg,
                        "target_node": hop.node_id,
                    },
                )
                peer_info = self._transport.peers.get(hop.node_id)
                if peer_info:
                    sent = await self._transport.send_udp(peer_info, p2p_msg)
                    if sent:
                        return True
                # Try WebSocket
                if peer_info:
                    sent = await self._transport.send_ws(peer_info, p2p_msg)
                    return sent
            except Exception as exc:
                logger.debug(f"Transport send failed to {hop.node_id[:8]}: {exc}")

        # Fallback: raw UDP
        if hop.address:
            try:
                data = json.dumps(msg).encode("utf-8")
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(3.0)
                sock.sendto(data, hop.address)
                sock.close()
                return True
            except Exception as exc:
                logger.debug(f"Raw send failed to {hop.address}: {exc}")

        return False

    async def _broadcast_to_neighbors(
        self,
        msg: Dict[str, Any],
        exclude: Optional[str] = None,
    ) -> int:
        """Broadcast a message to all known neighbors."""
        sent = 0
        for node_id, hop in list(self._neighbors.items()):
            if node_id == exclude:
                continue
            success = await self._send_to_peer(hop, msg)
            if success:
                sent += 1
        return sent

    # ─── Maintenance Loops ────────────────────────────────────────────────────

    async def _maintenance_loop(self) -> None:
        """Periodic maintenance: clean stale routes, dedup sets."""
        while self._running:
            await asyncio.sleep(300)  # 5 minutes

            # Clean expired routes
            async with self._routes_lock:
                for dest_id, routes in list(self._routes.items()):
                    routes = [r for r in routes if not r.is_expired]
                    if routes:
                        self._routes[dest_id] = routes
                    else:
                        del self._routes[dest_id]
                        self._forwarding_table.pop(dest_id, None)

            # Clean stale neighbors
            now = time.time()
            stale_neighbors = [
                nid for nid, hop in self._neighbors.items()
                if now - hop.last_seen > _MAX_PATH_AGE_SEC
            ]
            for nid in stale_neighbors:
                self._neighbors.pop(nid, None)

            # Limit dedup set size
            if len(self._seen_discovery_ids) > 10000:
                self._seen_discovery_ids.clear()
            if len(self._seen_message_ids) > 10000:
                self._seen_message_ids.clear()

    async def _path_refresh_loop(self) -> None:
        """Periodically refresh active paths."""
        while self._running:
            await asyncio.sleep(_PATH_REFRESH_INTERVAL_SEC)

            async with self._routes_lock:
                destinations = list(self._routes.keys())

            for dest_id in destinations:
                route = await self._get_best_route(dest_id)
                if route and route.status == PathStatus.ACTIVE:
                    # Probe the path with a health check
                    health_msg = {
                        "type": RouteMessageType.HEALTH_CHECK.value,
                        "source_id": self._node_id,
                        "destination_id": dest_id,
                        "timestamp": time.time(),
                    }
                    next_hop = await self._get_next_hop(dest_id)
                    if next_hop:
                        await self._send_to_peer(next_hop, health_msg)

    async def _store_retry_loop(self) -> None:
        """Periodically retry delivery of stored messages."""
        while self._running:
            await asyncio.sleep(_MULTIHOP_RETRY_INTERVAL_SEC)

            async with self._store_lock:
                destinations = list(self._stored_messages.keys())

            for dest_id in destinations:
                await self.deliver_stored_messages(dest_id)

            # Clean expired messages
            async with self._store_lock:
                for dest_id, msgs in list(self._stored_messages.items()):
                    msgs = [m for m in msgs if not m.is_expired]
                    if msgs:
                        self._stored_messages[dest_id] = msgs
                    else:
                        del self._stored_messages[dest_id]

    # ─── Route Registration (for external path injection) ────────────────────

    async def register_route(self, path: RoutePath) -> None:
        """Register an externally discovered route."""
        async with self._routes_lock:
            if path.destination_id not in self._routes:
                self._routes[path.destination_id] = []
            self._routes[path.destination_id].append(path)
            self._update_forwarding_table(path.destination_id, path)

    async def discover_route_via_dht(
        self,
        destination_id: str,
    ) -> Optional[RoutePath]:
        """Discover a route via DHT peer lookup + sequential probing."""
        if not self._dht:
            return None

        from mesh.kademlia_dht import NodeID, DHTNode

        try:
            target_id = NodeID.from_string(destination_id)
            closest_nodes = self._dht.find_closest_nodes(target_id, count=8)

            path: List[HopInfo] = []
            for node in closest_nodes:
                if node.node_id == self._node_id:
                    continue
                hop = HopInfo(
                    node_id=str(node.node_id),
                    address=(node.ip_address, node.port_udp) if hasattr(node, 'port_udp') else None,
                    latency_ms=0.0,
                )
                path.append(hop)

            if path:
                route = RoutePath(
                    destination_id=destination_id,
                    hops=path,
                    source_id=self._node_id,
                )
                await self.register_route(route)
                return route

        except Exception as exc:
            logger.debug(f"DHT route discovery failed: {exc}")

        return None

    # ─── Stats ────────────────────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        """Get multi-hop routing statistics."""
        route_count = len(self._routes)
        total_stored = sum(len(msgs) for msgs in self._stored_messages.values())
        active_paths = sum(
            1 for routes in self._routes.values()
            for r in routes if r.status == PathStatus.ACTIVE
        )
        return {
            "node_id": self._node_id[:16],
            "routes": route_count,
            "active_paths": active_paths,
            "neighbors": len(self._neighbors),
            "stored_messages": total_stored,
            "forwarding_entries": len(self._forwarding_table),
            "pending_discoveries": len(self._pending_discoveries),
        }


# ─── Singleton Accessors ─────────────────────────────────────────────────────

_MULTI_HOP_ROUTER: Optional[MultiHopRouter] = None
_MULTI_HOP_ROUTER_LOCK = asyncio.Lock()


async def get_multi_hop_router(
    node_id: str,
    transport=None,
    dht=None,
    crdt_store=None,
) -> MultiHopRouter:
    """Get or create the singleton MultiHopRouter."""
    global _MULTI_HOP_ROUTER
    if _MULTI_HOP_ROUTER is None:
        async with _MULTI_HOP_ROUTER_LOCK:
            if _MULTI_HOP_ROUTER is None:
                _MULTI_HOP_ROUTER = MultiHopRouter(
                    node_id=node_id,
                    transport=transport,
                    dht=dht,
                    crdt_store=crdt_store,
                )
                await _MULTI_HOP_ROUTER.start()
    return _MULTI_HOP_ROUTER


def reset_multi_hop_router() -> None:
    """Reset the singleton (for testing)."""
    global _MULTI_HOP_ROUTER
    if _MULTI_HOP_ROUTER:
        # Note: caller should await _MULTI_HOP_ROUTER.stop() first
        _MULTI_HOP_ROUTER = None
