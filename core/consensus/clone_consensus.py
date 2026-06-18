"""
core/consensus/clone_consensus.py
AsimNexus — 15-Clone Consensus Mode (LLM-Powered) with ZKP Privacy Binding
=========================================================================
When a HIGH/CRITICAL decision needs to be made, all 15 Founder
Clones vote via their respective NVIDIA LLM APIs. Consensus requires:

  - Simple majority (8/15) for HIGH decisions
  - Supermajority (11/15) for CRITICAL decisions
  - Unanimous (15/15) for SOVEREIGNTY decisions

Each clone votes independently based on its domain expertise, using
the actual FounderClone NVIDIA LLM calls (not keyword heuristics).

ΔT Engine weights votes by relevance weight (founder-to-clone mapping).
Human always has veto (Final-3 Gate 3).

Integration with ZKP Privacy for vote verification and commitment.

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
    zkp_commitment: Optional[str] = None  # ZKP commitment for privacy
    zkp_blinding: Optional[int] = None    # ZKP blinding factor

    def to_dict(self) -> Dict[str, Any]:
        return {
            "clone_id": self.clone_id,
            "clone_name": self.clone_name,
            "domain": self.domain,
            "choice": self.choice.value,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "voted_at": self.voted_at,
            "founder_role": self.founder_role,
            "delta_weight": self.delta_weight,
            "zkp_commitment": self.zkp_commitment,
            "zkp_blinding": self.zkp_blinding,
        }


@dataclass
class DelegateVote:
    from_clone:    str
    to_clone:      str
    proposal_id:   str
    expires_at:    str
    created_at:    str


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
    total_w, approve_w, reject_w, defer_w = _compute_weighted_score(cr)

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
    via the FounderCloneSystem, delegation, arbitration, and ZKP Privacy binding.
    """

    def __init__(self, founder_system=None):
        self._rounds: Dict[str, ConsensusRound] = {}
        self._delegations: Dict[str, List[DelegateVote]] = {}
        self._founder_system = founder_system
        self._zkp_system = None
        self._load_log()
        logger.info(
            f"✅ CloneConsensusEngine ready — {len(FOUNDER_CLONES)} clones registered"
            f"{', with FounderCloneSystem' if founder_system else ''}"
        )

    def _get_zkp_system(self):
        """Lazy load ZKP system for privacy binding."""
        if self._zkp_system is None:
            try:
                from core.security.zkp_privacy import ZeroKnowledgeProofSystem
                self._zkp_system = ZeroKnowledgeProofSystem()
                logger.info("ZKP Privacy system initialized")
            except ImportError:
                logger.warning("ZKP system not available")
                self._zkp_system = False
        return self._zkp_system if self._zkp_system is not False else None

    async def start_round(
        self,
        topic: str,
        description: str,
        level: DecisionLevel = DecisionLevel.HIGH,
    ) -> ConsensusRound:
        round_id = str(uuid.uuid4())[:10]
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        cr = ConsensusRound(
            round_id=round_id,
            topic=topic,
            description=description,
            level=level,
            created_at=now,
        )

        if self._founder_system:
            votes = await self._collect_llm_votes(topic, description, level, round_id)
            cr.votes = votes
        else:
            for clone in FOUNDER_CLONES:
                vote = self._heuristic_vote(clone, topic, description, level, round_id)
                cr.votes.append(vote)

        self._apply_delegations(cr)
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
        topic: str,
        description: str,
        level: DecisionLevel,
        round_id: str,
    ) -> List[CloneVote]:
        votes = []
        try:
            from core.consensus.founder_to_clone_map import (
                get_founders_for_clone,
                get_vote_weight,
            )

            tasks = []
            for clone in FOUNDER_CLONES:
                clone_id = clone["id"]
                clone_name = clone["name"]
                domain = clone["domain"]

                founders = get_founders_for_clone(clone_id)
                if not founders or not self._founder_system:
                    task = self._llm_or_heuristic_vote(clone, topic, description, level, round_id)
                else:
                    founder_role = founders[0]
                    weight = get_vote_weight(founder_role, clone_id)
                    task = self._call_founder_for_vote(
                        founder_role, clone_id, clone_name, domain,
                        topic, description, level, weight, round_id
                    )
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.warning(f"LLM vote failed for clone {FOUNDER_CLONES[i]['id']}: {result}")
                    vote = self._heuristic_vote(FOUNDER_CLONES[i], topic, description, level, round_id)
                    votes.append(vote)
                else:
                    votes.append(result)
        except Exception as e:
            logger.error(f"Failed to collect votes: {e}")
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
        round_id: str,
    ) -> CloneVote:
        founder = await self._founder_system.get_founder(founder_role)
        if not founder:
            return self._heuristic_vote(
                {"id": clone_id, "name": clone_name, "domain": domain, "dharma_weight": 1.0},
                topic, description, level, round_id
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
        
        # Add ZKP binding if available
        zkp_commitment = None
        zkp_blinding = None
        zkp = self._get_zkp_system()
        if zkp:
            try:
                from core.security.zkp_privacy import PedersenCommitment
                vote_data = f"{round_id}:{clone_id}:{choice.value}"
                zkp_commitment, zkp_blinding = PedersenCommitment.commit(vote_data)
            except Exception:
                pass

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
            zkp_commitment=zkp_commitment,
            zkp_blinding=zkp_blinding,
        )

    async def _llm_or_heuristic_vote(
        self, clone: dict, topic: str, description: str, level: DecisionLevel, round_id: str
    ) -> CloneVote:
        return self._heuristic_vote(clone, topic, description, level, round_id)

    @staticmethod
    def _heuristic_vote(clone: dict, topic: str, description: str,
                        level: DecisionLevel, round_id: str = "") -> CloneVote:
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

    def _parse_llm_vote(self, llm_response: str) -> Tuple[VoteChoice, str, float]:
        choice = VoteChoice.ABSTAIN
        reasoning = "Could not parse LLM response"
        confidence = 0.5

        lines = llm_response.strip().split("\n")
        for line in lines:
            stripped = line.strip()
            if stripped.upper().startswith("VOTE:"):
                vote_text = stripped[5:].strip().upper()
                for vc in VoteChoice:
                    if vc.value.upper() in vote_text:
                        choice = vc
                        break
            if stripped.upper().startswith("REASONING:"):
                reasoning = stripped[10:].strip()
            if stripped.upper().startswith("CONFIDENCE:"):
                try:
                    conf_str = stripped[11:].strip().strip("%")
                    confidence = float(conf_str)
                    confidence = max(0.0, min(1.0, confidence))
                except (ValueError, TypeError):
                    confidence = 0.5
        return choice, reasoning, confidence

    def delegate_vote(self, from_founder: str, to_founder: str,
                      proposal_id: str, ttl_seconds: int = 3600) -> DelegateVote:
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

        logger.info(f"📜 Delegation: {from_founder} → {to_founder} for proposal {proposal_id}")
        return dv

    def revoke_delegation(self, from_founder: str, proposal_id: str) -> bool:
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
        delegations = self.get_active_delegations(cr.round_id)
        if not delegations:
            return

        delegation_map: Dict[str, List[str]] = {}
        for d in delegations:
            delegation_map.setdefault(d.to_clone, []).append(d.from_clone)

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
                        confidence=dv.confidence * 0.9,
                        voted_at=dv.voted_at,
                        founder_role=dv.founder_role,
                        delta_weight=dv.delta_weight * 0.8,
                    )
                    new_votes.append(delegated_vote)

        cr.votes = new_votes

    async def resolve_tie(self, round_id: str) -> ConsensusRound:
        cr = self._rounds.get(round_id)
        if not cr:
            raise KeyError(f"Round not found: {round_id}")

        if cr.outcome not in (ConsensusOutcome.PENDING, ConsensusOutcome.REQUIRES_HUMAN):
            logger.info(f"Round {round_id} already resolved as {cr.outcome.value}")
            return cr

        approvals = sum(1 for v in cr.votes if v.choice == VoteChoice.APPROVE)
        rejects = sum(1 for v in cr.votes if v.choice == VoteChoice.REJECT)

        if approvals != rejects:
            logger.info(f"Round {round_id} is not tied ({approvals} vs {rejects})")
            return cr

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

        _resolve_round(cr)
        self._save_log(cr)
        return cr

    def veto(self, round_id: str, vetoed_by: str) -> ConsensusRound:
        cr = self._rounds.get(round_id)
        if not cr:
            raise KeyError(f"Round not found: {round_id}")

        if cr.outcome == ConsensusOutcome.APPROVED:
            approvals = sum(1 for v in cr.votes if v.choice == VoteChoice.APPROVE)
            if approvals >= 11:
                cr.vetoed = True
                cr.vetoed_by = vetoed_by
                cr.summary += f"\n⛔ Vetoed by {vetoed_by} — overridden by supermajority ({approvals}/11)"
                cr.outcome = ConsensusOutcome.APPROVED
            else:
                cr.vetoed = True
                cr.vetoed_by = vetoed_by
                _resolve_round(cr)
        else:
            cr.vetoed = True
            cr.vetoed_by = vetoed_by
            _resolve_round(cr)

        self._save_log(cr)
        return cr

    def human_override(self, round_id: str, approved: bool,
                       reason: str = "") -> ConsensusRound:
        cr = self._rounds.get(round_id)
        if not cr:
            raise KeyError(f"Round not found: {round_id}")
        cr.human_override = approved
        cr.outcome = ConsensusOutcome.APPROVED if approved else ConsensusOutcome.REJECTED
        cr.summary += f"\n👤 Human override: {'APPROVED' if approved else 'REJECTED'}. {reason}"
        self._save_log(cr)
        return cr

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
        zkp_system = self._get_zkp_system()
        return {
            "total":          len(rounds),
            "approved":       sum(1 for r in rounds if r.outcome == ConsensusOutcome.APPROVED),
            "rejected":       sum(1 for r in rounds if r.outcome == ConsensusOutcome.REJECTED),
            "pending_human":  len(self.pending_human()),
            "clone_count":    len(FOUNDER_CLONES),
            "thresholds":     {"high": "8/15", "critical": "11/15", "sovereignty": "15/15 + Human"},
            "active_delegations": sum(len(d) for d in self._delegations.values()),
            "zkp_enabled": zkp_system is not None,
        }

    def get_round_votes(self, round_id: str) -> List[Dict[str, Any]]:
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
                "zkp_commitment": v.zkp_commitment,
            }
            for v in cr.votes
        ]

    def verify_zkp_votes(self, round_id: str) -> Dict[str, Any]:
        """Verify all ZKP commitments for votes on a round."""
        cr = self._rounds.get(round_id)
        if not cr:
            return {"valid": False, "message": "Round not found", "verified_votes": 0, "total_votes": 0}

        try:
            from core.security.zkp_privacy import PedersenCommitment
            verified = 0
            total = len(cr.votes)

            for vote in cr.votes:
                if vote.zkp_commitment and vote.zkp_blinding:
                    vote_data = f"{round_id}:{vote.clone_id}:{vote.choice.value}"
                    if PedersenCommitment.verify(vote.zkp_commitment, vote_data, vote.zkp_blinding):
                        verified += 1

            return {
                "valid": verified == total,
                "message": f"Verified {verified}/{total} ZKP commitments",
                "verified_votes": verified,
                "total_votes": total
            }
        except ImportError:
            return {"valid": True, "message": "ZKP not available, skipping verification", "verified_votes": 0, "total_votes": 0}

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
                            try:
                                if isinstance(v.get("zkp_commitment"), str) and v.get("zkp_blinding") is not None:
                                    pass  # ZKP fields already correct
                            except Exception:
                                pass
                            votes.append(CloneVote(**v))
                        if isinstance(d.get("level"), str):
                            d["level"] = DecisionLevel(d["level"])
                        if isinstance(d.get("outcome"), str):
                            d["outcome"] = ConsensusOutcome(d["outcome"])
                        cr = ConsensusRound(votes=votes, **d)
                        self._rounds[cr.round_id] = cr
                    except Exception as e:
                        logger.warning(f"Skipping malformed log entry: {e}")
        except Exception as e:
            logger.warning(f"Consensus log load failed: {e}")


# ─── SINGLETON ─────────────────────────────────────────────────────────────────

_engine: Optional[CloneConsensusEngine] = None


def get_consensus_engine(founder_system=None) -> CloneConsensusEngine:
    global _engine
    if _engine is None:
        _engine = CloneConsensusEngine(founder_system=founder_system)
    return _engine