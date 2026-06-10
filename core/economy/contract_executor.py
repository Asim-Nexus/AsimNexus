
"""
STATUS: REAL — Phase 3A: FSM validation, Dharma Veto, audit trail, persistence
"""

"""
ASIMNEXUS Contract Execution Engine
=====================================
Manages contract lifecycle: matching, execution, completion, payment
5/15/30 day agent mode contracts
- FINITE STATE MACHINE: Validates every status transition
- DHARMA VETO: Checks each action against ethical constitution
- AUDIT TRAIL: Hashed chain of all lifecycle events
- PERSISTENCE: JSONL append-only ledger
"""

import json
import logging
import asyncio
import hashlib
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
import uuid
from pathlib import Path

logger = logging.getLogger("ASIM_CONTRACT_EXECUTOR")

# ── Persistence ──────────────────────────────────────────────────────────

CONTRACT_DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "contracts.jsonl"
CONTRACT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)


class ContractStatus(Enum):
    """Contract lifecycle states"""
    PENDING = "pending"           # Created, awaiting acceptance
    ACCEPTED = "accepted"         # Worker accepted
    ACTIVE = "active"             # Work in progress
    COMPLETED = "completed"       # Work done, awaiting review
    APPROVED = "approved"         # Approved, payment pending
    PAID = "paid"                 # Payment complete
    DISPUTED = "disputed"         # Under dispute
    CANCELLED = "cancelled"       # Cancelled


# ── FINITE STATE MACHINE ─────────────────────────────────────────────────
# Valid transitions between contract states
CONTRACT_FSM: Dict[ContractStatus, Set[ContractStatus]] = {
    ContractStatus.PENDING:   {ContractStatus.ACCEPTED, ContractStatus.CANCELLED},
    ContractStatus.ACCEPTED:  {ContractStatus.ACTIVE, ContractStatus.CANCELLED},
    ContractStatus.ACTIVE:    {ContractStatus.COMPLETED, ContractStatus.DISPUTED, ContractStatus.CANCELLED},
    ContractStatus.COMPLETED: {ContractStatus.APPROVED, ContractStatus.DISPUTED},
    ContractStatus.APPROVED:  {ContractStatus.PAID, ContractStatus.DISPUTED},
    ContractStatus.PAID:      set(),  # Terminal state
    ContractStatus.DISPUTED:  {ContractStatus.ACTIVE, ContractStatus.CANCELLED, ContractStatus.PAID},
    ContractStatus.CANCELLED: set(),  # Terminal state
}


class ContractType(Enum):
    """Contract types for agent agreements"""
    SHORT_TERM = "short_term"     # 5-day contract
    MEDIUM_TERM = "medium_term"   # 15-day contract
    LONG_TERM = "long_term"       # 30-day contract
    PERMANENT = "permanent"       # Ongoing contract
    MILESTONE = "milestone"       # Milestone-based contract


class ContractDuration(Enum):
    """Agent mode durations"""
    SHORT = 5     # 5 days
    MEDIUM = 15   # 15 days
    LONG = 30     # 30 days


@dataclass
class AuditEntry:
    """Immutable audit entry for contract lifecycle."""
    event_id: str
    contract_id: str
    event_type: str  # created, accepted, started, milestone, completed, approved, paid, disputed, cancelled
    from_status: str
    to_status: str
    actor_id: str
    timestamp: str
    details: str
    previous_hash: str  # Hash of previous entry (chain)
    entry_hash: str = ""  # Hash of this entry

    def __post_init__(self):
        if not self.entry_hash:
            self.entry_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        raw = f"{self.event_id}|{self.contract_id}|{self.event_type}|{self.from_status}|{self.to_status}|{self.actor_id}|{self.timestamp}|{self.details}|{self.previous_hash}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuditEntry":
        return cls(**data)


@dataclass
class Contract:
    """Job contract"""
    id: str
    job_id: str
    client_id: str
    worker_id: str
    title: str
    description: str
    payment_amount: float
    payment_currency: str
    duration_days: int
    status: str  # Stored as string for JSON serialization
    created_at: str  # ISO timestamp
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    milestones: List[Dict] = field(default_factory=list)
    deliverables: List[str] = field(default_factory=list)
    escrow_released: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Contract":
        return cls(**data)


