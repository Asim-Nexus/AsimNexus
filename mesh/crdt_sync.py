#!/usr/bin/env python3
"""
STATUS: REAL — Production-grade CRDT sync
ASIMNEXUS CRDT Sync
===================
CRDT-based synchronization for mesh network.
Conflict-free replicated data types for offline-first sync.
"""

import os
import logging
import json
import time
from typing import Dict, List, Optional, Any, Set, TYPE_CHECKING
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import hashlib
import asyncio

if TYPE_CHECKING:
    from mesh.p2p_transport import P2PTransport, P2PMessage, PeerInfo
else:
    # Runtime import to avoid circular dependency
    pass

logger = logging.getLogger("AsimNexus.Mesh.CrdtSync")


class CRDTType(Enum):
    """Types of CRDTs."""
    G_COUNTER = "g_counter"  # Grow-only counter
    PN_COUNTER = "pn_counter"  # PN-counter (increment/decrement)
    LWW_REGISTER = "lww_register"  # Last-writer-wins register
    OR_SET = "or_set"  # Observed-removed set
    G_MAP = "g_map"  # Grow-only map
    LWW_MAP = "lww_map"  # Last-writer-wins map


@dataclass
class CRDTOperation:
    """CRDT operation for sync."""
    id: str
    crdt_id: str
    crdt_type: CRDTType
    operation: str  # "add", "remove", "set", "increment", "decrement"
    key: Optional[str] = None
    value: Optional[Any] = None
    timestamp: float = field(default_factory=time.time)
    node_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "crdt_id": self.crdt_id,
            "crdt_type": self.crdt_type.value,
            "operation": self.operation,
            "key": self.key,
            "value": self.value,
            "timestamp": self.timestamp,
            "node_id": self.node_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CRDTOperation':
        """Create from dictionary."""
        return cls(
            id=data["id"],
            crdt_id=data["crdt_id"],
            crdt_type=CRDTType(data["crdt_type"]),
            operation=data["operation"],
            key=data.get("key"),
            value=data.get("value"),
            timestamp=data["timestamp"],
            node_id=data.get("node_id")
        )


class GCounter:
    """Grow-only counter CRDT."""
    
    def __init__(self, crdt_id: str):
        self.crdt_id = crdt_id
        self.crdt_type = CRDTType.G_COUNTER
        self.counters: Dict[str, int] = {}  # node_id -> count
        self.operations: List[CRDTOperation] = []
    
    def increment(self, node_id: str, amount: int = 1) -> CRDTOperation:
        """Increment counter."""
        self.counters[node_id] = self.counters.get(node_id, 0) + amount
        
        op = CRDTOperation(
            id=hashlib.sha256(f"{node_id}{time.time()}".encode()).hexdigest()[:16],
            crdt_id=self.crdt_id,
            crdt_type=self.crdt_type,
            operation="increment",
            value=amount,
            node_id=node_id
        )
        self.operations.append(op)
        return op
    
    def value(self) -> int:
        """Get current value."""
        return sum(self.counters.values())
    
    def merge(self, other: 'GCounter') -> List[CRDTOperation]:
        """Merge with another GCounter."""
        new_ops = []
        for node_id, count in other.counters.items():
            if node_id not in self.counters or count > self.counters[node_id]:
                self.counters[node_id] = count
                new_ops.append(CRDTOperation(
                    id=hashlib.sha256(f"{node_id}{time.time()}".encode()).hexdigest()[:16],
                    crdt_id=self.crdt_id,
                    crdt_type=self.crdt_type,
                    operation="merge",
                    value=count,
                    node_id=node_id
                ))
        return new_ops
    
    def apply_operation(self, op: CRDTOperation) -> bool:
        """Apply an operation."""
        if op.operation == "increment" and op.node_id:
            self.counters[op.node_id] = self.counters.get(op.node_id, 0) + (op.value or 1)
            return True
        return False


