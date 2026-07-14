#!/usr/bin/env python3
"""
STATUS: NEW — Gap 3 Implementation
ASIMNEXUS Power Balance Constitution
=====================================
Encodes the 51% public / 49% private power balance as an immutable
constitutional rule with sector-specific weighting, automated enforcement,
and supermajority amendment protocol.

Extends [`security/immutable_constitution.py`](immutable_constitution.py) by
adding the 51/49 golden-ratio balance to the existing principle system.

Key concepts:
  - PUBLIC_COORDINATED sectors: Infrastructure, Governance, Healthcare,
    Education → min 51% public decision power
  - PRIVATE_OPERATED sectors: Commercial, Technology → max 49% public
    decision power (i.e., 51%+ private)
  - MIXED sectors: Finance, Communication → case-by-case evaluation
  - All balance checks are append-only logged for audit
  - Amendments require 90% supermajority consensus

Integrates with:
  - [`security/immutable_constitution.py`](immutable_constitution.py) — Principle integration
  - [`core/clone_orchestrator.py`](../core/clone_orchestrator.py) — Consensus checks
  - [`governance/compliance_engine.py`](../governance/compliance_engine.py) — Compliance
  - [`core/policy_gate.py`](../core/policy_gate.py) — Policy evaluation
"""

import os
import time
import json
import uuid
import logging
import threading
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger("AsimNexus.Security.PowerBalance")

# ─── Environment Configuration ────────────────────────────────────────────────
_POWER_BALANCE_DB_PATH = os.getenv(
    "ASIM_POWER_BALANCE_DB_PATH",
    "data/power_balance.jsonl",
)


class SectorControl(str, Enum):
    """Governance mode for a sector under the 51/49 constitution."""
    PUBLIC_COORDINATED = "public_coordinated"   # 51%+ public decision power
    PRIVATE_OPERATED = "private_operated"        # 49%- public decision power
    MIXED = "mixed"                               # Case-by-case evaluation


class BalanceVerdict(str, Enum):
    """Result of a balance check."""
    PASS = "pass"           # Decision preserves balance
    WARN = "warn"           # Decision shifts balance but within threshold
    BLOCK = "block"         # Decision violates the constitution


@dataclass
class BalanceResult:
    """Result of checking a decision against the power balance."""
    verdict: BalanceVerdict
    sector: str
    current_public_share: float
    current_private_share: float
    decision_impact: float  # How much this decision shifts the balance
    message: str
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "verdict": self.verdict.value,
            "sector": self.sector,
            "current_public_share": self.current_public_share,
            "current_private_share": self.current_private_share,
            "decision_impact": self.decision_impact,
            "message": self.message,
            "timestamp": self.timestamp,
        }


@dataclass
class SectorBalance:
    """Current power balance state for a sector."""
    sector: str
    control: SectorControl
    public_share: float     # 0.0 to 1.0
    private_share: float    # 0.0 to 1.0
    total_decisions: int = 0
    public_decisions: int = 0
    private_decisions: int = 0
    last_updated: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sector": self.sector,
            "control": self.control.value,
            "public_share": self.public_share,
            "private_share": self.private_share,
            "total_decisions": self.total_decisions,
            "public_decisions": self.public_decisions,
            "private_decisions": self.private_decisions,
            "last_updated": self.last_updated,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SectorBalance":
        data = dict(data)
        data["control"] = SectorControl(data["control"])
        return cls(**data)


@dataclass
class AmendmentProposal:
    """Proposal to amend the balance for a sector."""
    id: str
    sector: str
    proposed_control: SectorControl
    proposed_public_share: float
    rationale: str
    proposer: str
    votes_for: int = 0
    votes_against: int = 0
    votes_total: int = 0
    status: str = "pending"  # pending, approved, rejected
    created_at: float = field(default_factory=time.time)
    decided_at: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "sector": self.sector,
            "proposed_control": self.proposed_control.value,
            "proposed_public_share": self.proposed_public_share,
            "rationale": self.rationale,
            "proposer": self.proposer,
            "votes_for": self.votes_for,
            "votes_against": self.votes_against,
            "votes_total": self.votes_total,
            "status": self.status,
            "created_at": self.created_at,
            "decided_at": self.decided_at,
        }


