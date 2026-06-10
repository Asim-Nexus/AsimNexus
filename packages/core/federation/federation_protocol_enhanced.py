"""
Enhanced Federation Protocol — AsimNexus Cross-Instance Federation Layer.

Provides peer-to-peer handshake with DID-based authentication,
state-sync messaging, consensus-vote relaying, and heartbeat health
monitoring.  All I/O is async and integrates with the storage engines
(OLTP / ClickHouse) and the Clone Consensus Engine.

Usage:
    from core.federation.federation_protocol_enhanced import (
        FederationHandshake,
        SyncStateMessage,
        ConsensusVoteMessage,
        HeartbeatMonitor,
    )
"""

from __future__ import annotations

import asyncio
import enum
import hashlib
import logging
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from core.mesh.federation_protocol import FederationLevel, TrustLevel

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HANDSHAKE_TIMEOUT_SEC: float = 30.0
SYNC_INTERVAL_SEC: int = 60
HEARTBEAT_INTERVAL_SEC: int = 15
HEARTBEAT_TIMEOUT_SEC: float = 45.0
MAX_SYNC_BATCH: int = 100

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class HandshakeStatus(str, enum.Enum):
    """Outcome of a handshake attempt."""
    PENDING = "pending"
    CHALLENGED = "challenged"
    VERIFIED = "verified"
    REJECTED = "rejected"
    TIMEOUT = "timeout"

class MessageType(str, enum.Enum):
    """Types of messages exchanged between federation peers."""
    HANDSHAKE_INIT = "handshake_init"
    HANDSHAKE_CHALLENGE = "handshake_challenge"
    HANDSHAKE_RESPONSE = "handshake_response"
    HANDSHAKE_VERIFIED = "handshake_verified"
    STATE_SYNC = "state_sync"
    CONSENSUS_VOTE = "consensus_vote"
    HEARTBEAT = "heartbeat"
    HEARTBEAT_ACK = "heartbeat_ack"
    LEAVE = "leave"

class PeerStatus(str, enum.Enum):
    """Current connectivity status of a federation peer."""
    UNKNOWN = "unknown"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    SUSPECTED = "suspected"
    DEAD = "dead"

class SyncScope(str, enum.Enum):
    """What data to include in a sync message."""
    DELTA_ONLY = "delta_only"
    FULL_STATE = "full_state"
    CONSENSUS_ONLY = "consensus_only"
    GOVERNANCE_ONLY = "governance_only"

# ---------------------------------------------------------------------------
# Data-classes
# ---------------------------------------------------------------------------

@dataclass
class FederationHandshake:
    """
    DID-based authentication handshake between two federation peers.

    Flow:
        1. Initiator → Peer:   HANDSHAKE_INIT  (did, node_id, nonce)
        2. Peer → Initiator:   HANDSHAKE_CHALLENGE (challenge_nonce)
        3. Initiator → Peer:   HANDSHAKE_RESPONSE (signed_challenge, cert)
        4. Peer → Initiator:   HANDSHAKE_VERIFIED (session_id)
    """

    handshake_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    initiator_did: str = ""
    initiator_node_id: str = ""
    peer_did: str = ""
    peer_node_id: str = ""
    nonce: str = field(default_factory=lambda: uuid.uuid4().hex[:24])
    challenge_nonce: str = ""
    signed_challenge: str = ""
    session_id: str = ""
    status: HandshakeStatus = HandshakeStatus.PENDING
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def elapsed(self) -> float:
        """Seconds since handshake was created."""
        return time.time() - self.created_at

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FederationHandshake":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class SyncStateMessage:
    """
    A state-synchronisation message exchanged between federation peers.

    Carries CRDT-style state packets so peers can converge on a common
    view of the federation graph, governance decisions, and consensus
    outcomes.
    """

    message_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    sender_node_id: str = ""
    sender_did: str = ""
    scope: SyncScope = SyncScope.DELTA_ONLY
    state_packet: Dict[str, Any] = field(default_factory=dict)
    round_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    ttl: int = 3  # remaining hops
    signature: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "sender_node_id": self.sender_node_id,
            "sender_did": self.sender_did,
            "scope": self.scope.value,
            "state_packet": self.state_packet,
            "round_id": self.round_id,
            "timestamp": self.timestamp,
            "ttl": self.ttl,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SyncStateMessage":
        scope_val = data.get("scope", SyncScope.DELTA_ONLY.value)
        if isinstance(scope_val, str):
            try:
                scope = SyncScope(scope_val)
            except ValueError:
                scope = SyncScope.DELTA_ONLY
        else:
            scope = scope_val
        return cls(
            message_id=data.get("message_id", ""),
            sender_node_id=data.get("sender_node_id", ""),
            sender_did=data.get("sender_did", ""),
            scope=scope,
            state_packet=data.get("state_packet", {}),
            round_id=data.get("round_id"),
            timestamp=data.get("timestamp", time.time()),
            ttl=data.get("ttl", 3),
            signature=data.get("signature", ""),
        )


