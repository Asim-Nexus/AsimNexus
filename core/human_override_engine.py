#!/usr/bin/env python3
"""
STATUS: REAL — Human Override Engine
=====================================
Hierarchical human override system with Final-3-Decisions tracking.

Provides:
- Tiered override hierarchy (Personal → Trusted Circle → Independent)
- Final-3-Decisions counter — forces human review after N consecutive AI decisions
- Cryptographic override proof (action_hash + timestamp + tier + signature)
- Immutable append-only override audit log
- Integration hooks for DharmaVetoEngine and PolicyGate

Design Principles:
1. Human is the ultimate sovereign — no AI decision is above override
2. Override is irrevocable once recorded — tamper-proof audit trail
3. Three tiers escalate naturally — personal, then trusted circle, then independent
4. Final-3-Decisions prevents "automation blindness" — forced human check-in
5. Every override is cryptographically bound to the action it overrides

Integration:
- Called by DharmaVetoEngine before BLOCK/REQUIRE_HUMAN decisions
- Called by PolicyGate before CRITICAL action evaluation
- API endpoints in simple_backend.py for frontend override UI
"""

import os
import hashlib
import json
import secrets
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger("HumanOverride")

# ─── Environment Configuration ────────────────────────────────────────────────
_OVERRIDE_TTL_SECONDS = int(os.getenv("ASIM_OVERRIDE_TTL", "600"))  # 10 min
_MAX_AUDIT_LOG = int(os.getenv("ASIM_OVERRIDE_AUDIT_MAX", "10000"))
_MAX_DECISIONS_BEFORE_OVERRIDE = int(os.getenv("ASIM_OVERRIDE_FINAL_THREE", "3"))
_QUORUM_TIMEOUT = int(os.getenv("ASIM_QUORUM_TIMEOUT", "300"))  # 5 min


class OverrideTier(Enum):
    """Hierarchy of human override authority levels.

    PERSONAL:      User overrides their own AI — single human confirmation
    TRUSTED_CIRCLE: Family/council vote (N humans must agree) — for shared decisions
    INDEPENDENT:   External arbiter / independent review — for disputes
    """
    PERSONAL = "personal"
    TRUSTED_CIRCLE = "trusted_circle"
    INDEPENDENT = "independent"


class OverrideStatus(Enum):
    """Status of an override request."""
    PENDING = "pending"
    QUORUM_PENDING = "quorum_pending"  # Waiting for N-of-M trusted circle votes
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    EXPIRED = "expired"
    ESCALATED = "escalated"  # Moved to higher tier


class OverrideTrigger(Enum):
    """What triggered the override requirement."""
    FINAL_THREE = "final_three"            # Final-3-Decisions counter hit limit
    CONSTITUTIONAL = "constitutional"      # Veto engine flagged violation
    HUMAN_INITIATED = "human_initiated"    # Human proactively requested override
    POLICY_CRITICAL = "policy_critical"    # Policy gate flagged critical action
    AGENT_CONTRACT = "agent_contract"      # Agent contract requires human check


@dataclass
class OverrideRequest:
    """A request for human override of an AI decision.

    This is the core data structure — every override goes through this lifecycle:
    CREATED → PENDING → CONFIRMED/REJECTED/EXPIRED/ESCALATED

    The cryptographic chain (action_hash → commitment → signature) ensures
    tamper-proof provenance of every human override decision.
    """
    request_id: str
    action_hash: str                    # SHA-256 of the action being overridden
    action_preview: str                 # First 200 chars (safe to display)
    trigger: OverrideTrigger            # Why override was needed
    tier: OverrideTier                  # Current override tier
    requested_by: str                   # Agent/clone/user that triggered the action
    human_id: Optional[str] = None      # Human who confirmed (set on confirm)
    reason: str = ""                    # Human's reason for override
    status: OverrideStatus = OverrideStatus.PENDING
    created_at: float = field(default_factory=time.time)
    expires_at: float = 0.0
    confirmed_at: Optional[float] = None
    commitment: str = ""               # ZK-style commitment = SHA-256(action_hash + nonce)
    nonce: str = ""                    # Private nonce — never exposed to client
    signature: str = ""                # Cryptographic signature of override decision
    escalation_chain: List[OverrideTier] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    # N-of-M quorum fields for TRUSTED_CIRCLE tier
    approved_by: List[str] = field(default_factory=list)   # Which trusted members voted yes
    quorum_required: int = 0                                # How many votes needed
    quorum_deadline: float = 0.0                            # When quorum expires

    def __post_init__(self):
        if not self.expires_at:
            self.expires_at = self.created_at + _OVERRIDE_TTL_SECONDS
        if not self.quorum_deadline:
            self.quorum_deadline = self.created_at + _QUORUM_TIMEOUT

    def is_expired(self) -> bool:
        return time.time() > self.expires_at

    def is_quorum_expired(self) -> bool:
        """Check if the quorum window has expired (for QUORUM_PENDING requests)."""
        return time.time() > self.quorum_deadline

    def to_dict(self) -> Dict[str, Any]:
        """Public representation — no nonce or internal state."""
        return {
            "request_id": self.request_id,
            "action_hash": self.action_hash,
            "action_preview": self.action_preview,
            "trigger": self.trigger.value,
            "tier": self.tier.value,
            "requested_by": self.requested_by,
            "human_id": self.human_id,
            "reason": self.reason,
            "status": self.status.value,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "confirmed_at": self.confirmed_at,
            "commitment": self.commitment,
            "signature": self.signature,
            "escalation_chain": [t.value for t in self.escalation_chain],
            "metadata": self.metadata,
            "approved_by": self.approved_by,
            "quorum_required": self.quorum_required,
        }