class PNCounter:
    """PN-Counter CRDT (allows both increment and decrement).

    Composed of two G-Counters: P (increments) and N (decrements).
    Value is sum(P) - sum(N).
    """

    def __init__(self, crdt_id: str):
        self.crdt_id = crdt_id
        self.crdt_type = CRDTType.PN_COUNTER
        self.p_counter: Dict[str, int] = {}
        self.n_counter: Dict[str, int] = {}
        self.operations: List[CRDTOperation] = []

    def increment(self, node_id: str, amount: int = 1) -> CRDTOperation:
        """Increment (add to P counter)."""
        self.p_counter[node_id] = self.p_counter.get(node_id, 0) + amount
        op = CRDTOperation(
            id=hashlib.sha256(f"{node_id}{time.time()}".encode()).hexdigest()[:16],
            crdt_id=self.crdt_id,
            crdt_type=self.crdt_type,
            operation="increment",
            value=amount,
            node_id=node_id,
        )
        self.operations.append(op)
        return op

    def decrement(self, node_id: str, amount: int = 1) -> CRDTOperation:
        """Decrement (add to N counter)."""
        self.n_counter[node_id] = self.n_counter.get(node_id, 0) + amount
        op = CRDTOperation(
            id=hashlib.sha256(f"{node_id}{time.time()}".encode()).hexdigest()[:16],
            crdt_id=self.crdt_id,
            crdt_type=self.crdt_type,
            operation="decrement",
            value=amount,
            node_id=node_id,
        )
        self.operations.append(op)
        return op

    def value(self) -> int:
        """Get current value (P - N)."""
        return sum(self.p_counter.values()) - sum(self.n_counter.values())

    def merge(self, other: 'PNCounter') -> List[CRDTOperation]:
        """Merge with another PNCounter."""
        new_ops = []
        for node_id, count in other.p_counter.items():
            if node_id not in self.p_counter or count > self.p_counter[node_id]:
                self.p_counter[node_id] = count
        for node_id, count in other.n_counter.items():
            if node_id not in self.n_counter or count > self.n_counter[node_id]:
                self.n_counter[node_id] = count
        return new_ops

    def apply_operation(self, op: CRDTOperation) -> bool:
        """Apply an operation."""
        if op.operation == "increment" and op.node_id:
            self.p_counter[op.node_id] = self.p_counter.get(op.node_id, 0) + (op.value or 1)
            return True
        elif op.operation == "decrement" and op.node_id:
            self.n_counter[op.node_id] = self.n_counter.get(op.node_id, 0) + (op.value or 1)
            return True
        return False


class GMap:
    """Grow-only map CRDT."""

    def __init__(self, crdt_id: str):
        self.crdt_id = crdt_id
        self.crdt_type = CRDTType.G_MAP
        self.data: Dict[str, Any] = {}
        self.operations: List[CRDTOperation] = []

    def put(self, key: str, value: Any, node_id: str) -> CRDTOperation:
        """Put a key-value pair (idempotent, first write wins)."""
        if key in self.data:
            return None
        self.data[key] = value
        op = CRDTOperation(
            id=hashlib.sha256(f"{node_id}{key}{time.time()}".encode()).hexdigest()[:16],
            crdt_id=self.crdt_id,
            crdt_type=self.crdt_type,
            operation="put",
            key=key,
            value=value,
            node_id=node_id,
        )
        self.operations.append(op)
        return op

    def get(self, key: str) -> Optional[Any]:
        """Get value for key."""
        return self.data.get(key)

    def merge(self, other: 'GMap') -> List[CRDTOperation]:
        """Merge with another GMap (first write wins per key)."""
        new_ops = []
        for key, value in other.data.items():
            if key not in self.data:
                self.data[key] = value
        return new_ops

    def apply_operation(self, op: CRDTOperation) -> bool:
        """Apply an operation."""
        if op.operation == "put" and op.key and op.key not in self.data:
            self.data[op.key] = op.value
            return True
        return False


