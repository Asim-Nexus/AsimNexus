"""
ASIMNEXUS Escrow Service
========================
Secure transaction escrow with dispute resolution and timeout-based auto-release.

Pattern: core/economy/contract_executor.py reference
"""

import asyncio
import logging
import json
import uuid
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field, asdict

logger = logging.getLogger("EscrowService")

# ── Types ────────────────────────────────────────────────────────────────────

class EscrowStatus(Enum):
    PENDING = "pending"            # Created, awaiting deposit
    FUNDED = "funded"              # Funds deposited
    IN_DISPUTE = "in_dispute"      # Dispute raised
    RELEASED = "released"          # Released to seller
    REFUNDED = "refunded"          # Refunded to buyer
    EXPIRED = "expired"            # Timed out
    CANCELLED = "cancelled"        # Cancelled by mutual agreement


class DisputeReason(Enum):
    ITEM_NOT_RECEIVED = "item_not_received"
    ITEM_DEFECTIVE = "item_defective"
    MISREPRESENTATION = "misrepresentation"
    NON_PAYMENT = "non_payment"
    OTHER = "other"


# ── Data Models ──────────────────────────────────────────────────────────────

@dataclass
class EscrowTransaction:
    """An escrow transaction."""
    escrow_id: str
    buyer_id: str
    seller_id: str
    token_type: str
    amount: float
    fee: float = 0.0
    status: str = "pending"
    created_at: str = ""
    funded_at: Optional[str] = None
    released_at: Optional[str] = None
    expires_at: Optional[str] = None
    reference: Optional[str] = None
    terms_hash: Optional[str] = None
    arbitrator_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def total_amount(self) -> float:
        return self.amount + self.fee

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EscrowTransaction":
        return cls(**data)


@dataclass
class Dispute:
    """A dispute on an escrow transaction."""
    dispute_id: str
    escrow_id: str
    raised_by: str
    reason: str
    description: str = ""
    status: str = "open"  # open, investigating, resolved
    resolution: Optional[str] = None
    resolved_by: Optional[str] = None
    raised_at: str = ""
    resolved_at: Optional[str] = None
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Dispute":
        return cls(**data)


@dataclass
class EscrowRelease:
    """Record of a fund release."""
    release_id: str
    escrow_id: str
    release_type: str  # release_to_seller, refund_to_buyer, partial
    amount: float
    recipient_id: str
    reason: str = ""
    timestamp: str = ""
    signature: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EscrowRelease":
        return cls(**data)


# ── Escrow Engine ────────────────────────────────────────────────────────────