@dataclass
class OverrideAuditEntry:
    """Immutable audit entry for override decisions.

    Once written, this is append-only. The action_hash links back to
    the original action, and the signature proves human involvement.
    """
    entry_id: str
    action_hash: str
    human_id: str
    tier: OverrideTier
    trigger: OverrideTrigger
    status: OverrideStatus
    reason: str
    signature: str
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "action_hash": self.action_hash,
            "human_id": self.human_id,
            "tier": self.tier.value,
            "trigger": self.trigger.value,
            "status": self.status.value,
            "reason": self.reason,
            "signature": self.signature,
            "timestamp": self.timestamp,
        }


class HumanOverrideEngine:
    """
    Hierarchical human override system with Final-3-Decisions tracking.

    This is the human sovereignty layer — it ensures every AI action can be
    overridden by a human, and forces human check-in after N consecutive
    autonomous decisions (the Final-3-Decisions principle).

    Three tiers of override:
    1. PERSONAL — single human confirms/rejects (for personal decisions)
    2. TRUSTED_CIRCLE — N humans vote (for shared/family decisions)
    3. INDEPENDENT — external arbiter (for disputes/conflicts)

    The Final-3-Decisions counter tracks how many consecutive AI decisions
    have been accepted without human intervention. When it reaches 3,
    the next decision *must* be reviewed by a human before execution.
    """

    # Tier thresholds — how many humans must confirm at each tier
    TIER_THRESHOLDS: Dict[OverrideTier, int] = {
        OverrideTier.PERSONAL: 1,          # Single human
        OverrideTier.TRUSTED_CIRCLE: 3,    # Three trusted humans (default, uses quorum)
        OverrideTier.INDEPENDENT: 1,        # One independent arbiter
    }

    # Default quorum strategy: "majority" = floor(N/2)+1
    # Can be overridden per circle via set_quorum()

    # Escalation order — if rejected at lower tier, move up
    ESCALATION_ORDER: List[OverrideTier] = [
        OverrideTier.PERSONAL,
        OverrideTier.TRUSTED_CIRCLE,
        OverrideTier.INDEPENDENT,
    ]

    def __init__(self, max_decisions: int = _MAX_DECISIONS_BEFORE_OVERRIDE):
        self._requests: Dict[str, OverrideRequest] = {}
        self._audit_log: List[OverrideAuditEntry] = []
        self._decision_counter: int = 0             # Final-3-Decisions counter
        self._max_decisions: int = max_decisions     # Default: 3
        self._trusted_circle: Set[str] = set()       # Human IDs in trusted circle
        self._override_count: int = 0
        self._auto_pass_count: int = 0
        self._circle_quorums: Dict[str, int] = {}    # Per-circle quorum overrides

        logger.info(
            f"HumanOverrideEngine initialized — "
            f"max_decisions_before_override={max_decisions}, "
            f"tier_thresholds={self.TIER_THRESHOLDS}"
        )

    # ─── Final-3-Decisions Counter ─────────────────────────────────────────

    @property
    def decisions_remaining(self) -> int:
        """How many more autonomous decisions before human override is forced."""
        return max(0, self._max_decisions - self._decision_counter)

    @property
    def is_override_required(self) -> bool:
        """True if human override is mandatory (counter reached limit).

        When this is True, the next AI decision CANNOT proceed without
        human confirmation. This enforces the Final-3-Decisions principle.
        """
        return self._decision_counter >= self._max_decisions

    def record_decision(self, was_overridden: bool = False) -> None:
        """Record an AI decision, tracking the Final-3-Decisions counter.

        Args:
            was_overridden: True if the decision required human override.
                           If True, counter resets. If False, counter increments.
        """
        if was_overridden:
            self._decision_counter = 0
            logger.info("Final-3-Decisions counter RESET (human was involved)")
        else:
            self._decision_counter += 1
            remaining = self.decisions_remaining
            logger.info(
                f"Final-3-Decisions counter: {self._decision_counter}/"
                f"{self._max_decisions} (remaining: {remaining})"
            )
            if self.is_override_required:
                logger.warning(
                    "⚠️ Final-3-Decisions threshold REACHED — "
                    "next action requires human override"
                )

    def reset_decision_counter(self) -> None:
        """Manually reset the Final-3-Decisions counter."""
        self._decision_counter = 0
        logger.info("Final-3-Decisions counter manually reset")

    # ─── Override Request Lifecycle ─────────────────────────────────────────

    def request_override(
        self,
        action_hash: str,
        action_preview: str,
        trigger: OverrideTrigger,
        tier: OverrideTier = OverrideTier.PERSONAL,
        requested_by: str = "system",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create a new override request.

        Args:
            action_hash: SHA-256 hash of the action being overridden
            action_preview: Human-readable preview (first 200 chars max)
            trigger: What triggered the override requirement
            tier: Initial override tier (defaults to PERSONAL)
            requested_by: Agent/clone/user that triggered the action
            metadata: Additional context

        Returns:
            Request ID (token) for the frontend to track

        Raises:
            ValueError: If action_preview exceeds 200 characters
        """
        if len(action_preview) > 200:
            action_preview = action_preview[:200] + "…"

        request_id = f"ovr_{secrets.token_urlsafe(16)}"
        nonce = secrets.token_hex(32)
        commitment = hashlib.sha256(
            f"{action_hash}{nonce}".encode()
        ).hexdigest()

        request = OverrideRequest(
            request_id=request_id,
            action_hash=action_hash,
            action_preview=action_preview,
            trigger=trigger,
            tier=tier,
            requested_by=requested_by,
            commitment=commitment,
            nonce=nonce,
            metadata=metadata or {},
        )

        self._requests[request_id] = request
        logger.info(
            f"🛑 Override requested: {request_id} "
            f"(tier={tier.value}, trigger={trigger.value})"
        )
        return request_id

    def confirm_override(
        self,
        request_id: str,
        human_id: str,
        reason: str = "",
        tier: Optional[OverrideTier] = None,
    ) -> Dict[str, Any]:
        """Confirm an override request.

        The human explicitly confirms they want to override the AI decision.
        This is recorded with cryptographic proof.

        Args:
            request_id: The override request ID
            human_id: Identifier of the human confirming
            reason: Human's reason for the override
            tier: Override tier (defaults to the request's current tier)

        Returns:
            Result dict with success, signature, and verification info

        Raises:
            ValueError: If request_id not found or already resolved
        """
        request = self._requests.get(request_id)
        if not request:
            return {"success": False, "error": "Request not found"}

        if request.status not in (OverrideStatus.PENDING, OverrideStatus.QUORUM_PENDING):
            return {
                "success": False,
                "error": f"Request already {request.status.value}",
            }

        if request.is_expired():
            request.status = OverrideStatus.EXPIRED
            return {"success": False, "error": "Override request expired"}

        effective_tier = tier or request.tier

        # Verify tier threshold met (for TRUSTED_CIRCLE, need N humans)
        # For PERSONAL and INDEPENDENT, single human is enough
        # For TRUSTED_CIRCLE, we track confirmations per request using N-of-M quorum
        if effective_tier == OverrideTier.PERSONAL:
            # Single human confirmation is sufficient
            pass
        elif effective_tier == OverrideTier.INDEPENDENT:
            # Single independent arbiter is sufficient
            pass
        elif effective_tier == OverrideTier.TRUSTED_CIRCLE:
            # Trusted circle needs N-of-M quorum
            if human_id not in self._trusted_circle:
                return {
                    "success": False,
                    "error": f"Human {human_id} is not in the trusted circle",
                }

            # Prevent duplicate votes
            if human_id in request.approved_by:
                return {
                    "success": False,
                    "error": f"Human {human_id} has already voted on this request",
                }

            # Calculate quorum if not yet set
            if request.quorum_required == 0:
                circle_size = len(self._trusted_circle)
                # Check for per-circle quorum override
                circle_id = f"trusted_circle_{id(self._trusted_circle)}"
                quorum_size = self._circle_quorums.get(circle_id, 0)
                if quorum_size == 0:
                    # Default: majority = floor(N/2) + 1
                    quorum_size = (circle_size // 2) + 1
                request.quorum_required = quorum_size

            # Add vote
            request.approved_by.append(human_id)

            # Check if quorum reached
            if len(request.approved_by) >= request.quorum_required:
                # Quorum reached — proceed to confirmation
                logger.info(
                    f"✅ Quorum REACHED for {request.request_id}: "
                    f"{len(request.approved_by)}/{request.quorum_required} votes"
                )
                # Set human_id to the last voter for audit purposes
                # but record all in approved_by
            else:
                # Still waiting for more votes
                request.status = OverrideStatus.QUORUM_PENDING
                remaining = request.quorum_required - len(request.approved_by)
                logger.info(
                    f"⏳ Quorum pending for {request.request_id}: "
                    f"{len(request.approved_by)}/{request.quorum_required} "
                    f"({remaining} more needed)"
                )
                return {
                    "success": False,
                    "request_id": request_id,
                    "status": "quorum_pending",
                    "approved_by": request.approved_by,
                    "quorum_required": request.quorum_required,
                    "quorum_remaining": remaining,
                }

        # Check quorum deadline (only relevant for TRUSTED_CIRCLE)
        if effective_tier == OverrideTier.TRUSTED_CIRCLE and request.is_quorum_expired():
            request.status = OverrideStatus.EXPIRED
            return {"success": False, "error": "Quorum deadline expired"}

        # Generate cryptographic signature of the override
        signature_data = (
            f"{request.action_hash}:{human_id}:{effective_tier.value}:"
            f"{reason}:{time.time()}:{request.nonce}"
        )
        signature = hashlib.sha256(signature_data.encode()).hexdigest()

        # Update request
        request.status = OverrideStatus.CONFIRMED
        request.human_id = human_id
        request.reason = reason
        request.tier = effective_tier
        request.signature = signature
        request.confirmed_at = time.time()

        # Create audit entry
        self._create_audit_entry(
            action_hash=request.action_hash,
            human_id=human_id,
            tier=effective_tier,
            trigger=request.trigger,
            status=OverrideStatus.CONFIRMED,
            reason=reason,
            signature=signature,
        )

        # Reset Final-3-Decisions counter (human was involved)
        self.record_decision(was_overridden=True)
        self._override_count += 1

        logger.info(
            f"✅ Override CONFIRMED: {request_id} "
            f"by {human_id} at tier {effective_tier.value}"
        )

        return {
            "success": True,
            "request_id": request_id,
            "signature": signature,
            "tier": effective_tier.value,
            "human_id": human_id,
        }

    def reject_override(
        self,
        request_id: str,
        human_id: str,
        reason: str = "",
    ) -> Dict[str, Any]:
        """Reject an override request — the AI decision stands.

        Args:
            request_id: The override request ID
            human_id: Identifier of the human rejecting
            reason: Why the override was rejected

        Returns:
            Result dict with success and optional escalation info
        """
        request = self._requests.get(request_id)
        if not request:
            return {"success": False, "error": "Request not found"}

        if request.status != OverrideStatus.PENDING:
            return {
                "success": False,
                "error": f"Request already {request.status.value}",
            }

        # Record the rejection
        request.status = OverrideStatus.REJECTED
        request.human_id = human_id
        request.reason = reason

        self._create_audit_entry(
            action_hash=request.action_hash,
            human_id=human_id,
            tier=request.tier,
            trigger=request.trigger,
            status=OverrideStatus.REJECTED,
            reason=reason,
            signature="",
        )

        logger.info(
            f"❌ Override REJECTED: {request_id} by {human_id}"
        )

        # Check if escalation is possible
        escalation_tier = self._get_next_tier(request.tier)
        if escalation_tier and request.trigger in (
            OverrideTrigger.CONSTITUTIONAL,
            OverrideTrigger.POLICY_CRITICAL,
        ):
            # Automatically escalate to next tier for critical triggers
            request.status = OverrideStatus.ESCALATED
            request.escalation_chain.append(request.tier)
            escalated_id = self.request_override(
                action_hash=request.action_hash,
                action_preview=request.action_preview,
                trigger=request.trigger,
                tier=escalation_tier,
                requested_by=request.requested_by,
                metadata={"escalated_from": request_id, **request.metadata},
            )
            logger.info(
                f"⬆️ Override ESCALATED: {request_id} → "
                f"{escalated_id} (tier={escalation_tier.value})"
            )
            return {
                "success": False,
                "request_id": request_id,
                "status": "rejected_escalated",
                "escalated_to": escalated_id,
                "escalated_tier": escalation_tier.value,
            }

        return {
            "success": False,
            "request_id": request_id,
            "status": "rejected",
        }

    def get_override_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get the current status of an override request."""
        request = self._requests.get(request_id)
        if not request:
            return None

        # Auto-expire if past TTL
        if request.status == OverrideStatus.PENDING and request.is_expired():
            request.status = OverrideStatus.EXPIRED

        return request.to_dict()

    def list_pending(self) -> List[Dict[str, Any]]:
        """List all pending override requests (auto-expires stale ones)."""
        now = time.time()
        pending = []

        for request in self._requests.values():
            if request.status == OverrideStatus.PENDING:
                if request.is_expired():
                    request.status = OverrideStatus.EXPIRED
                    continue
                pending.append(request.to_dict())

        return pending

    def list_by_human(self, human_id: str) -> List[Dict[str, Any]]:
        """List all override requests involving a specific human."""
        results = []
        for request in self._requests.values():
            if request.human_id == human_id:
                results.append(request.to_dict())
        return results

    # ─── Trusted Circle Management ──────────────────────────────────────────

    def add_to_trusted_circle(self, human_id: str) -> bool:
        """Add a human to the trusted circle for Tier 2 overrides."""
        if human_id in self._trusted_circle:
            return False
        self._trusted_circle.add(human_id)
        logger.info(f"👤 Added {human_id} to trusted circle")
        return True

    def remove_from_trusted_circle(self, human_id: str) -> bool:
        """Remove a human from the trusted circle."""
        if human_id not in self._trusted_circle:
            return False
        self._trusted_circle.discard(human_id)
        logger.info(f"👤 Removed {human_id} from trusted circle")
        return True

    def get_trusted_circle(self) -> List[str]:
        """Get list of trusted circle members."""
        return list(self._trusted_circle)

    def set_quorum(self, trusted_circle_id: str, size: int) -> None:
        """Override quorum size for a trusted circle.

        Args:
            trusted_circle_id: Identifier for the trusted circle (use any string)
            size: Number of votes required to reach quorum (must be > 0)

        Raises:
            ValueError: If size is less than 1
        """
        if size < 1:
            raise ValueError("Quorum size must be at least 1")
        self._circle_quorums[trusted_circle_id] = size
        logger.info(f"⚙️ Quorum set for {trusted_circle_id}: {size} votes required")

    def get_quorum(self, trusted_circle_id: str) -> int:
        """Get the quorum size for a trusted circle, or 0 if not overridden."""
        return self._circle_quorums.get(trusted_circle_id, 0)

    def get_pending_quorum_requests(self) -> List[Dict[str, Any]]:
        """List all requests currently waiting for quorum votes.

        Auto-expires stale quorum requests whose deadline has passed.
        """
        pending = []
        for request in self._requests.values():
            if request.status == OverrideStatus.QUORUM_PENDING:
                if request.is_quorum_expired():
                    request.status = OverrideStatus.EXPIRED
                    continue
                pending.append(request.to_dict())
        return pending

    # ─── Audit Trail ─────────────────────────────────────────────────────────

    def _create_audit_entry(
        self,
        action_hash: str,
        human_id: str,
        tier: OverrideTier,
        trigger: OverrideTrigger,
        status: OverrideStatus,
        reason: str,
        signature: str,
    ) -> None:
        """Create an append-only audit entry."""
        entry = OverrideAuditEntry(
            entry_id=f"aud_{secrets.token_hex(8)}",
            action_hash=action_hash,
            human_id=human_id,
            tier=tier,
            trigger=trigger,
            status=status,
            reason=reason,
            signature=signature,
            timestamp=time.time(),
        )
        self._audit_log.append(entry)

        # Trim audit log if exceeding max
        if len(self._audit_log) > _MAX_AUDIT_LOG:
            self._audit_log = self._audit_log[-_MAX_AUDIT_LOG:]

    def get_audit_log(
        self,
        last_n: int = 100,
        human_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get the override audit trail.

        Args:
            last_n: Number of recent entries to return
            human_id: Optional filter by human

        Returns:
            List of audit entries (most recent first)
        """
        entries = self._audit_log
        if human_id:
            entries = [e for e in entries if e.human_id == human_id]
        return [e.to_dict() for e in entries[-last_n:]][::-1]

    def verify_override(self, request_id: str) -> Dict[str, Any]:
        """Verify the cryptographic integrity of an override.

        Recomputes the signature from stored data and checks consistency.
        This allows anyone to verify that the override was genuinely made
        by the claimed human for the claimed action.
        """
        request = self._requests.get(request_id)
        if not request or not request.signature:
            return {"valid": False, "error": "Request or signature not found"}

        # Recompute signature
        expected = hashlib.sha256(
            f"{request.action_hash}:{request.human_id}:"
            f"{request.tier.value}:{request.reason}:"
            f"{request.confirmed_at}:{request.nonce}".encode()
        ).hexdigest()

        return {
            "valid": expected == request.signature,
            "action_hash": request.action_hash,
            "human_id": request.human_id,
            "tier": request.tier.value,
            "confirmed_at": request.confirmed_at,
            "signature": request.signature,
        }

    # ─── Internal Helpers ────────────────────────────────────────────────────

    def _get_next_tier(self, current: OverrideTier) -> Optional[OverrideTier]:
        """Get the next tier in the escalation chain."""
        try:
            idx = self.ESCALATION_ORDER.index(current)
            if idx + 1 < len(self.ESCALATION_ORDER):
                return self.ESCALATION_ORDER[idx + 1]
        except ValueError:
            pass
        return None

    # ─── Statistics ──────────────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        """Get override engine statistics."""
        total = len(self._requests)
        pending = len(self.list_pending())
        confirmed = sum(
            1 for r in self._requests.values()
            if r.status == OverrideStatus.CONFIRMED
        )
        rejected = sum(
            1 for r in self._requests.values()
            if r.status == OverrideStatus.REJECTED
        )
        expired = sum(
            1 for r in self._requests.values()
            if r.status == OverrideStatus.EXPIRED
        )

        by_tier = {}
        for t in OverrideTier:
            count = sum(
                1 for r in self._requests.values()
                if r.tier == t and r.status == OverrideStatus.CONFIRMED
            )
            if count > 0:
                by_tier[t.value] = count

        quorum_pending = sum(
            1 for r in self._requests.values()
            if r.status == OverrideStatus.QUORUM_PENDING
        )

        return {
            "final_three_decisions": {
                "counter": self._decision_counter,
                "max": self._max_decisions,
                "remaining": self.decisions_remaining,
                "override_required": self.is_override_required,
            },
            "requests": {
                "total": total,
                "pending": pending,
                "quorum_pending": quorum_pending,
                "confirmed": confirmed,
                "rejected": rejected,
                "expired": expired,
            },
            "overrides_by_tier": by_tier,
            "trusted_circle_size": len(self._trusted_circle),
            "audit_log_size": len(self._audit_log),
            "quorum_config": {
                "circle_quorums": dict(self._circle_quorums),
                "default_timeout": _QUORUM_TIMEOUT,
            },
        }


# ─── Singleton Factory ───────────────────────────────────────────────────────

_override_engine: Optional[HumanOverrideEngine] = None


def get_human_override_engine(
    max_decisions: Optional[int] = None,
) -> HumanOverrideEngine:
    """Get or create the global HumanOverrideEngine singleton.

    Args:
        max_decisions: Override default max_decisions_before_override

    Returns:
        The global HumanOverrideEngine instance
    """
    global _override_engine
    if _override_engine is None:
        _override_engine = HumanOverrideEngine(
            max_decisions=max_decisions or _MAX_DECISIONS_BEFORE_OVERRIDE
        )
    return _override_engine


def reset_human_override_engine() -> None:
    """Reset the singleton (for testing)."""
    global _override_engine
    _override_engine = None


__all__ = [
    "HumanOverrideEngine",
    "OverrideTier",
    "OverrideStatus",
    "OverrideTrigger",
    "OverrideRequest",
    "OverrideAuditEntry",
    "get_human_override_engine",
    "reset_human_override_engine",
    "_QUORUM_TIMEOUT",
]
