"""
Raft Consensus Engine
=====================
Implements Raft Consensus (DDIA Chapter 9: Consensus & Transactions)
for distributed leader election and log replication across mesh nodes.

Raft is a distributed consensus algorithm that provides:
  1. Leader Election — one leader per term, with randomized election timeouts
  2. Log Replication — leader appends entries, replicates to followers
  3. Safety — at most one leader per term, committed entries are durable

Reference: "In Search of an Understandable Consensus Algorithm" (Ongaro & Ousterhout, 2014)
           DDIA Chapter 9 ("Consensus and Transactions")
"""

import json
import logging
import random
import threading
import time
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from core.consensus.consensus_engine import (
    ConsensusEngine,
    VotingMode,
    VoteChoice,
    ProposalStatus,
    Voter,
    Vote,
    Proposal
)

logger = logging.getLogger("AsimNexus.ConsensusEngine.Raft")

RAFT_LOG_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "raft_log.jsonl"


# ═══════════════════════════════════════════════════════════════════════════════
# Raft Consensus (DDIA Chapter 9)
# ═══════════════════════════════════════════════════════════════════════════════


class RaftNodeState(str, Enum):
    """Raft node state machine."""
    FOLLOWER = "follower"
    CANDIDATE = "candidate"
    LEADER = "leader"


@dataclass
class RaftLogEntry:
    """A single entry in the Raft replicated log."""
    term: int
    index: int
    command: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "term": self.term,
            "index": self.index,
            "command": self.command,
            "data": self.data,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RaftLogEntry":
        return cls(
            term=data["term"],
            index=data["index"],
            command=data["command"],
            data=data.get("data", {}),
            timestamp=data.get("timestamp", time.time()),
        )


