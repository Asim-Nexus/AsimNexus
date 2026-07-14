"""
AsimNexus — Escrow Engine
=========================
Manages escrow transactions, dispute resolution, and timeouts.
"""

import json
import os
import threading
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any


LEDGER_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "escrow_ledger.jsonl"
)


class EscrowStatus(str, Enum):
    PENDING = "pending"
    FUNDED = "funded"
    HELD = "held"
    RELEASED = "released"
    DISPUTED = "disputed"
    IN_DISPUTE = "in_dispute"
    REFUNDED = "refunded"
    EXPIRED = "expired"


class DisputeReason(str, Enum):
    ITEM_NOT_RECEIVED = "item_not_received"
    ITEM_DEFECTIVE = "item_defective"
    MISMATCH = "mismatch"
    MISREPRESENTATION = "misrepresentation"
    FRAUD = "fraud"
    OTHER = "other"


@dataclass
class Dispute:
    dispute_id: str
    escrow_id: str
    raised_by: str
    reason: str
    description: str = ""
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "open"
    resolved: bool = False
    resolution: str = ""
    created_at: float = field(default_factory=lambda: datetime.utcnow().timestamp())
    resolved_at: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dispute_id": self.dispute_id,
            "escrow_id": self.escrow_id,
            "raised_by": self.raised_by,
            "reason": self.reason,
            "description": self.description,
            "evidence": self.evidence,
            "status": self.status,
            "resolved": self.resolved,
            "resolution": self.resolution,
            "created_at": self.created_at,
            "resolved_at": self.resolved_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Dispute":
        return cls(
            dispute_id=data["dispute_id"],
            escrow_id=data["escrow_id"],
            raised_by=data["raised_by"],
            reason=data.get("reason", "other"),
            description=data.get("description", ""),
            evidence=data.get("evidence", []),
            status=data.get("status", "open"),
            resolved=data.get("resolved", False),
            resolution=data.get("resolution", ""),
            created_at=data.get("created_at", 0.0),
            resolved_at=data.get("resolved_at"),
        )


@dataclass
class EscrowRelease:
    release_id: str
    escrow_id: str
    released_by: str
    amount: float
    recipient_id: str = ""
    timestamp: float = field(default_factory=lambda: datetime.utcnow().timestamp())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "release_id": self.release_id,
            "escrow_id": self.escrow_id,
            "released_by": self.released_by,
            "amount": self.amount,
            "recipient_id": self.recipient_id,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EscrowRelease":
        return cls(
            release_id=data["release_id"],
            escrow_id=data["escrow_id"],
            released_by=data.get("released_by", ""),
            amount=data.get("amount", 0.0),
            recipient_id=data.get("recipient_id", ""),
            timestamp=data.get("timestamp", 0.0),
        )


@dataclass
class EscrowTransaction:
    escrow_id: str
    buyer_id: str
    seller_id: str
    token_type: str
    amount: float
    fee: float = 0.0
    total_amount: float = 0.0
    reference: str = ""
    status: str = "pending"
    dispute: Optional[Dispute] = None
    release: Optional[EscrowRelease] = None
    created_at: float = field(default_factory=lambda: datetime.utcnow().timestamp())
    expires_at: Optional[float] = None
    updated_at: float = field(default_factory=lambda: datetime.utcnow().timestamp())
    funded_at: Optional[float] = None
    released_at: Optional[float] = None

    def __post_init__(self):
        if self.total_amount == 0.0 and self.amount > 0:
            self.total_amount = self.amount + self.fee
        if self.expires_at is None:
            self.expires_at = (datetime.utcnow() + timedelta(days=30)).timestamp()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "escrow_id": self.escrow_id,
            "buyer_id": self.buyer_id,
            "seller_id": self.seller_id,
            "token_type": self.token_type,
            "amount": self.amount,
            "fee": self.fee,
            "total_amount": self.total_amount,
            "reference": self.reference,
            "status": self.status,
            "dispute": self.dispute.to_dict() if self.dispute else None,
            "release": asdict(self.release) if self.release else None,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "updated_at": self.updated_at,
            "funded_at": self.funded_at,
            "released_at": self.released_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EscrowTransaction":
        dispute = None
        if data.get("dispute"):
            dispute = Dispute.from_dict(data["dispute"])
        release = None
        if data.get("release"):
            release = EscrowRelease.from_dict(data["release"])
        return cls(
            escrow_id=data["escrow_id"],
            buyer_id=data["buyer_id"],
            seller_id=data["seller_id"],
            token_type=data["token_type"],
            amount=data["amount"],
            fee=data.get("fee", 0.0),
            total_amount=data.get("total_amount", 0.0),
            reference=data.get("reference", ""),
            status=data.get("status", "pending"),
            dispute=dispute,
            release=release,
            created_at=data.get("created_at", 0.0),
            expires_at=data.get("expires_at"),
            updated_at=data.get("updated_at", 0.0),
            funded_at=data.get("funded_at"),
            released_at=data.get("released_at"),
        )


