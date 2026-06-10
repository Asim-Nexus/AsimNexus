#!/usr/bin/env python3
"""
STATUS: NEW — Phase 9 Vote Layer
ASIMNEXUS Power Balance Constitution — Vote Layer
===================================================
Provides a vote-based constitutional governance system with sector
representation, weighted voting, veto powers, and audit trails.

This module complements [`security/power_balance_constitution.py`]
(../../security/power_balance_constitution.py) which handles the 51/49
balance enforcement. This module provides the HIGHER-LEVEL voting and
governance mechanics.

Key concepts:
  - 4 sectors (Government 51%, Private 49%) split into sub-sectors
  - Weighted voting proportional to allocation
  - Government/Private sector veto powers
  - Founder (clone_01) emergency veto (overridable by 75%)
  - Constitutional amendments require BOTH sides passing
  - Emergency powers require 66% government supermajority
  - All votes audit-logged to JSONL
"""

import json
import logging
import os
import threading
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger("AsimNexus.Constitution.Vote")

# ─── Environment Configuration ────────────────────────────────────────────────
_VOTE_DB_PATH = os.getenv("ASIM_CONSTITUTION_VOTE_DB_PATH",
                          "data/constitution_votes.jsonl")


# ─── Sector Definitions ────────────────────────────────────────────────────────

# Government sectors (51% total)
GOVERNMENT_SECTORS: Dict[str, float] = {
    "executive":  0.20,  # 20% of total vote
    "judicial":   0.15,  # 15%
    "legislative": 0.10, # 10%
    "military":   0.06,  # 6%
}

# Private sectors (49% total)
PRIVATE_SECTORS: Dict[str, float] = {
    "corporate":  0.20,  # 20% of total vote
    "startup":    0.10,  # 10%
    "public":     0.10,  # 10%
    "non_profit": 0.09,  # 9%
}

TOTAL_WEIGHT = sum(GOVERNMENT_SECTORS.values()) + sum(PRIVATE_SECTORS.values())  # 1.0


def get_sector_group(sector: str) -> str:
    """Determine if a sector is 'government' or 'private'."""
    if sector in GOVERNMENT_SECTORS:
        return "government"
    if sector in PRIVATE_SECTORS:
        return "private"
    raise ValueError(f"Unknown sector: {sector}")


# ─── Dataclasses ──────────────────────────────────────────────────────────────

@dataclass
class Sector:
    """A voting sector with sub-sector weight allocations."""
    name: str
    sub_sectors: Dict[str, float]  # sub_sector_name -> weight (0-1)


@dataclass
class Vote:
    """A single vote cast by a voter."""
    sector: str
    sub_sector: str
    voter_id: str
    proposal_id: str
    choice: bool   # True=yes, False=no
    weight: float
    timestamp: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Vote":
        return cls(**d)


@dataclass
class Proposal:
    """A governance proposal that can be voted on."""
    proposal_id: str
    title: str
    description: str
    is_constitutional_amendment: bool
    is_emergency: bool
    created_at: float
    votes: List[Vote] = field(default_factory=list)
    status: str = "PENDING"  # PENDING, PASSED, REJECTED, VETOED
    vetoed_by: Optional[str] = None
    founder_veto_active: bool = False

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["votes"] = [v.to_dict() for v in self.votes]
        return d


# ─── Main Class ──────────────────────────────────────────────────────────────