@dataclass
class ConsensusVoteMessage:
    """
    A consensus-vote message relayed between federation peers.

    Carries a decision proposal from one peer's CloneConsensusEngine
    to another, allowing cross-instance consensus for decisions that
    affect the global federation (e.g. admitting a new peer, changing
    governance parameters).
    """

    vote_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    proposal_id: str = ""
    proposal_topic: str = ""
    proposal_description: str = ""
    voter_node_id: str = ""
    voter_did: str = ""
    vote_choice: str = ""       # approve / reject / abstain / defer
    reasoning: str = ""
    confidence: float = 0.0
    dharma_weight: float = 0.0
    decision_level: str = "HIGH"   # LOW / HIGH / CRITICAL / SOVEREIGNTY
    timestamp: float = field(default_factory=time.time)
    signature: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConsensusVoteMessage":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class PeerHealthRecord:
    """Health record for a single federation peer."""
    peer_id: str
    peer_did: str
    status: PeerStatus = PeerStatus.UNKNOWN
    last_heartbeat: float = 0.0
    last_heartbeat_ack: float = 0.0
    missed_beats: int = 0
    latency_ms: float = 0.0
    consecutive_failures: int = 0
    last_seen: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# HeartbeatMonitor
# ---------------------------------------------------------------------------