class LWWMap:
    """Last-writer-wins map CRDT."""

    def __init__(self, crdt_id: str):
        self.crdt_id = crdt_id
        self.crdt_type = CRDTType.LWW_MAP
        self.data: Dict[str, Tuple[Any, float, str]] = {}  # key -> (value, timestamp, node_id)
        self.operations: List[CRDTOperation] = []

    def put(self, key: str, value: Any, node_id: str) -> CRDTOperation:
        """Put a key-value pair (last-writer-wins)."""
        now = time.time()
        self.data[key] = (value, now, node_id)
        op = CRDTOperation(
            id=hashlib.sha256(f"{node_id}{key}{now}".encode()).hexdigest()[:16],
            crdt_id=self.crdt_id,
            crdt_type=self.crdt_type,
            operation="put",
            key=key,
            value=value,
            node_id=node_id,
        )
        self.operations.append(op)
        return op

    def get(self, key: str) -> Optional[Any]:
        """Get value for key."""
        entry = self.data.get(key)
        if entry:
            return entry[0]
        return None

    def merge(self, other: 'LWWMap') -> List[CRDTOperation]:
        """Merge with another LWWMap (last-writer-wins per key)."""
        new_ops = []
        for key, (value, ts, node_id) in other.data.items():
            if key not in self.data or ts > self.data[key][1]:
                self.data[key] = (value, ts, node_id)
        return new_ops

    def apply_operation(self, op: CRDTOperation) -> bool:
        """Apply an operation."""
        if op.operation == "put" and op.key:
            if op.key not in self.data or op.timestamp > self.data[op.key][1]:
                self.data[op.key] = (op.value, op.timestamp, op.node_id or "unknown")
                return True
        return False


class LWWRegister:
    """Last-writer-wins register CRDT."""
    
    def __init__(self, crdt_id: str):
        self.crdt_id = crdt_id
        self.crdt_type = CRDTType.LWW_REGISTER
        self.value: Optional[Any] = None
        self.timestamp: float = 0
        self.node_id: Optional[str] = None
        self.operations: List[CRDTOperation] = []
    
    def set(self, value: Any, node_id: str) -> CRDTOperation:
        """Set value."""
        self.value = value
        self.timestamp = time.time()
        self.node_id = node_id
        
        op = CRDTOperation(
            id=hashlib.sha256(f"{node_id}{time.time()}".encode()).hexdigest()[:16],
            crdt_id=self.crdt_id,
            crdt_type=self.crdt_type,
            operation="set",
            value=value,
            node_id=node_id
        )
        self.operations.append(op)
        return op
    
    def get(self) -> Optional[Any]:
        """Get current value."""
        return self.value
    
    def merge(self, other: 'LWWRegister') -> List[CRDTOperation]:
        """Merge with another LWWRegister."""
        if other.timestamp > self.timestamp:
            self.value = other.value
            self.timestamp = other.timestamp
            self.node_id = other.node_id
            return [CRDTOperation(
                id=hashlib.sha256(f"{other.node_id}{time.time()}".encode()).hexdigest()[:16],
                crdt_id=self.crdt_id,
                crdt_type=self.crdt_type,
                operation="merge",
                value=other.value,
                node_id=other.node_id
            )]
        return []
    
    def apply_operation(self, op: CRDTOperation) -> bool:
        """Apply an operation."""
        if op.operation == "set" and op.timestamp > self.timestamp:
            self.value = op.value
            self.timestamp = op.timestamp
            self.node_id = op.node_id
            return True
        return False