class PowerBalanceConstitutionVoting:
    """
    Vote-based constitutional governance system.

    Provides sector-weighted voting, veto powers, emergency powers,
    and a complete audit trail for all governance decisions.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._proposals: Dict[str, Proposal] = {}
        self._sectors: Dict[str, Sector] = {}
        self._audit_log: List[Dict[str, Any]] = []
        self._init_sectors()
        self._load_state()
        logger.info(
            f"🗳️ PowerBalanceConstitutionVoting initialized — "
            f"{len(self._sectors)} sectors registered"
        )

    def _init_sectors(self) -> None:
        """Initialize the 8 sub-sectors from the constitutional definition."""
        # Government sector
        self._sectors["government"] = Sector(
            name="government",
            sub_sectors=dict(GOVERNMENT_SECTORS),
        )
        # Private sector
        self._sectors["private"] = Sector(
            name="private",
            sub_sectors=dict(PRIVATE_SECTORS),
        )

    # ─── Sector Management ─────────────────────────────────────────────────

    def register_sector(self, sector: Sector) -> bool:
        """
        Register a new voting sector.

        Args:
            sector: Sector definition with sub-sector weights.

        Returns:
            True if registered, False if already exists.
        """
        with self._lock:
            if sector.name in self._sectors:
                return False
            self._sectors[sector.name] = sector
            logger.info(f"📋 Sector registered: {sector.name}")
            return True

    def get_sectors(self) -> Dict[str, Sector]:
        """Get all registered sectors."""
        with self._lock:
            return dict(self._sectors)

    def get_sub_sector_weight(self, sector_name: str,
                              sub_sector: str) -> float:
        """Get the weight of a sub-sector within its sector."""
        with self._lock:
            sector = self._sectors.get(sector_name)
            if not sector:
                raise ValueError(f"Unknown sector: {sector_name}")
            weight = sector.sub_sectors.get(sub_sector)
            if weight is None:
                raise ValueError(
                    f"Unknown sub-sector '{sub_sector}' in sector '{sector_name}'"
                )
            return weight

    # ─── Proposal Management ───────────────────────────────────────────────

    def create_proposal(self, title: str, description: str,
                        is_constitutional: bool = False,
                        is_emergency: bool = False) -> str:
        """
        Create a new governance proposal.

        Args:
            title: Short title for the proposal.
            description: Detailed description.
            is_constitutional: True if this is a constitutional amendment.
            is_emergency: True if this requires emergency powers.

        Returns:
            Unique proposal ID.
        """
        with self._lock:
            proposal_id = str(uuid.uuid4())
            proposal = Proposal(
                proposal_id=proposal_id,
                title=title,
                description=description,
                is_constitutional_amendment=is_constitutional,
                is_emergency=is_emergency,
                created_at=time.time(),
                status="PENDING",
            )
            self._proposals[proposal_id] = proposal
            self._audit({
                "action": "proposal_created",
                "proposal_id": proposal_id,
                "title": title,
                "is_constitutional": is_constitutional,
                "is_emergency": is_emergency,
            })
            logger.info(
                f"📜 Proposal created: {proposal_id[:8]} — '{title}'"
            )
            return proposal_id

    def get_proposal(self, proposal_id: str) -> Optional[Proposal]:
        """Get a proposal by ID."""
        with self._lock:
            return self._proposals.get(proposal_id)

    def get_proposal_status(self, proposal_id: str) -> Optional[str]:
        """Get the current status of a proposal."""
        with self._lock:
            proposal = self._proposals.get(proposal_id)
            if not proposal:
                return None
            return proposal.status

    def get_all_proposals(self, status: Optional[str] = None) -> List[Proposal]:
        """Get all proposals, optionally filtered by status."""
        with self._lock:
            results = list(self._proposals.values())
            if status:
                results = [p for p in results if p.status == status]
            return sorted(results, key=lambda p: p.created_at, reverse=True)

    # ─── Voting ────────────────────────────────────────────────────────────

    def cast_vote(self, proposal_id: str, sector: str,
                  sub_sector: str, voter_id: str,
                  choice: bool) -> Tuple[bool, str]:
        """
        Cast a vote on a proposal.

        Args:
            proposal_id: The proposal to vote on.
            sector: The voter's sector.
            sub_sector: The voter's sub-sector.
            voter_id: Unique identifier for the voter.
            choice: True for yes, False for no.

        Returns:
            Tuple of (success, message).
        """
        with self._lock:
            proposal = self._proposals.get(proposal_id)
            if not proposal:
                return (False, f"Proposal {proposal_id[:8]} not found.")

            if proposal.status != "PENDING":
                return (False, f"Proposal is already {proposal.status}.")

            # Validate sector
            sector_group = get_sector_group(sector)

            # Get weight
            try:
                weight = self.get_sub_sector_weight(sector_group, sub_sector)
            except ValueError as e:
                return (False, str(e))

            # Check for duplicate vote
            for existing in proposal.votes:
                if (existing.sector == sector and
                    existing.sub_sector == sub_sector and
                    existing.voter_id == voter_id):
                    return (False, f"Voter {voter_id} already voted on this proposal.")

            vote = Vote(
                sector=sector,
                sub_sector=sub_sector,
                voter_id=voter_id,
                proposal_id=proposal_id,
                choice=choice,
                weight=weight,
                timestamp=time.time(),
            )
            proposal.votes.append(vote)
            self._persist_vote(vote)

            self._audit({
                "action": "vote_cast",
                "proposal_id": proposal_id,
                "sector": sector,
                "sub_sector": sub_sector,
                "voter_id": voter_id,
                "choice": choice,
                "weight": weight,
            })

            logger.debug(
                f"🗳️ Vote cast: {voter_id} ({sector}/{sub_sector}) "
                f"{'YES' if choice else 'NO'} on {proposal_id[:8]} "
                f"(weight={weight:.2f})"
            )

            return (True, "Vote recorded.")

    def tally_votes(self, proposal_id: str) -> Dict[str, Any]:
        """
        Tally votes and compute the outcome for a proposal.

        Applies sector rules:
          - Simple majority within a sector to pass
          - Constitutional amendments require BOTH government AND private passing
          - Emergency powers require 66% government supermajority

        Args:
            proposal_id: The proposal to tally.

        Returns:
            Dict with tally results and outcome.
        """
        with self._lock:
            proposal = self._proposals.get(proposal_id)
            if not proposal:
                return {"error": f"Proposal {proposal_id[:8]} not found."}

            if not proposal.votes:
                return {
                    "proposal_id": proposal_id,
                    "total_votes": 0,
                    "outcome": "NO_QUORUM",
                    "message": "No votes cast.",
                }

            # Tally per sector group
            gov_yes = 0.0
            gov_no = 0.0
            gov_total = 0.0
            priv_yes = 0.0
            priv_no = 0.0
            priv_total = 0.0

            # Also tally per sub-sector
            breakdown: Dict[str, Dict[str, float]] = {}

            for vote in proposal.votes:
                sector_group = get_sector_group(vote.sector)
                weight = vote.weight

                if sector_group == "government":
                    gov_total += weight
                    if vote.choice:
                        gov_yes += weight
                    else:
                        gov_no += weight
                else:
                    priv_total += weight
                    if vote.choice:
                        priv_yes += weight
                    else:
                        priv_no += weight

                # Sub-sector breakdown
                if vote.sector not in breakdown:
                    breakdown[vote.sector] = {}
                if vote.sub_sector not in breakdown[vote.sector]:
                    breakdown[vote.sector][vote.sub_sector] = {"yes": 0.0, "no": 0.0, "total": 0.0}
                key = "yes" if vote.choice else "no"
                breakdown[vote.sector][vote.sub_sector][key] += weight
                breakdown[vote.sector][vote.sub_sector]["total"] += weight

            # Determine outcomes
            gov_majority = gov_yes > gov_no
            priv_majority = priv_yes > priv_no

            # Check quorum (at least some votes from each sector group)
            gov_has_votes = gov_total > 0
            priv_has_votes = priv_total > 0

            result = {
                "proposal_id": proposal_id,
                "total_votes": len(proposal.votes),
                "government": {
                    "yes": round(gov_yes, 4),
                    "no": round(gov_no, 4),
                    "total": round(gov_total, 4),
                    "majority": gov_majority,
                },
                "private": {
                    "yes": round(priv_yes, 4),
                    "no": round(priv_no, 4),
                    "total": round(priv_total, 4),
                    "majority": priv_majority,
                },
                "breakdown": breakdown,
            }

            # Determine outcome based on proposal type
            if proposal.is_emergency:
                # Emergency: 66% government supermajority required
                if gov_total > 0:
                    gov_ratio = gov_yes / gov_total
                    if gov_ratio >= 0.66:
                        result["outcome"] = "PASSED"
                        result["message"] = "Emergency powers approved (66% government supermajority)."
                        proposal.status = "PASSED"
                    else:
                        result["outcome"] = "REJECTED"
                        result["message"] = (f"Emergency powers rejected "
                                             f"({gov_ratio:.1%} government support, need 66%).")
                        proposal.status = "REJECTED"
                else:
                    result["outcome"] = "NO_QUORUM"
                    result["message"] = "No government votes for emergency decision."

            elif proposal.is_constitutional_amendment:
                # Constitutional amendment: BOTH sides must pass
                if gov_majority and priv_majority:
                    result["outcome"] = "PASSED"
                    result["message"] = "Constitutional amendment PASSED (both sectors approved)."
                    proposal.status = "PASSED"
                elif not gov_majority and not priv_majority:
                    result["outcome"] = "REJECTED"
                    result["message"] = "Amendment rejected by both sectors."
                    proposal.status = "REJECTED"
                elif not gov_majority:
                    result["outcome"] = "REJECTED"
                    result["message"] = "Amendment rejected by government sector."
                    proposal.status = "REJECTED"
                else:
                    result["outcome"] = "REJECTED"
                    result["message"] = "Amendment rejected by private sector."
                    proposal.status = "REJECTED"

            else:
                # Standard proposal: simple majority overall
                total_yes = gov_yes + priv_yes
                total_no = gov_no + priv_no
                if total_yes > total_no:
                    result["outcome"] = "PASSED"
                    result["message"] = "Proposal passed (majority yes)."
                    proposal.status = "PASSED"
                elif total_no > total_yes:
                    result["outcome"] = "REJECTED"
                    result["message"] = "Proposal rejected (majority no)."
                    proposal.status = "REJECTED"
                else:
                    result["outcome"] = "TIE"
                    result["message"] = "Proposal tied — chair casts deciding vote."
                    proposal.status = "PASSED"  # Chair breaks tie in favor

            self._persist_proposal(proposal)
            self._audit({
                "action": "tally",
                "proposal_id": proposal_id,
                "outcome": result["outcome"],
            })

            logger.info(
                f"📊 Tally for {proposal_id[:8]}: {result['outcome']} "
                f"(gov={gov_yes:.2f}/{gov_no:.2f}, "
                f"priv={priv_yes:.2f}/{priv_no:.2f})"
            )

            return result

    # ─── Veto Powers ──────────────────────────────────────────────────────

    def apply_veto(self, proposal_id: str,
                   veto_sector: str) -> Tuple[bool, str]:
        """
        Apply a sector veto to a proposal.

        Rules:
          - Government can veto private-sector-only decisions with 66% government vote
          - Private sector can veto government-only decisions with 66% private vote
          - Veto requires the vetoing sector to have 66% internal support

        Args:
            proposal_id: The proposal to veto.
            veto_sector: "government" or "private"

        Returns:
            Tuple of (success, message).
        """
        with self._lock:
            proposal = self._proposals.get(proposal_id)
            if not proposal:
                return (False, f"Proposal {proposal_id[:8]} not found.")

            if proposal.status == "VETOED":
                return (False, "Proposal already vetoed.")

            if proposal.status not in ("PASSED", "PENDING"):
                return (False, f"Cannot veto proposal with status {proposal.status}.")

            if veto_sector not in ("government", "private"):
                return (False, f"Invalid veto sector: {veto_sector}")

            # Calculate support for veto within the vetoing sector
            veto_yes = 0.0
            veto_total = 0.0
            for vote in proposal.votes:
                sector_group = get_sector_group(vote.sector)
                if sector_group == veto_sector:
                    veto_total += vote.weight
                    if vote.choice:
                        veto_yes += vote.weight

            # Need 66% support within the vetoing sector to apply veto
            if veto_total > 0 and (veto_yes / veto_total) >= 0.66:
                proposal.status = "VETOED"
                proposal.vetoed_by = veto_sector
                self._persist_proposal(proposal)
                self._audit({
                    "action": "veto_applied",
                    "proposal_id": proposal_id,
                    "veto_sector": veto_sector,
                    "support_ratio": round(veto_yes / veto_total, 4),
                })
                logger.warning(
                    f"⛔ Veto applied by {veto_sector} on {proposal_id[:8]}"
                )
                return (True, f"{veto_sector.capitalize()} sector veto applied.")
            else:
                return (False, f"Insufficient support for veto "
                               f"({veto_yes:.2f}/{veto_total:.2f}, need 66%).")

    def founder_veto(self, proposal_id: str) -> Tuple[bool, str]:
        """
        Apply founder (clone_01) emergency veto.

        The founder veto can be overridden by 75% total vote.

        Args:
            proposal_id: The proposal to veto.

        Returns:
            Tuple of (success, message).
        """
        with self._lock:
            proposal = self._proposals.get(proposal_id)
            if not proposal:
                return (False, f"Proposal {proposal_id[:8]} not found.")

            if proposal.status == "VETOED" and proposal.founder_veto_active:
                return (False, "Founder veto already active.")

            proposal.status = "VETOED"
            proposal.vetoed_by = "founder_clone_01"
            proposal.founder_veto_active = True
            self._persist_proposal(proposal)
            self._audit({
                "action": "founder_veto",
                "proposal_id": proposal_id,
            })
            logger.warning(
                f"👑 Founder veto applied on {proposal_id[:8]}"
            )
            return (True, "Founder emergency veto applied.")

    def override_founder_veto(self, proposal_id: str) -> Tuple[bool, str]:
        """
        Override a founder veto with 75% supermajority.

        Args:
            proposal_id: The proposal to override.

        Returns:
            Tuple of (success, message).
        """
        with self._lock:
            proposal = self._proposals.get(proposal_id)
            if not proposal:
                return (False, f"Proposal {proposal_id[:8]} not found.")

            if not proposal.founder_veto_active:
                return (False, "No active founder veto to override.")

            # Calculate total support (75% required)
            total_yes = 0.0
            total_votes = 0.0
            for vote in proposal.votes:
                total_votes += vote.weight
                if vote.choice:
                    total_yes += vote.weight

            if total_votes > 0 and (total_yes / total_votes) >= 0.75:
                proposal.status = "PASSED"
                proposal.founder_veto_active = False
                proposal.vetoed_by = None
                self._persist_proposal(proposal)
                self._audit({
                    "action": "founder_veto_overridden",
                    "proposal_id": proposal_id,
                    "support_ratio": round(total_yes / total_votes, 4),
                })
                logger.warning(
                    f"🔥 Founder veto overridden on {proposal_id[:8]} "
                    f"({total_yes:.1%}/{total_votes:.1%} support)"
                )
                return (True, "Founder veto overridden by 75% supermajority.")
            else:
                ratio = total_yes / max(total_votes, 1)
                return (False, f"Insufficient support to override founder veto "
                               f"({ratio:.1%}, need 75%).")

    # ─── Audit Trail ──────────────────────────────────────────────────────

    def get_audit_trail(self, since: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Get the complete audit trail, optionally filtered by timestamp.

        Args:
            since: Optional Unix timestamp — only return entries after this time.

        Returns:
            List of audit log entries.
        """
        with self._lock:
            if since is None:
                return list(self._audit_log)
            return [e for e in self._audit_log
                    if e.get("timestamp", 0) >= since]

    def _audit(self, entry: Dict[str, Any]) -> None:
        """Add an entry to the in-memory audit log."""
        entry["timestamp"] = time.time()
        self._audit_log.append(entry)

    # ─── Stats ────────────────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive voting statistics."""
        with self._lock:
            total = len(self._proposals)
            passed = sum(1 for p in self._proposals.values()
                         if p.status == "PASSED")
            rejected = sum(1 for p in self._proposals.values()
                           if p.status == "REJECTED")
            vetoed = sum(1 for p in self._proposals.values()
                         if p.status == "VETOED")
            pending = sum(1 for p in self._proposals.values()
                          if p.status == "PENDING")
            total_votes = sum(len(p.votes) for p in self._proposals.values())

            return {
                "total_proposals": total,
                "passed": passed,
                "rejected": rejected,
                "vetoed": vetoed,
                "pending": pending,
                "total_votes_cast": total_votes,
                "audit_log_entries": len(self._audit_log),
                "sectors_registered": len(self._sectors),
                "government_weight": sum(GOVERNMENT_SECTORS.values()),
                "private_weight": sum(PRIVATE_SECTORS.values()),
            }

    # ─── Persistence ─────────────────────────────────────────────────────

    def _persist_vote(self, vote: Vote) -> None:
        """Append a vote to the persistent JSONL store."""
        try:
            os.makedirs(os.path.dirname(_VOTE_DB_PATH), exist_ok=True)
            entry = {
                "_type": "vote",
                "data": vote.to_dict(),
                "timestamp": time.time(),
            }
            with open(_VOTE_DB_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
                f.flush()
        except Exception as e:
            logger.warning(f"Failed to persist vote: {e}")

    def _persist_proposal(self, proposal: Proposal) -> None:
        """Append proposal state to JSONL."""
        try:
            os.makedirs(os.path.dirname(_VOTE_DB_PATH), exist_ok=True)
            entry = {
                "_type": "proposal",
                "data": proposal.to_dict(),
                "timestamp": time.time(),
            }
            with open(_VOTE_DB_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
                f.flush()
        except Exception as e:
            logger.warning(f"Failed to persist proposal: {e}")

    def _load_state(self) -> None:
        """Load persisted state from JSONL."""
        try:
            if not os.path.exists(_VOTE_DB_PATH):
                return

            with open(_VOTE_DB_PATH, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        entry_type = entry.get("_type")
                        data = entry.get("data", {})

                        if entry_type == "vote":
                            vote = Vote.from_dict(data)
                            pid = vote.proposal_id
                            if pid in self._proposals:
                                self._proposals[pid].votes.append(vote)

                        elif entry_type == "proposal":
                            votes_data = data.pop("votes", [])
                            proposal = Proposal(**data)
                            proposal.votes = [
                                Vote.from_dict(v) for v in votes_data
                            ]
                            self._proposals[proposal.proposal_id] = proposal

                    except (json.JSONDecodeError, KeyError, TypeError):
                        continue

            logger.info(
                f"📂 Loaded {len(self._proposals)} proposals from DB"
            )
        except Exception as e:
            logger.warning(f"Failed to load constitution state: {e}")


# ─── Singleton Factory ────────────────────────────────────────────────────────

_instance: Optional[PowerBalanceConstitutionVoting] = None
_instance_lock = threading.Lock()


def get_power_balance_constitution() -> PowerBalanceConstitutionVoting:
    """Get or create the singleton PowerBalanceConstitutionVoting instance."""
    global _instance
    if _instance is None:
        with _instance_lock:
            if _instance is None:
                _instance = PowerBalanceConstitutionVoting()
    return _instance


def reset_power_balance_constitution() -> None:
    """Reset the singleton (for testing) and clean persisted state."""
    global _instance
    with _instance_lock:
        _instance = None
    try:
        p = Path(_VOTE_DB_PATH)
        if p.exists():
            p.unlink()
    except Exception:
        pass


# ─── Module Exports ───────────────────────────────────────────────────────────

__all__ = [
    "Sector",
    "Vote",
    "Proposal",
    "PowerBalanceConstitutionVoting",
    "GOVERNMENT_SECTORS",
    "PRIVATE_SECTORS",
    "get_sector_group",
    "get_power_balance_constitution",
    "reset_power_balance_constitution",
]