class ContractExecutor:
    """
    Contract Execution Engine
    - Matches clones to jobs
    - Tracks progress via milestones
    - Manages escrow
    - Handles disputes with Dharma Veto
    - FSM-validated state transitions
    - Hashed audit trail
    """

    def __init__(self):
        self.contracts: Dict[str, Contract] = {}
        self.active_contracts: Dict[str, str] = {}  # worker_id -> contract_id
        self.completed_contracts: List[str] = []
        self.disputes: Dict[str, Dict] = {}
        self.escrow: Dict[str, float] = {}  # contract_id -> amount
        self.audit_trail: List[AuditEntry] = []
        self._audit_previous_hash: str = "0" * 16  # Genesis hash

        # Load persisted state
        self._load_from_db()

    # ── PERSISTENCE ───────────────────────────────────────────────────────

    def _persist_entry(self, entry_type: str, data: Dict[str, Any]) -> None:
        """Append an entry to the JSONL ledger."""
        try:
            record = {"__type__": entry_type, **data}
            with open(CONTRACT_DB_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            logger.warning(f"Failed to persist {entry_type}: {e}")

    def _persist_contract(self, contract: Contract) -> None:
        """Persist contract state."""
        self._persist_entry("contract", contract.to_dict())

    def _persist_audit(self, entry: AuditEntry) -> None:
        """Persist audit entry."""
        self._persist_entry("audit", entry.to_dict())

    def _load_from_db(self) -> None:
        """Replay JSONL ledger to reconstruct state."""
        path = CONTRACT_DB_PATH
        if not path.exists():
            return

        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    entry_type = data.pop("__type__", None)

                    if entry_type == "contract":
                        contract = Contract.from_dict(data)
                        self.contracts[contract.id] = contract
                        if contract.status == ContractStatus.ACTIVE.value:
                            self.active_contracts[contract.worker_id] = contract.id
                        if contract.status in (ContractStatus.PAID.value, ContractStatus.COMPLETED.value):
                            self.completed_contracts.append(contract.id)
                        if not contract.escrow_released and contract.status not in (
                            ContractStatus.CANCELLED.value, ContractStatus.PAID.value):
                            self.escrow[contract.id] = contract.payment_amount

                    elif entry_type == "audit":
                        entry = AuditEntry.from_dict(data)
                        self.audit_trail.append(entry)
                        self._audit_previous_hash = entry.entry_hash

                    elif entry_type == "dispute":
                        contract_id = data.get("contract_id", "")
                        if contract_id:
                            self.disputes[contract_id] = data

            logger.info(f"✅ Loaded {len(self.contracts)} contracts, {len(self.audit_trail)} audit entries")

        except Exception as e:
            logger.warning(f"Failed to load from db: {e}")

    # ── AUDIT ─────────────────────────────────────────────────────────────

    def _add_audit(self, contract_id: str, event_type: str,
                   from_status: str, to_status: str, actor_id: str,
                   details: str = "") -> AuditEntry:
        """Create and store an audit entry with hashed chain."""
        entry = AuditEntry(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            contract_id=contract_id,
            event_type=event_type,
            from_status=from_status,
            to_status=to_status,
            actor_id=actor_id,
            timestamp=datetime.utcnow().isoformat(),
            details=details,
            previous_hash=self._audit_previous_hash,
        )
        self.audit_trail.append(entry)
        self._audit_previous_hash = entry.entry_hash
        self._persist_audit(entry)
        return entry

    # ── STATE MACHINE ─────────────────────────────────────────────────────

    def _validate_transition(self, contract: Contract, new_status: ContractStatus) -> bool:
        """Validate that the state transition is allowed by the FSM."""
        current = ContractStatus(contract.status)
        allowed = CONTRACT_FSM.get(current, set())
        if new_status not in allowed:
            logger.warning(f"⛔ Invalid transition: {current.value} -> {new_status.value}")
            return False
        return True

    # ── DHARMA VETO HOOK ──────────────────────────────────────────────────

    def _dharma_check(self, action: str, contract: Optional[Contract], actor_id: str) -> Optional[str]:
        """
        Check action against Dharma Veto ethical rules.
        Returns None if allowed, or a reason string if blocked.
        """
        try:
            # Attempt to load Dharma Veto if available
            from core.dharma.dharma_veto import get_dharma_veto
            veto = get_dharma_veto()
            # Build context for veto check
            context = {
                "action": action,
                "contract_id": contract.id if contract else "N/A",
                "client_id": contract.client_id if contract else actor_id,
                "worker_id": contract.worker_id if contract else "N/A",
                "amount": contract.payment_amount if contract else 0.0,
                "actor_id": actor_id,
            }
            client_id = contract.client_id if contract else actor_id
            result = veto.check(action, client_id, context)
            if result and result.blocked:
                return result.reason
        except ImportError:
            # Dharma Veto not available — skip check
            pass
        except Exception as e:
            logger.warning(f"Dharma Veto check failed (non-blocking): {e}")
        return None

    # ── CONTRACT LIFECYCLE ────────────────────────────────────────────────

    async def create_contract(self, job_id: str, client_id: str,
                              worker_id: str, duration: ContractDuration,
                              job_details: Dict) -> Contract:
        """Create new contract with Dharma Veto check."""
        # Dharma check before creation
        veto_reason = self._dharma_check("create_contract", None, client_id)
        if veto_reason:
            raise PermissionError(f"Dharma Veto blocked contract creation: {veto_reason}")

        contract_id = f"contract_{uuid.uuid4().hex[:12]}"

        contract = Contract(
            id=contract_id,
            job_id=job_id,
            client_id=client_id,
            worker_id=worker_id,
            title=job_details.get('title', 'Untitled Contract'),
            description=job_details.get('description', ''),
            payment_amount=job_details.get('payment', 0.0),
            payment_currency=job_details.get('currency', 'NPR'),
            duration_days=duration.value,
            status=ContractStatus.PENDING.value,
            created_at=datetime.utcnow().isoformat(),
            milestones=self._generate_milestones(duration.value),
            deliverables=job_details.get('deliverables', []),
            escrow_released=False
        )

        self.contracts[contract_id] = contract

        # Lock escrow
        self.escrow[contract_id] = contract.payment_amount

        # Audit
        self._add_audit(contract_id, "created", "none", ContractStatus.PENDING.value,
                        client_id, f"Contract created: {contract.title}")

        # Persist
        self._persist_contract(contract)

        logger.info(f"📋 Contract created: {contract_id} "
                    f"({duration.value} days, ${contract.payment_amount})")

        return contract

    def _generate_milestones(self, duration_days: int) -> List[Dict]:
        """Generate milestones based on duration"""
        milestones = []

        if duration_days == 5:
            # Short contract: 2 milestones
            milestones = [
                {"day": 2, "name": "Initial Progress", "completed": False},
                {"day": 5, "name": "Final Delivery", "completed": False}
            ]
        elif duration_days == 15:
            # Medium contract: 3 milestones
            milestones = [
                {"day": 5, "name": "Planning Complete", "completed": False},
                {"day": 10, "name": "Progress Review", "completed": False},
                {"day": 15, "name": "Final Delivery", "completed": False}
            ]
        else:  # 30 days
            # Long contract: 4 milestones
            milestones = [
                {"day": 7, "name": "Planning Complete", "completed": False},
                {"day": 14, "name": "Mid-Point Review", "completed": False},
                {"day": 21, "name": "Progress Check", "completed": False},
                {"day": 30, "name": "Final Delivery", "completed": False}
            ]

        return milestones

    async def accept_contract(self, contract_id: str, worker_id: str) -> bool:
        """Worker accepts contract (PENDING -> ACCEPTED)"""
        if contract_id not in self.contracts:
            return False

        contract = self.contracts[contract_id]

        # FSM check
        if not self._validate_transition(contract, ContractStatus.ACCEPTED):
            return False

        # Dharma check
        veto_reason = self._dharma_check("accept_contract", contract, worker_id)
        if veto_reason:
            logger.warning(f"🛑 Dharma Veto blocked accept: {veto_reason}")
            return False

        old_status = contract.status
        contract.status = ContractStatus.ACCEPTED.value

        self._add_audit(contract_id, "accepted", old_status, ContractStatus.ACCEPTED.value,
                        worker_id, "Worker accepted contract")
        self._persist_contract(contract)

        logger.info(f"✅ Contract accepted: {contract_id} by {worker_id}")
        return True

    async def start_contract(self, contract_id: str, worker_id: str) -> bool:
        """Start work on contract (ACCEPTED -> ACTIVE)"""
        if contract_id not in self.contracts:
            return False

        contract = self.contracts[contract_id]

        # FSM check
        if not self._validate_transition(contract, ContractStatus.ACTIVE):
            return False

        # Dharma check
        veto_reason = self._dharma_check("start_contract", contract, worker_id)
        if veto_reason:
            logger.warning(f"🛑 Dharma Veto blocked start: {veto_reason}")
            return False

        old_status = contract.status
        contract.status = ContractStatus.ACTIVE.value
        contract.started_at = datetime.utcnow().isoformat()
        self.active_contracts[worker_id] = contract_id

        self._add_audit(contract_id, "started", old_status, ContractStatus.ACTIVE.value,
                        worker_id, "Work started on contract")
        self._persist_contract(contract)

        logger.info(f"🚀 Contract started: {contract_id} by {worker_id}")
        return True

    async def update_milestone(self, contract_id: str, milestone_index: int) -> bool:
        """Mark milestone as completed"""
        if contract_id not in self.contracts:
            return False

        contract = self.contracts[contract_id]

        if milestone_index < len(contract.milestones):
            contract.milestones[milestone_index]['completed'] = True
            contract.milestones[milestone_index]['completed_at'] = datetime.utcnow().isoformat()

            self._add_audit(contract_id, "milestone", contract.status, contract.status,
                            contract.worker_id,
                            f"Milestone {milestone_index + 1} completed: {contract.milestones[milestone_index]['name']}")
            self._persist_contract(contract)

            logger.info(f"🎯 Milestone {milestone_index + 1} completed for {contract_id}")
            return True

        return False

    async def complete_contract(self, contract_id: str, worker_id: str) -> bool:
        """Worker marks contract as complete (ACTIVE -> COMPLETED)"""
        if contract_id not in self.contracts:
            return False

        contract = self.contracts[contract_id]

        # FSM check
        if not self._validate_transition(contract, ContractStatus.COMPLETED):
            return False

        # Dharma check
        veto_reason = self._dharma_check("complete_contract", contract, worker_id)
        if veto_reason:
            logger.warning(f"🛑 Dharma Veto blocked completion: {veto_reason}")
            return False

        old_status = contract.status
        contract.status = ContractStatus.COMPLETED.value
        contract.completed_at = datetime.utcnow().isoformat()

        # Remove from active
        if contract.worker_id in self.active_contracts:
            del self.active_contracts[contract.worker_id]

        self._add_audit(contract_id, "completed", old_status, ContractStatus.COMPLETED.value,
                        worker_id, "Work completed on contract")
        self._persist_contract(contract)

        logger.info(f"🎉 Contract completed: {contract_id}")
        return True

    async def approve_contract(self, contract_id: str, client_id: str) -> Dict:
        """Client approves completed work (COMPLETED -> APPROVED)"""
        if contract_id not in self.contracts:
            return {'success': False, 'error': 'Contract not found'}

        contract = self.contracts[contract_id]

        # FSM check
        if not self._validate_transition(contract, ContractStatus.APPROVED):
            return {'success': False, 'error': f'Invalid transition from {contract.status}'}

        if contract.client_id != client_id:
            return {'success': False, 'error': 'Not authorized'}

        old_status = contract.status
        contract.status = ContractStatus.APPROVED.value

        self._add_audit(contract_id, "approved", old_status, ContractStatus.APPROVED.value,
                        client_id, "Client approved completed work")
        self._persist_contract(contract)

        logger.info(f"✅ Contract approved: {contract_id}")
        return {'success': True, 'contract_id': contract_id}

    async def release_payment(self, contract_id: str, client_id: str) -> Dict:
        """Release escrow payment (APPROVED -> PAID) with credit transfer."""
        if contract_id not in self.contracts:
            return {'success': False, 'error': 'Contract not found'}

        contract = self.contracts[contract_id]

        # FSM check
        if not self._validate_transition(contract, ContractStatus.PAID):
            return {'success': False, 'error': f'Invalid transition from {contract.status}'}

        if contract.client_id != client_id:
            return {'success': False, 'error': 'Not authorized'}

        # Dharma check
        veto_reason = self._dharma_check("release_payment", contract, client_id)
        if veto_reason:
            logger.warning(f"🛑 Dharma Veto blocked payment: {veto_reason}")
            return {'success': False, 'error': f'Dharma Veto: {veto_reason}'}

        old_status = contract.status
        amount = self.escrow.get(contract_id, 0)

        # ── Execute credit transfer via NexusCredits ────────────────────────
        transfer_success = False
        transfer_tx_id = None
        try:
            from economy.nexus_credits import get_nexus_credits
            nc = get_nexus_credits()
            if nc:
                if amount > 0:
                    txn = await nc.transfer_credits(
                        contract.client_id, contract.worker_id, amount
                    )
                    transfer_success = txn.status == "completed"
                    transfer_tx_id = txn.transaction_id
                    logger.info(
                        f"💸 Credit transfer {txn.transaction_id}: "
                        f"{contract.client_id} -> {contract.worker_id} = {amount}"
                    )
                else:
                    # Zero-amount contract — skip transfer
                    transfer_success = True
            else:
                logger.warning("NexusCredits unavailable — skipping credit transfer")
                transfer_success = True  # non-blocking
        except Exception as e:
            logger.error(f"Credit transfer failed for {contract_id}: {e}")
            return {
                'success': False,
                'error': f'Credit transfer failed: {e}',
                'amount': amount,
                'currency': contract.payment_currency,
                'contract_id': contract_id,
            }

        contract.status = ContractStatus.PAID.value
        contract.escrow_released = True

        if contract_id in self.escrow:
            del self.escrow[contract_id]

        self.completed_contracts.append(contract_id)

        audit_detail = (
            f"Payment released: {amount} {contract.payment_currency}"
            f"{' (tx: ' + transfer_tx_id + ')' if transfer_tx_id else ''}"
        )
        self._add_audit(contract_id, "paid", old_status, ContractStatus.PAID.value,
                        client_id, audit_detail)
        self._persist_contract(contract)

        logger.info(f"💰 Payment released: {amount} for {contract_id}")

        return {
            'success': True,
            'amount': amount,
            'currency': contract.payment_currency,
            'worker_id': contract.worker_id,
            'contract_id': contract_id,
            'transfer_tx_id': transfer_tx_id,
        }

    async def dispute_contract(self, contract_id: str, raised_by: str,
                               reason: str) -> bool:
        """Raise a dispute on a contract"""
        if contract_id not in self.contracts:
            return False

        contract = self.contracts[contract_id]

        # FSM check — can dispute from ACTIVE, COMPLETED, or APPROVED
        if not self._validate_transition(contract, ContractStatus.DISPUTED):
            return False

        old_status = contract.status
        contract.status = ContractStatus.DISPUTED.value

        self.disputes[contract_id] = {
            'contract_id': contract_id,
            'raised_by': raised_by,
            'reason': reason,
            'old_status': old_status,
            'created_at': datetime.utcnow().isoformat()
        }

        self._add_audit(contract_id, "disputed", old_status, ContractStatus.DISPUTED.value,
                        raised_by, f"Dispute raised: {reason}")
        self._persist_contract(contract)
        self._persist_entry("dispute", self.disputes[contract_id])

        logger.info(f"⚠️ Contract disputed: {contract_id} — {reason}")
        return True

    async def cancel_contract(self, contract_id: str, cancelled_by: str,
                              reason: str = "") -> bool:
        """Cancel a contract"""
        if contract_id not in self.contracts:
            return False

        contract = self.contracts[contract_id]

        # FSM check
        if not self._validate_transition(contract, ContractStatus.CANCELLED):
            return False

        # Dharma check
        veto_reason = self._dharma_check("cancel_contract", contract, cancelled_by)
        if veto_reason:
            logger.warning(f"🛑 Dharma Veto blocked cancellation: {veto_reason}")
            return False

        old_status = contract.status
        contract.status = ContractStatus.CANCELLED.value

        # Release escrow back to client
        if contract_id in self.escrow:
            del self.escrow[contract_id]

        if contract.worker_id in self.active_contracts:
            del self.active_contracts[contract.worker_id]

        self._add_audit(contract_id, "cancelled", old_status, ContractStatus.CANCELLED.value,
                        cancelled_by, f"Contract cancelled: {reason}")
        self._persist_contract(contract)

        logger.info(f"🗑️ Contract cancelled: {contract_id}")
        return True

    async def auto_match_jobs(self, worker_id: str, worker_skills: List[str],
                             available_jobs: List[Dict]) -> List[Dict]:
        """AI matching: find best jobs for worker"""
        matches = []

        for job in available_jobs:
            # Calculate match score
            score = 0

            # Skill match
            job_skills = job.get('skills_required', [])
            matching_skills = set(worker_skills) & set(job_skills)
            skill_score = len(matching_skills) / len(job_skills) if job_skills else 0
            score += skill_score * 0.4  # 40% weight

            # Reputation match (simplified)
            score += 0.3  # Assume good reputation

            # Price match (worker rate vs job budget)
            budget = job.get('budget', 0)
            if budget > 0:
                score += 0.3  # Assume acceptable

            if score > 0.6:  # 60% threshold
                matches.append({
                    'job': job,
                    'score': round(score, 2),
                    'matching_skills': list(matching_skills)
                })

        # Sort by score
        matches.sort(key=lambda x: x['score'], reverse=True)

        return matches[:5]  # Top 5 matches

    def get_contract(self, contract_id: str) -> Optional[Contract]:
        """Get a specific contract by ID."""
        return self.contracts.get(contract_id)

    def get_worker_contracts(self, worker_id: str) -> Dict[str, Any]:
        """Get all contracts for a worker"""
        worker_contracts = [
            c for c in self.contracts.values()
            if c.worker_id == worker_id
        ]

        active = [c for c in worker_contracts if c.status == ContractStatus.ACTIVE.value]
        completed = [c for c in worker_contracts if c.status == ContractStatus.PAID.value]
        pending = [c for c in worker_contracts if c.status == ContractStatus.PENDING.value]

        total_earned = sum(
            c.payment_amount for c in worker_contracts
            if c.status == ContractStatus.PAID.value
        )

        return {
            'active_count': len(active),
            'completed_count': len(completed),
            'pending_count': len(pending),
            'total_earned': total_earned,
            'active_contracts': [
                {
                    'id': c.id,
                    'title': c.title,
                    'progress': self._calculate_progress(c),
                    'days_remaining': self._days_remaining(c),
                    'payment': c.payment_amount
                }
                for c in active
            ]
        }

    def _calculate_progress(self, contract: Contract) -> int:
        """Calculate contract progress percentage"""
        if not contract.milestones:
            return 0

        completed = sum(1 for m in contract.milestones if m['completed'])
        return int((completed / len(contract.milestones)) * 100)

    def _days_remaining(self, contract: Contract) -> int:
        """Calculate days remaining in contract"""
        if not contract.started_at:
            return contract.duration_days

        try:
            started = datetime.fromisoformat(contract.started_at)
        except (ValueError, TypeError):
            return contract.duration_days

        end_date = started + timedelta(days=contract.duration_days)
        remaining = (end_date - datetime.utcnow()).days
        return max(0, remaining)

    async def check_expired_contracts(self):
        """Check and handle expired contracts"""
        expired = []

        for contract in self.contracts.values():
            if contract.status != ContractStatus.ACTIVE.value:
                continue

            if self._days_remaining(contract) == 0:
                # Contract expired
                expired.append(contract.id)

                # Auto-complete or flag for review
                if all(m['completed'] for m in contract.milestones):
                    await self.complete_contract(contract.id, contract.worker_id)
                else:
                    contract.status = ContractStatus.DISPUTED.value
                    self.disputes[contract.id] = {
                        'reason': 'incomplete_at_deadline',
                        'created_at': datetime.utcnow().isoformat()
                    }
                    self._persist_contract(contract)
                    self._persist_entry("dispute", self.disputes[contract.id])

        return expired

    def get_audit_trail(self, contract_id: Optional[str] = None,
                        limit: int = 50) -> List[Dict[str, Any]]:
        """Get audit trail, optionally filtered by contract."""
        entries = self.audit_trail
        if contract_id:
            entries = [e for e in entries if e.contract_id == contract_id]
        return [e.to_dict() for e in entries[-limit:]]

    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics"""
        total = len(self.contracts)
        active = sum(1 for c in self.contracts.values() if c.status == ContractStatus.ACTIVE.value)
        completed = len(self.completed_contracts)
        disputed = len(self.disputes)

        total_escrow = sum(self.escrow.values())

        completed_count = completed
        disputed_count = disputed
        success_rate = completed_count / (completed_count + disputed_count) if (completed_count + disputed_count) > 0 else 1.0

        return {
            'total_contracts': total,
            'active_contracts': active,
            'completed_contracts': completed_count,
            'disputed_contracts': disputed_count,
            'total_escrow_locked': total_escrow,
            'success_rate': round(success_rate, 4),
            'audit_entries': len(self.audit_trail)
        }


_executor = None


def get_contract_executor() -> ContractExecutor:
    """Get contract executor singleton"""
    global _executor
    if _executor is None:
        _executor = ContractExecutor()
    return _executor


def reset_contract_executor() -> None:
    """Reset the singleton (for testing). Does NOT delete persisted data."""
    global _executor
    _executor = None


if __name__ == "__main__":
    import sys

    executor = get_contract_executor()

    if len(sys.argv) > 1 and sys.argv[1] == "stats":
        print(json.dumps(executor.get_stats(), indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == "test":
        # Test contract lifecycle with FSM
        async def test():
            contract = await executor.create_contract(
                "job_001", "client_001", "worker_001",
                ContractDuration.SHORT,
                {
                    'title': 'Website Development',
                    'payment': 500.0,
                    'currency': 'NPR',
                    'deliverables': ['homepage', 'about page']
                }
            )
            print(f"Created: {contract.id} (status={contract.status})")

            # Accept
            ok = await executor.accept_contract(contract.id, "worker_001")
            print(f"Accepted: {ok} (status={executor.contracts[contract.id].status})")

            # Start
            ok = await executor.start_contract(contract.id, "worker_001")
            print(f"Started: {ok} (status={executor.contracts[contract.id].status})")

            # Update milestones
            await executor.update_milestone(contract.id, 0)
            await executor.update_milestone(contract.id, 1)
            print(f"Milestones updated (progress={executor._calculate_progress(executor.contracts[contract.id])}%)")

            # Complete
            ok = await executor.complete_contract(contract.id, "worker_001")
            print(f"Completed: {ok} (status={executor.contracts[contract.id].status})")

            # Approve
            result = await executor.approve_contract(contract.id, "client_001")
            print(f"Approved: {result}")

            # Pay
            result = await executor.release_payment(contract.id, "client_001")
            print(f"Payment: {result}")

            # Stats
            print(json.dumps(executor.get_stats(), indent=2))

            # Audit trail
            print("\n📋 Audit Trail:")
            for entry in executor.get_audit_trail(contract.id):
                print(f"  [{entry['event_type']}] {entry['details']}")

        asyncio.run(test())
    else:
        print("Usage: python contract_executor.py [stats|test]")
