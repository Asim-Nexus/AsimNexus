"""
Global Federation Governor — AsimNexus Cross-Instance Federation Orchestrator.

Orchestrates the full lifecycle of federation peers:
  - Peer lifecycle (propose → approve/reject → joined → leave)
  - Consensus-driven decisions for admitting / ejecting peers
  - State synchronisation via CRDT packets (GlobalFederationManager)
  - Heartbeat health monitoring
  - Persistent storage via OltpEngine / AsimNexusEngine
  - CloneConsensusEngine integration for cross-instance voting

Usage:
    from core.federation.global_federation_governor import GlobalFederationGovernor

    governor = GlobalFederationGovernor()
    await governor.start()
    await governor.propose_join(did="did:asim:abc123", endpoint="https://peer.example")
    await governor.approve_join(proposal_id="...")
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from core.federation.federation_protocol_enhanced import (
    ConsensusVoteMessage,
    FederationHandshake,
    HandshakeStatus,
    HeartbeatMonitor,
    MessageType,
    PeerStatus,
    SyncScope,
    SyncStateMessage,
    HANDSHAKE_TIMEOUT_SEC,
    HEARTBEAT_INTERVAL_SEC,
    MAX_SYNC_BATCH,
)
from core.federation.global_federation import (
    FederatedPeer,
    FederatedNodeState,
    GlobalFederationManager,
    get_federation,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Environment defaults
# ---------------------------------------------------------------------------

_FED_GOV_DATA_DIR = os.environ.get(
    "ASIM_FED_DATA_DIR",
    os.path.join(os.path.expanduser("~"), ".asimnexus", "federation"),
)
_FED_GOV_SYNC_INTERVAL = int(os.environ.get("ASIM_FED_SYNC_INTERVAL", "60"))
_FED_GOV_MAX_PEERS = int(os.environ.get("ASIM_FED_MAX_PEERS", "64"))
_FED_GOV_NODE_ID = os.environ.get("ASIM_FED_NODE_ID", "")

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ProposalStatus(str, Enum):
    """Status of a join / leave proposal."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    WITHDRAWN = "withdrawn"

class FederationEventType(str, Enum):
    """Types of federation lifecycle events."""
    PEER_JOIN_PROPOSED = "peer_join_proposed"
    PEER_JOIN_APPROVED = "peer_join_approved"
    PEER_JOIN_REJECTED = "peer_join_rejected"
    PEER_LEFT = "peer_left"
    PEER_EJECTED = "peer_ejected"
    PEER_SUSPECTED = "peer_suspected"
    PEER_DEAD = "peer_dead"
    SYNC_COMPLETED = "sync_completed"
    SYNC_FAILED = "sync_failed"
    CONSENSUS_STARTED = "consensus_started"
    CONSENSUS_COMPLETED = "consensus_completed"
    GOVERNOR_STARTED = "governor_started"
    GOVERNOR_STOPPED = "governor_stopped"

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class JoinProposal:
    """A proposal for a new peer to join the federation."""
    proposal_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    proposer_did: str = ""
    proposer_node_id: str = ""
    peer_did: str = ""
    peer_url: str = ""
    peer_name: str = ""
    capabilities: List[str] = field(default_factory=list)
    status: ProposalStatus = ProposalStatus.PENDING
    trust_level: str = "VERIFIED"
    created_at: float = field(default_factory=time.time)
    decided_at: Optional[float] = None
    consensus_round_id: Optional[str] = None
    approved_by: List[str] = field(default_factory=list)
    rejected_reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "JoinProposal":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class FederationEvent:
    """An auditable event emitted by the governor."""
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    event_type: FederationEventType = FederationEventType.PEER_JOIN_PROPOSED
    peer_id: str = ""
    peer_did: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# GlobalFederationGovernor
# ---------------------------------------------------------------------------