# ─── Sector Balance Map (The Constitutional Rule) ──────────────────────────
# This defines the immutable 51/49 balance for each sector.
# Changing this requires the amendment protocol with 90% supermajority.

SECTOR_BALANCE_MAP: Dict[str, SectorControl] = {
    "infrastructure": SectorControl.PUBLIC_COORDINATED,
    "governance": SectorControl.PUBLIC_COORDINATED,
    "healthcare": SectorControl.PUBLIC_COORDINATED,
    "education": SectorControl.PUBLIC_COORDINATED,
    "commercial": SectorControl.PRIVATE_OPERATED,
    "finance": SectorControl.MIXED,
    "technology": SectorControl.PRIVATE_OPERATED,
    "communication": SectorControl.MIXED,
}

# Default balance thresholds per control type
DEFAULT_PUBLIC_THRESHOLD = 0.51   # 51% minimum public
DEFAULT_PRIVATE_THRESHOLD = 0.49  # 49% maximum public (i.e., 51% private)

# Amendment requires 90% supermajority
AMENDMENT_SUPERMAJORITY = 0.90


class PowerBalanceConstitution:
    """
    Enforces the 51/49 power balance as an immutable constitutional rule.

    The core principle:
      - Public/Government coordination holds 51% minimum decision power
      - Private/Company operation holds 49% maximum decision power
      - Sector-specific weighting applies
      - Amendments require 90% supermajority consensus
    """

    def __init__(self):
        self._lock = threading.RLock()
        # Current balance state per sector
        self._balances: Dict[str, SectorBalance] = {}
        self._amendments: Dict[str, AmendmentProposal] = {}
        self._audit_log: List[Dict[str, Any]] = []
        self._init_balances()
        self._load_from_db()
        logger.info(
            f"⚖️ PowerBalanceConstitution initialized — "
            f"{len(self._balances)} sectors, {len(self._amendments)} amendments"
        )

    def _init_balances(self) -> None:
        """Initialize sector balances from the constitutional map."""
        for sector, control in SECTOR_BALANCE_MAP.items():
            if control == SectorControl.PUBLIC_COORDINATED:
                public_share = DEFAULT_PUBLIC_THRESHOLD
                private_share = 1.0 - DEFAULT_PUBLIC_THRESHOLD
            elif control == SectorControl.PRIVATE_OPERATED:
                public_share = DEFAULT_PRIVATE_THRESHOLD
                private_share = 1.0 - DEFAULT_PRIVATE_THRESHOLD
            else:  # MIXED
                public_share = 0.5
                private_share = 0.5

            self._balances[sector] = SectorBalance(
                sector=sector,
                control=control,
                public_share=public_share,
                private_share=private_share,
            )

    # ─── Core API ────────────────────────────────────────────────────────────

    def check_decision(self, sector: str,
                       is_public_decision: bool,
                       weight: float = 1.0,
                       context: Optional[Dict[str, Any]] = None) -> BalanceResult:
        """
        Check if a decision preserves the constitutional balance.

        Args:
            sector: The sector this decision belongs to (e.g., "healthcare").
            is_public_decision: True if this is a public/government decision,
                                False if private/company.
            weight: Relative weight of this decision (default 1.0).
            context: Optional context dict for logging.

        Returns:
            BalanceResult with PASS, WARN, or BLOCK verdict.
        """
        context = context or {}
        with self._lock:
            balance = self._balances.get(sector)
            if not balance:
                return BalanceResult(
                    verdict=BalanceVerdict.BLOCK,
                    sector=sector,
                    current_public_share=0.0,
                    current_private_share=0.0,
                    decision_impact=0.0,
                    message=f"Unknown sector: {sector}",
                )

            sector_control = SECTOR_BALANCE_MAP.get(sector, SectorControl.MIXED)
            decision_impact = weight / max(balance.total_decisions + 1, 1)

            # Calculate what the balance would be after this decision
            if is_public_decision:
                new_public_decisions = balance.public_decisions + 1
                new_total = balance.total_decisions + 1
                new_public_share = new_public_decisions / max(new_total, 1)
                new_private_share = 1.0 - new_public_share
            else:
                new_private_decisions = balance.private_decisions + 1
                new_total = balance.total_decisions + 1
                new_private_share = new_private_decisions / max(new_total, 1)
                new_public_share = 1.0 - new_private_share

            # Evaluate against constitutional thresholds
            if sector_control == SectorControl.PUBLIC_COORDINATED:
                # Must maintain >= 51% public
                if new_public_share < DEFAULT_PUBLIC_THRESHOLD:
                    verdict = BalanceVerdict.BLOCK
                    msg = (f"BLOCKED: {sector} requires >= 51% public "
                           f"coordination (would be {new_public_share:.1%})")
                elif new_public_share < DEFAULT_PUBLIC_THRESHOLD + 0.05:
                    verdict = BalanceVerdict.WARN
                    msg = (f"WARN: {sector} public share dropping to "
                           f"{new_public_share:.1%} (threshold {DEFAULT_PUBLIC_THRESHOLD:.0%})")
                else:
                    verdict = BalanceVerdict.PASS
                    msg = (f"PASS: {sector} public share "
                           f"{new_public_share:.1%}")

            elif sector_control == SectorControl.PRIVATE_OPERATED:
                # Must maintain <= 49% public (i.e., >= 51% private)
                if new_public_share > DEFAULT_PRIVATE_THRESHOLD:
                    verdict = BalanceVerdict.BLOCK
                    msg = (f"BLOCKED: {sector} requires <= 49% public "
                           f"coordination (would be {new_public_share:.1%})")
                elif new_public_share > DEFAULT_PRIVATE_THRESHOLD - 0.05:
                    verdict = BalanceVerdict.WARN
                    msg = (f"WARN: {sector} public share rising to "
                           f"{new_public_share:.1%} (threshold {DEFAULT_PRIVATE_THRESHOLD:.0%})")
                else:
                    verdict = BalanceVerdict.PASS
                    msg = (f"PASS: {sector} private operation "
                           f"{1.0 - new_public_share:.1%}")

            else:  # MIXED
                # Case-by-case: flag for review if imbalance > 60/40
                if new_public_share > 0.60 or new_public_share < 0.40:
                    verdict = BalanceVerdict.WARN
                    msg = (f"WARN: {sector} balance at "
                           f"{new_public_share:.0%}/{1.0 - new_public_share:.0%} "
                           f"— review recommended")
                else:
                    verdict = BalanceVerdict.PASS
                    msg = (f"PASS: {sector} mixed balance "
                           f"{new_public_share:.0%}/{1.0 - new_public_share:.0%}")

            result = BalanceResult(
                verdict=verdict,
                sector=sector,
                current_public_share=balance.public_share,
                current_private_share=balance.private_share,
                decision_impact=decision_impact,
                message=msg,
            )

            # If PASS or WARN, record the decision
            if verdict in (BalanceVerdict.PASS, BalanceVerdict.WARN):
                if is_public_decision:
                    balance.public_decisions += 1
                else:
                    balance.private_decisions += 1
                balance.total_decisions += 1

                # Recalculate shares
                balance.public_share = (
                    balance.public_decisions / max(balance.total_decisions, 1)
                )
                balance.private_share = (
                    balance.private_decisions / max(balance.total_decisions, 1)
                )
                balance.last_updated = time.time()

            # Audit log
            self._audit_log.append({
                "type": "check_decision",
                "sector": sector,
                "is_public_decision": is_public_decision,
                "weight": weight,
                "verdict": verdict.value,
                "message": msg,
                "timestamp": time.time(),
                **context,
            })
            self._persist_balance(balance)
            self._persist_audit_entry(result, context)

            return result

    def get_current_balance(self,
                            sector: Optional[str] = None) -> Dict[str, Any]:
        """
        Get current public/private balance across all sectors or one sector.

        Args:
            sector: Optional sector name. If None, returns aggregate.

        Returns:
            Dict with balance information.
        """
        with self._lock:
            if sector:
                bal = self._balances.get(sector)
                if not bal:
                    return {"error": f"Unknown sector: {sector}"}
                return bal.to_dict()

            total_public = sum(b.public_decisions for b in self._balances.values())
            total_private = sum(b.private_decisions for b in self._balances.values())
            total_decisions = total_public + total_private

            return {
                "overall_public_share": total_public / max(total_decisions, 1),
                "overall_private_share": total_private / max(total_decisions, 1),
                "total_decisions": total_decisions,
                "total_public_decisions": total_public,
                "total_private_decisions": total_private,
                "sectors": {
                    name: bal.to_dict()
                    for name, bal in self._balances.items()
                },
                "sectors_defined": len(self._balances),
            }

    def propose_amendment(self, sector: str,
                          proposed_control: SectorControl,
                          proposed_public_share: float,
                          rationale: str,
                          proposer: str) -> AmendmentProposal:
        """
        Propose changing the balance for a sector.

        Requires 90% supermajority consensus to pass.

        Args:
            sector: Sector to amend.
            proposed_control: New sector control type.
            proposed_public_share: New target public share (0.0 to 1.0).
            rationale: Why this amendment is needed.
            proposer: Who is proposing the amendment.

        Returns:
            AmendmentProposal with a unique ID.
        """
        with self._lock:
            if sector not in SECTOR_BALANCE_MAP:
                raise ValueError(f"Unknown sector: {sector}")

            if not (0.0 <= proposed_public_share <= 1.0):
                raise ValueError(
                    f"proposed_public_share must be between 0.0 and 1.0, "
                    f"got {proposed_public_share}"
                )

            amendment = AmendmentProposal(
                id=str(uuid.uuid4()),
                sector=sector,
                proposed_control=proposed_control,
                proposed_public_share=proposed_public_share,
                rationale=rationale,
                proposer=proposer,
            )
            self._amendments[amendment.id] = amendment
            self._persist_amendment(amendment)

            logger.warning(
                f"⚡ Amendment proposed: {sector} → "
                f"{proposed_control.value} ({proposed_public_share:.0%} public) "
                f"by {proposer}"
            )
            return amendment

    def vote_on_amendment(self, amendment_id: str,
                          vote_for: bool) -> Tuple[bool, str]:
        """
        Cast a vote on an amendment proposal.

        Args:
            amendment_id: The amendment to vote on.
            vote_for: True for yes, False for no.

        Returns:
            Tuple of (approved, message).
        """
        with self._lock:
            amendment = self._amendments.get(amendment_id)
            if not amendment:
                return (False, f"Amendment {amendment_id} not found.")

            if amendment.status != "pending":
                return (False, f"Amendment already {amendment.status}.")

            if vote_for:
                amendment.votes_for += 1
            else:
                amendment.votes_against += 1
            amendment.votes_total += 1

            # Check if supermajority reached
            if amendment.votes_total >= 10:  # Minimum votes for quorum
                approval_ratio = (
                    amendment.votes_for / max(amendment.votes_total, 1)
                )
                if approval_ratio >= AMENDMENT_SUPERMAJORITY:
                    amendment.status = "approved"
                    amendment.decided_at = time.time()
                    self._apply_amendment(amendment)
                    self._persist_amendment(amendment)
                    logger.warning(
                        f"✅ Amendment {amendment_id[:8]} APPROVED — "
                        f"{amendment.sector} rebalanced"
                    )
                    return (True, "Amendment approved with supermajority.")
                elif (amendment.votes_total >= 100
                      and approval_ratio < AMENDMENT_SUPERMAJORITY):
                    amendment.status = "rejected"
                    amendment.decided_at = time.time()
                    self._persist_amendment(amendment)
                    return (False,
                            "Amendment rejected — insufficient support.")

            self._persist_amendment(amendment)
            return (False,
                    f"Vote recorded ({amendment.votes_for}/{amendment.votes_total}). "
                    f"Need {AMENDMENT_SUPERMAJORITY:.0%} majority.")

    def _apply_amendment(self, amendment: AmendmentProposal) -> None:
        """Apply an approved amendment to the balance state."""
        # Update the sector balance
        balance = self._balances.get(amendment.sector)
        if balance:
            balance.control = amendment.proposed_control
            balance.public_share = amendment.proposed_public_share
            balance.private_share = 1.0 - amendment.proposed_public_share
            balance.last_updated = time.time()
            self._persist_balance(balance)

    def get_amendments(self,
                       status: Optional[str] = None) -> List[AmendmentProposal]:
        """Get amendment proposals, optionally filtered by status."""
        with self._lock:
            results = list(self._amendments.values())
            if status:
                results = [a for a in results if a.status == status]
            return sorted(results, key=lambda a: a.created_at, reverse=True)

    def get_sector_info(self, sector: str) -> Optional[Dict[str, Any]]:
        """Get detailed info about a sector including control type.

        Uses runtime balance state so approved amendments are reflected.
        """
        with self._lock:
            balance = self._balances.get(sector)
            if not balance:
                return None

            control = balance.control
            return {
                "sector": sector,
                "control": control.value,
                "public_threshold": (DEFAULT_PUBLIC_THRESHOLD
                                     if control == SectorControl.PUBLIC_COORDINATED
                                     else DEFAULT_PRIVATE_THRESHOLD
                                     if control == SectorControl.PRIVATE_OPERATED
                                     else 0.5),
                "current_balance": balance.to_dict(),
            }

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive power balance statistics."""
        with self._lock:
            total_public = sum(b.public_decisions
                               for b in self._balances.values())
            total_private = sum(b.private_decisions
                                for b in self._balances.values())
            total_decisions = total_public + total_private

            sectors_by_control: Dict[str, int] = {}
            for control in SECTOR_BALANCE_MAP.values():
                key = control.value
                sectors_by_control[key] = sectors_by_control.get(key, 0) + 1

            pending_amendments = sum(
                1 for a in self._amendments.values()
                if a.status == "pending"
            )

            return {
                "total_sectors": len(self._balances),
                "total_decisions": total_decisions,
                "total_public_decisions": total_public,
                "total_private_decisions": total_private,
                "overall_public_share": (
                    total_public / max(total_decisions, 1)
                ),
                "overall_private_share": (
                    total_private / max(total_decisions, 1)
                ),
                "sectors_by_control": sectors_by_control,
                "pending_amendments": pending_amendments,
                "total_amendments": len(self._amendments),
                "public_threshold": DEFAULT_PUBLIC_THRESHOLD,
                "private_threshold": DEFAULT_PRIVATE_THRESHOLD,
                "amendment_supermajority": AMENDMENT_SUPERMAJORITY,
            }

    # ─── Persistence ─────────────────────────────────────────────────────────

    def _persist_balance(self, balance: SectorBalance) -> None:
        """Append sector balance state to JSONL."""
        try:
            os.makedirs(os.path.dirname(_POWER_BALANCE_DB_PATH), exist_ok=True)
            entry = {
                "_type": "balance",
                "sector": balance.sector,
                "data": balance.to_dict(),
                "timestamp": time.time(),
            }
            with open(_POWER_BALANCE_DB_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
                f.flush()
        except Exception as e:
            logger.warning(f"Failed to persist balance: {e}")

    def _persist_amendment(self, amendment: AmendmentProposal) -> None:
        """Append amendment state to JSONL."""
        try:
            os.makedirs(os.path.dirname(_POWER_BALANCE_DB_PATH), exist_ok=True)
            entry = {
                "_type": "amendment",
                "id": amendment.id,
                "data": amendment.to_dict(),
                "timestamp": time.time(),
            }
            with open(_POWER_BALANCE_DB_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
                f.flush()
        except Exception as e:
            logger.warning(f"Failed to persist amendment: {e}")

    def _persist_audit_entry(self, result: BalanceResult,
                             context: Dict[str, Any]) -> None:
        """Append audit entry to JSONL."""
        try:
            os.makedirs(os.path.dirname(_POWER_BALANCE_DB_PATH), exist_ok=True)
            entry = {
                "_type": "audit",
                "data": result.to_dict(),
                "context": context,
                "timestamp": time.time(),
            }
            with open(_POWER_BALANCE_DB_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
                f.flush()
        except Exception as e:
            logger.warning(f"Failed to persist audit entry: {e}")

    def _load_from_db(self) -> None:
        """Load state from persistent storage."""
        try:
            path = _POWER_BALANCE_DB_PATH
            if not os.path.exists(path):
                return

            latest_balances: Dict[str, SectorBalance] = {}
            latest_amendments: Dict[str, AmendmentProposal] = {}

            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        entry_type = entry.get("_type")

                        if entry_type == "balance":
                            sector = entry["sector"]
                            balance = SectorBalance.from_dict(entry["data"])
                            latest_balances[sector] = balance

                        elif entry_type == "amendment":
                            aid = entry["id"]
                            data = entry["data"]
                            amendment = AmendmentProposal(
                                id=data["id"],
                                sector=data["sector"],
                                proposed_control=SectorControl(
                                    data["proposed_control"]
                                ),
                                proposed_public_share=data.get(
                                    "proposed_public_share", 0.5
                                ),
                                rationale=data.get("rationale", ""),
                                proposer=data.get("proposer", ""),
                                votes_for=data.get("votes_for", 0),
                                votes_against=data.get("votes_against", 0),
                                votes_total=data.get("votes_total", 0),
                                status=data.get("status", "pending"),
                                created_at=data.get("created_at", 0.0),
                                decided_at=data.get("decided_at"),
                            )
                            latest_amendments[aid] = amendment

                    except (json.JSONDecodeError, KeyError):
                        continue

            # Merge loaded state with initialized state
            for sector, balance in latest_balances.items():
                if sector in self._balances:
                    self._balances[sector] = balance

            self._amendments = latest_amendments

            logger.info(
                f"📂 Loaded {len(latest_balances)} sector balances "
                f"and {len(latest_amendments)} amendments from DB"
            )
        except Exception as e:
            logger.warning(f"Failed to load power balance state: {e}")


# ─── Singleton Factory ────────────────────────────────────────────────────────

_power_balance_instance: Optional[PowerBalanceConstitution] = None
_power_balance_lock = threading.Lock()


def get_power_balance() -> PowerBalanceConstitution:
    """Get or create the singleton PowerBalanceConstitution instance."""
    global _power_balance_instance
    if _power_balance_instance is None:
        with _power_balance_lock:
            if _power_balance_instance is None:
                _power_balance_instance = PowerBalanceConstitution()
    return _power_balance_instance


def reset_power_balance() -> None:
    """Reset the singleton (for testing) and clean persisted state."""
    global _power_balance_instance
    with _power_balance_lock:
        _power_balance_instance = None
    try:
        from pathlib import Path
        p = Path(_POWER_BALANCE_DB_PATH)
        if p.exists():
            p.unlink()
    except Exception:
        pass


# ─── Module Exports ───────────────────────────────────────────────────────────

__all__ = [
    "SectorControl",
    "BalanceVerdict",
    "BalanceResult",
    "SectorBalance",
    "AmendmentProposal",
    "PowerBalanceConstitution",
    "SECTOR_BALANCE_MAP",
    "DEFAULT_PUBLIC_THRESHOLD",
    "DEFAULT_PRIVATE_THRESHOLD",
    "AMENDMENT_SUPERMAJORITY",
    "get_power_balance",
    "reset_power_balance",
]
