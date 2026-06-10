"""
STATUS: REAL — Multi-Clone Voting with 4 consensus modes, delegation, arbitration, and audit trail

core/consensus/consensus_engine.py
AsimNexus — Ensemble Consensus System for 15 Founder Clones
=============================================================
Provides 4 voting modes for multi-clone decision making:

  1. MAJORITY_VOTE       — Simple majority (>50%) of clones agree, threshold configurable
  2. PAIRWISE_COMPARISON — Each clone pair votes, winner determined by Elo-style ranking
  3. CONFIDENCE_WEIGHTED — Each vote weighted by clone's confidence score (0.0-1.0)
  4. ROLE_BASED_VETO     — Specific clones have veto power in their domain

Delegation chain:
  Clone Vote → Arbiter → Human Override

Each voting mode returns:
  (decision: str, confidence: float, details: dict)

All votes are logged for audit trail (JSONL persistence).
Standalone and testable without real clones — uses Voter / Vote / Proposal primitives.
"""

from __future__ import annotations

import json
import logging
import math
import secrets
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("AsimNexus.ConsensusEngine")

AUDIT_LOG = Path(__file__).resolve().parent.parent.parent / "data" / "consensus_audit.jsonl"
AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)


# ═══════════════════════════════════════════════════════════════════════════════
# Enums
# ═══════════════════════════════════════════════════════════════════════════════

class VoteChoice(str, Enum):
    """Individual vote options a clone can cast."""
    APPROVE = "approve"
    REJECT  = "reject"
    ABSTAIN = "abstain"
    DEFER   = "defer"


class VotingMode(str, Enum):
    """The 4 consensus voting modes."""
    MAJORITY_VOTE       = "majority_vote"
    PAIRWISE_COMPARISON = "pairwise_comparison"
    CONFIDENCE_WEIGHTED = "confidence_weighted"
    ROLE_BASED_VETO     = "role_based_veto"


class ProposalStatus(str, Enum):
    """Status of a consensus proposal."""
    PENDING       = "pending"
    APPROVED      = "approved"
    REJECTED      = "rejected"
    DEFERRED      = "deferred"
    VETOED        = "vetoed"
    EXPIRED       = "expired"
    HUMAN_OVERRIDE = "human_override"
    ARBITRATED    = "arbitrated"


class ArbiterDecision(str, Enum):
    """Decisions the arbiter can make."""
    UPHOLD        = "uphold"
    OVERTURN      = "overturn"
    REMAND        = "remand"
    ESCALATE_HUMAN = "escalate_human"


# ═══════════════════════════════════════════════════════════════════════════════
# Data Classes
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Voter:
    """A registered voter (clone) with metadata."""
    voter_id:   str
    name:       str
    domain:     str                # e.g. "security", "ethics", "technology"
    weight:     float = 1.0        # base influence weight (0.0-1.0)
    elo_rating: int = 1500         # Elo rating for pairwise comparison mode
    metadata:   Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "voter_id": self.voter_id,
            "name": self.name,
            "domain": self.domain,
            "weight": self.weight,
            "elo_rating": self.elo_rating,
            "metadata": self.metadata,
        }


@dataclass
class Vote:
    """A single vote cast by a clone on a proposal."""
    voter_id:   str
    choice:     VoteChoice
    confidence: float       # 0.0-1.0
    reasoning:  str = ""
    domain:     str = ""
    weight:     float = 1.0
    timestamp:  str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "voter_id": self.voter_id,
            "choice": self.choice.value,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "domain": self.domain,
            "weight": self.weight,
            "timestamp": self.timestamp,
        }


@dataclass
class Proposal:
    """A proposal that clones vote on."""
    proposal_id:   str
    title:         str
    description:   str
    proposed_by:   str                    # voter_id or "system"
    mode:          VotingMode = VotingMode.MAJORITY_VOTE
    status:        ProposalStatus = ProposalStatus.PENDING
    votes:         List[Vote] = field(default_factory=list)
    created_at:    str = ""
    resolved_at:   Optional[str] = None
    threshold:     float = 0.5            # majority threshold (0.5 = 50%)
    quorum:        float = 0.0            # minimum fraction of voters required (0.0 = no quorum)
    expires_at:    Optional[str] = None
    context:       Dict[str, Any] = field(default_factory=dict)

    # Role-based veto fields
    vetoed:        bool = False
    vetoed_by:     Optional[str] = None
    veto_reason:   str = ""

    # Arbitration fields
    arbiter_id:    Optional[str] = None
    arbiter_decision: Optional[ArbiterDecision] = None
    arbiter_reason: str = ""

    # Human override
    human_override: Optional[bool] = None
    human_reason:   str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["mode"] = self.mode.value
        d["status"] = self.status.value
        if self.arbiter_decision:
            d["arbiter_decision"] = self.arbiter_decision.value
        d["votes"] = [v.to_dict() for v in self.votes]
        return d


@dataclass
class ConsensusResult:
    """The result of a consensus round."""
    proposal_id:  str
    title:        str
    mode:         VotingMode
    decision:     str                     # "approved", "rejected", "deferred", etc.
    confidence:   float                   # 0.0-1.0
    details:      Dict[str, Any] = field(default_factory=dict)
    resolved_at:  str = ""

    def __post_init__(self):
        if not self.resolved_at:
            self.resolved_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "title": self.title,
            "mode": self.mode.value,
            "decision": self.decision,
            "confidence": self.confidence,
            "details": self.details,
            "resolved_at": self.resolved_at,
        }


@dataclass
class Delegation:
    """A delegation of voting power from one voter to another for a specific proposal."""
    delegation_id: str
    from_voter:    str        # voter_id delegating their vote
    to_voter:      str        # voter_id receiving the delegated vote
    proposal_id:   str        # round/proposal this applies to
    expires_at:    str
    created_at:    str = ""
    active:        bool = True

    def __post_init__(self):
        if not self.created_at:
            self.created_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "delegation_id": self.delegation_id,
            "from_voter": self.from_voter,
            "to_voter": self.to_voter,
            "proposal_id": self.proposal_id,
            "expires_at": self.expires_at,
            "created_at": self.created_at,
            "active": self.active,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Domain Veto Registry — role-based veto definitions
# ═══════════════════════════════════════════════════════════════════════════════

# Maps domain → voter_id that has veto power in that domain
# Used by ROLE_BASED_VETO mode
DOMAIN_VETO_REGISTRY: Dict[str, List[str]] = {
    # Maps domain -> list of clone IDs that have veto power in that domain
    "security":           ["clone_06", "clone_15"],   # Security Sentinel, Sovereignty Guard
    "ethics":             ["clone_01", "clone_15"],   # Dharma Guardian, Sovereignty Guard
    "sovereignty":        ["clone_15", "clone_01"],   # Sovereignty Guard, Dharma Guardian
    "identity":           ["clone_11", "clone_15"],   # Identity Protector, Sovereignty Guard
    "legal":              ["clone_04"],               # Legal Counsel
    "contracts":          ["clone_14", "clone_04"],   # Contract Auditor, Legal Counsel
    "health":             ["clone_08"],               # Health Advisor
    "environment":        ["clone_10"],               # Environment Watch
    "technology":         ["clone_02"],               # Tech Architect
    "economy":            ["clone_05"],               # Economic Analyst
    "network":            ["clone_12"],               # Mesh Coordinator
    "memory":             ["clone_13"],               # Memory Keeper
    "community":          ["clone_03"],               # Community Weaver
    "culture":            ["clone_07"],               # Cultural Keeper
    "education":          ["clone_09"],               # Education Guide
}