class EscrowEngine:
    """Manages escrow transactions."""

    LEDGER_PATH = LEDGER_PATH

    def __init__(self):
        self._escrows: Dict[str, EscrowTransaction] = {}
        self._disputes: Dict[str, Dispute] = {}
        self._releases: Dict[str, EscrowRelease] = {}
        self._lock = threading.Lock()
        self._load()

    async def create_escrow(
        self,
        buyer_id: str,
        seller_id: str,
        token_type: str,
        amount: float,
        fee: float = 0.0,
        reference: str = "",
        timeout_hours: int = 720,  # 30 days default
        arbitrator_id: str = "",
    ) -> EscrowTransaction:
        """Create a new escrow transaction."""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if fee < 0:
            raise ValueError("Fee must be non-negative")

        expires_at = (datetime.utcnow() + timedelta(hours=timeout_hours)).timestamp()
        escrow = EscrowTransaction(
            escrow_id=f"esc_{uuid.uuid4().hex[:16]}",
            buyer_id=buyer_id,
            seller_id=seller_id,
            token_type=token_type,
            amount=amount,
            fee=fee,
            reference=reference,
            expires_at=expires_at,
        )
        with self._lock:
            self._escrows[escrow.escrow_id] = escrow
            self._persist(escrow)
        return escrow

    async def fund_escrow(self, escrow_id: str) -> tuple:
        """Fund an escrow (mark as funded)."""
        with self._lock:
            escrow = self._escrows.get(escrow_id)
            if not escrow:
                return (False, "Escrow not found")
            if escrow.status != "pending":
                return (False, "Escrow is not pending")
            escrow.status = "funded"
            escrow.funded_at = datetime.utcnow().timestamp()
            escrow.updated_at = datetime.utcnow().timestamp()
            self._persist(escrow)
        return (True, "Escrow funded")

    async def hold(self, escrow_id: str) -> bool:
        """Mark escrow as held (funds deposited)."""
        with self._lock:
            escrow = self._escrows.get(escrow_id)
            if not escrow or escrow.status not in ("pending", "funded"):
                return False
            escrow.status = "held"
            escrow.updated_at = datetime.utcnow().timestamp()
            self._persist(escrow)
        return True

    async def release_to_seller(
        self, escrow_id: str, released_by: str = "system"
    ) -> tuple:
        """Release funds from escrow to seller."""
        with self._lock:
            escrow = self._escrows.get(escrow_id)
            if not escrow or escrow.status not in ("funded", "held"):
                return (False, "Escrow not in fundable state")
            release = EscrowRelease(
                release_id=f"rel_{uuid.uuid4().hex[:16]}",
                escrow_id=escrow_id,
                released_by=released_by,
                amount=escrow.amount,
                recipient_id=escrow.seller_id,
            )
            escrow.status = "released"
            escrow.release = release
            escrow.released_at = datetime.utcnow().timestamp()
            escrow.updated_at = datetime.utcnow().timestamp()
            self._releases[release.release_id] = release
            self._persist(escrow)
        return (True, release.release_id)

    async def refund_to_buyer(
        self,
        escrow_id: str,
        refunded_by: str = "system",
        partial_amount: Optional[float] = None,
        reason: str = "",
    ) -> tuple:
        """Refund escrow to buyer."""
        with self._lock:
            escrow = self._escrows.get(escrow_id)
            if not escrow or escrow.status not in ("funded", "held"):
                return (False, "Escrow not in refundable state")
            escrow.status = "refunded"
            escrow.updated_at = datetime.utcnow().timestamp()
            self._persist(escrow)
        return (True, f"refund_{uuid.uuid4().hex[:16]}")

    async def release(
        self, escrow_id: str, released_by: str
    ) -> Optional[EscrowRelease]:
        """Release funds from escrow to seller (legacy)."""
        with self._lock:
            escrow = self._escrows.get(escrow_id)
            if not escrow or escrow.status not in ("funded", "held"):
                return None
            release = EscrowRelease(
                release_id=f"rel_{uuid.uuid4().hex[:16]}",
                escrow_id=escrow_id,
                released_by=released_by,
                amount=escrow.amount,
                recipient_id=escrow.seller_id,
            )
            escrow.status = "released"
            escrow.release = release
            escrow.released_at = datetime.utcnow().timestamp()
            escrow.updated_at = datetime.utcnow().timestamp()
            self._releases[release.release_id] = release
            self._persist(escrow)
        return release

    async def refund(self, escrow_id: str) -> bool:
        """Refund escrow to buyer (legacy)."""
        with self._lock:
            escrow = self._escrows.get(escrow_id)
            if not escrow or escrow.status not in ("funded", "held", "disputed", "in_dispute"):
                return False
            escrow.status = "refunded"
            escrow.updated_at = datetime.utcnow().timestamp()
            self._persist(escrow)
        return True

    async def raise_dispute(
        self,
        escrow_id: str,
        raised_by: str,
        reason: str = "other",
        description: str = "",
        evidence: Optional[List[Dict[str, Any]]] = None,
    ) -> tuple:
        """Raise a dispute on an escrow."""
        with self._lock:
            escrow = self._escrows.get(escrow_id)
            if not escrow:
                return (False, "Escrow not found")
            if raised_by not in (escrow.buyer_id, escrow.seller_id) and raised_by != "arbitrator":
                return (False, "Unauthorized")
            if escrow.status not in ("funded", "held", "in_dispute"):
                return (False, "Escrow not in disputable state")
            dispute = Dispute(
                dispute_id=f"disp_{uuid.uuid4().hex[:16]}",
                escrow_id=escrow_id,
                raised_by=raised_by,
                reason=reason,
                description=description,
                evidence=evidence or [],
            )
            if escrow.status != "in_dispute":
                escrow.status = "in_dispute"
            escrow.dispute = dispute
            escrow.updated_at = datetime.utcnow().timestamp()
            self._disputes[dispute.dispute_id] = dispute
            self._persist(escrow)
        return (True, dispute.dispute_id)

    async def resolve_dispute(
        self,
        dispute_id: str,
        resolution: str,
        resolved_by: str = "arbitrator",
        release_to_seller: bool = True,
    ) -> tuple:
        """Resolve a dispute."""
        with self._lock:
            dispute = self._disputes.get(dispute_id)
            if not dispute:
                return (False, "Dispute not found")
            if dispute.resolved:
                return (False, "Dispute already resolved")

            escrow = self._escrows.get(dispute.escrow_id)
            if not escrow:
                return (False, "Escrow not found")

            dispute.resolved = True
            dispute.resolution = resolution
            dispute.resolved_at = datetime.utcnow().timestamp()
            dispute.status = "resolved"

            if release_to_seller:
                escrow.status = "released"
                escrow.released_at = datetime.utcnow().timestamp()
            else:
                escrow.status = "refunded"
            escrow.updated_at = datetime.utcnow().timestamp()
            self._persist(escrow)
        return (True, "Dispute resolved")

    async def get_escrow(self, escrow_id: str) -> Optional[EscrowTransaction]:
        """Get escrow by ID."""
        with self._lock:
            return self._escrows.get(escrow_id)

    async def get_dispute(self, dispute_id: str) -> Optional[Dispute]:
        """Get dispute by ID."""
        with self._lock:
            return self._disputes.get(dispute_id)

    async def get_escrow_disputes(self, escrow_id: str) -> List[Dispute]:
        """Get all disputes for an escrow."""
        with self._lock:
            return [d for d in self._disputes.values() if d.escrow_id == escrow_id]

    async def get_escrows_for_user(
        self, user_id: str, status: Optional[str] = None
    ) -> List[EscrowTransaction]:
        """Get escrows where user is buyer or seller, optionally filtered by status."""
        with self._lock:
            results = [
                e for e in self._escrows.values()
                if e.buyer_id == user_id or e.seller_id == user_id
            ]
        if status:
            results = [e for e in results if e.status == status]
        return results

    async def list_escrows(
        self, buyer_id: Optional[str] = None, seller_id: Optional[str] = None
    ) -> List[EscrowTransaction]:
        """List escrows with optional filters."""
        with self._lock:
            results = list(self._escrows.values())
        if buyer_id:
            results = [e for e in results if e.buyer_id == buyer_id]
        if seller_id:
            results = [e for e in results if e.seller_id == seller_id]
        return results

    async def check_expired(self) -> List[str]:
        """Expire escrows past their timeout."""
        expired = []
        now = datetime.utcnow()
        now_ts = now.timestamp()
        with self._lock:
            for escrow_id, escrow in self._escrows.items():
                if escrow.status == "pending" and escrow.expires_at:
                    try:
                        expires_dt = datetime.fromisoformat(escrow.expires_at)
                        if now > expires_dt:
                            escrow.status = "expired"
                            escrow.updated_at = now_ts
                            self._persist(escrow)
                            expired.append(escrow_id)
                    except (ValueError, TypeError):
                        pass
        return expired

    async def get_stats(self) -> Dict[str, Any]:
        """Get escrow statistics."""
        with self._lock:
            total = len(self._escrows)
            open_disputes = sum(
                1 for d in self._disputes.values() if d.status == "open"
            )
            resolved_disputes = sum(
                1 for d in self._disputes.values() if d.status == "resolved"
            )
            return {
                "total_escrows": total,
                "open_disputes": open_disputes,
                "resolved_disputes": resolved_disputes,
            }

    async def _ensure_loaded(self) -> None:
        """Ensure data is loaded (for testing)."""
        self._load()

    def _persist(self, escrow: EscrowTransaction) -> None:
        try:
            os.makedirs(os.path.dirname(self.LEDGER_PATH), exist_ok=True)
            with open(self.LEDGER_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(escrow.to_dict()) + "\n")
        except Exception:
            pass

    def _load(self) -> None:
        try:
            if os.path.exists(self.LEDGER_PATH):
                with open(self.LEDGER_PATH, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                data = json.loads(line)
                                escrow = EscrowTransaction.from_dict(data)
                                self._escrows[escrow.escrow_id] = escrow
                                if escrow.dispute:
                                    self._disputes[escrow.dispute.dispute_id] = escrow.dispute
                                if escrow.release:
                                    self._releases[escrow.release.release_id] = escrow.release
                            except json.JSONDecodeError:
                                pass
        except Exception:
            pass


# Singleton support
_escrow_engine: Optional[EscrowEngine] = None
_escrow_engine_lock = threading.Lock()


def get_escrow_engine() -> EscrowEngine:
    global _escrow_engine
    if _escrow_engine is None:
        with _escrow_engine_lock:
            if _escrow_engine is None:
                _escrow_engine = EscrowEngine()
    return _escrow_engine


def reset_escrow_engine() -> None:
    global _escrow_engine
    _escrow_engine = None
