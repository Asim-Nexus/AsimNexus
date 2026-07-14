#!/usr/bin/env python3
"""
STATUS: REAL — Production-grade Kademlia DHT
ASIMNEXUS Kademlia DHT
=======================
Distributed Hash Table for mesh network.
Implements Kademlia protocol for distributed lookup and discovery.
"""

import os
import logging
import hashlib
import secrets
import time
from typing import Dict, List, Optional, Tuple, Any, Callable, TYPE_CHECKING
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio

if TYPE_CHECKING:
    from core.mesh.p2p_transport import P2PTransport, P2PMessage

from core.mesh.p2p_transport import PeerInfo, RPCMessageType, P2PMessage

logger = logging.getLogger("AsimNexus.Mesh.KademliaDHT")


# Kademlia constants (env var configurable)
K = int(os.getenv("ASIM_MESH_DHT_K", "20"))  # Replication parameter
ALPHA = int(os.getenv("ASIM_MESH_DHT_ALPHA", "3"))  # Concurrency parameter
ID_LENGTH = int(os.getenv("ASIM_MESH_DHT_ID_LENGTH", "160"))  # 160-bit IDs (SHA-1)
BUCKET_SIZE = K


class NodeType(Enum):
    """Types of nodes in DHT."""
    LOCAL = "local"
    REMOTE = "remote"


