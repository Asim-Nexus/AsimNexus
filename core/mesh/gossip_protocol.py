"""
core/mesh/gossip_protocol.py
AsimNexus — Gossip Protocol for Epidemic State Dissemination
==============================================================

Implements a gossip/epidemic protocol for propagating state changes
across the mesh network without requiring a central coordinator.

Protocol:
  - Push-Pull Gossip: each round, each node pushes its state digest to
    a random subset of peers, and pulls any missing updates.
  - Anti-Entropy: periodic full-state reconciliation with random peers.
  - Phi-Accrual Failure Detection: adaptive suspicion based on heartbeat
    timing history (instead of fixed timeouts).
  - Pluggable transport: works over DHT, direct TCP, or NAT hole-punch.

Design:
  - Each node maintains a version vector (vector clock) for causal ordering.
  - Gossip rounds run on a configurable interval (default: 5s).
  - Fanout controls how many peers each round gossips with (default: 3).
  - State entries have TTLs and are automatically pruned.

Usage:
    from core.mesh.gossip_protocol import GossipProtocol, GossipMessage

    gp = GossipProtocol(node_id="node_001")
    gp.add_peer("peer_001")
    gp.update_state("key", {"value": 123})
    await gp.gossip_round()
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import math
import random
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("AsimNexus.Gossip")

# ─── Constants ────────────────────────────────────────────────────────────────

DEFAULT_GOSSIP_INTERVAL = 5.0       # seconds between gossip rounds
DEFAULT_FANOUT = 3                  # peers to gossip with per round
DEFAULT_PULL_TIMEOUT = 2.0          # seconds to wait for pull response
DEFAULT_STATE_TTL = 300.0           # seconds before state entry expires
DEFAULT_MAX_STATE_ENTRIES = 10_000  # max entries in local state store
DEFAULT_PHI_THRESHOLD = 8.0         # phi value above which peer is suspected
DEFAULT_WINDOW_SIZE = 20            # heartbeat history window for phi calc


# ─── Enums ────────────────────────────────────────────────────────────────────

class GossipMessageType(str, Enum):
    """Types of gossip messages."""
    PUSH = "push"               # Push state digest
    PULL_REQUEST = "pull_req"   # Request missing entries
    PULL_RESPONSE = "pull_resp" # Response with requested entries
    SYNC = "sync"               # Full state sync
    SYNC_ACK = "sync_ack"       # Acknowledge sync


class PeerState(str, Enum):
    """Gossip peer state."""
    UNKNOWN = "unknown"
    ALIVE = "alive"
    SUSPECTED = "suspected"
    DEAD = "dead"


# ─── Data Classes ─────────────────────────────────────────────────────────────

@dataclass
class StateEntry:
    """A single state entry in the gossip store."""
    key: str
    value: Any
    version: int                    # monotonic version number
    node_id: str                    # originating node
    timestamp: float                # when this entry was created
    ttl: float = DEFAULT_STATE_TTL  # seconds until expiry

    @property
    def expired(self) -> bool:
        return (time.time() - self.timestamp) > self.ttl

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value,
            "version": self.version,
            "node_id": self.node_id,
            "timestamp": self.timestamp,
            "ttl": self.ttl,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StateEntry":
        return cls(
            key=data["key"],
            value=data["value"],
            version=data["version"],
            node_id=data["node_id"],
            timestamp=data.get("timestamp", time.time()),
            ttl=data.get("ttl", DEFAULT_STATE_TTL),
        )


@dataclass
class GossipMessage:
    """A message exchanged during gossip rounds."""
    message_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    msg_type: GossipMessageType = GossipMessageType.PUSH
    sender_id: str = ""
    sender_version: int = 0          # sender's current version vector sum
    entries: List[Dict[str, Any]] = field(default_factory=list)
    digest: Dict[str, int] = field(default_factory=dict)  # key → version map
    timestamp: float = field(default_factory=time.time)
    ttl: int = 3                     # remaining hops

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "msg_type": self.msg_type.value,
            "sender_id": self.sender_id,
            "sender_version": self.sender_version,
            "entries": self.entries,
            "digest": self.digest,
            "timestamp": self.timestamp,
            "ttl": self.ttl,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GossipMessage":
        msg_type_str = data.get("msg_type", "push")
        try:
            msg_type = GossipMessageType(msg_type_str)
        except ValueError:
            msg_type = GossipMessageType.PUSH
        return cls(
            message_id=data.get("message_id", ""),
            msg_type=msg_type,
            sender_id=data.get("sender_id", ""),
            sender_version=data.get("sender_version", 0),
            entries=data.get("entries", []),
            digest=data.get("digest", {}),
            timestamp=data.get("timestamp", time.time()),
            ttl=data.get("ttl", 3),
        )


@dataclass
class PeerRecord:
    """Gossip peer tracking record."""
    peer_id: str
    address: str = ""
    state: PeerState = PeerState.UNKNOWN
    last_gossip: float = 0.0
    last_seen: float = 0.0
    version: int = 0                 # last known version of this peer
    heartbeat_history: List[float] = field(default_factory=list)
    phi: float = 0.0                 # current phi suspicion level
    consecutive_failures: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


# ─── Phi-Accrual Failure Detector ─────────────────────────────────────────────

class PhiAccrualFailureDetector:
    """
    Adaptive failure detector using the phi-accrual model.

    Instead of a fixed timeout, phi measures the likelihood that a peer
    has failed based on the distribution of past heartbeat intervals.
    A higher phi means higher suspicion.  Threshold is typically 8-16.

    Reference: "The Phi-Accrual Failure Detector" (Hayashibara et al.)
    """

    def __init__(self, window_size: int = DEFAULT_WINDOW_SIZE,
                 phi_threshold: float = DEFAULT_PHI_THRESHOLD):
        self._window_size = window_size
        self._phi_threshold = phi_threshold
        self._intervals: Dict[str, List[float]] = {}  # peer_id → [intervals]

    def record_heartbeat(self, peer_id: str, interval: float) -> None:
        """Record a heartbeat interval for a peer."""
        if peer_id not in self._intervals:
            self._intervals[peer_id] = []
        self._intervals[peer_id].append(interval)
        # Keep only the last N intervals
        if len(self._intervals[peer_id]) > self._window_size:
            self._intervals[peer_id] = self._intervals[peer_id][-self._window_size:]

    def compute_phi(self, peer_id: str, elapsed: float) -> float:
        """
        Compute the phi value for a peer given the time elapsed since
        the last heartbeat.  Higher phi = more likely failed.
        """
        intervals = self._intervals.get(peer_id, [])
        if not intervals:
            # No history — use a default assumption
            return 0.0

        mean = sum(intervals) / len(intervals)
        if mean <= 0:
            return 0.0

        variance = sum((x - mean) ** 2 for x in intervals) / len(intervals)
        std_dev = math.sqrt(variance) if variance > 0 else mean * 0.1

        # Probability that a heartbeat would arrive after 'elapsed' time
        # using a normal distribution approximation
        if std_dev <= 0:
            return float("inf") if elapsed > mean else 0.0

        z = (elapsed - mean) / std_dev
        # Approximation of -log10(1 - Φ(z)) where Φ is the CDF of normal dist
        # Using the complementary error function
        phi = -math.log10(self._normal_cdf_tail(z))
        return max(0.0, phi)

    def is_suspected(self, peer_id: str, elapsed: float) -> bool:
        """Check if a peer should be suspected based on phi."""
        phi = self.compute_phi(peer_id, elapsed)
        return phi >= self._phi_threshold

    def _normal_cdf_tail(self, z: float) -> float:
        """Approximate tail probability P(X > z) for standard normal."""
        # Using the Abramowitz and Stegun approximation for erfc
        if z < 0:
            return 1.0 - self._normal_cdf_tail(-z)
        t = 1.0 / (1.0 + 0.2316419 * abs(z))
        d = 0.3989422804014327 * math.exp(-z * z / 2.0)
        p = d * (t * (0.319381530 + t * (-0.356563782 + t * (1.781477937 +
                 t * (-1.821255978 + t * 1.330274429)))))
        return max(0.0, min(1.0, p))


# ─── Gossip Protocol ──────────────────────────────────────────────────────────

class GossipProtocol:
    """
    Epidemic gossip protocol for state dissemination across the mesh.

    Features:
      - Push-Pull gossip rounds
      - Phi-accrual failure detection
      - Version-vector based conflict resolution
      - TTL-based state pruning
      - Pluggable transport callbacks
    """

    def __init__(
        self,
        node_id: str,
        gossip_interval: float = DEFAULT_GOSSIP_INTERVAL,
        fanout: int = DEFAULT_FANOUT,
        pull_timeout: float = DEFAULT_PULL_TIMEOUT,
        state_ttl: float = DEFAULT_STATE_TTL,
        max_entries: int = DEFAULT_MAX_STATE_ENTRIES,
    ):
        self._node_id = node_id
        self._gossip_interval = gossip_interval
        self._fanout = fanout
        self._pull_timeout = pull_timeout
        self._state_ttl = state_ttl
        self._max_entries = max_entries

        # State store: key → StateEntry
        self._state: Dict[str, StateEntry] = {}
        # Version vector: node_id → version
        self._version_vector: Dict[str, int] = {node_id: 0}
        # Peers: peer_id → PeerRecord
        self._peers: Dict[str, PeerRecord] = {}
        # Failure detector
        self._failure_detector = PhiAccrualFailureDetector()
        # Running state
        self._running = False
        self._task: Optional[asyncio.Task[None]] = None
        self._lock = asyncio.Lock()

        # Transport callbacks — set by integrator
        self._send_message: Optional[Callable] = None
        self._on_state_update: Optional[Callable] = None
        self._on_peer_dead: Optional[Callable] = None

        # Stats
        self._stats: Dict[str, Any] = {
            "messages_sent": 0,
            "messages_received": 0,
            "pushes_sent": 0,
            "pulls_sent": 0,
            "state_updates": 0,
            "state_prunes": 0,
            "rounds_completed": 0,
            "peers_suspected": 0,
            "peers_declared_dead": 0,
        }

    # ── Public API ──────────────────────────────────────────────────────────

    def set_transport(self, send_fn: Callable) -> None:
        """
        Set the transport callback for sending messages.

        ``send_fn`` signature: ``async def send_fn(peer_id: str, message: GossipMessage)``
        """
        self._send_message = send_fn

    def set_on_state_update(self, callback: Callable) -> None:
        """
        Callback invoked when state is updated via gossip.

        ``callback`` signature: ``def callback(key: str, value: Any, node_id: str)``
        """
        self._on_state_update = callback

    def set_on_peer_dead(self, callback: Callable) -> None:
        """
        Callback invoked when a peer is declared dead.

        ``callback`` signature: ``def callback(peer_id: str)``
        """
        self._on_peer_dead = callback

    def add_peer(self, peer_id: str, address: str = "",
                 metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add a peer to the gossip pool."""
        if peer_id not in self._peers:
            self._peers[peer_id] = PeerRecord(
                peer_id=peer_id,
                address=address,
                metadata=metadata or {},
            )
            logger.info("Gossip: added peer %s", peer_id)

    def remove_peer(self, peer_id: str) -> None:
        """Remove a peer from the gossip pool."""
        self._peers.pop(peer_id, None)
        logger.info("Gossip: removed peer %s", peer_id)

    def update_state(self, key: str, value: Any,
                     node_id: Optional[str] = None) -> None:
        """Update local state and increment version vector."""
        origin = node_id or self._node_id
        current = self._state.get(key)
        new_version = (current.version + 1) if current else 1

        self._state[key] = StateEntry(
            key=key,
            value=value,
            version=new_version,
            node_id=origin,
            timestamp=time.time(),
            ttl=self._state_ttl,
        )
        # Update version vector
        self._version_vector[origin] = max(
            self._version_vector.get(origin, 0), new_version
        )
        self._stats["state_updates"] += 1

    def get_state(self, key: str) -> Optional[Any]:
        """Get a state value by key."""
        entry = self._state.get(key)
        if entry and not entry.expired:
            return entry.value
        return None

    def get_all_state(self) -> Dict[str, Any]:
        """Get all non-expired state entries."""
        self._prune_expired()
        return {k: v.value for k, v in self._state.items() if not v.expired}

    def get_digest(self) -> Dict[str, int]:
        """Get the state digest (key → version) for push messages."""
        self._prune_expired()
        return {k: v.version for k, v in self._state.items() if not v.expired}

    @property
    def version(self) -> int:
        """Current version sum (for gossip comparison)."""
        return sum(self._version_vector.values())

    def get_peers(self, state: Optional[PeerState] = None) -> List[str]:
        """Get peer IDs, optionally filtered by state."""
        if state:
            return [pid for pid, rec in self._peers.items() if rec.state == state]
        return list(self._peers.keys())

    def get_alive_peers(self) -> List[str]:
        """Get peers that are currently ALIVE."""
        return self.get_peers(PeerState.ALIVE)

    def record_heartbeat(self, peer_id: str) -> None:
        """Record a heartbeat from a peer (for phi calculation)."""
        record = self._peers.get(peer_id)
        if record is None:
            return

        now = time.time()
        if record.last_seen > 0:
            interval = now - record.last_seen
            self._failure_detector.record_heartbeat(peer_id, interval)
            record.heartbeat_history.append(interval)
            if len(record.heartbeat_history) > DEFAULT_WINDOW_SIZE:
                record.heartbeat_history = record.heartbeat_history[-DEFAULT_WINDOW_SIZE:]

        record.last_seen = now
        record.state = PeerState.ALIVE
        record.consecutive_failures = 0

    async def start(self) -> None:
        """Start the gossip loop."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._gossip_loop())
        logger.info("GossipProtocol started (interval=%ss, fanout=%d)",
                     self._gossip_interval, self._fanout)

    async def stop(self) -> None:
        """Stop the gossip loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("GossipProtocol stopped")

    async def handle_message(self, message: GossipMessage) -> Optional[GossipMessage]:
        """
        Handle an incoming gossip message from a peer.

        Returns a response message if one is needed (e.g., pull response).
        """
        self._stats["messages_received"] += 1

        if message.ttl <= 0:
            return None

        # Record heartbeat from sender
        self.record_heartbeat(message.sender_id)

        if message.msg_type == GossipMessageType.PUSH:
            return await self._handle_push(message)
        elif message.msg_type == GossipMessageType.PULL_REQUEST:
            return await self._handle_pull_request(message)
        elif message.msg_type == GossipMessageType.PULL_RESPONSE:
            await self._handle_pull_response(message)
            return None
        elif message.msg_type == GossipMessageType.SYNC:
            return await self._handle_sync(message)
        elif message.msg_type == GossipMessageType.SYNC_ACK:
            await self._handle_sync_ack(message)
            return None

        return None

    def get_stats(self) -> Dict[str, Any]:
        """Get gossip protocol statistics."""
        alive = len(self.get_alive_peers())
        total = len(self._peers)
        return {
            **self._stats,
            "node_id": self._node_id,
            "version": self.version,
            "state_entries": len(self._state),
            "peers_alive": alive,
            "peers_total": total,
            "peers_suspected": len(self.get_peers(PeerState.SUSPECTED)),
            "peers_dead": len(self.get_peers(PeerState.DEAD)),
            "running": self._running,
        }

    # ── Internal: Gossip Loop ───────────────────────────────────────────────

    async def _gossip_loop(self) -> None:
        """Main gossip loop — runs periodic gossip rounds."""
        while self._running:
            try:
                await self._gossip_round()
                await self._check_failures()
                self._prune_expired()
                await asyncio.sleep(self._gossip_interval)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.warning("Gossip loop error: %s", exc)
                await asyncio.sleep(1.0)

    async def _gossip_round(self) -> None:
        """Execute one gossip round: push to random peers, pull from random peers."""
        alive_peers = self.get_alive_peers()
        if not alive_peers:
            return

        # Select random subset for push
        push_targets = random.sample(
            alive_peers, min(self._fanout, len(alive_peers))
        )

        for peer_id in push_targets:
            await self._push_to_peer(peer_id)

        # Select random subset for pull (different from push targets)
        pull_candidates = [p for p in alive_peers if p not in push_targets]
        if pull_candidates:
            pull_targets = random.sample(
                pull_candidates, min(self._fanout, len(pull_candidates))
            )
            for peer_id in pull_targets:
                await self._pull_from_peer(peer_id)

        self._stats["rounds_completed"] += 1

    # ── Internal: Push ──────────────────────────────────────────────────────

    async def _push_to_peer(self, peer_id: str) -> None:
        """Push our state digest to a peer."""
        if not self._send_message:
            return

        message = GossipMessage(
            msg_type=GossipMessageType.PUSH,
            sender_id=self._node_id,
            sender_version=self.version,
            digest=self.get_digest(),
        )

        try:
            await self._send_message(peer_id, message)
            self._stats["messages_sent"] += 1
            self._stats["pushes_sent"] += 1
            record = self._peers.get(peer_id)
            if record:
                record.last_gossip = time.time()
        except Exception as exc:
            logger.debug("Gossip push to %s failed: %s", peer_id, exc)
            self._record_failure(peer_id)

    async def _handle_push(self, message: GossipMessage) -> Optional[GossipMessage]:
        """
        Handle an incoming push message.

        Compare digests and return a PULL_RESPONSE with any entries
        the sender is missing, or a PULL_REQUEST if we're missing entries.
        """
        # Determine what we have that the sender might be missing
        our_digest = self.get_digest()
        missing_for_sender: List[Dict[str, Any]] = []

        for key, our_version in our_digest.items():
            their_version = message.digest.get(key, 0)
            if our_version > their_version:
                entry = self._state.get(key)
                if entry and not entry.expired:
                    missing_for_sender.append(entry.to_dict())

        # Determine what the sender has that we're missing
        we_need_keys = []
        for key, their_version in message.digest.items():
            our_version = our_digest.get(key, 0)
            if their_version > our_version:
                we_need_keys.append(key)

        if missing_for_sender:
            # Respond with entries the sender is missing (push-pull)
            return GossipMessage(
                msg_type=GossipMessageType.PULL_RESPONSE,
                sender_id=self._node_id,
                sender_version=self.version,
                entries=missing_for_sender,
            )

        if we_need_keys:
            # Request missing entries
            return GossipMessage(
                msg_type=GossipMessageType.PULL_REQUEST,
                sender_id=self._node_id,
                sender_version=self.version,
                digest={k: message.digest[k] for k in we_need_keys},
            )

        return None

    # ── Internal: Pull ──────────────────────────────────────────────────────

    async def _pull_from_peer(self, peer_id: str) -> None:
        """Send a pull request to a peer."""
        if not self._send_message:
            return

        message = GossipMessage(
            msg_type=GossipMessageType.PULL_REQUEST,
            sender_id=self._node_id,
            sender_version=self.version,
            digest=self.get_digest(),
        )

        try:
            await self._send_message(peer_id, message)
            self._stats["messages_sent"] += 1
            self._stats["pulls_sent"] += 1
        except Exception as exc:
            logger.debug("Gossip pull from %s failed: %s", peer_id, exc)
            self._record_failure(peer_id)

    async def _handle_pull_request(self, message: GossipMessage) -> Optional[GossipMessage]:
        """
        Handle a pull request — return entries the requester is missing.
        """
        their_digest = message.digest
        our_digest = self.get_digest()
        missing_entries: List[Dict[str, Any]] = []

        for key, our_version in our_digest.items():
            their_version = their_digest.get(key, 0)
            if our_version > their_version:
                entry = self._state.get(key)
                if entry and not entry.expired:
                    missing_entries.append(entry.to_dict())

        if missing_entries:
            return GossipMessage(
                msg_type=GossipMessageType.PULL_RESPONSE,
                sender_id=self._node_id,
                sender_version=self.version,
                entries=missing_entries,
            )

        return None

    async def _handle_pull_response(self, message: GossipMessage) -> None:
        """Apply entries received in a pull response."""
        for entry_data in message.entries:
            entry = StateEntry.from_dict(entry_data)
            await self._apply_entry(entry)

    # ── Internal: Full Sync ─────────────────────────────────────────────────

    async def _handle_sync(self, message: GossipMessage) -> Optional[GossipMessage]:
        """Handle a full sync request — return all state."""
        entries = []
        for entry in self._state.values():
            if not entry.expired:
                entries.append(entry.to_dict())

        return GossipMessage(
            msg_type=GossipMessageType.SYNC_ACK,
            sender_id=self._node_id,
            sender_version=self.version,
            entries=entries,
        )

    async def _handle_sync_ack(self, message: GossipMessage) -> None:
        """Apply entries from a full sync response."""
        for entry_data in message.entries:
            entry = StateEntry.from_dict(entry_data)
            await self._apply_entry(entry)

    # ── Internal: Entry Application ─────────────────────────────────────────

    async def _apply_entry(self, entry: StateEntry) -> bool:
        """
        Apply a state entry from a peer.

        Uses version-vector based conflict resolution:
        - Higher version wins
        - If same version, node_id lexicographic order breaks ties
        """
        if entry.expired:
            return False

        current = self._state.get(entry.key)
        if current:
            if entry.version > current.version:
                # Newer version — apply
                self._state[entry.key] = entry
                self._version_vector[entry.node_id] = max(
                    self._version_vector.get(entry.node_id, 0), entry.version
                )
                if self._on_state_update:
                    self._on_state_update(entry.key, entry.value, entry.node_id)
                return True
            elif entry.version == current.version and entry.node_id > current.node_id:
                # Same version, tiebreak by node_id
                self._state[entry.key] = entry
                if self._on_state_update:
                    self._on_state_update(entry.key, entry.value, entry.node_id)
                return True
            return False
        else:
            # New entry
            self._state[entry.key] = entry
            self._version_vector[entry.node_id] = max(
                self._version_vector.get(entry.node_id, 0), entry.version
            )
            if self._on_state_update:
                self._on_state_update(entry.key, entry.value, entry.node_id)
            return True

    # ── Internal: Failure Detection ─────────────────────────────────────────

    async def _check_failures(self) -> None:
        """Check all peers for suspected failures using phi-accrual."""
        now = time.time()
        for peer_id, record in list(self._peers.items()):
            if record.state == PeerState.DEAD:
                continue

            elapsed = now - record.last_seen
            phi = self._failure_detector.compute_phi(peer_id, elapsed)
            record.phi = phi

            if self._failure_detector.is_suspected(peer_id, elapsed):
                if record.state == PeerState.ALIVE:
                    record.state = PeerState.SUSPECTED
                    self._stats["peers_suspected"] += 1
                    logger.info("Gossip: peer %s SUSPECTED (phi=%.2f)", peer_id, phi)

                # Escalate to DEAD after sustained suspicion
                if record.state == PeerState.SUSPECTED and elapsed > self._gossip_interval * 6:
                    record.state = PeerState.DEAD
                    self._stats["peers_declared_dead"] += 1
                    logger.warning("Gossip: peer %s DECLARED DEAD (phi=%.2f)", peer_id, phi)
                    if self._on_peer_dead:
                        try:
                            self._on_peer_dead(peer_id)
                        except Exception as exc:
                            logger.error("on_peer_dead callback failed: %s", exc)

    def _record_failure(self, peer_id: str) -> None:
        """Record a communication failure with a peer."""
        record = self._peers.get(peer_id)
        if record:
            record.consecutive_failures += 1
            if record.consecutive_failures >= 3:
                record.state = PeerState.SUSPECTED

    # ── Internal: Pruning ───────────────────────────────────────────────────

    def _prune_expired(self) -> None:
        """Remove expired state entries."""
        before = len(self._state)
        self._state = {k: v for k, v in self._state.items() if not v.expired}
        pruned = before - len(self._state)
        if pruned > 0:
            self._stats["state_prunes"] += pruned

    # ── Internal: Helpers ───────────────────────────────────────────────────

    def _reset_peer_state(self, peer_id: str) -> None:
        """Reset a peer's state to ALIVE (e.g., after reconnection)."""
        record = self._peers.get(peer_id)
        if record:
            record.state = PeerState.ALIVE
            record.consecutive_failures = 0
            record.phi = 0.0


# ─── Singleton Factory ────────────────────────────────────────────────────────

_gossip_instance: Optional[GossipProtocol] = None


def get_gossip_protocol(node_id: Optional[str] = None) -> GossipProtocol:
    """Get or create the gossip protocol singleton."""
    global _gossip_instance
    if _gossip_instance is None:
        _gossip_instance = GossipProtocol(
            node_id=node_id or f"gossip_{uuid.uuid4().hex[:8]}"
        )
    return _gossip_instance


def reset_gossip_protocol() -> None:
    """Reset the gossip singleton (for testing)."""
    global _gossip_instance
    _gossip_instance = None