class EscrowEngine:
    """
    Escrow service managing secure transactions between parties.

    Features:
    - Create escrow with buyer/seller
    - Fund escrow
    - Release to seller on completion
    - Refund to buyer on cancellation
    - Dispute resolution
    - Timeout-based auto-release
    """

    LEDGER_PATH = "data/escrow_ledger.jsonl"
    DEFAULT_TIMEOUT_HOURS = 72  # 3 days

    def __init__(self):
        self._escrows: Dict[str, EscrowTransaction] = {}
        self._disputes: Dict[str, Dispute] = {}
        self._releases: Dict[str, EscrowRelease] = {}
        self._lock = asyncio.Lock()
        self._loaded = False

    # ── Lifecycle ────────────────────────────────────────────────────────

    async def _ensure_loaded(self):
        if not self._loaded:
            await self._load_ledger()
            self._loaded = True

    async def _load_ledger(self):
        from pathlib import Path
        ledger = Path(self.LEDGER_PATH)
        if not ledger.exists():
            ledger.parent.mkdir(parents=True, exist_ok=True)
            return
        try:
            for line in ledger.read_text().strip().split("\n"):
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                    etype = entry.get("_type", "")
                    data = entry["data"]
                    if etype == "escrow":
                        e = EscrowTransaction.from_dict(data)
                        self._escrows[e.escrow_id] = e
                    elif etype == "dispute":
                        d = Dispute.from_dict(data)
                        self._disputes[d.dispute_id] = d
                    elif etype == "release":
                        r = EscrowRelease.from_dict(data)
                        self._releases[r.release_id] = r
                except (json.JSONDecodeError, KeyError):
                    continue
            logger.info(f"Loaded {len(self._escrows)} escrows, {len(self._disputes)} disputes")
        except Exception as e:
            logger.error(f"Failed to load escrow ledger: {e}")

    async def _append_ledger(self, entry_type: str, data: dict):
        from pathlib import Path
        ledger = Path(self.LEDGER_PATH)
        ledger.parent.mkdir(parents=True, exist_ok=True)
        record = json.dumps({"_type": entry_type, "data": data, "_ts": datetime.utcnow().isoformat()})
        async with self._lock:
            with ledger.open("a") as f:
                f.write(record + "\n")

    # ── Core Operations ──────────────────────────────────────────────────

    async def create_escrow(
        self,
        buyer_id: str,
        seller_id: str,
        token_type: str,
        amount: float,
        fee: float = 0.0,
        timeout_hours: int = DEFAULT_TIMEOUT_HOURS,
        reference: str = "",
        terms_hash: str = "",
        arbitrator_id: str = "",
        metadata: Optional[Dict] = None,
    ) -> EscrowTransaction:
        """Create a new escrow transaction."""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if fee < 0:
            raise ValueError("Fee must be non-negative")

        await self._ensure_loaded()
        now = datetime.utcnow()
        expires = now + timedelta(hours=timeout_hours)

        escrow = EscrowTransaction(
            escrow_id=f"esc_{uuid.uuid4().hex[:16]}",
            buyer_id=buyer_id,
            seller_id=seller_id,
            token_type=token_type,
            amount=amount,
            fee=fee,
            status="pending",
            created_at=now.isoformat(),
            expires_at=expires.isoformat(),
            reference=reference,
            terms_hash=terms_hash or "",
            arbitrator_id=arbitrator_id,
            metadata=metadata or {},
        )

        async with self._lock:
            self._escrows[escrow.escrow_id] = escrow
        await self._append_ledger("escrow", escrow.to_dict())
        logger.info(f"Created escrow {escrow.escrow_id}: {amount} {token_type}")
        return escrow

    async def fund_escrow(self, escrow_id: str) -> Tuple[bool, str]:
        """Mark an escrow as funded (buyer deposited)."""
        escrow = await self.get_escrow(escrow_id)
        if not escrow:
            return False, "Escrow not found"
        if escrow.status != "pending":
            return False, f"Escrow is {escrow.status}, not pending"
        if escrow.expires_at and datetime.utcnow().isoformat() > escrow.expires_at:
            escrow.status = "expired"
            await self._append_ledger("escrow", escrow.to_dict())
            return False, "Escrow has expired"

        escrow.status = "funded"
        escrow.funded_at = datetime.utcnow().isoformat()
        await self._append_ledger("escrow", escrow.to_dict())
        logger.info(f"Escrow {escrow_id} funded")
        return True, escrow_id

    async def release_to_seller(
        self,
        escrow_id: str,
        released_by: str = "system",
        reason: str = "completed",
    ) -> Tuple[bool, str]:
        """Release escrow funds to the seller."""
        escrow = await self.get_escrow(escrow_id)
        if not escrow:
            return False, "Escrow not found"
        if escrow.status not in ("funded", "in_dispute"):
            return False, f"Cannot release escrow in status {escrow.status}"

        release = EscrowRelease(
            release_id=f"rel_{uuid.uuid4().hex[:16]}",
            escrow_id=escrow_id,
            release_type="release_to_seller",
            amount=escrow.amount,
            recipient_id=escrow.seller_id,
            reason=reason,
            timestamp=datetime.utcnow().isoformat(),
            metadata={"released_by": released_by},
        )

        escrow.status = "released"
        escrow.released_at = release.timestamp

        async with self._lock:
            self._releases[release.release_id] = release
        await self._append_ledger("release", release.to_dict())
        await self._append_ledger("escrow", escrow.to_dict())
        logger.info(f"Escrow {escrow_id} released to seller {escrow.seller_id}")
        return True, release.release_id

    async def refund_to_buyer(
        self,
        escrow_id: str,
        refunded_by: str = "system",
        reason: str = "cancelled",
        partial_amount: Optional[float] = None,
    ) -> Tuple[bool, str]:
        """Refund escrow funds to the buyer."""
        escrow = await self.get_escrow(escrow_id)
        if not escrow:
            return False, "Escrow not found"
        if escrow.status not in ("funded", "in_dispute", "pending"):
            return False, f"Cannot refund escrow in status {escrow.status}"

        amount = partial_amount if partial_amount is not None else escrow.amount

        release = EscrowRelease(
            release_id=f"rel_{uuid.uuid4().hex[:16]}",
            escrow_id=escrow_id,
            release_type="refund_to_buyer",
            amount=amount,
            recipient_id=escrow.buyer_id,
            reason=reason,
            timestamp=datetime.utcnow().isoformat(),
            metadata={"refunded_by": refunded_by},
        )

        escrow.status = "refunded"
        escrow.released_at = release.timestamp

        async with self._lock:
            self._releases[release.release_id] = release
        await self._append_ledger("release", release.to_dict())
        await self._append_ledger("escrow", escrow.to_dict())
        logger.info(f"Escrow {escrow_id} refunded to buyer {escrow.buyer_id}")
        return True, release.release_id

    # ── Disputes ─────────────────────────────────────────────────────────

    async def raise_dispute(
        self,
        escrow_id: str,
        raised_by: str,
        reason: str,
        description: str = "",
        evidence: Optional[List[Dict]] = None,
    ) -> Tuple[bool, str]:
        """Raise a dispute on an escrow."""
        escrow = await self.get_escrow(escrow_id)
        if not escrow:
            return False, "Escrow not found"
        if raised_by not in (escrow.buyer_id, escrow.seller_id, escrow.arbitrator_id):
            return False, "Only buyer, seller, or arbitrator can raise disputes"
        if escrow.status == "released":
            return False, "Funds already released"
        if escrow.status == "refunded":
            return False, "Funds already refunded"

        dispute = Dispute(
            dispute_id=f"disp_{uuid.uuid4().hex[:16]}",
            escrow_id=escrow_id,
            raised_by=raised_by,
            reason=reason,
            description=description,
            status="open",
            raised_at=datetime.utcnow().isoformat(),
            evidence=evidence or [],
        )

        escrow.status = "in_dispute"

        async with self._lock:
            self._disputes[dispute.dispute_id] = dispute
        await self._append_ledger("dispute", dispute.to_dict())
        await self._append_ledger("escrow", escrow.to_dict())
        logger.info(f"Dispute {dispute.dispute_id} raised on {escrow_id}")
        return True, dispute.dispute_id

    async def resolve_dispute(
        self,
        dispute_id: str,
        resolution: str,
        resolved_by: str,
        release_to_seller: bool = True,
    ) -> Tuple[bool, str]:
        """Resolve a dispute, releasing funds accordingly."""
        dispute = self._disputes.get(dispute_id)
        if not dispute:
            return False, "Dispute not found"
        if dispute.status != "open":
            return False, "Dispute already resolved"

        dispute.status = "resolved"
        dispute.resolution = resolution
        dispute.resolved_by = resolved_by
        dispute.resolved_at = datetime.utcnow().isoformat()

        if release_to_seller:
            result = await self.release_to_seller(
                dispute.escrow_id,
                released_by=resolved_by,
                reason=f"dispute_resolved:{dispute_id}",
            )
        else:
            result = await self.refund_to_buyer(
                dispute.escrow_id,
                refunded_by=resolved_by,
                reason=f"dispute_resolved:{dispute_id}",
            )

        await self._append_ledger("dispute", dispute.to_dict())
        logger.info(f"Dispute {dispute_id} resolved by {resolved_by}")
        return result

    # ── Queries ──────────────────────────────────────────────────────────

    async def get_escrow(self, escrow_id: str) -> Optional[EscrowTransaction]:
        """Get an escrow transaction."""
        await self._ensure_loaded()
        return self._escrows.get(escrow_id)

    async def get_escrows_for_user(
        self, user_id: str, status: Optional[str] = None
    ) -> List[EscrowTransaction]:
        """Get escrows where user is buyer or seller."""
        await self._ensure_loaded()
        result = [
            e for e in self._escrows.values()
            if e.buyer_id == user_id or e.seller_id == user_id
        ]
        if status:
            result = [e for e in result if e.status == status]
        result.sort(key=lambda e: e.created_at, reverse=True)
        return result

    async def get_dispute(self, dispute_id: str) -> Optional[Dispute]:
        """Get a dispute."""
        return self._disputes.get(dispute_id)

    async def get_escrow_disputes(self, escrow_id: str) -> List[Dispute]:
        """Get all disputes for an escrow."""
        return [
            d for d in self._disputes.values()
            if d.escrow_id == escrow_id
        ]

    async def check_expired(self) -> List[str]:
        """Find and expire escrows past their timeout."""
        await self._ensure_loaded()
        now = datetime.utcnow().isoformat()
        expired = []
        for e in self._escrows.values():
            if e.status == "pending" and e.expires_at and e.expires_at < now:
                e.status = "expired"
                await self._append_ledger("escrow", e.to_dict())
                expired.append(e.escrow_id)
        if expired:
            logger.info(f"Expired {len(expired)} escrows")
        return expired

    async def get_stats(self) -> Dict[str, Any]:
        """Get escrow service statistics."""
        await self._ensure_loaded()
        status_counts = {}
        for e in self._escrows.values():
            status_counts[e.status] = status_counts.get(e.status, 0) + 1
        return {
            "total_escrows": len(self._escrows),
            "open_disputes": sum(1 for d in self._disputes.values() if d.status == "open"),
            "resolved_disputes": sum(1 for d in self._disputes.values() if d.status == "resolved"),
            "total_releases": len(self._releases),
            "status_breakdown": status_counts,
        }


# ── Singleton ────────────────────────────────────────────────────────────────

_engine: Optional[EscrowEngine] = None


def get_escrow_engine() -> EscrowEngine:
    """Get or create the singleton escrow engine."""
    global _engine
    if _engine is None:
        _engine = EscrowEngine()
    return _engine


def reset_escrow_engine():
    """Reset the escrow engine (for testing)."""
    global _engine
    _engine = None