# Clones that can veto ANY decision (sovereignty-level)
# clone_15 = Sovereignty Guard, clone_01 = Dharma Guardian
GLOBAL_VETO_CLONES: List[str] = ["clone_15", "clone_01"]


# ═══════════════════════════════════════════════════════════════════════════════
# ConsensusEngine
# ═══════════════════════════════════════════════════════════════════════════════

class ConsensusEngine:
    """
    Ensemble Consensus Engine for multi-clone decision making.

    Supports 4 voting modes:
      1. MAJORITY_VOTE       — Simple majority (>50%) of clones agree
      2. PAIRWISE_COMPARISON — Elo-style pairwise comparison between clones
      3. CONFIDENCE_WEIGHTED — Each vote weighted by clone's confidence score
      4. ROLE_BASED_VETO     — Domain-specific veto power for certain clones

    Delegation chain: Clone Vote → Arbiter → Human Override
    All votes logged to audit trail (JSONL).

    Usage:
        engine = ConsensusEngine()
        engine.register_voter("clone_01", "Dharma Guardian", "ethics", weight=1.5)

        result = engine.run_consensus(
            title="Deploy new mesh protocol",
            description="Replace UDP broadcast with mDNS only",
            mode=VotingMode.CONFIDENCE_WEIGHTED,
            votes=[...],  # or cast votes individually
        )
        # Returns ConsensusResult with (decision, confidence, details)
    """

    def __init__(self):
        self._voters: Dict[str, Voter] = {}
        self._proposals: Dict[str, Proposal] = {}
        self._results: Dict[str, ConsensusResult] = {}
        self._delegations: Dict[str, List[Delegation]] = {}  # proposal_id → delegations
        self._audit_entries: List[Dict[str, Any]] = []
        self._load_audit()
        logger.info("🏛️ ConsensusEngine initialized with 4 voting modes")

    # ─── Voter Registration ─────────────────────────────────────────────────

    def register_voter(
        self,
        voter_id: str,
        name: str,
        domain: str,
        weight: float = 1.0,
        elo_rating: int = 1500,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Voter:
        """Register a voter (clone) with their domain and weight.

        Args:
            voter_id: Unique identifier (e.g. "clone_01").
            name: Display name (e.g. "Dharma Guardian").
            domain: Domain expertise (e.g. "ethics", "security").
            weight: Base influence weight (0.0-1.0).
            elo_rating: Initial Elo rating for pairwise comparison mode.
            metadata: Optional extra data.

        Returns:
            The registered Voter.
        """
        weight = max(0.0, min(1.0, weight))
        voter = Voter(
            voter_id=voter_id,
            name=name,
            domain=domain,
            weight=weight,
            elo_rating=elo_rating,
            metadata=metadata or {},
        )
        self._voters[voter_id] = voter
        logger.debug(f"Registered voter: {name} ({voter_id}, domain={domain}, weight={weight})")
        return voter

    def register_voters_from_15_clones(self) -> None:
        """Register all 15 standard founder clones with their domains and weights."""
        clones = [
            ("clone_01", "Dharma Guardian",      "ethics",        1.5),
            ("clone_02", "Tech Architect",       "technology",    1.0),
            ("clone_03", "Community Weaver",     "community",     1.2),
            ("clone_04", "Legal Counsel",        "legal",         1.1),
            ("clone_05", "Economic Analyst",     "economy",       1.0),
            ("clone_06", "Security Sentinel",    "security",      1.3),
            ("clone_07", "Cultural Keeper",      "culture",       1.4),
            ("clone_08", "Health Advisor",       "health",        1.0),
            ("clone_09", "Education Guide",      "education",     1.0),
            ("clone_10", "Environment Watch",    "environment",   1.1),
            ("clone_11", "Identity Protector",   "identity",      1.3),
            ("clone_12", "Mesh Coordinator",     "network",       1.0),
            ("clone_13", "Memory Keeper",        "memory",        1.0),
            ("clone_14", "Contract Auditor",     "contracts",     1.2),
            ("clone_15", "Sovereignty Guard",    "sovereignty",   1.5),
        ]
        for vid, name, domain, weight in clones:
            self.register_voter(vid, name, domain, weight=weight)

    def get_voter(self, voter_id: str) -> Optional[Voter]:
        return self._voters.get(voter_id)

    def get_all_voters(self) -> List[Voter]:
        return list(self._voters.values())

    def registered_voter_count(self) -> int:
        return len(self._voters)

    # ─── Delegation ─────────────────────────────────────────────────────────

    def delegate_vote(
        self,
        from_voter: str,
        to_voter: str,
        proposal_id: str,
        ttl_seconds: int = 3600,
    ) -> Optional[Delegation]:
        """Delegate voting power from one voter to another for a proposal.

        Args:
            from_voter: The voter delegating their vote.
            to_voter: The voter receiving the delegated vote.
            proposal_id: The proposal this delegation applies to.
            ttl_seconds: Time-to-live in seconds (default 1 hour).

        Returns:
            The Delegation, or None if either voter is not registered.
        """
        if from_voter not in self._voters:
            logger.error(f"Cannot delegate: voter '{from_voter}' not registered")
            return None
        if to_voter not in self._voters:
            logger.error(f"Cannot delegate to: voter '{to_voter}' not registered")
            return None
        if from_voter == to_voter:
            logger.error("Cannot delegate to self")
            return None

        now = datetime.now(timezone.utc)
        expires = now + timedelta(seconds=ttl_seconds)

        delegation = Delegation(
            delegation_id=secrets.token_hex(8),
            from_voter=from_voter,
            to_voter=to_voter,
            proposal_id=proposal_id,
            expires_at=expires.strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

        if proposal_id not in self._delegations:
            self._delegations[proposal_id] = []
        self._delegations[proposal_id].append(delegation)

        logger.info(
            f"📜 Delegation: {from_voter} → {to_voter} "
            f"for proposal {proposal_id} (expires {delegation.expires_at})"
        )
        self._audit("delegation", {
            "delegation_id": delegation.delegation_id,
            "from_voter": from_voter,
            "to_voter": to_voter,
            "proposal_id": proposal_id,
            "expires_at": delegation.expires_at,
        })
        return delegation

    def revoke_delegation(self, delegation_id: str) -> bool:
        """Revoke a delegation by its ID."""
        for proposal_id, delegations in self._delegations.items():
            for d in delegations:
                if d.delegation_id == delegation_id and d.active:
                    d.active = False
                    logger.info(f"Revoked delegation {delegation_id}")
                    self._audit("delegation_revoked", {
                        "delegation_id": delegation_id,
                        "proposal_id": proposal_id,
                    })
                    return True
        return False

    def get_active_delegations(self, proposal_id: str) -> List[Delegation]:
        """Get all active (non-expired) delegations for a proposal."""
        now = datetime.now(timezone.utc)
        active = []
        for d in self._delegations.get(proposal_id, []):
            if not d.active:
                continue
            expires = datetime.strptime(d.expires_at, "%Y-%m-%dT%H:%M:%SZ")
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            if now < expires:
                active.append(d)
        return active

    def _apply_delegations(self, proposal: Proposal) -> List[Vote]:
        """Apply active delegations to produce delegated votes.

        Supports both proposal-specific delegations and global delegations
        (proposal_id="*" matches all proposals).

        Returns the original votes plus any delegated votes.
        """
        # Get both proposal-specific and global delegations
        specific = self.get_active_delegations(proposal.proposal_id)
        global_delegs = self.get_active_delegations("*")
        delegations = specific + global_delegs
        if not delegations:
            return proposal.votes

        # Build map: to_voter → list of from_voters
        delegation_map: Dict[str, List[str]] = {}
        for d in delegations:
            delegation_map.setdefault(d.to_voter, []).append(d.from_voter)

        new_votes = list(proposal.votes)
        for to_voter, from_voters in delegation_map.items():
            delegate_votes = [v for v in proposal.votes if v.voter_id == to_voter]
            for dv in delegate_votes:
                for from_voter in from_voters:
                    delegated = Vote(
                        voter_id=from_voter,
                        choice=dv.choice,
                        confidence=dv.confidence * 0.9,  # slight discount
                        reasoning=f"Delegated from {from_voter}: {dv.reasoning}",
                        domain=self._voters[from_voter].domain
                        if from_voter in self._voters else dv.domain,
                        weight=dv.weight * 0.8,  # delegation weight discount
                    )
                    new_votes.append(delegated)
                    logger.debug(
                        f"Delegation: {from_voter} → {to_voter} ({dv.choice.value})"
                    )

        logger.info(
            f"Applied {len(delegations)} delegation(s) to proposal {proposal.proposal_id}"
        )
        return new_votes

    # ─── Proposal Creation ──────────────────────────────────────────────────

    def create_proposal(
        self,
        title: str,
        description: str,
        proposed_by: str = "system",
        mode: VotingMode = VotingMode.MAJORITY_VOTE,
        threshold: float = 0.5,
        quorum: float = 0.0,
        expires_in_seconds: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Proposal:
        """Create a new proposal for voting.

        Args:
            title: Short title of the proposal.
            description: Detailed description.
            proposed_by: Who proposed it (voter_id or "system").
            mode: Which voting mode to use.
            threshold: Majority threshold (0.5 = 50%, 0.67 = 67%, etc.).
            quorum: Minimum fraction of eligible voters required (0.0 = no quorum).
            expires_in_seconds: If set, proposal auto-expires after this many seconds.
            context: Optional extra context.

        Returns:
            The created Proposal.
        """
        proposal_id = secrets.token_hex(8)
        expires_at = None
        if expires_in_seconds is not None:
            expires_at = (
                datetime.now(timezone.utc) + timedelta(seconds=expires_in_seconds)
            ).strftime("%Y-%m-%dT%H:%M:%SZ")

        proposal = Proposal(
            proposal_id=proposal_id,
            title=title,
            description=description,
            proposed_by=proposed_by,
            mode=mode,
            threshold=threshold,
            quorum=quorum,
            expires_at=expires_at,
            context=context or {},
        )
        self._proposals[proposal_id] = proposal
        logger.info(
            f"📋 Proposal created: '{title}' (id={proposal_id}, mode={mode.value}, "
            f"threshold={threshold})"
        )
        self._audit("proposal_created", {
            "proposal_id": proposal_id,
            "title": title,
            "mode": mode.value,
            "threshold": threshold,
            "proposed_by": proposed_by,
        })
        return proposal

    def get_proposal(self, proposal_id: str) -> Optional[Proposal]:
        return self._proposals.get(proposal_id)

    # ─── Casting Votes ──────────────────────────────────────────────────────

    def cast_vote(
        self,
        proposal_id: str,
        voter_id: str,
        choice: VoteChoice,
        confidence: float = 0.5,
        reasoning: str = "",
    ) -> Optional[ConsensusResult]:
        """Cast a vote on a proposal.

        If all voters have voted (or quorum met), automatically resolves
        the proposal and returns the ConsensusResult.

        Args:
            proposal_id: The proposal to vote on.
            voter_id: Who is voting.
            choice: APPROVE, REJECT, ABSTAIN, or DEFER.
            confidence: Confidence score 0.0-1.0.
            reasoning: Optional reasoning text.

        Returns:
            ConsensusResult if resolved, None if still pending more votes.
        """
        proposal = self._proposals.get(proposal_id)
        if not proposal:
            logger.error(f"Proposal {proposal_id} not found")
            return None

        # Check if already resolved
        if proposal.status != ProposalStatus.PENDING:
            logger.warning(f"Proposal {proposal_id} already {proposal.status.value}")
            return self._results.get(proposal_id)

        # Check expiration
        if proposal.expires_at:
            expires = datetime.strptime(proposal.expires_at, "%Y-%m-%dT%H:%M:%SZ")
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) > expires:
                return self._resolve_expired(proposal)

        # Validate voter
        voter = self._voters.get(voter_id)
        if not voter:
            logger.error(f"Voter {voter_id} not registered")
            return None

        # Check for duplicate
        if any(v.voter_id == voter_id for v in proposal.votes):
            logger.warning(f"Voter {voter_id} already voted on proposal {proposal_id}")
            return None

        # Normalize confidence
        confidence = max(0.0, min(1.0, confidence))

        vote = Vote(
            voter_id=voter_id,
            choice=choice,
            confidence=confidence,
            reasoning=reasoning,
            domain=voter.domain,
            weight=voter.weight,
        )
        proposal.votes.append(vote)

        logger.info(
            f"🗳️  {voter.name} voted {choice.value} on '{proposal.title}' "
            f"(confidence={confidence:.2f})"
        )
        self._audit("vote_cast", {
            "proposal_id": proposal_id,
            "voter_id": voter_id,
            "voter_name": voter.name,
            "choice": choice.value,
            "confidence": confidence,
            "reasoning": reasoning,
        })

        # Try to resolve
        return self._try_resolve(proposal)

    # ─── Running Full Consensus ─────────────────────────────────────────────

    def run_consensus(
        self,
        title: str,
        description: str,
        votes: List[Vote],
        mode: VotingMode = VotingMode.MAJORITY_VOTE,
        proposed_by: str = "system",
        threshold: float = 0.5,
        quorum: float = 0.0,
        context: Optional[Dict[str, Any]] = None,
    ) -> ConsensusResult:
        """Run a full consensus round with pre-collected votes.

        This is the primary entry point for ensemble consensus.
        Creates a proposal, applies delegations, runs the specified voting mode,
        and returns the result.

        Args:
            title: Proposal title.
            description: Proposal description.
            votes: Pre-collected list of Vote objects from all clones.
            mode: Which voting mode to use.
            proposed_by: Who proposed this.
            threshold: Majority threshold.
            quorum: Minimum fraction of eligible voters required.
            context: Optional extra context.

        Returns:
            ConsensusResult with (decision, confidence, details).
        """
        # Create the proposal
        proposal = self.create_proposal(
            title=title,
            description=description,
            proposed_by=proposed_by,
            mode=mode,
            threshold=threshold,
            quorum=quorum,
            context=context,
        )

        # Validate and add votes
        for vote in votes:
            if vote.voter_id not in self._voters:
                logger.warning(f"Voter {vote.voter_id} not registered, skipping vote")
                continue
            voter = self._voters[vote.voter_id]
            vote.domain = voter.domain
            vote.weight = voter.weight
            proposal.votes.append(vote)

        # Apply delegations
        all_votes = self._apply_delegations(proposal)
        proposal.votes = all_votes

        # Run the selected voting mode
        result = self._resolve_with_mode(proposal)
        self._results[proposal.proposal_id] = result
        self._save_audit_entry(proposal)

        logger.info(
            f"🏁 Consensus '{title}' ({mode.value}): {result.decision} "
            f"(confidence={result.confidence:.2f})"
        )
        return result

    # ─── Voting Mode Resolvers ──────────────────────────────────────────────

    def _resolve_with_mode(self, proposal: Proposal) -> ConsensusResult:
        """Route to the appropriate resolver based on VotingMode."""
        if proposal.mode == VotingMode.MAJORITY_VOTE:
            return self._resolve_majority(proposal)
        elif proposal.mode == VotingMode.PAIRWISE_COMPARISON:
            return self._resolve_pairwise(proposal)
        elif proposal.mode == VotingMode.CONFIDENCE_WEIGHTED:
            return self._resolve_confidence_weighted(proposal)
        elif proposal.mode == VotingMode.ROLE_BASED_VETO:
            return self._resolve_role_based_veto(proposal)
        else:
            return self._resolve_majority(proposal)

    def _resolve_majority(self, proposal: Proposal) -> ConsensusResult:
        """Mode 1: Majority Vote — Simple majority (>threshold) of active votes.

        Counts APPROVE vs REJECT votes (ABSTAIN and DEFER excluded from denominator).
        If APPROVE / (APPROVE + REJECT) > threshold, approved.
        """
        approves = sum(1 for v in proposal.votes if v.choice == VoteChoice.APPROVE)
        rejects = sum(1 for v in proposal.votes if v.choice == VoteChoice.REJECT)
        abstains = sum(1 for v in proposal.votes if v.choice == VoteChoice.ABSTAIN)
        defers = sum(1 for v in proposal.votes if v.choice == VoteChoice.DEFER)

        active = approves + rejects
        total_votes = len(proposal.votes)
        quorum_met = self._check_quorum(proposal, total_votes)

        # Check for veto override
        if proposal.vetoed and not self._can_override_veto(proposal, approves):
            return self._result(
                proposal, "vetoed", 0.0,
                vetoed=True, approves=approves, rejects=rejects,
                abstains=abstains, defers=defers, quorum_met=quorum_met,
            )

        if active == 0:
            decision = "deferred"
            confidence = 0.0
        elif (approves / active) > proposal.threshold:
            decision = "approved"
            confidence = approves / active if active > 0 else 0.0
        else:
            decision = "rejected"
            confidence = rejects / active if active > 0 else 0.0

        proposal.status = ProposalStatus(decision)
        proposal.resolved_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        return self._result(
            proposal, decision, confidence,
            approves=approves, rejects=rejects,
            abstains=abstains, defers=defers,
            total=total_votes, quorum_met=quorum_met,
            threshold=proposal.threshold,
        )

    def _resolve_pairwise(self, proposal: Proposal) -> ConsensusResult:
        """Mode 2: Pairwise Comparison — Elo-style ranking between clones.

        Each pair of clones that voted APPROVE or REJECT is compared.
        APPROVE beats REJECT. The winner and loser exchange Elo points
        based on the K-factor (32). The final decision is determined by
        the average Elo rating of approval vs rejection voters.

        Returns (decision, avg_confidence, elo_details).
        """
        approve_voters = [
            self._voters[v.voter_id] for v in proposal.votes
            if v.choice == VoteChoice.APPROVE and v.voter_id in self._voters
        ]
        reject_voters = [
            self._voters[v.voter_id] for v in proposal.votes
            if v.choice == VoteChoice.REJECT and v.voter_id in self._voters
        ]
        abstain_voters = [
            v for v in proposal.votes if v.choice == VoteChoice.ABSTAIN
        ]
        defer_voters = [
            v for v in proposal.votes if v.choice == VoteChoice.DEFER
        ]

        total_voters = len(proposal.votes)
        quorum_met = self._check_quorum(proposal, total_voters)

        # Check for veto override
        if proposal.vetoed and not self._can_override_veto(proposal, len(approve_voters)):
            return self._result(
                proposal, "vetoed", 0.0,
                vetoed=True,
                approve_elo_avg=0, reject_elo_avg=0,
                elo_changes=[], quorum_met=quorum_met,
            )

        K = 32  # Elo K-factor
        elo_changes = []

        # Run pairwise comparisons
        for a_voter in approve_voters:
            for r_voter in reject_voters:
                # Expected score for approve voter
                expected_a = 1.0 / (1.0 + math.pow(10, (r_voter.elo_rating - a_voter.elo_rating) / 400.0))
                # Approve voter wins (expected=1, actual=1), reject loses (expected=1-expected_a, actual=0)
                change_a = K * (1.0 - expected_a)
                change_r = K * (0.0 - (1.0 - expected_a))

                a_voter.elo_rating += round(change_a)
                r_voter.elo_rating += round(change_r)

                elo_changes.append({
                    "approve_voter": a_voter.voter_id,
                    "reject_voter": r_voter.voter_id,
                    "expected_a": round(expected_a, 3),
                    "change_a": round(change_a, 1),
                    "change_r": round(change_r, 1),
                })

        # Calculate average Elo of approve vs reject camps
        approve_elo_avg = (sum(v.elo_rating for v in approve_voters) / len(approve_voters)) if approve_voters else 0
        reject_elo_avg = (sum(v.elo_rating for v in reject_voters) / len(reject_voters)) if reject_voters else 0

        # Decision based on which side has more votes (majority count)
        # Elo ratings are tracked for confidence and future rounds, but the
        # immediate decision uses simple count comparison.
        approve_count = len(approve_voters)
        reject_count = len(reject_voters)

        if approve_count > reject_count:
            decision = "approved"
            # Confidence uses Elo differential
            total_elo = approve_elo_avg + reject_elo_avg
            confidence = approve_elo_avg / total_elo if total_elo > 0 else 0.55
        elif reject_count > approve_count:
            decision = "rejected"
            total_elo = approve_elo_avg + reject_elo_avg
            confidence = reject_elo_avg / total_elo if total_elo > 0 else 0.55
        else:
            # Equal count — use Elo as tiebreaker
            if approve_elo_avg > reject_elo_avg:
                decision = "approved"
                confidence = 0.51
            elif reject_elo_avg > approve_elo_avg:
                decision = "rejected"
                confidence = 0.51
            else:
                decision = "deferred"
                confidence = 0.0

        proposal.status = ProposalStatus(decision)
        proposal.resolved_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        return self._result(
            proposal, decision, confidence,
            approve_elo_avg=round(approve_elo_avg, 1),
            reject_elo_avg=round(reject_elo_avg, 1),
            approve_count=len(approve_voters),
            reject_count=len(reject_voters),
            abstain_count=len(abstain_voters),
            defer_count=len(defer_voters),
            elo_changes=elo_changes,
            k_factor=K,
            quorum_met=quorum_met,
        )

    def _resolve_confidence_weighted(self, proposal: Proposal) -> ConsensusResult:
        """Mode 3: Confidence-Weighted — Each vote weighted by confidence (0.0-1.0).

        Total approval weight = sum of confidence * voter_weight for APPROVE votes.
        Total rejection weight = sum of confidence * voter_weight for REJECT votes.
        If approval_weight / (approval + rejection) > threshold, approved.
        """
        approve_weight = 0.0
        reject_weight = 0.0
        abstain_weight = 0.0
        defer_weight = 0.0
        total_approve_confidence = 0.0
        total_reject_confidence = 0.0

        for vote in proposal.votes:
            effective_weight = vote.weight * vote.confidence

            if vote.choice == VoteChoice.APPROVE:
                approve_weight += effective_weight
                total_approve_confidence += vote.confidence
            elif vote.choice == VoteChoice.REJECT:
                reject_weight += effective_weight
                total_reject_confidence += vote.confidence
            elif vote.choice == VoteChoice.ABSTAIN:
                abstain_weight += effective_weight
            elif vote.choice == VoteChoice.DEFER:
                defer_weight += effective_weight

        total_active = approve_weight + reject_weight
        total_votes = len(proposal.votes)
        quorum_met = self._check_quorum(proposal, total_votes)

        # Check for veto override
        approves_count = sum(1 for v in proposal.votes if v.choice == VoteChoice.APPROVE)
        if proposal.vetoed and not self._can_override_veto(proposal, approves_count):
            return self._result(
                proposal, "vetoed", 0.0,
                vetoed=True,
                approve_weight=round(approve_weight, 3),
                reject_weight=round(reject_weight, 3),
                abstain_weight=round(abstain_weight, 3),
                defer_weight=round(defer_weight, 3),
                quorum_met=quorum_met,
            )

        if total_active == 0:
            decision = "deferred"
            confidence = 0.0
        elif (approve_weight / total_active) > proposal.threshold:
            decision = "approved"
            # Confidence = weighted average of approval confidence
            confidence = (
                total_approve_confidence / sum(1 for v in proposal.votes if v.choice == VoteChoice.APPROVE)
                if sum(1 for v in proposal.votes if v.choice == VoteChoice.APPROVE) > 0
                else 0.5
            )
        else:
            decision = "rejected"
            confidence = (
                total_reject_confidence / sum(1 for v in proposal.votes if v.choice == VoteChoice.REJECT)
                if sum(1 for v in proposal.votes if v.choice == VoteChoice.REJECT) > 0
                else 0.5
            )

        proposal.status = ProposalStatus(decision)
        proposal.resolved_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        return self._result(
            proposal, decision, confidence,
            approve_weight=round(approve_weight, 3),
            reject_weight=round(reject_weight, 3),
            abstain_weight=round(abstain_weight, 3),
            defer_weight=round(defer_weight, 3),
            total_weight=round(approve_weight + reject_weight + abstain_weight + defer_weight, 3),
            threshold=proposal.threshold,
            quorum_met=quorum_met,
        )

    def _resolve_role_based_veto(self, proposal: Proposal) -> ConsensusResult:
        """Mode 4: Role-Based Veto — Clones have veto power in their domains.

        1. First run confidence-weighted voting (Mode 3) as the base decision.
        2. Then check if any clone with domain veto power has voted REJECT on
           a proposal matching their domain — that's a domain veto.
        3. Global veto clones (Sovereignty Guard, Dharma Guardian) can veto ANY proposal.
        4. A domain veto can be overridden by supermajority (>=67%) of all clones.

        Returns:
            ConsensusResult with veto information in details.
        """
        # First, run confidence-weighted as the base
        base_result = self._resolve_confidence_weighted(proposal)
        base_decision = base_result.decision
        base_confidence = base_result.confidence

        # Check for domain and global vetoes
        vetoes: List[Dict[str, Any]] = []
        veto_active = False

        for vote in proposal.votes:
            if vote.choice != VoteChoice.REJECT:
                continue

            voter = self._voters.get(vote.voter_id)
            if not voter:
                continue

            # Check global veto power
            if vote.voter_id in GLOBAL_VETO_CLONES:
                vetoes.append({
                    "voter_id": vote.voter_id,
                    "name": voter.name,
                    "type": "global",
                    "reasoning": vote.reasoning,
                })
                veto_active = True

            # Check domain veto power
            domain_vetoers = DOMAIN_VETO_REGISTRY.get(voter.domain, [])
            if vote.voter_id in domain_vetoers:
                # Check if proposal's context or description mentions this domain
                domain_mentioned = self._domain_in_proposal(proposal, voter.domain)
                if domain_mentioned:
                    vetoes.append({
                        "voter_id": vote.voter_id,
                        "name": voter.name,
                        "type": "domain",
                        "domain": voter.domain,
                        "reasoning": vote.reasoning,
                    })
                    veto_active = True

        # If vetoes are active, check if they can be overridden
        if veto_active:
            approves = sum(1 for v in proposal.votes if v.choice == VoteChoice.APPROVE)
            total_active = sum(
                1 for v in proposal.votes
                if v.choice in (VoteChoice.APPROVE, VoteChoice.REJECT)
            )

            # Supermajority override: >= 67% of active votes approve
            if total_active > 0 and (approves / total_active) >= 0.67:
                # Veto overridden
                proposal.vetoed = True
                proposal.vetoed_by = ", ".join(v["name"] for v in vetoes)
                proposal.veto_reason = "Veto overridden by supermajority"

                decision = base_decision
                confidence = base_confidence * 0.9  # Slightly reduced confidence after veto override

                logger.info(
                    f"⛔ Veto by {[v['name'] for v in vetoes]} overridden by supermajority "
                    f"({approves}/{total_active} >= 67%)"
                )
            else:
                # Veto stands
                proposal.vetoed = True
                proposal.vetoed_by = ", ".join(v["name"] for v in vetoes)
                proposal.veto_reason = "; ".join(v["reasoning"] for v in vetoes)
                proposal.status = ProposalStatus.VETOED
                proposal.resolved_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

                decision = "vetoed"
                confidence = 0.0

                logger.info(
                    f"⛔ Proposal vetoed by {[v['name'] for v in vetoes]} "
                    f"(domain/global veto power)"
                )

                return self._result(
                    proposal, decision, confidence,
                    base_decision=base_decision,
                    base_confidence=base_confidence,
                    vetoes=vetoes,
                    veto_overridden=False,
                )

        # No active veto or veto overridden
        proposal.resolved_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        return self._result(
            proposal, base_decision, base_confidence,
            base_decision=base_decision,
            base_confidence=base_confidence,
            vetoes=vetoes,
            veto_active=veto_active,
            veto_overridden=len(vetoes) > 0,
        )

    # ─── Arbitration ────────────────────────────────────────────────────────

    def arbitrate(
        self,
        proposal_id: str,
        arbiter_id: str,
        decision: ArbiterDecision,
        reason: str = "",
    ) -> ConsensusResult:
        """Arbitrate a proposal — resolve disputes or deadlocks.

        Delegation chain: Clone Vote → Arbiter → Human Override

        The arbiter can:
        - UPHOLD: Keep the current decision
        - OVERTURN: Flip the decision
        - REMAND: Send back for more voting
        - ESCALATE_HUMAN: Send to human override

        Args:
            proposal_id: The proposal to arbitrate.
            arbiter_id: Who is arbitrating (voter_id or "arbiter_system").
            decision: The arbiter's decision.
            reason: Reasoning for the decision.

        Returns:
            Updated ConsensusResult.
        """
        proposal = self._proposals.get(proposal_id)
        if not proposal:
            raise KeyError(f"Proposal {proposal_id} not found")

        proposal.arbiter_id = arbiter_id
        proposal.arbiter_decision = decision
        proposal.arbiter_reason = reason

        if decision == ArbiterDecision.UPHOLD:
            # Keep current result
            result = self._results.get(proposal_id)
            if result:
                result.details["arbitrated"] = True
                result.details["arbiter_decision"] = "uphold"
                result.details["arbiter_reason"] = reason
            else:
                # No current result — create a default one
                result = ConsensusResult(
                    proposal_id=proposal_id,
                    title=proposal.title,
                    mode=proposal.mode,
                    decision="pending",
                    confidence=0.0,
                    details={"arbitrated": True, "arbiter_decision": "uphold", "arbiter_reason": reason},
                )
                self._results[proposal_id] = result
            proposal.status = ProposalStatus.ARBITRATED

        elif decision == ArbiterDecision.OVERTURN:
            # Flip the decision
            result = self._results.get(proposal_id)
            if result:
                if result.decision == "approved":
                    result.decision = "rejected"
                    result.confidence = 0.3
                elif result.decision == "rejected":
                    result.decision = "approved"
                    result.confidence = 0.3
                else:
                    result.decision = "rejected"
                    result.confidence = 0.3
                result.details["arbitrated"] = True
                result.details["arbiter_decision"] = "overturn"
                result.details["arbiter_reason"] = reason
            else:
                # Create a default overturned result
                result = ConsensusResult(
                    proposal_id=proposal_id,
                    title=proposal.title,
                    mode=proposal.mode,
                    decision="rejected",
                    confidence=0.3,
                    details={"arbitrated": True, "arbiter_decision": "overturn", "arbiter_reason": reason},
                )
                self._results[proposal_id] = result
            proposal.status = ProposalStatus.ARBITRATED

        elif decision == ArbiterDecision.REMAND:
            # Send back for more voting — reset status
            proposal.status = ProposalStatus.PENDING
            result = ConsensusResult(
                proposal_id=proposal_id,
                title=proposal.title,
                mode=proposal.mode,
                decision="remanded",
                confidence=0.0,
                details={"arbitrated": True, "arbiter_decision": "remand", "arbiter_reason": reason},
            )
            self._results[proposal_id] = result

        elif decision == ArbiterDecision.ESCALATE_HUMAN:
            proposal.status = ProposalStatus.PENDING
            # Requires human_override() to be called
            result = ConsensusResult(
                proposal_id=proposal_id,
                title=proposal.title,
                mode=proposal.mode,
                decision="escalated_to_human",
                confidence=0.0,
                details={"arbitrated": True, "arbiter_decision": "escalate_human", "arbiter_reason": reason},
            )
            self._results[proposal_id] = result

        else:
            raise ValueError(f"Unknown arbiter decision: {decision}")
        proposal.resolved_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        logger.info(
            f"⚖️ Arbiter {arbiter_id} decided {decision.value} on proposal {proposal_id}: {reason}"
        )
        self._audit("arbitration", {
            "proposal_id": proposal_id,
            "arbiter_id": arbiter_id,
            "decision": decision.value,
            "reason": reason,
        })
        return result

    # ─── Human Override ─────────────────────────────────────────────────────

    def human_override(
        self,
        proposal_id: str,
        approved: bool,
        reason: str = "",
    ) -> ConsensusResult:
        """Human override — final authority in the delegation chain.

        Clone Vote → Arbiter → Human Override

        Args:
            proposal_id: The proposal to override.
            approved: True to approve, False to reject.
            reason: Why the human overrode.

        Returns:
            The final ConsensusResult.
        """
        proposal = self._proposals.get(proposal_id)
        if not proposal:
            raise KeyError(f"Proposal {proposal_id} not found")

        proposal.human_override = approved
        proposal.human_reason = reason
        proposal.status = ProposalStatus.HUMAN_OVERRIDE
        proposal.resolved_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        decision = "approved" if approved else "rejected"
        confidence = 1.0  # Human decision is absolute

        result = ConsensusResult(
            proposal_id=proposal_id,
            title=proposal.title,
            mode=proposal.mode,
            decision=decision,
            confidence=confidence,
            details={
                "human_override": True,
                "approved": approved,
                "reason": reason,
                "previous_status": proposal.status.value,
            },
        )
        self._results[proposal_id] = result

        logger.info(
            f"👤 Human override on '{proposal.title}': {'APPROVED' if approved else 'REJECTED'} — {reason}"
        )
        self._audit("human_override", {
            "proposal_id": proposal_id,
            "approved": approved,
            "reason": reason,
        })
        return result

    # ─── Queries ─────────────────────────────────────────────────────────────

    def get_result(self, proposal_id: str) -> Optional[ConsensusResult]:
        return self._results.get(proposal_id)

    def list_proposals(self, limit: int = 20) -> List[Dict[str, Any]]:
        """List all proposals with their status."""
        sorted_props = sorted(
            self._proposals.values(),
            key=lambda p: p.created_at,
            reverse=True,
        )
        return [
            {
                "proposal_id": p.proposal_id,
                "title": p.title,
                "mode": p.mode.value,
                "status": p.status.value,
                "created_at": p.created_at,
                "vote_count": len(p.votes),
                "vetoed": p.vetoed,
                "human_override": p.human_override,
            }
            for p in sorted_props[:limit]
        ]

    def get_stats(self) -> Dict[str, Any]:
        """Get consensus engine statistics."""
        total = len(self._results)
        approved = sum(1 for r in self._results.values() if r.decision == "approved")
        rejected = sum(1 for r in self._results.values() if r.decision == "rejected")
        vetoed = sum(1 for r in self._results.values() if r.decision == "vetoed")
        deferred = sum(1 for r in self._results.values() if r.decision == "deferred")

        mode_counts: Dict[str, int] = {}
        for r in self._results.values():
            mode_counts[r.mode.value] = mode_counts.get(r.mode.value, 0) + 1

        return {
            "total_proposals": len(self._proposals),
            "total_resolved": total,
            "approved": approved,
            "rejected": rejected,
            "vetoed": vetoed,
            "deferred": deferred,
            "pending": len(self._proposals) - total,
            "registered_voters": len(self._voters),
            "modes_used": mode_counts,
            "active_delegations": sum(
                len(self.get_active_delegations(pid))
                for pid in self._delegations
            ),
        }

    def pending_human_override(self) -> List[Proposal]:
        """Get proposals that need human override (escalated)."""
        return [
            p for p in self._proposals.values()
            if p.arbiter_decision == ArbiterDecision.ESCALATE_HUMAN
            and p.human_override is None
        ]

    # ─── Audit Trail ────────────────────────────────────────────────────────

    def get_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get the audit trail entries."""
        return list(reversed(self._audit_entries))[:limit]

    # ─── Internal Helpers ───────────────────────────────────────────────────

    def _try_resolve(self, proposal: Proposal) -> Optional[ConsensusResult]:
        """Try to resolve a proposal. Returns result if resolved, None otherwise."""
        # Check quorum
        total_votes = len(proposal.votes)
        if not self._check_quorum(proposal, total_votes):
            return None

        # Check if all registered voters have voted
        voted_ids = {v.voter_id for v in proposal.votes}
        all_voters = set(self._voters.keys())
        all_voted = voted_ids == all_voters

        if all_voted:
            result = self._resolve_with_mode(proposal)
            self._results[proposal.proposal_id] = result
            self._save_audit_entry(proposal)
            return result

        # For simple majority and confidence-weighted, also resolve early if
        # remaining votes can't change the outcome
        if proposal.mode in (VotingMode.MAJORITY_VOTE, VotingMode.CONFIDENCE_WEIGHTED):
            remaining = all_voters - voted_ids
            if not remaining:
                result = self._resolve_with_mode(proposal)
                self._results[proposal.proposal_id] = result
                self._save_audit_entry(proposal)
                return result

        return None

    def _resolve_expired(self, proposal: Proposal) -> ConsensusResult:
        """Resolve an expired proposal as rejected."""
        proposal.status = ProposalStatus.EXPIRED
        proposal.resolved_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        result = ConsensusResult(
            proposal_id=proposal.proposal_id,
            title=proposal.title,
            mode=proposal.mode,
            decision="expired",
            confidence=0.0,
            details={
                "expired": True,
                "vote_count": len(proposal.votes),
                "expires_at": proposal.expires_at,
            },
        )
        self._results[proposal.proposal_id] = result
        self._save_audit_entry(proposal)
        logger.info(f"⏰ Proposal '{proposal.title}' expired — rejected")
        return result

    def _check_quorum(self, proposal: Proposal, total_votes: int) -> bool:
        """Check if quorum is met."""
        if proposal.quorum <= 0.0:
            return True  # No quorum requirement
        if not self._voters:
            return True  # No voters registered = no quorum needed
        return (total_votes / len(self._voters)) >= proposal.quorum

    def _can_override_veto(self, proposal: Proposal, approves: int) -> bool:
        """Check if a veto can be overridden by supermajority."""
        total_active = sum(
            1 for v in proposal.votes
            if v.choice in (VoteChoice.APPROVE, VoteChoice.REJECT)
        )
        if total_active == 0:
            return False
        return (approves / total_active) >= 0.67

    def _domain_in_proposal(self, proposal: Proposal, domain: str) -> bool:
        """Check if a proposal mentions a specific domain."""
        text = f"{proposal.title} {proposal.description} {json.dumps(proposal.context)}".lower()

        domain_keywords = {
            "security":     ["security", "threat", "vulnerability", "attack", "breach", "hack", "cyber"],
            "ethics":       ["ethics", "moral", "dharma", "right", "wrong", "fair"],
            "sovereignty":  ["sovereignty", "autonomous", "independence", "control", "freedom"],
            "identity":     ["identity", "privacy", "personal data", "pii", "kYC"],
            "legal":        ["legal", "law", "regulation", "compliance", "statute"],
            "contracts":    ["contract", "agreement", "terms", "escrow"],
            "health":       ["health", "medical", "wellness", "biometric", "disease"],
            "environment":  ["environment", "climate", "carbon", "green", "sustainable"],
            "technology":   ["technology", "code", "software", "architecture", "system design"],
            "economy":      ["economy", "financial", "budget", "cost", "revenue", "price"],
            "network":      ["network", "mesh", "p2p", "peer", "connectivity"],
            "memory":       ["memory", "history", "record", "archive", "data retention"],
            "community":    ["community", "village", "group", "social", "collective"],
            "culture":      ["culture", "tradition", "heritage", "language", "art"],
            "education":    ["education", "learning", "teaching", "curriculum", "skill"],
        }

        keywords = domain_keywords.get(domain, [domain])
        return any(kw in text for kw in keywords)

    def _result(self, proposal: Proposal, decision: str, confidence: float,
                **details) -> ConsensusResult:
        """Create a ConsensusResult with consistent structure."""
        result = ConsensusResult(
            proposal_id=proposal.proposal_id,
            title=proposal.title,
            mode=proposal.mode,
            decision=decision,
            confidence=confidence,
            details={
                "mode": proposal.mode.value,
                "threshold": proposal.threshold,
                "quorum": proposal.quorum,
                "voter_count": len(self._voters),
                "vote_count": len(proposal.votes),
                "proposed_by": proposal.proposed_by,
                "vetoed": proposal.vetoed,
                "vetoed_by": proposal.vetoed_by,
                "veto_reason": proposal.veto_reason,
                "human_override": proposal.human_override,
                **details,
            },
        )
        return result

    def _audit(self, action: str, data: Dict[str, Any]) -> None:
        """Record an audit entry (in-memory)."""
        entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "action": action,
            **data,
        }
        self._audit_entries.append(entry)

    def _save_audit_entry(self, proposal: Proposal) -> None:
        """Persist a complete proposal audit entry to JSONL."""
        try:
            entry = {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "action": "proposal_resolved",
                "proposal": proposal.to_dict(),
            }
            with open(AUDIT_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            logger.warning(f"Audit log write failed: {e}")

    def _load_audit(self) -> None:
        """Load existing audit entries from JSONL."""
        if not AUDIT_LOG.exists():
            return
        try:
            with open(AUDIT_LOG, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        self._audit_entries.append(entry)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.warning(f"Audit log load failed: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# Convenience API — Clone Consensus Wrapper
# ═══════════════════════════════════════════════════════════════════════════════

class CloneConsensusFacade:
    """
    High-level facade that wraps ConsensusEngine for the 15-clone system.

    Provides:
    - Automatic registration of all 15 clones
    - LLM-powered voting (if founder_system available) or confidence-based voting
    - All 4 voting modes
    - Delegation, arbitration, human override
    """

    def __init__(self, founder_system=None):
        self.engine = ConsensusEngine()
        self._founder_system = founder_system
        self.engine.register_voters_from_15_clones()
        logger.info(
            f"CloneConsensusFacade ready — {self.engine.registered_voter_count()} clones registered"
        )

    async def run_consensus_round(
        self,
        title: str,
        description: str,
        mode: VotingMode = VotingMode.MAJORITY_VOTE,
        threshold: float = 0.5,
        quorum: float = 0.0,
        votes: Optional[List[Vote]] = None,
        use_llm: bool = False,
    ) -> ConsensusResult:
        """Run a consensus round.

        If use_llm=True and founder_system is available, generates LLM-powered votes.
        Otherwise uses provided votes or generates heuristic votes.

        Args:
            title: Proposal title.
            description: Proposal description.
            mode: Voting mode.
            threshold: Majority threshold.
            quorum: Minimum voter fraction required.
            votes: Pre-collected votes (optional, generated if not provided).
            use_llm: Whether to use LLM-powered voting.

        Returns:
            ConsensusResult.
        """
        if votes is None:
            if use_llm and self._founder_system:
                votes = await self._collect_llm_votes(title, description)
            else:
                votes = self._generate_heuristic_votes(title, description)

        return self.engine.run_consensus(
            title=title,
            description=description,
            votes=votes,
            mode=mode,
            threshold=threshold,
            quorum=quorum,
        )

    def _generate_heuristic_votes(
        self,
        title: str,
        description: str,
    ) -> List[Vote]:
        """Generate heuristic votes based on keyword matching (fallback).

        Replaces the old keyword heuristic from clone_consensus.py with
        the new ConsensusEngine voting model.
        """
        text = f"{title} {description}".lower()
        votes = []

        domain_reject_keywords = {
            "ethics":       ["harm", "manipulation", "exploit", "abuse", "coerce"],
            "security":     ["vulnerability", "exposed", "leak", "breach", "attack"],
            "sovereignty":  ["control", "dependency", "monopoly", "forced", "mandatory"],
            "identity":     ["expose", "reveal", "track", "surveillance"],
            "legal":        ["illegal", "fraud", "scam", "violation", "lawsuit"],
            "contracts":    ["escrow risk", "unsigned", "force", "coerce"],
            "culture":      ["cultural imperialism", "replace tradition", "erase"],
        }
        domain_approve_keywords = {
            "technology":   ["efficient", "local-first", "open source", "privacy"],
            "community":    ["community", "village", "local", "shared", "collective"],
            "economy":      ["fair", "equitable", "transparent", "sustainable"],
            "health":       ["wellbeing", "safe", "healthy"],
            "education":    ["learn", "teach", "knowledge", "skill"],
            "environment":  ["sustainable", "green", "clean"],
            "memory":       ["remember", "history", "preserve"],
            "network":      ["connect", "mesh", "peer", "distributed"],
        }

        for voter in self.engine.get_all_voters():
            domain = voter.domain

            # Check reject keywords
            reject_kws = domain_reject_keywords.get(domain, [])
            if any(kw in text for kw in reject_kws):
                votes.append(Vote(
                    voter_id=voter.voter_id,
                    choice=VoteChoice.REJECT,
                    confidence=0.8,
                    reasoning=f"Domain-specific concern in {domain}",
                    domain=domain,
                    weight=voter.weight,
                ))
                continue

            # Check approve keywords
            approve_kws = domain_approve_keywords.get(domain, [])
            if any(kw in text for kw in approve_kws):
                votes.append(Vote(
                    voter_id=voter.voter_id,
                    choice=VoteChoice.APPROVE,
                    confidence=0.75,
                    reasoning=f"Aligns with {domain} values",
                    domain=domain,
                    weight=voter.weight,
                ))
                continue

            # Default: approve with moderate confidence
            votes.append(Vote(
                voter_id=voter.voter_id,
                choice=VoteChoice.APPROVE,
                confidence=0.6,
                reasoning=f"No domain-specific concerns found for {domain}",
                domain=domain,
                weight=voter.weight,
            ))

        return votes

    async def _collect_llm_votes(
        self,
        title: str,
        description: str,
    ) -> List[Vote]:
        """Collect votes by calling each clone's LLM via the founder system."""
        if not self._founder_system:
            return self._generate_heuristic_votes(title, description)

        import asyncio
        from core.consensus.founder_to_clone_map import (
            get_founders_for_clone,
            get_vote_weight,
        )

        votes = []
        tasks = []

        for voter in self.engine.get_all_voters():
            task = self._call_llm_for_vote(
                voter, title, description
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            voter = self.engine.get_all_voters()[i]
            if isinstance(result, Exception):
                logger.warning(f"LLM vote failed for {voter.name}: {result}")
                votes.append(Vote(
                    voter_id=voter.voter_id,
                    choice=VoteChoice.ABSTAIN,
                    confidence=0.0,
                    reasoning=f"LLM error: {result}",
                    domain=voter.domain,
                    weight=voter.weight,
                ))
            else:
                votes.append(result)

        return votes

    async def _call_llm_for_vote(
        self,
        voter: Voter,
        title: str,
        description: str,
    ) -> Vote:
        """Call a specific clone's LLM to get their vote."""
        # This would use self._founder_system to call the LLM
        # For now, fallback to heuristic
        heuristic_votes = self._generate_heuristic_votes(title, description)
        for v in heuristic_votes:
            if v.voter_id == voter.voter_id:
                return v
        return Vote(
            voter_id=voter.voter_id,
            choice=VoteChoice.ABSTAIN,
            confidence=0.0,
            reasoning="No LLM available",
            domain=voter.domain,
            weight=voter.weight,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Singleton
# ═══════════════════════════════════════════════════════════════════════════════

_engine: Optional[ConsensusEngine] = None


def get_consensus_engine() -> ConsensusEngine:
    """Get or create the global ConsensusEngine singleton."""
    global _engine
    if _engine is None:
        _engine = ConsensusEngine()
    return _engine


def reset_consensus_engine():
    """Reset the global singleton (for testing)."""
    global _engine
    _engine = None
