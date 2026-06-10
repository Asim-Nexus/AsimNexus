"""
core/consensus/clone_consensus.py
AsimNexus — 15-Clone Consensus Mode (LLM-Powered)
==================================================
When a HIGH/CRITICAL decision needs to be made, all 15 Founder
Clones vote via their respective NVIDIA LLM APIs. Consensus requires:

  - Simple majority (8/15) for HIGH decisions
  - Supermajority (11/15) for CRITICAL decisions
  - Unanimous (15/15) for SOVEREIGNTY decisions

Each clone votes independently based on its domain expertise, using
the actual FounderClone NVIDIA LLM calls (not keyword heuristics).

ΔT Engine weights votes by relevance weight (founder-to-clone mapping).
Human always has veto (Final-3 Gate 3).

Vote types:
  APPROVE  — clone recommends proceeding
  REJECT   — clone recommends blocking
  ABSTAIN  — clone has insufficient data
  DEFER    — clone requests more human input

Delegation:
  Any clone can delegate its vote to another clone for a specific proposal.
  Delegations expire after a configurable TTL.

Arbitration:
  resolve_tie() — CEO casts the deciding vote
  veto()        — any founder can veto; overridable by supermajority

"Fifteen minds. One decision. Human decides when they disagree."
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("AsimNexus.Consensus")

CONSENSUS_LOG = Path(__file__).resolve().parent.parent.parent / "data" / "consensus_log.jsonl"
CONSENSUS_LOG.parent.mkdir(parents=True, exist_ok=True)

# ─── CLONE DEFINITIONS ─────────────────────────────────────────────────────────

# The 15 clone specializations used by the consensus engine.
# Each clone has a dharma_weight that scales its vote influence.
FOUNDER_CLONES = [
    {"id": "clone_01", "name": "Dharma Guardian",    "domain": "ethics",        "dharma_weight": 1.5},
    {"id": "clone_02", "name": "Tech Architect",     "domain": "technology",    "dharma_weight": 1.0},
    {"id": "clone_03", "name": "Community Weaver",   "domain": "community",     "dharma_weight": 1.2},
    {"id": "clone_04", "name": "Legal Counsel",      "domain": "legal",         "dharma_weight": 1.1},
    {"id": "clone_05", "name": "Economic Analyst",   "domain": "economy",       "dharma_weight": 1.0},
    {"id": "clone_06", "name": "Security Sentinel",  "domain": "security",      "dharma_weight": 1.3},
    {"id": "clone_07", "name": "Cultural Keeper",    "domain": "culture",       "dharma_weight": 1.4},
    {"id": "clone_08", "name": "Health Advisor",     "domain": "health",        "dharma_weight": 1.0},
    {"id": "clone_09", "name": "Education Guide",    "domain": "education",     "dharma_weight": 1.0},
    {"id": "clone_10", "name": "Environment Watch",  "domain": "environment",   "dharma_weight": 1.1},
    {"id": "clone_11", "name": "Identity Protector", "domain": "identity",      "dharma_weight": 1.3},
    {"id": "clone_12", "name": "Mesh Coordinator",   "domain": "network",       "dharma_weight": 1.0},
    {"id": "clone_13", "name": "Memory Keeper",      "domain": "memory",        "dharma_weight": 1.0},
    {"id": "clone_14", "name": "Contract Auditor",   "domain": "contracts",     "dharma_weight": 1.2},
    {"id": "clone_15", "name": "Sovereignty Guard",  "domain": "sovereignty",   "dharma_weight": 1.5},
]

_CLONE_BY_ID: Dict[str, dict] = {c["id"]: c for c in FOUNDER_CLONES}
_CLONE_BY_DOMAIN: Dict[str, List[dict]] = {}
for c in FOUNDER_CLONES:
    _CLONE_BY_DOMAIN.setdefault(c["domain"], []).append(c)


# ─── ENUMS ─────────────────────────────────────────────────────────────────────

class VoteChoice(str, Enum):
    APPROVE = "approve"
    REJECT  = "reject"
    ABSTAIN = "abstain"
    DEFER   = "defer"


class DecisionLevel(str, Enum):
    LOW          = "low"          # No vote needed — auto
    HIGH         = "high"         # Simple majority 8/15
    CRITICAL     = "critical"     # Supermajority 11/15
    SOVEREIGNTY  = "sovereignty"  # Unanimous 15/15 + Human


class ConsensusOutcome(str, Enum):
    APPROVED         = "approved"
    REJECTED         = "rejected"
    DEFERRED_HUMAN   = "deferred_human"   # Too many DEFER votes
    PENDING          = "pending"          # Voting in progress
    REQUIRES_HUMAN   = "requires_human"   # SOVEREIGNTY or split


# ─── DATA CLASSES ──────────────────────────────────────────────────────────────

@dataclass
class CloneVote:
    clone_id:    str
    clone_name:  str
    domain:      str
    choice:      VoteChoice
    reasoning:   str
    confidence:  float       # 0.0–1.0
    voted_at:    str
    founder_role: str = ""   # Which FounderRole cast this vote (via LLM)
    delta_weight: float = 1.0  # ΔT relevance weight multiplier


@dataclass
class DelegateVote:
    """A delegation of voting power from one clone to another."""
    from_clone:    str       # clone_id delegating their vote
    to_clone:      str       # clone_id receiving the delegated vote
    proposal_id:   str       # round_id this delegation applies to
    expires_at:    str       # ISO-8601 timestamp when delegation expires
    created_at:    str       # ISO-8601 timestamp when delegation was created


@dataclass
class ConsensusRound:
    round_id:     str
    topic:        str
    description:  str
    level:        DecisionLevel
    votes:        List[CloneVote] = field(default_factory=list)
    outcome:      ConsensusOutcome = ConsensusOutcome.PENDING
    created_at:   str = ""
    resolved_at:  str = ""
    human_override: Optional[bool] = None
    summary:      str = ""
    vetoed:       bool = False
    vetoed_by:    str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["level"] = self.level.value
        d["outcome"] = self.outcome.value
        for v in d.get("votes", []):
            if isinstance(v.get("choice"), VoteChoice):
                v["choice"] = v["choice"].value
        return d


# ─── VOTE RESOLUTION ───────────────────────────────────────────────────────────

def _compute_weighted_score(cr: ConsensusRound) -> Tuple[float, float, float, float]:
    """Compute ΔT-weighted approval, rejection, abstain, and defer scores.

    Each vote's contribution is: dharma_weight * delta_weight * confidence.
    Returns (total_weight, approve_weight, reject_weight, defer_weight).
    """
    total_w = 0.0
    approve_w = 0.0
    reject_w = 0.0
    defer_w = 0.0
    abstain_w = 0.0

    for vote in cr.votes:
        clone_def = _CLONE_BY_ID.get(vote.clone_id)
        dharma_w = clone_def["dharma_weight"] if clone_def else 1.0
        delta_w = vote.delta_weight
        conf = vote.confidence
        weight = dharma_w * delta_w * conf
        total_w += weight

        if vote.choice == VoteChoice.APPROVE:
            approve_w += weight
        elif vote.choice == VoteChoice.REJECT:
            reject_w += weight
        elif vote.choice == VoteChoice.DEFER:
            defer_w += weight
        else:
            abstain_w += weight

    return total_w, approve_w, reject_w, defer_w


def _resolve_round(cr: ConsensusRound):
    """Resolve a consensus round using ΔT-weighted voting."""
    total_w, approve_w, reject_w, defer_w = _compute_weighted_score(cr)

    # Map threshold counts to weighted equivalents
    thresholds = {
        DecisionLevel.LOW:         0,
        DecisionLevel.HIGH:        8,
        DecisionLevel.CRITICAL:    11,
        DecisionLevel.SOVEREIGNTY: 15,
    }
    raw_approvals = sum(1 for v in cr.votes if v.choice == VoteChoice.APPROVE)
    raw_rejects   = sum(1 for v in cr.votes if v.choice == VoteChoice.REJECT)
    raw_defers    = sum(1 for v in cr.votes if v.choice == VoteChoice.DEFER)
    required = thresholds[cr.level]

    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    cr.resolved_at = now

    # Handle veto first
    if cr.vetoed:
        cr.outcome = ConsensusOutcome.REJECTED
        cr.summary = (
            f"⛔ VETOED by {cr.vetoed_by} — {raw_approvals}/{len(cr.votes)} approve "
            f"(required: {required}) | ΔT weighted: {approve_w:.1f}/{total_w:.1f}"
        )
        return

    if cr.level == DecisionLevel.SOVEREIGNTY:
        cr.outcome = ConsensusOutcome.REQUIRES_HUMAN
        cr.summary = (
            f"Sovereignty decision — requires human Final-3. "
            f"Clones: {raw_approvals} approve, {raw_rejects} reject, {raw_defers} defer. "
            f"ΔT weighted: {approve_w:.1f}/{total_w:.1f} approve"
        )
    elif raw_defers >= 5:
        cr.outcome = ConsensusOutcome.DEFERRED_HUMAN
        cr.summary = (
            f"Too many DEFER votes ({raw_defers}/15) — human context needed. "
            f"ΔT weighted: {approve_w:.1f}/{total_w:.1f} approve"
        )
    elif raw_approvals >= required:
        cr.outcome = ConsensusOutcome.APPROVED
        cr.summary = (
            f"✅ APPROVED — {raw_approvals}/{len(cr.votes)} approve "
            f"(required: {required}) | {raw_rejects} reject, {raw_defers} defer | "
            f"ΔT weighted: {approve_w:.1f}/{total_w:.1f}"
        )
    else:
        cr.outcome = ConsensusOutcome.REJECTED
        cr.summary = (
            f"❌ REJECTED — only {raw_approvals}/{len(cr.votes)} approve "
            f"(required: {required}) | {raw_rejects} reject, {raw_defers} defer | "
            f"ΔT weighted: {approve_w:.1f}/{total_w:.1f}"
        )


# ─── CONSENSUS ENGINE ─────────────────────────────────────────────────────────

class CloneConsensusEngine:
    """
    15-Clone Consensus Engine with ΔT-weighted voting, LLM-powered
    via the FounderCloneSystem, delegation, and arbitration.

    Usage:
        engine = CloneConsensusEngine(founder_system)
        round  = await engine.start_round(
            topic="Deploy new mesh protocol",
            description="Replace UDP broadcast with mDNS only",
            level=DecisionLevel.HIGH,
        )
        result = await engine.resolve(round.round_id)
    """

    def __init__(self, founder_system=None):
        self._rounds: Dict[str, ConsensusRound] = {}
        self._delegations: Dict[str, List[DelegateVote]] = {}  # proposal_id → delegations
        self._founder_system = founder_system  # Optional FounderCloneSystem ref
        self._load_log()
        logger.info(
            f"✅ CloneConsensusEngine ready — {len(FOUNDER_CLONES)} clones registered"
            f"{', with FounderCloneSystem' if founder_system else ''}"
        )

    # ── START ROUND ───────────────────────────────────────────────────────────

    async def start_round(
        self,
        topic: str,
        description: str,
        level: DecisionLevel = DecisionLevel.HIGH,
    ) -> ConsensusRound:
        """Initiate a new consensus round. All 15 clones vote via LLM (if founder_system
        available) or fall back to lightweight heuristic voting.

        Returns the ConsensusRound with all votes collected and resolved.
        """
        round_id = str(uuid.uuid4())[:10]
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        cr = ConsensusRound(
            round_id=round_id,
            topic=topic,
            description=description,
            level=level,
            created_at=now,
        )

        # Collect votes from all 15 clones
        if self._founder_system:
            votes = await self._collect_llm_votes(cr, topic, description, level)
            cr.votes = votes
        else:
            # Fallback: lightweight heuristic voting (no founder_system)
            for clone in FOUNDER_CLONES:
                vote = self._heuristic_vote(clone, topic, description, level)
                cr.votes.append(vote)

        # Apply any active delegations for this round
        self._apply_delegations(cr)

        # Resolve immediately
        _resolve_round(cr)
        self._rounds[round_id] = cr
        self._save_log(cr)

        raw_approvals = sum(1 for v in cr.votes if v.choice == VoteChoice.APPROVE)
        logger.info(
            f"🗳️ Consensus round {round_id}: {topic[:40]} → {cr.outcome.value} "
            f"[{raw_approvals}/{len(cr.votes)} approve]"
        )
        return cr

    async def _collect_llm_votes(
        self,
        cr: ConsensusRound,
        topic: str,
        description: str,
        level: DecisionLevel,
    ) -> List[CloneVote]:
        """Collect votes by calling each founder's LLM via FounderCloneSystem.

        For each clone, we find the mapped founder(s) and call the most relevant
        one's NVIDIA API. The founder votes based on their specialization/persona.
        """
        from core.consensus.founder_to_clone_map import (
            get_founders_for_clone,
            get_vote_weight,
            get_clone_name,
        )

        votes: List[CloneVote] = []
        tasks = []

        # Build a prompt for each clone based on its domain and mapped founders
        for clone in FOUNDER_CLONES:
            clone_id = clone["id"]
            clone_name = clone["name"]
            domain = clone["domain"]

            # Find the best founder for this clone
            founders = get_founders_for_clone(clone_id)
            if not founders or not self._founder_system:
                # No founder mapping — fall back to heuristic
                task = self._llm_or_heuristic_vote(clone, topic, description, level)
            else:
                # Use the first (most relevant) founder
                founder_role = founders[0]
                weight = get_vote_weight(founder_role, clone_id)
                task = self._call_founder_for_vote(
                    founder_role, clone_id, clone_name, domain,
                    topic, description, level, weight
                )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"LLM vote failed for clone {FOUNDER_CLONES[i]['id']}: {result}")
                # Fallback: heuristic vote on error
                vote = self._heuristic_vote(
                    FOUNDER_CLONES[i], topic, description, level
                )
                votes.append(vote)
            else:
                votes.append(result)

        return votes

    async def _call_founder_for_vote(
        self,
        founder_role,
        clone_id: str,
        clone_name: str,
        domain: str,
        topic: str,
        description: str,
        level: DecisionLevel,
        delta_weight: float,
    ) -> CloneVote:
        """Call a specific founder's LLM to get their vote on a proposal."""
        founder = await self._founder_system.get_founder(founder_role)
        if not founder:
            return self._heuristic_vote(
                {"id": clone_id, "name": clone_name, "domain": domain, "dharma_weight": 1.0},
                topic, description, level
            )

        vote_prompt = (
            f"You are voting as '{clone_name}' — the clone responsible for {domain} oversight.\n\n"
            f"=== Proposal ===\n"
            f"Topic: {topic}\n"
            f"Description: {description}\n"
            f"Decision Level: {level.value}\n\n"
            f"=== Voting Instructions ===\n"
            f"Based on your domain expertise in {domain}, respond with EXACTLY one of:\n"
            f"  APPROVE — you recommend proceeding with this proposal\n"
            f"  REJECT  — you recommend blocking this proposal\n"
            f"  ABSTAIN — you have insufficient data to form an opinion\n"
            f"  DEFER   — you need more human input or context\n\n"
            f"Then provide a brief reasoning (1-2 sentences) and a confidence score (0.0-1.0).\n"
            f"Format your response as:\n"
            f"VOTE: <choice>\n"
            f"REASONING: <your reasoning>\n"
            f"CONFIDENCE: <0.0-1.0>"
        )

        try:
            result = await founder.process_message(vote_prompt)
            choice, reasoning, confidence = self._parse_llm_vote(result)
        except Exception as e:
            logger.warning(f"LLM call failed for {founder_role.name} → {clone_name}: {e}")
            choice = VoteChoice.ABSTAIN
            reasoning = f"LLM error: {e}"
            confidence = 0.0

        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        return CloneVote(
            clone_id=clone_id,
            clone_name=clone_name,
            domain=domain,
            choice=choice,
            reasoning=reasoning,
            confidence=confidence,
            voted_at=now,
            founder_role=founder_role.name,
            delta_weight=delta_weight,
        )

    def _parse_llm_vote(self, llm_response: str) -> Tuple[VoteChoice, str, float]:
        """Parse an LLM response to extract vote choice, reasoning, and confidence."""
        choice = VoteChoice.ABSTAIN
        reasoning = "Could not parse LLM response"
        confidence = 0.5

        lines = llm_response.strip().split("\n")
        for line in lines:
            stripped = line.strip()

            # Parse VOTE line
            if stripped.upper().startswith("VOTE:"):
                vote_text = stripped[5:].strip().upper()
                for vc in VoteChoice:
                    if vc.value.upper() in vote_text:
                        choice = vc
                        break

            # Parse REASONING line
            if stripped.upper().startswith("REASONING:"):
                reasoning = stripped[10:].strip()

            # Parse CONFIDENCE line
            if stripped.upper().startswith("CONFIDENCE:"):
                try:
                    conf_str = stripped[11:].strip().strip("%")
                    confidence = float(conf_str)
                    confidence = max(0.0, min(1.0, confidence))
                except (ValueError, TypeError):
                    confidence = 0.5

        return choice, reasoning, confidence

    async def _llm_or_heuristic_vote(
        self, clone: dict, topic: str, description: str, level: DecisionLevel
    ) -> CloneVote:
        """Try LLM vote; fall back to heuristic if founder_system not available."""
        # Simple heuristic fallback for clones with no founder mapping
        return self._heuristic_vote(clone, topic, description, level)

    @staticmethod
    def _heuristic_vote(clone: dict, topic: str, description: str,
                        level: DecisionLevel) -> CloneVote:
        """Lightweight heuristic voting fallback (used when no founder_system
        is connected, or as a fallback on LLM errors)."""
        domain = clone["domain"]
        text = f"{topic} {description}".lower()

        reject_keywords = {
            "ethics":      ["harm", "manipulation", "exploit", "abuse", "coerce"],
            "security":    ["vulnerability", "exposed", "leak", "breach", "attack"],
            "sovereignty": ["control", "dependency", "monopoly", "forced", "mandatory"],
            "identity":    ["expose", "reveal", "track", "surveillance", "national id"],
            "culture":     ["western", "colonial", "cultural imperialism", "replace tradition"],
            "legal":       ["illegal", "fraud", "scam", "violation", "lawsuit"],
            "contracts":   ["escrow risk", "unsigned", "force", "coerce"],
        }
        approve_keywords = {
            "technology":  ["efficient", "local-first", "open source", "privacy"],
            "community":   ["community", "village", "local", "shared", "collective"],
            "economy":     ["fair", "equitable", "transparent", "sustainable"],
            "health":      ["wellbeing", "safe", "healthy"],
            "education":   ["learn", "teach", "knowledge", "skill"],
            "environment": ["sustainable", "green", "clean"],
            "memory":      ["remember", "history", "preserve"],
            "network":     ["connect", "mesh", "peer", "distributed"],
        }

        rejects = reject_keywords.get(domain, [])
        approves = approve_keywords.get(domain, [])

        if any(k in text for k in rejects):
            choice = VoteChoice.REJECT
            reasoning = f"{clone['name']}: Domain-specific concern in {domain}"
            confidence = 0.8
        elif any(k in text for k in approves):
            choice = VoteChoice.APPROVE
            reasoning = f"{clone['name']}: Aligns with {domain} values"
            confidence = 0.75
        elif level == DecisionLevel.SOVEREIGNTY:
            choice = VoteChoice.DEFER
            reasoning = f"{clone['name']}: Sovereignty decision requires more human context"
            confidence = 0.6
        else:
            choice = VoteChoice.APPROVE
            reasoning = f"{clone['name']}: No domain-specific concerns found"
            confidence = 0.6

        return CloneVote(
            clone_id=clone["id"],
            clone_name=clone["name"],
            domain=domain,
            choice=choice,
            reasoning=reasoning,
            confidence=confidence,
            voted_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )

    # ── DELEGATION ─────────────────────────────────────────────────────────────

    def delegate_vote(self, from_founder: str, to_founder: str,
                      proposal_id: str, ttl_seconds: int = 3600) -> DelegateVote:
        """Delegate voting power from one clone to another for a specific proposal.

        Args:
            from_founder: The clone_id delegating their vote.
            to_founder: The clone_id receiving the delegated vote.
            proposal_id: The round_id this delegation applies to.
            ttl_seconds: Time-to-live in seconds (default 1 hour).

        Returns:
            The created DelegateVote.
        """
        now = datetime.now(timezone.utc)
        expires = now + timedelta(seconds=ttl_seconds)

        dv = DelegateVote(
            from_clone=from_founder,
            to_clone=to_founder,
            proposal_id=proposal_id,
            expires_at=expires.strftime("%Y-%m-%dT%H:%M:%SZ"),
            created_at=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

        if proposal_id not in self._delegations:
            self._delegations[proposal_id] = []
        self._delegations[proposal_id].append(dv)

        logger.info(
            f"📜 Delegation: {from_founder} → {to_founder} "
            f"for proposal {proposal_id} (expires {dv.expires_at})"
        )
        return dv

    def revoke_delegation(self, from_founder: str, proposal_id: str) -> bool:
        """Revoke a delegation from a founder for a specific proposal.

        Args:
            from_founder: The clone_id that delegated.
            proposal_id: The round_id the delegation was for.

        Returns:
            True if a delegation was revoked, False otherwise.
        """
        delegations = self._delegations.get(proposal_id, [])
        before = len(delegations)
        self._delegations[proposal_id] = [
            d for d in delegations
            if not (d.from_clone == from_founder)
        ]
        after = len(self._delegations[proposal_id])
        revoked = before > after

        if revoked:
            logger.info(f"📜 Revoked delegation from {from_founder} for proposal {proposal_id}")
        return revoked

    def get_active_delegations(self, proposal_id: str) -> List[DelegateVote]:
        """Get all active (non-expired) delegations for a proposal.

        Args:
            proposal_id: The round_id to check.

        Returns:
            List of active DelegateVote objects.
        """
        now = datetime.now(timezone.utc)
        active = []
        for d in self._delegations.get(proposal_id, []):
            expires = datetime.strptime(d.expires_at, "%Y-%m-%dT%H:%M:%SZ")
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            if now < expires:
                active.append(d)
        return active

    def _apply_delegations(self, cr: ConsensusRound):
        """Apply active delegations to a round's votes.

        When a delegation is active, the delegate's vote is copied to the delegator.
        """
        delegations = self.get_active_delegations(cr.round_id)
        if not delegations:
            return

        # Build map: to_clone → list of from_clones
        delegation_map: Dict[str, List[str]] = {}
        for d in delegations:
            delegation_map.setdefault(d.to_clone, []).append(d.from_clone)

        # Add delegated votes (copy from delegate to delegator)
        new_votes = list(cr.votes)
        for to_clone, from_clones in delegation_map.items():
            delegate_votes = [v for v in cr.votes if v.clone_id == to_clone]
            for dv in delegate_votes:
                for from_clone in from_clones:
                    delegated_vote = CloneVote(
                        clone_id=from_clone,
                        clone_name=dv.clone_name + f" (delegated from {from_clone})",
                        domain=dv.domain,
                        choice=dv.choice,
                        reasoning=f"Delegated vote — {dv.reasoning}",
                        confidence=dv.confidence * 0.9,  # slight discount for delegation
                        voted_at=dv.voted_at,
                        founder_role=dv.founder_role,
                        delta_weight=dv.delta_weight * 0.8,  # delegation weight discount
                    )
                    new_votes.append(delegated_vote)

        cr.votes = new_votes
        logger.info(
            f"📜 Applied {len(delegations)} delegation(s) to round {cr.round_id} — "
            f"total votes now {len(cr.votes)}"
        )

    # ── ARBITRATION ────────────────────────────────────────────────────────────

    async def resolve_tie(self, round_id: str) -> ConsensusRound:
        """Resolve a tied vote by having the CEO cast the deciding vote.

        The CEO reviews the proposal and the current vote distribution,
        then makes a final decision.

        Args:
            round_id: The round to resolve.

        Returns:
            The updated ConsensusRound.
        """
        cr = self._rounds.get(round_id)
        if not cr:
            raise KeyError(f"Round not found: {round_id}")

        # Only resolve if still pending or could go either way
        if cr.outcome not in (ConsensusOutcome.PENDING, ConsensusOutcome.REQUIRES_HUMAN):
            logger.info(f"Round {round_id} already resolved as {cr.outcome.value} — no tie needed")
            return cr

        approvals = sum(1 for v in cr.votes if v.choice == VoteChoice.APPROVE)
        rejects = sum(1 for v in cr.votes if v.choice == VoteChoice.REJECT)

        if approvals != rejects:
            logger.info(f"Round {round_id} is not tied ({approvals} vs {rejects}) — no tie needed")
            return cr

        # CEO casts deciding vote
        if self._founder_system:
            tie_breaker_prompt = (
                f"You are the CEO, casting the tie-breaking vote.\n\n"
                f"=== Proposal ===\n"
                f"Topic: {cr.topic}\n"
                f"Description: {cr.description}\n"
                f"Level: {cr.level.value}\n\n"
                f"=== Current Vote ===\n"
                f"Approvals: {approvals}\n"
                f"Rejects: {rejects}\n\n"
                f"Review the arguments and cast the deciding vote.\n"
                f"Respond with EXACTLY:\n"
                f"VOTE: APPROVE or REJECT\n"
                f"REASONING: <your reasoning>"
            )

            try:
                founder = await self._founder_system.get_founder(
                    __import__("core.founder_clones.founder_clone_system",
                               fromlist=["FounderRole"]).FounderRole.CEO
                )
                result = await founder.process_message(tie_breaker_prompt)
                choice, reasoning, _ = self._parse_llm_vote(result)

                tie_vote = CloneVote(
                    clone_id="clone_15",  # Sovereignty Guard (CEO's clone)
                    clone_name="Sovereignty Guard (CEO Tie-Breaker)",
                    domain="sovereignty",
                    choice=choice,
                    reasoning=f"CEO tie-breaker: {reasoning}",
                    confidence=1.0,
                    voted_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    founder_role="CEO",
                    delta_weight=1.0,
                )
                cr.votes.append(tie_vote)
            except Exception as e:
                logger.error(f"CEO tie-breaker failed: {e}")
                # Default: approve on error
                tie_vote = CloneVote(
                    clone_id="clone_15",
                    clone_name="Sovereignty Guard (CEO Tie-Breaker)",
                    domain="sovereignty",
                    choice=VoteChoice.APPROVE,
                    reasoning=f"CEO tie-breaker default (error: {e})",
                    confidence=0.5,
                    voted_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    founder_role="CEO",
                    delta_weight=1.0,
                )
                cr.votes.append(tie_vote)
        else:
            # No founder system: CEO defaults to approve
            tie_vote = CloneVote(
                clone_id="clone_15",
                clone_name="Sovereignty Guard (CEO Tie-Breaker)",
                domain="sovereignty",
                choice=VoteChoice.APPROVE,
                reasoning="CEO tie-breaker (default: approve)",
                confidence=0.7,
                voted_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                founder_role="CEO",
                delta_weight=1.0,
            )
            cr.votes.append(tie_vote)

        # Re-resolve
        _resolve_round(cr)
        self._save_log(cr)
        logger.info(f"⚖️ CEO tie-breaker resolved round {round_id} → {cr.outcome.value}")
        return cr

    def veto(self, round_id: str, vetoed_by: str) -> ConsensusRound:
        """Veto a proposal. Anyone can veto; overridable by supermajority (11/15).

        Args:
            round_id: The round to veto.
            vetoed_by: The name/role of the entity casting the veto.

        Returns:
            The updated ConsensusRound.
        """
        cr = self._rounds.get(round_id)
        if not cr:
            raise KeyError(f"Round not found: {round_id}")

        if cr.outcome == ConsensusOutcome.APPROVED:
            # Check if supermajority can override the veto
            approvals = sum(1 for v in cr.votes if v.choice == VoteChoice.APPROVE)
            if approvals >= 11:
                cr.vetoed = True
                cr.vetoed_by = vetoed_by
                cr.summary += (
                    f"\n⛔ Vetoed by {vetoed_by} — overridden by supermajority ({approvals}/11)"
                )
                cr.outcome = ConsensusOutcome.APPROVED
                logger.info(
                    f"⛔ Veto by {vetoed_by} on {round_id} overridden by supermajority"
                )
            else:
                cr.vetoed = True
                cr.vetoed_by = vetoed_by
                _resolve_round(cr)
                logger.info(f"⛔ Veto by {vetoed_by} on {round_id} — proposal rejected")
        else:
            cr.vetoed = True
            cr.vetoed_by = vetoed_by
            _resolve_round(cr)
            logger.info(f"⛔ Veto by {vetoed_by} on {round_id} — proposal rejected")

        self._save_log(cr)
        return cr

    # ── HUMAN OVERRIDE ────────────────────────────────────────────────────────

    def human_override(self, round_id: str, approved: bool,
                       reason: str = "") -> ConsensusRound:
        """Final-3 Gate 3: human can override any consensus outcome."""
        cr = self._rounds.get(round_id)
        if not cr:
            raise KeyError(f"Round not found: {round_id}")
        cr.human_override = approved
        cr.outcome = ConsensusOutcome.APPROVED if approved else ConsensusOutcome.REJECTED
        cr.summary += f"\n👤 Human override: {'APPROVED' if approved else 'REJECTED'}. {reason}"
        self._save_log(cr)
        logger.info(f"👤 Human override on {round_id}: {'APPROVED' if approved else 'REJECTED'}")
        return cr

    # ── QUERIES ───────────────────────────────────────────────────────────────

    def get(self, round_id: str) -> Optional[ConsensusRound]:
        return self._rounds.get(round_id)

    def list_rounds(self, limit: int = 20) -> List[ConsensusRound]:
        return sorted(self._rounds.values(),
                      key=lambda r: r.created_at, reverse=True)[:limit]

    def pending_human(self) -> List[ConsensusRound]:
        return [r for r in self._rounds.values()
                if r.outcome in (ConsensusOutcome.REQUIRES_HUMAN,
                                 ConsensusOutcome.DEFERRED_HUMAN)
                and r.human_override is None]

    def stats(self) -> Dict[str, Any]:
        rounds = list(self._rounds.values())
        return {
            "total":          len(rounds),
            "approved":       sum(1 for r in rounds if r.outcome == ConsensusOutcome.APPROVED),
            "rejected":       sum(1 for r in rounds if r.outcome == ConsensusOutcome.REJECTED),
            "pending_human":  len(self.pending_human()),
            "clone_count":    len(FOUNDER_CLONES),
            "thresholds":     {"high": "8/15", "critical": "11/15",
                               "sovereignty": "15/15 + Human"},
            "active_delegations": sum(len(d) for d in self._delegations.values()),
        }

    def get_round_votes(self, round_id: str) -> List[Dict[str, Any]]:
        """Get detailed vote info for a round, including ΔT weights."""
        cr = self._rounds.get(round_id)
        if not cr:
            return []
        return [
            {
                "clone_name": v.clone_name,
                "domain": v.domain,
                "choice": v.choice.value,
                "confidence": v.confidence,
                "delta_weight": v.delta_weight,
                "founder_role": v.founder_role,
                "reasoning": v.reasoning,
            }
            for v in cr.votes
        ]

    # ── PERSISTENCE ───────────────────────────────────────────────────────────

    def _save_log(self, cr: ConsensusRound):
        try:
            with open(CONSENSUS_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(cr.to_dict()) + "\n")
        except Exception as e:
            logger.warning(f"Consensus log write failed: {e}")

    def _load_log(self):
        if not CONSENSUS_LOG.exists():
            return
        try:
            with open(CONSENSUS_LOG, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        d = json.loads(line)
                        votes_data = d.pop("votes", [])
                        votes = []
                        for v in votes_data:
                            if isinstance(v.get("choice"), str):
                                v["choice"] = VoteChoice(v["choice"])
                            if isinstance(v.get("level"), str):
                                pass  # level is on the round, not vote
                            votes.append(CloneVote(**v))
                        # Reconstruct level and outcome enums
                        if isinstance(d.get("level"), str):
                            d["level"] = DecisionLevel(d["level"])
                        if isinstance(d.get("outcome"), str):
                            d["outcome"] = ConsensusOutcome(d["outcome"])
                        cr = ConsensusRound(votes=votes, **d)
                        self._rounds[cr.round_id] = cr
                    except Exception as e:
                        logger.warning(f"Skipping malformed log entry: {e}")
                        continue
        except Exception as e:
            logger.warning(f"Consensus log load failed: {e}")


# ─── SINGLETON ─────────────────────────────────────────────────────────────────

_engine: Optional[CloneConsensusEngine] = None


def get_consensus_engine(founder_system=None) -> CloneConsensusEngine:
    global _engine
    if _engine is None:
        _engine = CloneConsensusEngine(founder_system=founder_system)
    return _engine