@dataclass
class RaftSnapshot:
    """A snapshot of the Raft state machine for log compaction."""
    last_included_index: int
    last_included_term: int
    state: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class RaftNode:
    """
    A Raft consensus node implementing leader election and log replication.

    This is a single-node simulation of the Raft protocol. In a distributed
    deployment, each mesh node would run its own RaftNode and communicate
    via the P2P transport layer.

    Key parameters (configurable via env vars):
      - ASIM_RAFT_ELECTION_TIMEOUT_MIN: min election timeout in seconds (default: 1.5)
      - ASIM_RAFT_ELECTION_TIMEOUT_MAX: max election timeout in seconds (default: 3.0)
      - ASIM_RAFT_HEARTBEAT_INTERVAL: leader heartbeat interval in seconds (default: 0.5)
    """

    def __init__(
        self,
        node_id: str,
        cluster_size: int = 5,
        election_timeout_min: float = 1.5,
        election_timeout_max: float = 3.0,
        heartbeat_interval: float = 0.5,
    ):
        self.node_id = node_id
        self.cluster_size = cluster_size
        self.election_timeout_min = election_timeout_min
        self.election_timeout_max = election_timeout_max
        self.heartbeat_interval = heartbeat_interval

        # Persistent state (survives restarts)
        self.current_term: int = 0
        self.voted_for: Optional[str] = None  # candidate_id voted for in current term
        self.log: List[RaftLogEntry] = []  # index starts at 1

        # Volatile state
        self.state: RaftNodeState = RaftNodeState.FOLLOWER
        self.commit_index: int = 0  # highest log entry known to be committed
        self.last_applied: int = 0  # highest log entry applied to state machine

        # Leader-only volatile state
        self.next_index: Dict[str, int] = {}  # next log index to send per peer
        self.match_index: Dict[str, int] = {}  # highest log index known replicated per peer

        # Timing
        self._election_deadline: float = time.time() + self._random_election_timeout()
        self._last_heartbeat: float = time.time()
        self._leader_id: Optional[str] = None

        # State machine
        self._state_machine: Dict[str, Any] = {}  # key-value state
        self._commit_handlers: List[Callable[[RaftLogEntry], None]] = []

        # Thread safety
        self._lock = threading.Lock()

        # Callbacks for distributed communication
        self._send_request_vote_cb: Optional[Callable] = None
        self._send_append_entries_cb: Optional[Callable] = None

        # Ensure log directory exists
        RAFT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"⚙️  RaftNode initialized: {node_id} (cluster_size={cluster_size})")

    # ── Configuration ─────────────────────────────────────────────────────

    def set_send_request_vote_callback(self, cb: Callable) -> None:
        """Set callback for sending RequestVote RPCs to peers."""
        self._send_request_vote_cb = cb

    def set_send_append_entries_callback(self, cb: Callable) -> None:
        """Set callback for sending AppendEntries RPCs to peers."""
        self._send_append_entries_cb = cb

    def register_commit_handler(self, handler: Callable[[RaftLogEntry], None]) -> None:
        """Register a handler that is called when a log entry is committed."""
        self._commit_handlers.append(handler)

    # ── Core Raft API ─────────────────────────────────────────────────────

    def current_leader(self) -> Optional[str]:
        """Get the current leader ID."""
        return self._leader_id

    def is_leader(self) -> bool:
        """Check if this node is the current leader."""
        return self.state == RaftNodeState.LEADER

    def append_entry(self, command: str, data: Optional[Dict[str, Any]] = None) -> Optional[int]:
        """
        Append a new entry to the log (client-facing API).
        Returns the log index if successful, None if not the leader.
        """
        with self._lock:
            if self.state != RaftNodeState.LEADER:
                logger.warning(f"Not the leader — redirect to {self._leader_id}")
                return None

            entry = RaftLogEntry(
                term=self.current_term,
                index=len(self.log) + 1,
                command=command,
                data=data or {},
            )
            self.log.append(entry)
            self._persist_entry(entry)
            logger.info(f"📝 Log entry appended: term={entry.term} index={entry.index} cmd={command}")
            return entry.index

    def get_state(self) -> Dict[str, Any]:
        """Get the current state machine state."""
        with self._lock:
            return dict(self._state_machine)

    def get_log(self, since_index: int = 0) -> List[RaftLogEntry]:
        """Get log entries from a given index onward."""
        with self._lock:
            if since_index >= len(self.log):
                return []
            return self.log[since_index:]

    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive Raft node status."""
        with self._lock:
            return {
                "node_id": self.node_id,
                "state": self.state.value,
                "current_term": self.current_term,
                "voted_for": self.voted_for,
                "leader_id": self._leader_id,
                "log_size": len(self.log),
                "commit_index": self.commit_index,
                "last_applied": self.last_applied,
                "cluster_size": self.cluster_size,
            }

    # ── Raft RPC Handlers ─────────────────────────────────────────────────

    def handle_request_vote(
        self, candidate_id: str, term: int, last_log_index: int, last_log_term: int
    ) -> Dict[str, Any]:
        """
        Handle a RequestVote RPC from a candidate.
        Returns {"term": int, "vote_granted": bool}.
        """
        with self._lock:
            logger.info(f"🗳️  RequestVote from {candidate_id} (term={term})")

            # Reply with higher term if we're ahead
            if term < self.current_term:
                return {"term": self.current_term, "vote_granted": False}

            # Update term if candidate's term is higher
            if term > self.current_term:
                self.current_term = term
                self.voted_for = None
                self.state = RaftNodeState.FOLLOWER

            # Check if we already voted in this term
            if self.voted_for is not None and self.voted_for != candidate_id:
                return {"term": self.current_term, "vote_granted": False}

            # Check if candidate's log is at least as up-to-date as ours
            my_last_index = len(self.log)
            my_last_term = self.log[-1].term if self.log else 0

            if last_log_term < my_last_term or (
                last_log_term == my_last_term and last_log_index < my_last_index
            ):
                return {"term": self.current_term, "vote_granted": False}

            # Grant vote
            self.voted_for = candidate_id
            self._election_deadline = time.time() + self._random_election_timeout()
            logger.info(f"✅ Vote granted to {candidate_id} for term {term}")
            return {"term": self.current_term, "vote_granted": True}

    def handle_append_entries(
        self,
        leader_id: str,
        term: int,
        prev_log_index: int,
        prev_log_term: int,
        entries: List[Dict[str, Any]],
        leader_commit: int,
    ) -> Dict[str, Any]:
        """
        Handle an AppendEntries RPC from the leader.
        Returns {"term": int, "success": bool}.
        """
        with self._lock:
            # Reply with higher term if we're ahead
            if term < self.current_term:
                return {"term": self.current_term, "success": False}

            # Recognize leader
            self._leader_id = leader_id
            self._last_heartbeat = time.time()
            self._election_deadline = time.time() + self._random_election_timeout()

            if term > self.current_term:
                self.current_term = term
                self.voted_for = None
                self.state = RaftNodeState.FOLLOWER

            # Check log consistency
            if prev_log_index > 0:
                if prev_log_index > len(self.log):
                    return {"term": self.current_term, "success": False}
                if self.log[prev_log_index - 1].term != prev_log_term:
                    # Conflict — delete conflicting entry and all after it
                    self.log = self.log[: prev_log_index - 1]
                    return {"term": self.current_term, "success": False}

            # Append new entries
            for entry_data in entries:
                entry = RaftLogEntry.from_dict(entry_data)
                if entry.index <= len(self.log):
                    if self.log[entry.index - 1].term != entry.term:
                        # Conflict — overwrite
                        self.log = self.log[: entry.index - 1]
                        self.log.append(entry)
                    # else: already have this entry (no-op)
                else:
                    self.log.append(entry)
                self._persist_entry(entry)

            # Update commit index
            if leader_commit > self.commit_index:
                self.commit_index = min(leader_commit, len(self.log))
                self._apply_committed_entries()

            return {"term": self.current_term, "success": True}

    # ── Election Timer (call this periodically) ───────────────────────────

    def tick(self) -> None:
        """
        Called periodically to drive the Raft election timer.
        Should be called at least as often as the minimum election timeout.
        """
        with self._lock:
            if self.state == RaftNodeState.LEADER:
                # Leader sends heartbeats
                if time.time() - self._last_heartbeat >= self.heartbeat_interval:
                    self._send_heartbeat()
                return

            # Check for election timeout
            if time.time() >= self._election_deadline:
                self._start_election()

    # ── Internal Methods ──────────────────────────────────────────────────

    def _random_election_timeout(self) -> float:
        """Generate a random election timeout."""
        return self.election_timeout_min + random.random() * (
            self.election_timeout_max - self.election_timeout_min
        )

    def _start_election(self) -> None:
        """Start a leader election."""
        self.state = RaftNodeState.CANDIDATE
        self.current_term += 1
        self.voted_for = self.node_id
        self._election_deadline = time.time() + self._random_election_timeout()

        last_log_index = len(self.log)
        last_log_term = self.log[-1].term if self.log else 0

        logger.info(f"🗳️  Starting election for term {self.current_term}")

        # Request votes from peers (via callback)
        if self._send_request_vote_cb:
            self._send_request_vote_cb(
                self.node_id, self.current_term, last_log_index, last_log_term
            )

    def _send_heartbeat(self) -> None:
        """Send heartbeat (empty AppendEntries) to peers."""
        self._last_heartbeat = time.time()
        prev_log_index = len(self.log)
        prev_log_term = self.log[-1].term if self.log else 0

        if self._send_append_entries_cb:
            self._send_append_entries_cb(
                leader_id=self.node_id,
                term=self.current_term,
                prev_log_index=prev_log_index,
                prev_log_term=prev_log_term,
                entries=[],
                leader_commit=self.commit_index,
            )

    def _apply_committed_entries(self) -> None:
        """Apply committed log entries to the state machine."""
        while self.last_applied < self.commit_index:
            self.last_applied += 1
            entry = self.log[self.last_applied - 1]

            # Apply to state machine
            if entry.command == "set":
                key = entry.data.get("key")
                value = entry.data.get("value")
                if key is not None:
                    self._state_machine[key] = value
            elif entry.command == "delete":
                key = entry.data.get("key")
                if key is not None:
                    self._state_machine.pop(key, None)

            # Notify commit handlers
            for handler in self._commit_handlers:
                try:
                    handler(entry)
                except Exception as e:
                    logger.error(f"Commit handler error: {e}")

    # ── Persistence ───────────────────────────────────────────────────────

    def _persist_entry(self, entry: RaftLogEntry) -> None:
        """Persist a log entry to JSONL."""
        try:
            with open(RAFT_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry.to_dict()) + "\n")
        except Exception as e:
            logger.error(f"Failed to persist Raft entry: {e}")

    def load_from_log(self) -> None:
        """Load log entries from persistent storage."""
        try:
            if not RAFT_LOG_PATH.exists():
                return
            with open(RAFT_LOG_PATH, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        entry = RaftLogEntry.from_dict(data)
                        if entry.index > len(self.log):
                            self.log.append(entry)
                    except (json.JSONDecodeError, KeyError):
                        continue
            logger.info(f"Loaded {len(self.log)} Raft log entries")
        except Exception as e:
            logger.error(f"Failed to load Raft log: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# Extended Consensus Engine (legacy compatibility)
# ═══════════════════════════════════════════════════════════════════════════════

class ExtendedConsensusEngine(ConsensusEngine):
    """ConsensusEngine with backwards-compatible API for BFT integration tests"""

    def __init__(self):
        super().__init__()
        self._raft_node: Optional[RaftNode] = None

    def init_raft(self, node_id: str, cluster_size: int = 5) -> RaftNode:
        """Initialize the Raft consensus node."""
        self._raft_node = RaftNode(
            node_id=node_id,
            cluster_size=cluster_size,
        )
        self._raft_node.load_from_log()
        logger.info(f"Raft node initialized: {node_id}")
        return self._raft_node

    def get_raft_node(self) -> Optional[RaftNode]:
        """Get the Raft consensus node."""
        return self._raft_node

    def propose(self, proposal_id: str, title: str, sector: str = "general") -> Proposal:
        proposal = Proposal(
            proposal_id=proposal_id,
            title=title,
            description=title,
            proposed_by="system",
            mode=VotingMode.MAJORITY_VOTE,
            context={"sector": sector}
        )
        self._proposals[proposal_id] = proposal
        return proposal

    def cast_vote(self, proposal_id: str, choice_str: str, voter_id: Optional[str] = None):
        if proposal_id not in self._proposals:
            self.propose(proposal_id, f"Proposal {proposal_id}")

        proposal = self._proposals[proposal_id]

        if not voter_id:
            voter_id = f"voter_{len(proposal.votes) + 1}"

        if voter_id not in self._voters:
            self.register_voter(voter_id, voter_id, "general")

        choice = VoteChoice.APPROVE if choice_str == "approve" else VoteChoice.REJECT
        vote = Vote(
            voter_id=voter_id,
            choice=choice,
            confidence=1.0,
            reasoning="Legacy API vote",
            domain="general"
        )
        proposal.votes.append(vote)

    def tally(self, proposal_id: str) -> Dict[str, Any]:
        proposal = self._proposals.get(proposal_id)
        if not proposal:
            return {"status": "rejected"}

        approves = sum(1 for v in proposal.votes if v.choice == VoteChoice.APPROVE)
        total = len(proposal.votes)

        if total > 0 and (approves / total) >= 0.5:
            status_str = "passed"
        else:
            status_str = "rejected"

        return {"status": status_str}


# ═══════════════════════════════════════════════════════════════════════════════
# Singleton
# ═══════════════════════════════════════════════════════════════════════════════

_engine_instance: Optional[ExtendedConsensusEngine] = None


def get_consensus_engine() -> ExtendedConsensusEngine:
    """Get the singleton ExtendedConsensusEngine instance"""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = ExtendedConsensusEngine()
        _engine_instance.register_voters_from_15_clones()
    return _engine_instance


def reset_consensus_engine() -> None:
    """Reset the singleton instance (for testing)."""
    global _engine_instance
    _engine_instance = None
