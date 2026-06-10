"""
AsimNexus Policy Gateway: Actor-Split Immutable Audit Ledger
=============================================================
Records every request with full actor-split schema:
  Requester -> Approver -> Executor -> Policy
Uses cryptographic hash-chaining for tamper-evident logging.

Actor-Split Schema:
  - requester: Who initiated the action (Shell/User)
  - approver: Who approved it (Human/System)
  - executor: Who executed it (Gateway/Kernel/Sandbox)
  - policy_id: Which policy rule was applied

Hash-Chaining:
  Each entry stores previous_hash = SHA256(previous_entry).
  verify_integrity() walks the chain and validates every link.
  Tampering with any entry breaks all subsequent hashes.
"""

import hashlib, json, logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger("AuditLedger")

class AuditAction(Enum):
    REQUEST = "REQUEST"; APPROVE = "APPROVE"; REJECT = "REJECT"
    EXECUTE = "EXECUTE"; ESCALATE = "ESCALATE"; KILL_SWITCH = "KILL_SWITCH"
    ROLLBACK = "ROLLBACK"; POLICY_CHANGE = "POLICY_CHANGE"

@dataclass
class AuditEntry:
    entry_id: str; action: AuditAction; requester: str; approver: str; executor: str
    policy_id: str; capability_id: str; target: str; risk_tier: str; status: str; reason: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    previous_hash: Optional[str] = None; hash: Optional[str] = None

    def compute_hash(self) -> str:
        """Compute SHA256 hash of all entry fields (excluding the hash field itself)."""
        data = {"entry_id": self.entry_id, "action": self.action.value, "requester": self.requester,
                "approver": self.approver, "executor": self.executor, "policy_id": self.policy_id,
                "capability_id": self.capability_id, "target": self.target, "risk_tier": self.risk_tier,
                "status": self.status, "reason": self.reason, "metadata": self.metadata,
                "timestamp": self.timestamp, "previous_hash": self.previous_hash}
        return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Standardized export format for audit entries."""
        return {"entry_id": self.entry_id, "action": self.action.value,
                "requester": self.requester, "approver": self.approver,
                "executor": self.executor, "policy_id": self.policy_id,
                "capability_id": self.capability_id, "target": self.target,
                "risk_tier": self.risk_tier, "status": self.status,
                "reason": self.reason, "metadata": self.metadata,
                "timestamp": self.timestamp,
                "previous_hash": self.previous_hash, "hash": self.hash}

class AuditLedger:
    def __init__(self):
        self._chain: List[AuditEntry] = []
        self._init_genesis()

    def _init_genesis(self):
        """Create the genesis (first) block. Its previous_hash is None."""
        g = AuditEntry(entry_id="genesis-00000000", action=AuditAction.POLICY_CHANGE,
            requester="system", approver="system", executor="system", policy_id="genesis",
            capability_id="system:init", target="system", risk_tier="LOW", status="ALLOWED",
            reason="Genesis block", metadata={"version": "1.0.0"})
        g.previous_hash = None; g.hash = g.compute_hash()
        self._chain.append(g)

    def record(self, action, requester, approver, executor, policy_id, capability_id,
               target, risk_tier, status, reason, metadata=None):
        """Record a new audit entry. Automatically links to previous entry's hash."""
        prev_hash = self._chain[-1].hash if self._chain else None
        eid = f"audit-{hashlib.sha256(f'{requester}:{capability_id}:{target}:{datetime.now(timezone.utc).timestamp()}'.encode()).hexdigest()[:12]}"
        entry = AuditEntry(entry_id=eid, action=action, requester=requester, approver=approver,
            executor=executor, policy_id=policy_id, capability_id=capability_id, target=target,
            risk_tier=risk_tier, status=status, reason=reason, metadata=metadata or {},
            previous_hash=prev_hash)
        entry.hash = entry.compute_hash()
        self._chain.append(entry)
        return entry

    def verify_integrity(self) -> bool:
        """
        Verify the entire hash chain.
        Checks:
          1. Each entry's stored hash matches its computed hash
          2. Each entry's previous_hash matches the previous entry's hash
          3. Genesis block has previous_hash = None
        Returns True if chain is intact, False if tampering detected.
        """
        for i, e in enumerate(self._chain):
            if e.hash != e.compute_hash(): return False
            if i > 0 and e.previous_hash != self._chain[i-1].hash: return False
            if i == 0 and e.previous_hash is not None: return False
        return True

    def detect_tampering(self) -> List[Dict[str, Any]]:
        """Returns list of tampered entries with details."""
        tampered = []
        for i, e in enumerate(self._chain):
            if e.hash != e.compute_hash():
                tampered.append({"index": i, "entry_id": e.entry_id,
                                 "reason": "Hash mismatch", "stored": e.hash,
                                 "computed": e.compute_hash()})
            if i > 0 and e.previous_hash != self._chain[i-1].hash:
                tampered.append({"index": i, "entry_id": e.entry_id,
                                 "reason": "Previous hash broken",
                                 "expected": self._chain[i-1].hash,
                                 "got": e.previous_hash})
        return tampered

    def get_entries(self, requester=None, capability_id=None, status=None, risk_tier=None, limit=100):
        entries = self._chain[1:]  # Skip genesis
        if requester: entries = [e for e in entries if e.requester == requester]
        if capability_id: entries = [e for e in entries if e.capability_id == capability_id]
        if status: entries = [e for e in entries if e.status == status]
        if risk_tier: entries = [e for e in entries if e.risk_tier == risk_tier]
        return entries[-limit:]

    def export_json(self, path: str):
        """Export entire ledger to JSON file with integrity verification."""
        data = [e.to_dict() for e in self._chain]
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"ledger": data, "entry_count": len(data),
                       "verified": self.verify_integrity(),
                       "exported_at": datetime.now(timezone.utc).isoformat()}, f, indent=2)

    def export_entries(self) -> List[Dict[str, Any]]:
        """Standardized export of all audit entries (excluding genesis)."""
        return [e.to_dict() for e in self._chain[1:]]

    def get_stats(self) -> Dict[str, Any]:
        sc, rc = {}, {}
        for e in self._chain[1:]:
            sc[e.status] = sc.get(e.status, 0) + 1
            rc[e.risk_tier] = rc.get(e.risk_tier, 0) + 1
        return {"total_entries": len(self._chain)-1, "status_distribution": sc,
                "risk_distribution": rc, "chain_integrity": self.verify_integrity()}

ledger = AuditLedger()