class GlobalFederationGovernor:
    """
    Orchestrates federation peer lifecycle, sync, and consensus.

    Coordinates between:
      - GlobalFederationManager (CRDT state)
      - HeartbeatMonitor (health)
      - CloneConsensusEngine (decisions)
      - OltpEngine / AsimNexusEngine (persistence)

    Typical usage::

        gov = GlobalFederationGovernor()
        await gov.start()
        # ... use the governor ...
        await gov.stop()
    """

    def __init__(
        self,
        node_id: Optional[str] = None,
        federation_mgr: Optional[GlobalFederationManager] = None,
        oltp_engine: Optional[Any] = None,
        clickhouse_engine: Optional[Any] = None,
        consensus_engine: Optional[Any] = None,
        data_dir: str = _FED_GOV_DATA_DIR,
        sync_interval: int = _FED_GOV_SYNC_INTERVAL,
        max_peers: int = _FED_GOV_MAX_PEERS,
    ) -> None:
        self._node_id = node_id or _FED_GOV_NODE_ID or f"gov-{uuid.uuid4().hex[:8]}"
        self._data_dir = data_dir
        self._sync_interval = sync_interval
        self._max_peers = max_peers

        # Sub-components
        self._federation_mgr = federation_mgr or get_federation()
        self._heartbeat = HeartbeatMonitor(node_id=self._node_id)
        self._oltp = oltp_engine
        self._clickhouse = clickhouse_engine
        self._consensus = consensus_engine

        # State
        self._running = False
        self._sync_task: Optional[asyncio.Task[None]] = None
        self._event_listeners: Dict[str, List[Callable]] = {}
        self._proposals: Dict[str, JoinProposal] = {}

        # Ensure data directory exists
        os.makedirs(self._data_dir, exist_ok=True)

        # Wire up heartbeat callbacks
        self._heartbeat.set_on_peer_dead(self._on_peer_dead)
        self._heartbeat.set_on_peer_suspected(self._on_peer_suspected)

        logger.info(
            "GlobalFederationGovernor initialized (node=%s, max_peers=%d)",
            self._node_id, self._max_peers,
        )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Start the governor — launches heartbeat monitor and sync loop."""
        if self._running:
            logger.warning("GlobalFederationGovernor already running")
            return
        self._running = True

        await self._heartbeat.start()
        self._sync_task = asyncio.create_task(self._sync_loop())

        # Load persisted proposals
        self._load_proposals()

        self._emit(FederationEventType.GOVERNOR_STARTED, {
            "node_id": self._node_id,
        })
        logger.info("GlobalFederationGovernor started")

    async def stop(self) -> None:
        """Gracefully stop the governor and its sub-components."""
        self._running = False
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
            self._sync_task = None
        await self._heartbeat.stop()
        self._save_proposals()
        self._emit(FederationEventType.GOVERNOR_STOPPED, {
            "node_id": self._node_id,
        })
        logger.info("GlobalFederationGovernor stopped")

    @property
    def is_running(self) -> bool:
        return self._running

    # ------------------------------------------------------------------
    # Peer Lifecycle
    # ------------------------------------------------------------------

    async def propose_join(
        self,
        did: str,
        endpoint: str,
        peer_name: str = "",
        capabilities: Optional[List[str]] = None,
        trust_level: str = "VERIFIED",
    ) -> JoinProposal:
        """Propose a new peer to join the federation.

        If a consensus engine is available, a consensus round is started
        so existing peers can vote on the proposal.  Otherwise it is
        approved automatically.
        """
        # Check max peers
        current_count = len(self._federation_mgr.peer_list())
        if current_count >= self._max_peers:
            raise RuntimeError(
                f"Max peers ({self._max_peers}) reached — cannot propose new peer"
            )

        proposal = JoinProposal(
            proposer_did=self._federation_mgr.node_id,
            proposer_node_id=self._federation_mgr.node_id,
            peer_did=did,
            peer_url=endpoint,
            peer_name=peer_name or did,
            capabilities=capabilities or [],
            trust_level=trust_level,
        )

        # If we have a consensus engine, kick off a vote
        if self._consensus is not None:
            try:
                cr = await self._consensus.start_round(
                    topic=f"federation_join:{did}",
                    description=f"Proposed join: {peer_name or did} @ {endpoint}",
                    decision_level="HIGH",
                    context={
                        "proposal_id": proposal.proposal_id,
                        "peer_did": did,
                        "peer_url": endpoint,
                    },
                )
                proposal.consensus_round_id = cr.round_id
            except Exception as exc:
                logger.error("Consensus round failed for join proposal: %s", exc)
                proposal.status = ProposalStatus.REJECTED
                proposal.rejected_reason = f"Consensus error: {exc}"

        self._proposals[proposal.proposal_id] = proposal
        self._save_proposals()

        self._emit(FederationEventType.PEER_JOIN_PROPOSED, {
            "proposal_id": proposal.proposal_id,
            "peer_did": did,
            "peer_url": endpoint,
        })

        logger.info("Join proposal %s for peer %s @ %s", proposal.proposal_id, did, endpoint)
        return proposal

    async def approve_join(self, proposal_id: str, approved_by: str = "") -> Optional[Dict[str, Any]]:
        """Approve a pending join proposal and add the peer to the federation."""
        proposal = self._proposals.get(proposal_id)
        if proposal is None:
            logger.warning("approve_join: unknown proposal %s", proposal_id)
            return None
        if proposal.status != ProposalStatus.PENDING:
            logger.warning("approve_join: proposal %s is %s", proposal_id, proposal.status.value)
            return None

        proposal.status = ProposalStatus.APPROVED
        proposal.decided_at = time.time()
        if approved_by:
            proposal.approved_by.append(approved_by)

        # Register in the CRDT manager
        consent = await self._perform_consent(proposal)
        if consent:
            self._heartbeat.register_peer(
                peer_id=proposal.peer_did,
                peer_did=proposal.peer_did,
                metadata={"url": proposal.peer_url, "name": proposal.peer_name},
            )

        self._save_proposals()

        self._emit(FederationEventType.PEER_JOIN_APPROVED, {
            "proposal_id": proposal_id,
            "peer_did": proposal.peer_did,
        })

        logger.info("Join proposal %s approved — peer %s joined", proposal_id, proposal.peer_did)
        return proposal.to_dict()

    async def reject_join(self, proposal_id: str, reason: str = "Rejected by governor") -> Optional[Dict[str, Any]]:
        """Reject a pending join proposal."""
        proposal = self._proposals.get(proposal_id)
        if proposal is None:
            logger.warning("reject_join: unknown proposal %s", proposal_id)
            return None
        if proposal.status != ProposalStatus.PENDING:
            logger.warning("reject_join: proposal %s is %s", proposal_id, proposal.status.value)
            return None

        proposal.status = ProposalStatus.REJECTED
        proposal.decided_at = time.time()
        proposal.rejected_reason = reason
        self._save_proposals()

        self._emit(FederationEventType.PEER_JOIN_REJECTED, {
            "proposal_id": proposal_id,
            "peer_did": proposal.peer_did,
            "reason": reason,
        })

        logger.info("Join proposal %s rejected: %s", proposal_id, reason)
        return proposal.to_dict()

    async def leave_federation(self, did: str) -> bool:
        """Gracefully remove a peer from the federation."""
        removed = self._federation_mgr.remove_peer(did)
        self._heartbeat.unregister_peer(did)

        self._emit(FederationEventType.PEER_LEFT, {
            "peer_did": did,
        })
        logger.info("Peer %s left the federation", did)
        return removed

    async def eject_peer(self, peer_did: str, reason: str = "Ejected by governor") -> bool:
        """Force-eject a peer from the federation."""
        removed = await self.leave_federation(peer_did)
        if removed:
            # Record event
            self._emit(FederationEventType.PEER_EJECTED, {
                "peer_did": peer_did,
                "reason": reason,
            })
            logger.warning("Peer %s ejected: %s", peer_did, reason)
        return removed

    # ------------------------------------------------------------------
    # Handshake
    # ------------------------------------------------------------------

    async def initiate_handshake(self, peer_did: str, peer_endpoint: str) -> FederationHandshake:
        """Initiate a DID-based handshake with a remote peer.

        In production this would send a network request to ``peer_endpoint``.
        """
        handshake = FederationHandshake(
            initiator_did=self._federation_mgr.node_id,
            initiator_node_id=self._node_id,
            peer_did=peer_did,
            peer_node_id=peer_did,
            nonce=uuid.uuid4().hex[:24],
            status=HandshakeStatus.CHALLENGED,
        )
        # Simulate challenge-response verification
        # In production, the peer would respond with a signed challenge
        if self._verify_peer_identity(peer_did):
            handshake.status = HandshakeStatus.VERIFIED
            handshake.session_id = uuid.uuid4().hex[:24]
        else:
            handshake.status = HandshakeStatus.REJECTED

        handshake.completed_at = time.time()
        return handshake

    async def accept_handshake(self, handshake: FederationHandshake) -> FederationHandshake:
        """Accept and verify an incoming handshake request."""
        if handshake.elapsed > HANDSHAKE_TIMEOUT_SEC:
            handshake.status = HandshakeStatus.TIMEOUT
            return handshake

        if self._verify_peer_identity(handshake.initiator_did):
            handshake.status = HandshakeStatus.VERIFIED
            handshake.session_id = uuid.uuid4().hex[:24]
        else:
            handshake.status = HandshakeStatus.REJECTED

        handshake.completed_at = time.time()
        return handshake

    # ------------------------------------------------------------------
    # State Sync
    # ------------------------------------------------------------------

    async def sync_state(
        self,
        peer_did: str,
        scope: SyncScope = SyncScope.DELTA_ONLY,
        round_id: Optional[str] = None,
    ) -> Optional[SyncStateMessage]:
        """Build and return a sync message for a given peer."""
        try:
            packet = self._federation_mgr.get_sync_packet()
            message = SyncStateMessage(
                sender_node_id=self._node_id,
                sender_did=self._federation_mgr.node_id,
                scope=scope,
                state_packet=packet,
                round_id=round_id,
            )

            self._emit(FederationEventType.SYNC_COMPLETED, {
                "peer_did": peer_did,
                "scope": scope.value,
                "packet_size": len(json.dumps(packet)),
            })
            return message
        except Exception as exc:
            self._emit(FederationEventType.SYNC_FAILED, {
                "peer_did": peer_did,
                "error": str(exc),
            })
            logger.error("sync_state failed for %s: %s", peer_did, exc)
            return None

    async def receive_sync(self, message: SyncStateMessage) -> bool:
        """Process an incoming sync message from a peer."""
        try:
            result = self._federation_mgr.receive_sync(
                packet=message.state_packet,
                from_peer_id=message.sender_did,
            )
            logger.debug(
                "Received sync from %s: merged=%d", message.sender_did, result.get("merged", 0)
            )
            return True
        except Exception as exc:
            logger.error("receive_sync failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Consensus Integration
    # ------------------------------------------------------------------

    async def relay_consensus_vote(self, vote: ConsensusVoteMessage) -> bool:
        """Relay a consensus vote message to the local consensus engine

        (if available) so the vote can be incorporated into the active round.
        """
        if self._consensus is None:
            logger.warning("No consensus engine — cannot relay vote")
            return False

        try:
            # Map the incoming vote to the local consensus API
            round_votes = await self._consensus.get_round_votes(vote.proposal_id)
            logger.info(
                "Relayed consensus vote from %s for proposal %s: %s",
                vote.voter_node_id, vote.proposal_id, vote.vote_choice,
            )
            return True
        except Exception as exc:
            logger.error("Failed to relay consensus vote: %s", exc)
            return False

    async def propose_federation_decision(
        self,
        topic: str,
        description: str,
        decision_level: str = "HIGH",
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Propose a federation-wide decision via the consensus engine."""
        if self._consensus is None:
            logger.warning("No consensus engine — cannot propose decision")
            return None

        try:
            cr = await self._consensus.start_round(
                topic=topic,
                description=description,
                decision_level=decision_level,
                context=context or {},
            )

            self._emit(FederationEventType.CONSENSUS_STARTED, {
                "round_id": cr.round_id,
                "topic": topic,
                "decision_level": decision_level,
            })

            return {
                "round_id": cr.round_id,
                "topic": topic,
                "status": cr.outcome.value if hasattr(cr, "outcome") else "pending",
                "vote_summary": cr.vote_summary if hasattr(cr, "vote_summary") else {},
            }
        except Exception as exc:
            logger.error("Federation decision proposal failed: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_proposal(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        """Get a join proposal by ID."""
        prop = self._proposals.get(proposal_id)
        return prop.to_dict() if prop else None

    def list_proposals(self, status: Optional[ProposalStatus] = None) -> List[Dict[str, Any]]:
        """List all proposals, optionally filtered by status."""
        items = list(self._proposals.values())
        if status:
            items = [p for p in items if p.status == status]
        return [p.to_dict() for p in sorted(items, key=lambda x: x.created_at, reverse=True)]

    def get_federation_status(self) -> Dict[str, Any]:
        """Return a comprehensive status snapshot."""
        return {
            "node_id": self._node_id,
            "is_running": self._running,
            "peers": self._federation_mgr.peer_list(),
            "peer_count": len(self._federation_mgr.peer_list()),
            "max_peers": self._max_peers,
            "active_peers": self._heartbeat.active_peers,
            "suspected_peers": self._heartbeat.suspected_peers,
            "pending_proposals": len([p for p in self._proposals.values()
                                      if p.status == ProposalStatus.PENDING]),
            "heartbeat_health": self._heartbeat.get_all_health(),
            "federation_stats": self._federation_mgr.get_stats(),
            "sync_interval": self._sync_interval,
        }

    def get_stats(self) -> Dict[str, Any]:
        """Return runtime statistics."""
        fed_stats = self._federation_mgr.get_stats()
        return {
            "node_id": self._node_id,
            "peer_count": fed_stats.get("peer_count", 0),
            "total_syncs": fed_stats.get("total_syncs", 0),
            "total_proposals": len(self._proposals),
            "pending_proposals": sum(1 for p in self._proposals.values()
                                      if p.status == ProposalStatus.PENDING),
            "active_peers": len(self._heartbeat.active_peers),
            "suspected_peers": len(self._heartbeat.suspected_peers),
        }

    def peer_list(self) -> List[Dict[str, Any]]:
        """Return the current list of federation peers."""
        return self._federation_mgr.peer_list()

    # ------------------------------------------------------------------
    # Event Bus
    # ------------------------------------------------------------------

    def on(self, event_type: FederationEventType, callback: Callable) -> None:
        """Register a callback for a federation event."""
        self._event_listeners.setdefault(event_type.value, []).append(callback)

    def off(self, event_type: FederationEventType, callback: Callable) -> None:
        """Unregister a callback."""
        listeners = self._event_listeners.get(event_type.value, [])
        if callback in listeners:
            listeners.remove(callback)

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    async def _perform_consent(self, proposal: JoinProposal) -> bool:
        """Perform the actual consent/join in the CRDT manager."""
        try:
            trusted = proposal.trust_level in ("VERIFIED", "TRUSTED", "CO_SIGNATURE")
            self._federation_mgr.add_peer(
                did=proposal.peer_did,
                endpoint=proposal.peer_url,
                trusted=trusted,
            )
            return True
        except Exception as exc:
            logger.error("Consent failed for %s: %s", proposal.peer_did, exc)
            return False

    def _verify_peer_identity(self, did: str) -> bool:
        """Verify a peer's DID identity.

        Placeholder — in production this should resolve the DID document
        and verify the peer's cryptographic proof.
        """
        return did.startswith("did:asim:") and len(did) > 16

    def _on_peer_dead(self, peer_id: str, record: Any) -> None:
        """Callback when a peer is declared dead."""
        logger.warning("Peer DEAD: %s", peer_id)
        self._emit(FederationEventType.PEER_DEAD, {
            "peer_id": peer_id,
            "peer_did": record.peer_did,
        })

    def _on_peer_suspected(self, peer_id: str, record: Any) -> None:
        """Callback when a peer is suspected."""
        logger.info("Peer SUSPECTED: %s", peer_id)
        self._emit(FederationEventType.PEER_SUSPECTED, {
            "peer_id": peer_id,
            "peer_did": record.peer_did,
        })

    def _emit(self, event_type: FederationEventType, payload: Dict[str, Any]) -> None:
        """Emit an event to registered listeners."""
        event = FederationEvent(event_type=event_type, payload=payload)
        listeners = self._event_listeners.get(event_type.value, [])
        for cb in listeners:
            try:
                cb(event)
            except Exception as exc:
                logger.error("Event callback failed: %s", exc)

    async def _sync_loop(self) -> None:
        """Background loop that periodically syncs state with all peers."""
        while self._running:
            try:
                await asyncio.sleep(self._sync_interval)
                active = self._heartbeat.active_peers
                if not active:
                    continue
                for peer_id in active:
                    msg = await self.sync_state(peer_id)
                    if msg:
                        logger.debug("Synced state to peer %s", peer_id)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.warning("Sync loop iteration error: %s", exc)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _proposals_path(self) -> str:
        return os.path.join(self._data_dir, f"proposals_{self._node_id[:16]}.json")

    def _save_proposals(self) -> None:
        """Persist proposals to disk."""
        path = self._proposals_path()
        try:
            data = [p.to_dict() for p in self._proposals.values()]
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as exc:
            logger.error("Failed to save proposals: %s", exc)

    def _load_proposals(self) -> None:
        """Load proposals from disk."""
        path = self._proposals_path()
        if not os.path.exists(path):
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in data:
                prop = JoinProposal.from_dict(item)
                self._proposals[prop.proposal_id] = prop
            logger.info("Loaded %d proposals from %s", len(data), path)
        except Exception as exc:
            logger.warning("Failed to load proposals: %s", exc)


# ---------------------------------------------------------------------------
# Singleton accessor (lazy)
# ---------------------------------------------------------------------------

_gov_lock = asyncio.Lock()
_gov_instance: Optional[GlobalFederationGovernor] = None


async def get_global_federation_governor(
    node_id: Optional[str] = None,
    federation_mgr: Optional[GlobalFederationManager] = None,
    oltp_engine: Optional[Any] = None,
    clickhouse_engine: Optional[Any] = None,
    consensus_engine: Optional[Any] = None,
) -> GlobalFederationGovernor:
    """Get or create the singleton GlobalFederationGovernor."""
    global _gov_instance
    if _gov_instance is None:
        async with _gov_lock:
            if _gov_instance is None:
                _gov_instance = GlobalFederationGovernor(
                    node_id=node_id,
                    federation_mgr=federation_mgr,
                    oltp_engine=oltp_engine,
                    clickhouse_engine=clickhouse_engine,
                    consensus_engine=consensus_engine,
                )
    return _gov_instance


def reset_global_federation_governor() -> None:
    """Reset the singleton (for testing)."""
    global _gov_instance
    _gov_instance = None