@dataclass
class NodeID:
    """160-bit node identifier."""
    value: bytes
    
    def __post_init__(self):
        if len(self.value) != ID_LENGTH // 8:
            raise ValueError(f"NodeID must be {ID_LENGTH // 8} bytes")
    
    @classmethod
    def from_string(cls, s: str) -> 'NodeID':
        """Create NodeID from string."""
        hash_bytes = hashlib.sha1(s.encode()).digest()
        return cls(hash_bytes)
    
    @classmethod
    def random(cls) -> 'NodeID':
        """Generate random NodeID."""
        return cls(secrets.token_bytes(ID_LENGTH // 8))
    
    def distance_to(self, other: 'NodeID') -> int:
        """Calculate XOR distance to another node."""
        a = int.from_bytes(self.value, 'big')
        b = int.from_bytes(other.value, 'big')
        return a ^ b
    
    def __str__(self) -> str:
        return self.value.hex()
    
    def __repr__(self) -> str:
        return f"NodeID({self.value.hex()})"
    
    def __hash__(self) -> int:
        """Make NodeID hashable for use as dict keys."""
        return hash(self.value)
    
    def __eq__(self, other) -> bool:
        """Compare NodeIDs."""
        if not isinstance(other, NodeID):
            return False
        return self.value == other.value


@dataclass
class DHTNode:
    """Node in the DHT."""
    node_id: NodeID
    ip_address: str
    port: int
    last_seen: float = field(default_factory=time.time)
    last_ping: float = field(default_factory=time.time)
    ping_failures: int = 0
    
    def is_stale(self, max_age: Optional[float] = None) -> bool:
        """Check if node is stale."""
        age = max_age if max_age is not None else float(os.getenv("ASIM_MESH_DHT_NODE_STALE_SEC", "3600"))
        return time.time() - self.last_seen > age
    
    def is_bad(self, max_failures: Optional[int] = None) -> bool:
        """Check if node is bad (too many ping failures)."""
        failures = max_failures if max_failures is not None else int(os.getenv("ASIM_MESH_DHT_MAX_FAILURES", "3"))
        return self.ping_failures >= failures
    
    def touch(self):
        """Update last seen timestamp."""
        self.last_seen = time.time()
        self.last_ping = time.time()
        self.ping_failures = 0
    
    def ping_failed(self):
        """Record a ping failure."""
        self.ping_failures += 1


@dataclass
class KBucket:
    """Kademlia routing bucket."""
    prefix: bytes
    nodes: List[DHTNode] = field(default_factory=list)
    
    def add_node(self, node: DHTNode) -> bool:
        """Add node to bucket. Returns True if added."""
        # Check if node already exists
        for i, n in enumerate(self.nodes):
            if n.node_id.value == node.node_id.value:
                self.nodes[i].touch()
                return True
        
        # If bucket not full, add node
        if len(self.nodes) < BUCKET_SIZE:
            self.nodes.append(node)
            return True
        
        # If bucket full, try to replace stale node
        for i, n in enumerate(self.nodes):
            if n.is_stale():
                self.nodes[i] = node
                return True
        
        return False
    
    def remove_node(self, node_id: NodeID) -> bool:
        """Remove node from bucket."""
        for i, n in enumerate(self.nodes):
            if n.node_id.value == node_id.value:
                self.nodes.pop(i)
                return True
        return False
    
    def get_nodes(self, exclude: Optional[NodeID] = None) -> List[DHTNode]:
        """Get nodes from bucket, optionally excluding one."""
        nodes = self.nodes[:]
        if exclude:
            nodes = [n for n in nodes if n.node_id.value != exclude.value]
        return nodes
    
    def cleanup_stale(self, max_age: Optional[float] = None) -> int:
        """Remove stale nodes. Returns count removed."""
        age = max_age if max_age is not None else float(os.getenv("ASIM_MESH_DHT_NODE_STALE_SEC", "3600"))
        before = len(self.nodes)
        self.nodes = [n for n in self.nodes if not n.is_stale(age)]
        return before - len(self.nodes)


@dataclass
class DHTValue:
    """Value stored in DHT."""
    key: NodeID
    value: bytes
    timestamp: float = field(default_factory=time.time)
    ttl: float = 86400  # 24 hours default (configurable via ASIM_MESH_DHT_TTL)
    publisher: Optional[NodeID] = None
    
    def is_expired(self) -> bool:
        """Check if value is expired."""
        return time.time() - self.timestamp > self.ttl


class KademliaDHT:
    """
    Kademlia DHT implementation.
    Distributed hash table for peer discovery and data lookup.

    Phase 1C: Single-machine optimizations — shorter refresh intervals,
    direct node insertion from config peers, bypass network I/O on localhost.
    """
    
    def __init__(
        self,
        node_id: Optional[NodeID] = None,
        port: Optional[int] = None,
        transport: Optional['P2PTransport'] = None,
    ):
        self.node_id = node_id or NodeID.random()
        self.port = port if port is not None else int(os.getenv("ASIM_MESH_DHT_PORT", "7332"))
        self.ip_address = self._get_local_ip()
        
        # Create INDEPENDENT KBucket for each bit position (fixes [KBucket]*N bug)
        self.routing_table: List[KBucket] = [KBucket(bytes([i // 8])) for i in range(ID_LENGTH)]
        self.data_store: Dict[NodeID, DHTValue] = {}
        
        self._running = False
        self._refresh_task: Optional[asyncio.Task] = None
        self.transport = transport
        
        # Track which node IDs we already have in the routing table for O(1) dedup
        self._node_set: set = set()
        
        # Phase 1C: Single-machine detection
        self._single_machine = self._is_localhost()
        
        logger.info(f"🌐 KademliaDHT initialized - NodeID: {self.node_id}")
        if self._single_machine:
            logger.info("📋 Single-machine mode: DHT refresh interval shortened")

    def _is_localhost(self) -> bool:
        """Check if we are running on localhost (single-machine mode)."""
        return self.ip_address in ("127.0.0.1", "::1", "localhost", "0.0.0.0")
    
    # ------------------------------------------------------------------
    # Lifecycle — RPC handler registration on P2P transport
    # ------------------------------------------------------------------
    
    async def start(self, transport: Optional['P2PTransport'] = None):
        """Start the DHT and register RPC handlers on the P2P transport."""
        if transport is not None:
            self.transport = transport
        
        if self.transport is None:
            logger.warning("No P2PTransport provided — DHT running in local-only mode")
            return
        
        # Register inbound RPC handlers
        self.transport.on_rpc(RPCMessageType.PING.value, self._handle_ping)
        self.transport.on_rpc(RPCMessageType.FIND_NODE.value, self._handle_find_node)
        self.transport.on_rpc(RPCMessageType.FIND_VALUE.value, self._handle_find_value)
        self.transport.on_rpc(RPCMessageType.STORE.value, self._handle_store)
        
        self._running = True
        
        # Start periodic bucket refresh
        if self._refresh_task is None or self._refresh_task.done():
            self._refresh_task = asyncio.create_task(self._refresh_loop())
        
        logger.info("🌐 KademliaDHT RPC handlers registered on P2PTransport")
    
    async def stop(self):
        """Stop the DHT and unregister handlers."""
        self._running = False
        if self._refresh_task:
            self._refresh_task.cancel()
            try:
                await self._refresh_task
            except asyncio.CancelledError:
                pass
        logger.info("🌐 KademliaDHT stopped")
    
    # ------------------------------------------------------------------
    # Inbound RPC handlers
    # ------------------------------------------------------------------
    
    async def _handle_ping(self, msg: 'P2PMessage') -> Optional['P2PMessage']:
        """Respond to PING with PONG."""
        return P2PMessage(
            msg_type=RPCMessageType.PONG.value,
            sender_id=str(self.node_id),
            msg_id=msg.msg_id,
            payload={"echo": msg.payload},
        )
    
    async def _handle_find_node(self, msg: 'P2PMessage') -> Optional['P2PMessage']:
        """Handle FIND_NODE — return closest known nodes."""
        target_id_str = msg.payload.get("target", "")
        if not target_id_str:
            return None
        
        target_id = NodeID(bytes.fromhex(target_id_str))
        closest = self.find_closest_nodes(target_id, K)
        
        nodes_payload = [
            {
                "node_id": str(n.node_id),
                "host": n.ip_address,
                "port_udp": n.port,
                "port_ws": n.port + 1,
            }
            for n in closest
        ]
        return P2PMessage(
            msg_type=RPCMessageType.NODES_FOUND.value,
            sender_id=str(self.node_id),
            msg_id=msg.msg_id,
            payload={"nodes": nodes_payload},
        )
    
    async def _handle_find_value(self, msg: 'P2PMessage') -> Optional['P2PMessage']:
        """Handle FIND_VALUE — return stored value or closest nodes."""
        key_str = msg.payload.get("key", "")
        if not key_str:
            return None
        
        key = NodeID(bytes.fromhex(key_str))
        value = self.get(key)
        
        if value is not None:
            # Return the value
            return P2PMessage(
                msg_type=RPCMessageType.VALUE_FOUND.value,
                sender_id=str(self.node_id),
                msg_id=msg.msg_id,
                payload={"value": value.hex()},
            )
        else:
            # Return closest nodes
            closest = self.find_closest_nodes(key, K)
            nodes_payload = [
                {
                    "node_id": str(n.node_id),
                    "host": n.ip_address,
                    "port_udp": n.port,
                    "port_ws": n.port + 1,
                }
                for n in closest
            ]
            return P2PMessage(
                msg_type=RPCMessageType.NODES_FOUND.value,
                sender_id=str(self.node_id),
                msg_id=msg.msg_id,
                payload={"nodes": nodes_payload, "closest_to": key_str},
            )
    
    async def _handle_store(self, msg: 'P2PMessage') -> Optional['P2PMessage']:
        """Handle STORE — store a key-value pair locally."""
        key_str = msg.payload.get("key", "")
        value_hex = msg.payload.get("value", "")
        if not key_str or not value_hex:
            return None
        
        key = NodeID(bytes.fromhex(key_str))
        value = bytes.fromhex(value_hex)
        
        ttl = msg.payload.get("ttl", 86400)
        # sender_id may be transport node_id (UUID) not hex; handle gracefully
        publisher = None
        if msg.sender_id:
            try:
                publisher = NodeID(bytes.fromhex(msg.sender_id))
            except (ValueError, TypeError):
                publisher = None
        
        self.store(key, value, ttl=ttl, publisher=publisher)
        
        return P2PMessage(
            msg_type=RPCMessageType.STORE_ACK.value,
            sender_id=str(self.node_id),
            msg_id=msg.msg_id,
            payload={"key": key_str, "stored": True},
        )
    
    async def _refresh_loop(self):
        """Periodic bucket refresh loop."""
        # Phase 1C: Shorter interval on single-machine (30s vs 3600s)
        default_interval = "30" if self._single_machine else "3600"
        interval = float(os.getenv("ASIM_MESH_DHT_REFRESH_INTERVAL", default_interval))
        while self._running:
            try:
                await asyncio.sleep(interval)
                if not self._running:
                    break
                self.cleanup()
                logger.debug("🔄 DHT refresh cycle complete")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in DHT refresh loop: {e}")
                await asyncio.sleep(60)

    def _get_local_ip(self) -> str:
        """Get local IP address."""
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"
    
    def _get_bucket_index(self, node_id: NodeID) -> int:
        """Get bucket index for a node ID."""
        distance = self.node_id.distance_to(node_id)
        # Find the position of the most significant bit
        for i in range(ID_LENGTH):
            if distance & (1 << (ID_LENGTH - 1 - i)):
                return i
        return ID_LENGTH - 1
    
    def add_node(self, node: DHTNode) -> bool:
        """Add node to routing table."""
        # Skip self
        if node.node_id.value == self.node_id.value:
            return False
        
        # O(1) dedup check
        if node.node_id.value in self._node_set:
            # Already exists — just touch
            bucket_idx = self._get_bucket_index(node.node_id)
            self.routing_table[bucket_idx].add_node(node)
            return True
        
        bucket_idx = self._get_bucket_index(node.node_id)
        bucket = self.routing_table[bucket_idx]
        added = bucket.add_node(node)
        if added:
            self._node_set.add(node.node_id.value)
        return added
    
    def remove_node(self, node_id: NodeID) -> bool:
        """Remove node from routing table."""
        if node_id.value in self._node_set:
            self._node_set.discard(node_id.value)
        bucket_idx = self._get_bucket_index(node_id)
        bucket = self.routing_table[bucket_idx]
        return bucket.remove_node(node_id)
    
    def find_node(self, node_id: NodeID) -> Optional[DHTNode]:
        """Find a node in routing table."""
        bucket_idx = self._get_bucket_index(node_id)
        bucket = self.routing_table[bucket_idx]
        for node in bucket.nodes:
            if node.node_id.value == node_id.value:
                return node
        return None
    
    def find_closest_nodes(self, target: NodeID, count: int = K) -> List[DHTNode]:
        """Find K closest nodes to target."""
        candidates = []
        
        for bucket in self.routing_table:
            for node in bucket.nodes:
                if node.node_id.value != target.value:
                    distance = target.distance_to(node.node_id)
                    candidates.append((distance, node))
        
        # Sort by distance and return closest
        candidates.sort(key=lambda x: x[0])
        return [node for _, node in candidates[:count]]
    
    def store(self, key: NodeID, value: bytes, ttl: Optional[float] = None, publisher: Optional[NodeID] = None):
        """Store a key-value pair."""
        ttl_val = ttl if ttl is not None else float(os.getenv("ASIM_MESH_DHT_TTL", "86400"))
        dht_value = DHTValue(key, value, ttl=ttl_val, publisher=publisher)
        self.data_store[key] = dht_value
        logger.debug(f"📦 Stored key: {key}")
    
    def get(self, key: NodeID) -> Optional[bytes]:
        """Get value for a key."""
        dht_value = self.data_store.get(key)
        if dht_value and not dht_value.is_expired():
            return dht_value.value
        elif dht_value and dht_value.is_expired():
            del self.data_store[key]
        return None
    
    def remove(self, key: NodeID) -> bool:
        """Remove a key-value pair."""
        if key in self.data_store:
            del self.data_store[key]
            return True
        return False
    
    async def _rpc_find_value(self, peer: PeerInfo, key_str: str,
                               timeout: float = 3.0) -> Optional['P2PMessage']:
        """Send FIND_VALUE RPC to a peer."""
        try:
            return await self.transport.rpc_call(
                peer, RPCMessageType.FIND_VALUE.value,
                {"key": key_str}, timeout=timeout,
            )
        except Exception:
            return None

    async def _rpc_find_node(self, peer: PeerInfo, target_str: str,
                              timeout: float = 3.0) -> Optional['P2PMessage']:
        """Send FIND_NODE RPC to a peer."""
        try:
            return await self.transport.rpc_call(
                peer, RPCMessageType.FIND_NODE.value,
                {"target": target_str}, timeout=timeout,
            )
        except Exception:
            return None

    def _deserialize_nodes(self, nodes_list: List[Dict]) -> List[DHTNode]:
        """Deserialize a list of node dicts into DHTNode objects."""
        result = []
        for node_info in nodes_list:
            try:
                result.append(DHTNode(
                    node_id=NodeID(bytes.fromhex(node_info["node_id"])),
                    ip_address=node_info["host"],
                    port=node_info["port_udp"],
                ))
            except Exception:
                continue
        return result

    def _peer_from_node(self, node: DHTNode) -> PeerInfo:
        """Create a PeerInfo from a DHTNode."""
        return PeerInfo(
            node_id=str(node.node_id),
            host=node.ip_address,
            port_udp=node.port,
            port_ws=node.port + 1,
        )

    async def lookup(self, key: NodeID) -> Optional[bytes]:
        """
        Iterative Kademlia lookup for a key.
        
        1. Check local store first.
        2. Query ALPHA closest known nodes with FIND_VALUE in parallel.
        3. From NODES_FOUND responses, collect closer nodes, add to routing table.
        4. Repeat: query the closest ALPHA unseen nodes from the new set.
        5. Stop when VALUE_FOUND, or no closer nodes remain, or max iterations reached.
        """
        # 1. Check local store
        local_value = self.get(key)
        if local_value:
            return local_value

        # If no transport, can't query remote nodes
        if self.transport is None:
            return None

        key_str = str(key)
        max_iterations = int(os.getenv("ASIM_MESH_DHT_LOOKUP_ITERATIONS", "5"))

        # Track queried nodes to avoid re-querying
        queried: set = set()
        # Start with closest known nodes
        shortlist = self.find_closest_nodes(key, K)

        for iteration in range(max_iterations):
            if not shortlist:
                break

            # Select ALPHA closest unqueried nodes
            to_query = []
            for node in shortlist:
                if node.node_id.value not in queried and not node.is_bad():
                    to_query.append(node)
                    if len(to_query) >= ALPHA:
                        break

            if not to_query:
                break

            # Mark as queried
            for node in to_query:
                queried.add(node.node_id.value)

            # Query all ALPHA nodes in parallel
            tasks = [
                self._rpc_find_value(self._peer_from_node(n), key_str)
                for n in to_query
            ]
            responses = await asyncio.gather(*tasks, return_exceptions=True)

            # Process responses
            new_nodes: List[DHTNode] = []
            found_value = None

            for node, response in zip(to_query, responses):
                if isinstance(response, Exception) or response is None:
                    node.ping_failed()
                    continue

                node.touch()

                if response.msg_type == RPCMessageType.VALUE_FOUND.value:
                    value_hex = response.payload.get("value", "")
                    if value_hex:
                        value_bytes = bytes.fromhex(value_hex)
                        # Cache locally; sender_id may not be hex
                        pub = None
                        if response.sender_id:
                            try:
                                pub = NodeID(bytes.fromhex(response.sender_id))
                            except (ValueError, TypeError):
                                pass
                        self.store(key, value_bytes, publisher=pub)
                        logger.debug(f"✅ Lookup found value for {key} via {node.node_id}")
                        found_value = value_bytes
                        break

                elif response.msg_type == RPCMessageType.NODES_FOUND.value:
                    # Collect closer nodes
                    nodes_list = response.payload.get("nodes", [])
                    parsed = self._deserialize_nodes(nodes_list)
                    for n in parsed:
                        if n.node_id.value not in queried:
                            self.add_node(n)
                            new_nodes.append(n)

            if found_value is not None:
                return found_value

            # Merge new nodes into shortlist, keep K closest to key
            if new_nodes:
                all_candidates = shortlist + new_nodes
                # Dedup by node_id
                seen: set = set()
                deduped = []
                for n in all_candidates:
                    if n.node_id.value not in seen:
                        seen.add(n.node_id.value)
                        deduped.append(n)
                # Sort by distance to key and keep K closest
                deduped.sort(key=lambda n: key.distance_to(n.node_id))
                shortlist = deduped[:K]
            else:
                # No new nodes — lookup exhausted
                break

        return None
    
    async def publish(self, key: NodeID, value: bytes, ttl: float = 86400):
        """
        Publish a key-value pair to the DHT.
        Store locally and replicate to closest nodes via P2P RPC.
        """
        # Store locally
        self.store(key, value, ttl, self.node_id)
        
        # If no transport, local-only publish
        if self.transport is None:
            logger.debug("📦 Published locally only (no transport)")
            return
        
        # Replicate to closest nodes via P2P RPC
        closest_nodes = self.find_closest_nodes(key, K)
        key_str = str(key)
        value_hex = value.hex()
        
        replicate_count = 0
        for node in closest_nodes:
            if node.is_bad():
                continue
            
            try:
                # Convert DHTNode to PeerInfo for transport RPC
                peer = PeerInfo(
                    node_id=str(node.node_id),
                    host=node.ip_address,
                    port_udp=node.port,
                    port_ws=node.port + 1,
                )
                # Send STORE RPC to this peer
                response = await self.transport.rpc_call(
                    peer,
                    RPCMessageType.STORE.value,
                    {"key": key_str, "value": value_hex, "ttl": ttl},
                    timeout=3.0,
                )
                if response is not None and response.msg_type == RPCMessageType.STORE_ACK.value:
                    replicate_count += 1
                    node.touch()
                    logger.debug(f"📦 Replicated {key} to {node.node_id}")
            except Exception as e:
                logger.error(f"Publish error to {node.node_id}: {e}")
                node.ping_failed()
        
        if replicate_count > 0:
            logger.info(f"📦 Published {key} — replicated to {replicate_count} node(s)")
    
    def cleanup(self):
        """Cleanup stale nodes and expired values."""
        # Cleanup stale nodes
        for bucket in self.routing_table:
            removed = bucket.cleanup_stale()
            if removed > 0:
                logger.debug(f"🧹 Cleaned {removed} stale nodes from bucket")
        
        # Cleanup expired values
        expired_keys = [k for k, v in self.data_store.items() if v.is_expired()]
        for key in expired_keys:
            del self.data_store[key]
        
        if expired_keys:
            logger.debug(f"🧹 Cleaned {len(expired_keys)} expired values")
    
    def add_nodes_from_bootstrap(self, peers: List[Dict[str, Any]]) -> int:
        """Add peers discovered via bootstrap into the DHT routing table.
        
        Handles both hex-encoded 160-bit node IDs (from DHT-aware peers)
        and UUID-style node IDs (from P2PTransport/NodeRegistry) by
        hashing UUID strings with SHA-1 to produce a valid DHT node ID.
        
        Args:
            peers: List of peer info dicts with node_id, host, port_udp keys.
        
        Returns:
            Number of peers successfully added.
        """
        count = 0
        for peer in peers:
            try:
                node_id_str = peer.get("node_id", "")
                host = peer.get("host", "")
                port_udp = peer.get("port_udp", 0)
                if not node_id_str or not host or not port_udp:
                    continue
                
                # Try hex decode first (DHT-native node IDs), fall back to SHA-1 hash (UUID strings)
                try:
                    node_id_bytes = bytes.fromhex(node_id_str)
                except ValueError:
                    # UUID or string node_id — hash to 160 bits
                    node_id_bytes = hashlib.sha1(node_id_str.encode()).digest()
                
                node = DHTNode(
                    node_id=NodeID(node_id_bytes),
                    ip_address=host,
                    port=port_udp,
                )
                if self.add_node(node):
                    count += 1
            except Exception as e:
                logger.debug(f"Failed to add bootstrap peer to DHT: {e}")
                continue
        if count > 0:
            logger.info(f"📡 Added {count} bootstrap peers to DHT routing table")
        return count

    def add_nodes_from_single_machine_peers(self, peer_spec: str = "") -> int:
        """
        Parse ASIM_SINGLE_MACHINE_PEERS format and add nodes to DHT routing table.
        
        Format: "node_id:host:port_udp:port_ws,..."
        Port_ws is accepted but ignored for DHT routing (only port_udp is used).
        
        Args:
            peer_spec: String in ASIM_SINGLE_MACHINE_PEERS format.
                       If empty, reads from the ASIM_SINGLE_MACHINE_PEERS env var.
        
        Returns:
            Number of nodes successfully added.
        """
        if not peer_spec:
            peer_spec = os.getenv("ASIM_SINGLE_MACHINE_PEERS", "")
        if not peer_spec:
            return 0
        
        count = 0
        for entry in peer_spec.split(","):
            entry = entry.strip()
            if not entry:
                continue
            parts = entry.split(":")
            if len(parts) < 4:
                logger.warning(f"Malformed single-machine peer entry: {entry}")
                continue
            node_id_str = parts[0].strip()
            host = parts[1].strip()
            try:
                port_udp = int(parts[2])
            except ValueError:
                logger.warning(f"Invalid port in single-machine peer entry: {entry}")
                continue
            
            if not node_id_str or not host:
                continue
            
            # Hash the string node_id to a 160-bit DHT ID
            try:
                node_id_bytes = bytes.fromhex(node_id_str)
            except ValueError:
                node_id_bytes = hashlib.sha1(node_id_str.encode()).digest()
            
            node = DHTNode(
                node_id=NodeID(node_id_bytes),
                ip_address=host,
                port=port_udp,
            )
            if self.add_node(node):
                count += 1
        
        if count > 0:
            logger.info(f"📋 Added {count} single-machine peer(s) to DHT routing table")
        return count

    def get_stats(self) -> Dict[str, Any]:
        """Get DHT statistics."""
        total_nodes = sum(len(bucket.nodes) for bucket in self.routing_table)
        total_values = len(self.data_store)
        
        return {
            "node_id": str(self.node_id),
            "ip_address": self.ip_address,
            "port": self.port,
            "total_nodes": total_nodes,
            "total_values": total_values,
            "buckets": len(self.routing_table)
        }


# Global Kademlia DHT instance
_kademlia_dht: Optional[KademliaDHT] = None


def get_kademlia_dht(
    node_id: Optional[NodeID] = None,
    port: Optional[int] = None,
    transport: Optional['P2PTransport'] = None,
) -> KademliaDHT:
    """Get or create global Kademlia DHT instance."""
    global _kademlia_dht
    if _kademlia_dht is None:
        _kademlia_dht = KademliaDHT(node_id, port, transport)
    return _kademlia_dht


def reset_kademlia_dht():
    """Reset global Kademlia DHT instance (for testing)."""
    global _kademlia_dht
    _kademlia_dht = None