class HeartbeatMonitor:
    """
    Async health monitor for federation peers.

    Periodically sends heartbeats to connected peers, tracks acknowledgements,
    and marks peers as SUSPECTED or DEAD when they fail to respond.
    """

    def __init__(
        self,
        node_id: str,
        heartbeat_interval: float = HEARTBEAT_INTERVAL_SEC,
        heartbeat_timeout: float = HEARTBEAT_TIMEOUT_SEC,
        max_missed_beats: int = 3,
    ) -> None:
        self._node_id = node_id
        self._heartbeat_interval = heartbeat_interval
        self._heartbeat_timeout = heartbeat_timeout
        self._max_missed_beats = max_missed_beats

        self._peers: Dict[str, PeerHealthRecord] = {}
        self._running = False
        self._task: Optional[asyncio.Task[None]] = None
        self._on_peer_dead: Optional[callable] = None
        self._on_peer_suspected: Optional[callable] = None
        self._lock = asyncio.Lock()

    # -- Public API ----------------------------------------------------------

    def register_peer(self, peer_id: str, peer_did: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add a peer to the health monitor."""
        if peer_id not in self._peers:
            self._peers[peer_id] = PeerHealthRecord(
                peer_id=peer_id,
                peer_did=peer_did,
                metadata=metadata or {},
            )
            logger.info("HeartbeatMonitor: registered peer %s (%s)", peer_id, peer_did)

    def unregister_peer(self, peer_id: str) -> None:
        """Remove a peer from monitoring."""
        self._peers.pop(peer_id, None)
        logger.info("HeartbeatMonitor: unregistered peer %s", peer_id)

    def set_on_peer_dead(self, callback: callable) -> None:
        """Callback invoked when a peer is declared DEAD.  Signature: fn(peer_id, record)."""
        self._on_peer_dead = callback

    def set_on_peer_suspected(self, callback: callable) -> None:
        """Callback invoked when a peer becomes SUSPECTED.  Signature: fn(peer_id, record)."""
        self._on_peer_suspected = callback

    async def start(self) -> None:
        """Start the background heartbeat loop."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._heartbeat_loop())
        logger.info("HeartbeatMonitor started (interval=%ss, timeout=%ss)",
                     self._heartbeat_interval, self._heartbeat_timeout)

    async def stop(self) -> None:
        """Stop the heartbeat loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("HeartbeatMonitor stopped")

    def record_heartbeat(self, peer_id: str, latency_ms: float = 0.0) -> None:
        """Record an incoming heartbeat from a peer."""
        record = self._peers.get(peer_id)
        if record is None:
            return
        record.last_heartbeat = time.time()
        record.status = PeerStatus.CONNECTED
        record.latency_ms = latency_ms
        record.missed_beats = 0
        record.consecutive_failures = 0

    def record_ack(self, peer_id: str) -> None:
        """Record a heartbeat acknowledgement from a peer."""
        record = self._peers.get(peer_id)
        if record is None:
            return
        record.last_heartbeat_ack = time.time()
        record.missed_beats = 0

    def get_health(self, peer_id: str) -> Optional[Dict[str, Any]]:
        """Return a snapshot of a peer's health, or None if unknown."""
        record = self._peers.get(peer_id)
        if record is None:
            return None
        return {
            "peer_id": record.peer_id,
            "peer_did": record.peer_did,
            "status": record.status.value,
            "last_heartbeat": record.last_heartbeat,
            "last_heartbeat_ack": record.last_heartbeat_ack,
            "missed_beats": record.missed_beats,
            "latency_ms": record.latency_ms,
            "consecutive_failures": record.consecutive_failures,
            "last_seen": record.last_seen,
        }

    def get_all_health(self) -> Dict[str, Dict[str, Any]]:
        """Return health snapshots for all monitored peers."""
        return {pid: self.get_health(pid) for pid in list(self._peers.keys())}

    @property
    def active_peers(self) -> List[str]:
        """List of peer IDs that are currently CONNECTED."""
        return [pid for pid, rec in self._peers.items() if rec.status == PeerStatus.CONNECTED]

    @property
    def suspected_peers(self) -> List[str]:
        """List of peer IDs that are SUSPECTED."""
        return [pid for pid, rec in self._peers.items() if rec.status == PeerStatus.SUSPECTED]

    # -- Internal ------------------------------------------------------------

    async def _heartbeat_loop(self) -> None:
        """Background loop: send heartbeats and check for timeouts."""
        while self._running:
            try:
                await self._check_timeouts()
                await self._send_heartbeats()
                await asyncio.sleep(self._heartbeat_interval)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.warning("HeartbeatMonitor loop error: %s", exc)

    async def _send_heartbeats(self) -> None:
        """Send heartbeat signals to all registered peers.

        In a real deployment this would send an actual network message.
        Here we simulate by marking the heartbeat as sent (the transport
        layer would call ``record_ack`` when the peer responds).
        """
        now = time.time()
        async with self._lock:
            for peer_id, record in self._peers.items():
                # If we haven't heard back from the last heartbeat,
                # increment missed_beats so the timeout logic can fire.
                if now - record.last_heartbeat > self._heartbeat_timeout:
                    record.missed_beats += 1
                    record.consecutive_failures += 1

                    if record.missed_beats >= self._max_missed_beats and record.status != PeerStatus.DEAD:
                        old_status = record.status
                        record.status = PeerStatus.DEAD
                        record.last_seen = now
                        logger.warning("HeartbeatMonitor: peer %s is DEAD (missed %d beats)",
                                       peer_id, record.missed_beats)
                        if self._on_peer_dead:
                            try:
                                self._on_peer_dead(peer_id, record)
                            except Exception as exc:
                                logger.error("on_peer_dead callback failed: %s", exc)

                    elif record.missed_beats >= 1 and record.status == PeerStatus.CONNECTED:
                        record.status = PeerStatus.SUSPECTED
                        logger.info("HeartbeatMonitor: peer %s is SUSPECTED", peer_id)
                        if self._on_peer_suspected:
                            try:
                                self._on_peer_suspected(peer_id, record)
                            except Exception as exc:
                                logger.error("on_peer_suspected callback failed: %s", exc)

    async def _check_timeouts(self) -> None:
        """Check if any peers have exceeded the heartbeat timeout."""
        now = time.time()
        async with self._lock:
            for peer_id, record in self._peers.items():
                if record.status == PeerStatus.DEAD:
                    continue
                if now - record.last_heartbeat > self._heartbeat_timeout:
                    record.missed_beats += 1


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def create_did_challenge(did: str, nonce: str) -> str:
    """Create a deterministic challenge string from a DID and nonce."""
    raw = f"{did}::{nonce}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def verify_handshake_signature(
    did: str,
    challenge: str,
    signature: str,
    public_key_pem: Optional[str] = None,
) -> bool:
    """Verify a handshake response signature.

    Currently uses a SHA-256 digest comparison as a placeholder.
    In production this should verify an actual cryptographic signature
    (e.g. Ed25519) using the peer's DID document public key.
    """
    expected = hashlib.sha256(f"{did}:{challenge}:{signature}".encode()).hexdigest()
    # Placeholder: accept if the signature is a non-empty string that matches
    # the expected pattern.  Replace with real crypto verification.
    return bool(signature) and len(signature) > 8