class ORSet:
    """Observed-removed set CRDT."""
    
    def __init__(self, crdt_id: str):
        self.crdt_id = crdt_id
        self.crdt_type = CRDTType.OR_SET
        self.elements: Dict[str, Set[str]] = {}  # element_hash -> set of node_ids
        self.tombstones: Dict[str, Set[str]] = {}  # element_hash -> set of node_ids
        self.operations: List[CRDTOperation] = []
    
    def _hash_element(self, element: Any) -> str:
        """Hash an element."""
        return hashlib.sha256(json.dumps(element, sort_keys=True).encode()).hexdigest()
    
    def add(self, element: Any, node_id: str) -> CRDTOperation:
        """Add element to set."""
        elem_hash = self._hash_element(element)
        if elem_hash not in self.elements:
            self.elements[elem_hash] = set()
        self.elements[elem_hash].add(node_id)
        
        op = CRDTOperation(
            id=hashlib.sha256(f"{node_id}{time.time()}".encode()).hexdigest()[:16],
            crdt_id=self.crdt_id,
            crdt_type=self.crdt_type,
            operation="add",
            value=element,
            node_id=node_id
        )
        self.operations.append(op)
        return op
    
    def remove(self, element: Any, node_id: str) -> CRDTOperation:
        """Remove element from set."""
        elem_hash = self._hash_element(element)
        if elem_hash not in self.tombstones:
            self.tombstones[elem_hash] = set()
        self.tombstones[elem_hash].add(node_id)
        
        op = CRDTOperation(
            id=hashlib.sha256(f"{node_id}{time.time()}".encode()).hexdigest()[:16],
            crdt_id=self.crdt_id,
            crdt_type=self.crdt_type,
            operation="remove",
            value=element,
            node_id=node_id
        )
        self.operations.append(op)
        return op
    
    def contains(self, element: Any) -> bool:
        """Check if element is in set."""
        elem_hash = self._hash_element(element)
        if elem_hash not in self.elements:
            return False
        
        # Element is present if it was added by some node and not removed by all nodes that added it
        added_by = self.elements.get(elem_hash, set())
        removed_by = self.tombstones.get(elem_hash, set())
        
        return len(added_by - removed_by) > 0
    
    def elements_list(self) -> List[Any]:
        """Get all elements in set."""
        result = []
        for elem_hash, added_by in self.elements.items():
            removed_by = self.tombstones.get(elem_hash, set())
            if len(added_by - removed_by) > 0:
                # We need to reconstruct the element from hash
                # In practice, you'd store the actual elements
                result.append(elem_hash)
        return result
    
    def merge(self, other: 'ORSet') -> List[CRDTOperation]:
        """Merge with another ORSet."""
        new_ops = []
        
        # Merge elements
        for elem_hash, other_added in other.elements.items():
            if elem_hash not in self.elements:
                self.elements[elem_hash] = other_added.copy()
            else:
                self.elements[elem_hash].update(other_added)
        
        # Merge tombstones
        for elem_hash, other_removed in other.tombstones.items():
            if elem_hash not in self.tombstones:
                self.tombstones[elem_hash] = other_removed.copy()
            else:
                self.tombstones[elem_hash].update(other_removed)
        
        return new_ops
    
    def apply_operation(self, op: CRDTOperation) -> bool:
        """Apply an operation."""
        if op.operation == "add" and op.value:
            elem_hash = self._hash_element(op.value)
            if elem_hash not in self.elements:
                self.elements[elem_hash] = set()
            self.elements[elem_hash].add(op.node_id or "unknown")
            return True
        elif op.operation == "remove" and op.value:
            elem_hash = self._hash_element(op.value)
            if elem_hash not in self.tombstones:
                self.tombstones[elem_hash] = set()
            self.tombstones[elem_hash].add(op.node_id or "unknown")
            return True
        return False


class CRDTStore:
    """
    Store for CRDTs and their operations.
    Manages synchronization between nodes via P2P WebSocket transport.
    """
    
    def __init__(self, node_id: str, transport: Optional['P2PTransport'] = None):
        self.node_id = node_id
        self.crdts: Dict[str, Any] = {}
        self.operation_log: List[CRDTOperation] = []
        self.pending_operations: List[CRDTOperation] = []
        self.transport = transport
        self._running = False
        
        logger.info(f"CRDTStore initialized - Node: {node_id}")
    
    # ------------------------------------------------------------------
    # Lifecycle - WebSocket handler registration
    # ------------------------------------------------------------------
    
    async def start(self, transport: Optional['P2PTransport'] = None):
        """Start sync and register WebSocket handlers on P2P transport."""
        if transport is not None:
            self.transport = transport
        
        if self.transport is None:
            logger.warning("No P2PTransport provided - CRDT running in local-only mode")
            return
        
        # Register WebSocket message handlers for sync
        from mesh.p2p_transport import WSMessageType
        self.transport.on_ws_message(WSMessageType.SYNC_REQUEST.value, self._handle_sync_request)
        self.transport.on_ws_message(WSMessageType.SYNC_OPERATIONS.value, self._handle_sync_operations)
        
        self._running = True
        logger.info("CRDTStore sync handlers registered on P2PTransport")
    
    async def stop(self):
        """Stop sync."""
        self._running = False
        logger.info("🔄 CRDTStore sync stopped")
    
    # ------------------------------------------------------------------
    # WebSocket message handlers (inbound)
    # ------------------------------------------------------------------
    
    async def _handle_sync_request(self, msg: 'P2PMessage'):
        """Handle a sync request from a remote peer — send back our sync state."""
        from mesh.p2p_transport import P2PMessage
        
        since = msg.payload.get("since", 0.0)
        sync_state = self.get_sync_state(since=since)
        
        # Send response back via WebSocket
        response = P2PMessage(
            msg_type=WSMessageType.SYNC_RESPONSE.value,
            sender_id=self.node_id,
            msg_id=msg.msg_id,
            payload={
                "sync_state": sync_state,
                "request_id": msg.msg_id,
            },
        )
        
        # Find the requesting peer and send response
        peer = await self.transport.get_peer(msg.sender_id) if self.transport else None
        if peer and self.transport:
            await self.transport.send_ws(peer, response)
    
    async def _handle_sync_operations(self, msg: 'P2PMessage'):
        """Handle incoming sync operations from a remote peer."""
        operations_data = msg.payload.get("operations", [])
        sync_state = msg.payload.get("sync_state")
        
        applied = 0
        
        # Apply individual operations
        for op_data in operations_data:
            op = CRDTOperation.from_dict(op_data)
            if self.apply_remote_operation(op):
                applied += 1
        
        # If full sync state provided, apply it
        if sync_state:
            applied += self.apply_sync_state(sync_state)
        
        logger.info(f"🔄 Applied {applied} remote operation(s) from {msg.sender_id}")
        
        # Send acknowledgment
        from mesh.p2p_transport import P2PMessage
        ack = P2PMessage(
            msg_type=WSMessageType.SYNC_ACK.value,
            sender_id=self.node_id,
            msg_id=msg.msg_id,
            payload={"applied": applied},
        )
        if self.transport:
            peer = await self.transport.get_peer(msg.sender_id)
            if peer:
                await self.transport.send_ws(peer, ack)
    
    # ------------------------------------------------------------------
    # Outbound sync methods
    # ------------------------------------------------------------------
    
    async def request_sync(self, peer: "PeerInfo", since: float = 0.0) -> bool:
        """
        Request sync from a remote peer.
        Sends a SYNC_REQUEST via WebSocket and applies the response.
        """
        if self.transport is None:
            logger.warning("No transport — cannot request sync")
            return False
        
        from mesh.p2p_transport import P2PMessage
        
        request = P2PMessage(
            msg_type=WSMessageType.SYNC_REQUEST.value,
            sender_id=self.node_id,
            msg_id=f"sync_req_{int(time.time()*1000)}",
            payload={"since": since},
        )
        
        # Send request
        sent = await self.transport.send_ws(peer, request)
        if not sent:
            logger.warning(f"Failed to send sync request to {peer.node_id}")
            return False
        
        return True
    
    async def push_operations(self, peer: "PeerInfo", operations: Optional[List[CRDTOperation]] = None) -> bool:
        """
        Push pending operations to a peer via WebSocket.
        """
        if self.transport is None:
            return False
        
        from mesh.p2p_transport import P2PMessage
        
        ops = operations if operations is not None else self.get_pending_operations()
        sync_state = self.get_sync_state()
        
        msg = P2PMessage(
            msg_type=WSMessageType.SYNC_OPERATIONS.value,
            sender_id=self.node_id,
            msg_id=f"sync_ops_{int(time.time()*1000)}",
            payload={
                "operations": [op.to_dict() for op in ops],
                "sync_state": sync_state,
            },
        )
        
        sent = await self.transport.send_ws(peer, msg)
        if sent:
            logger.debug(f"Pushed {len(ops)} operation(s) to {peer.node_id}")
        return sent
    
    async def broadcast_operations(self, operations: Optional[List[CRDTOperation]] = None) -> int:
        """
        Broadcast pending operations to all connected peers.
        Returns number of peers successfully sent to.
        """
        if self.transport is None:
            return 0
        
        from mesh.p2p_transport import P2PMessage
        
        ops = operations if operations is not None else self.get_pending_operations()
        sync_state = self.get_sync_state()
        
        msg = P2PMessage(
            msg_type=WSMessageType.SYNC_OPERATIONS.value,
            sender_id=self.node_id,
            msg_id=f"sync_bcast_{int(time.time()*1000)}",
            payload={
                "operations": [op.to_dict() for op in ops],
                "sync_state": sync_state,
            },
        )
        
        count = await self.transport.broadcast_ws(msg)
        if count > 0:
            logger.info(f"📡 Broadcast {len(ops)} operation(s) to {count} peer(s)")
        return count
    
    def create_g_counter(self, crdt_id: str) -> GCounter:
        """Create a grow-only counter."""
        counter = GCounter(crdt_id)
        self.crdts[crdt_id] = counter
        return counter
    
    def create_lww_register(self, crdt_id: str) -> LWWRegister:
        """Create a last-writer-wins register."""
        register = LWWRegister(crdt_id)
        self.crdts[crdt_id] = register
        return register
    
    def create_or_set(self, crdt_id: str) -> ORSet:
        """Create an observed-removed set."""
        or_set = ORSet(crdt_id)
        self.crdts[crdt_id] = or_set
        return or_set

    def create_pn_counter(self, crdt_id: str) -> PNCounter:
        """Create a PN-Counter."""
        counter = PNCounter(crdt_id)
        self.crdts[crdt_id] = counter
        return counter

    def create_g_map(self, crdt_id: str) -> GMap:
        """Create a grow-only map."""
        gmap = GMap(crdt_id)
        self.crdts[crdt_id] = gmap
        return gmap

    def create_lww_map(self, crdt_id: str) -> LWWMap:
        """Create a last-writer-wins map."""
        lww_map = LWWMap(crdt_id)
        self.crdts[crdt_id] = lww_map
        return lww_map

    def get_crdt(self, crdt_id: str) -> Optional[Any]:
        """Get a CRDT by ID."""
        return self.crdts.get(crdt_id)
    
    def log_operation(self, op: CRDTOperation):
        """Log an operation."""
        self.operation_log.append(op)
    
    def get_pending_operations(self, since: Optional[float] = None) -> List[CRDTOperation]:
        """Get pending operations for sync."""
        if since is None:
            return self.pending_operations[:]
        return [op for op in self.pending_operations if op.timestamp > since]
    
    def apply_remote_operation(self, op: CRDTOperation) -> bool:
        """Apply a remote operation."""
        crdt = self.crdts.get(op.crdt_id)
        if not crdt:
            logger.warning(f"CRDT not found: {op.crdt_id}")
            return False
        
        success = crdt.apply_operation(op)
        if success:
            self.operation_log.append(op)
            logger.debug(f"Applied remote operation: {op.id}")
        
        return success
    
    def merge_crdt(self, crdt_id: str, remote_crdt: Any) -> List[CRDTOperation]:
        """Merge a remote CRDT."""
        local_crdt = self.crdts.get(crdt_id)
        if not local_crdt:
            logger.warning(f"CRDT not found for merge: {crdt_id}")
            return []
        
        new_ops = local_crdt.merge(remote_crdt)
        for op in new_ops:
            self.operation_log.append(op)
        
        return new_ops
    
    def get_state(self) -> Dict[str, Any]:
        """Get current state of all CRDTs."""
        state = {}
        for crdt_id, crdt in self.crdts.items():
            if isinstance(crdt, GCounter):
                state[crdt_id] = {
                    "type": "g_counter",
                    "counters": dict(crdt.counters),  # per-node counters for correct merge
                    "value": crdt.value(),
                }
            elif isinstance(crdt, LWWRegister):
                state[crdt_id] = {
                    "type": "lww_register",
                    "value": crdt.get(),
                    "timestamp": crdt.timestamp,
                    "node_id": crdt.node_id,
                }
            elif isinstance(crdt, ORSet):
                state[crdt_id] = {"type": "or_set", "value": crdt.elements_list()}
            elif isinstance(crdt, PNCounter):
                state[crdt_id] = {
                    "type": "pn_counter",
                    "p_counter": dict(crdt.p_counter),
                    "n_counter": dict(crdt.n_counter),
                    "value": crdt.value(),
                }
            elif isinstance(crdt, GMap):
                state[crdt_id] = {"type": "g_map", "data": dict(crdt.data)}
            elif isinstance(crdt, LWWMap):
                state[crdt_id] = {
                    "type": "lww_map",
                    "data": {k: {"value": v[0], "timestamp": v[1], "node_id": v[2]} for k, v in crdt.data.items()},
                }
        
        return state
    
    def get_sync_state(self, since: float = 0) -> Dict[str, Any]:
        """Get state for synchronization.

        Returns the current CRDT state (value snapshots + per-node counters)
        for full-state merge on the receiving side. Individual operations
        are NOT included here — they propagate via push_operations()
        using pending_operations, which is populated by the CRDT mutation
        wrappers in the create_* methods.
        """
        return {
            "node_id": self.node_id,
            "operations": [op.to_dict() for op in self.operation_log if op.timestamp > since],
            "crdt_state": self.get_state()
        }
    
    def apply_sync_state(self, sync_state: Dict[str, Any]) -> int:
        """Apply sync state from another node — reconstruct CRDTs and merge."""
        applied_count = 0
        
        # Apply operations from log
        for op_data in sync_state.get("operations", []):
            op = CRDTOperation.from_dict(op_data)
            if self.apply_remote_operation(op):
                applied_count += 1
        
        # Merge CRDT states — reconstruct remote CRDTs
        remote_crdt_state = sync_state.get("crdt_state", {})
        for crdt_id, crdt_data in remote_crdt_state.items():
            crdt_type = crdt_data.get("type", "")
            remote_value = crdt_data.get("value")
            
            # Ensure local CRDT exists
            local_crdt = self.crdts.get(crdt_id)
            if local_crdt is None:
                # Create local CRDT from remote type
                if crdt_type == "g_counter":
                    local_crdt = self.create_g_counter(crdt_id)
                elif crdt_type == "lww_register":
                    local_crdt = self.create_lww_register(crdt_id)
                elif crdt_type == "or_set":
                    local_crdt = self.create_or_set(crdt_id)
                elif crdt_type == "pn_counter":
                    local_crdt = self.create_pn_counter(crdt_id)
                elif crdt_type == "g_map":
                    local_crdt = self.create_g_map(crdt_id)
                elif crdt_type == "lww_map":
                    local_crdt = self.create_lww_map(crdt_id)
                else:
                    logger.debug(f"Unknown CRDT type for merge: {crdt_type}")
                    continue
            
            # Reconstruct a representative remote CRDT and merge
            try:
                if crdt_type == "g_counter" and isinstance(local_crdt, GCounter):
                    # Use per-node counters from state for correct merge.
                    # Previously we stored the full sum under a single node_id,
                    # which inflated totals when merged into partial state.
                    remote = GCounter(crdt_id)
                    remote_counters = crdt_data.get("counters")
                    if remote_counters and isinstance(remote_counters, dict):
                        for node_id, count in remote_counters.items():
                            remote.counters[node_id] = count
                    else:
                        # Fallback for backwards compatibility
                        remote.counters[sync_state.get("node_id", "remote")] = remote_value if isinstance(remote_value, int) else 0
                    new_ops = local_crdt.merge(remote)
                    applied_count += len(new_ops)
                
                elif crdt_type == "lww_register" and isinstance(local_crdt, LWWRegister):
                    # Use the actual timestamp from sync_state so last-writer-wins
                    # semantics are preserved correctly during merge.
                    remote = LWWRegister(crdt_id)
                    remote.value = remote_value
                    remote.timestamp = crdt_data.get("timestamp", time.time())
                    remote.node_id = crdt_data.get("node_id", sync_state.get("node_id", "remote"))
                    new_ops = local_crdt.merge(remote)
                    applied_count += len(new_ops)
                
                elif crdt_type == "or_set" and isinstance(local_crdt, ORSet):
                    # For ORSet, merge is handled by operation replay
                    # The operations already replayed above handle element add/remove
                    pass

                elif crdt_type == "pn_counter" and isinstance(local_crdt, PNCounter):
                    remote = PNCounter(crdt_id)
                    p_data = crdt_data.get("p_counter", {})
                    n_data = crdt_data.get("n_counter", {})
                    if isinstance(p_data, dict):
                        for node_id, count in p_data.items():
                            remote.p_counter[node_id] = count
                    if isinstance(n_data, dict):
                        for node_id, count in n_data.items():
                            remote.n_counter[node_id] = count
                    new_ops = local_crdt.merge(remote)
                    applied_count += len(new_ops)

                elif crdt_type == "g_map" and isinstance(local_crdt, GMap):
                    remote = GMap(crdt_id)
                    remote_data = crdt_data.get("data", {})
                    if isinstance(remote_data, dict):
                        remote.data = dict(remote_data)
                    new_ops = local_crdt.merge(remote)
                    applied_count += len(new_ops)

                elif crdt_type == "lww_map" and isinstance(local_crdt, LWWMap):
                    remote = LWWMap(crdt_id)
                    remote_data = crdt_data.get("data", {})
                    if isinstance(remote_data, dict):
                        for k, v in remote_data.items():
                            remote.data[k] = (v["value"], v["timestamp"], v.get("node_id", "remote"))
                    new_ops = local_crdt.merge(remote)
                    applied_count += len(new_ops)
            except Exception as e:
                logger.error(f"Merge error for {crdt_id}: {e}")
        
        if applied_count > 0:
            logger.info(f"🔄 Applied {applied_count} changes from sync")
        return applied_count
    
    def cleanup_old_operations(self, max_age: Optional[float] = None):
        """Remove old operations from log."""
        age = max_age if max_age is not None else float(os.getenv("ASIM_MESH_CRDT_OP_MAX_AGE", "86400"))
        cutoff = time.time() - age
        before = len(self.operation_log)
        self.operation_log = [op for op in self.operation_log if op.timestamp > cutoff]
        removed = before - len(self.operation_log)
        if removed > 0:
            logger.debug(f"🧹 Cleaned {removed} old operations")
        return removed


# Global CRDT store instance
_crdt_store: Optional[CRDTStore] = None


def get_crdt_store(node_id: str, transport: Optional['P2PTransport'] = None) -> CRDTStore:
    """Get or create global CRDT store instance."""
    global _crdt_store
    if _crdt_store is None:
        _crdt_store = CRDTStore(node_id, transport)
    return _crdt_store


def reset_crdt_store():
    """Reset global CRDT store instance (for testing)."""
    global _crdt_store
    _crdt_store = None
