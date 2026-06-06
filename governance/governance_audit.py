"""
Governance Audit Trail — AsimNexus Tamper-Evident Governance Audit Log.

Provides an immutable, cryptographically-linked audit trail for all
governance actions (proposals, votes, vetoes, compliance checks,
federation decisions, etc.).  Each audit entry is hashed into a
Merkle-style chain so that tampering with past entries is detectable.

Integration points:
  - Storage: OLTP (OltpEngine) for persistent audit records,
             ClickHouse (AsimNexusEngine) for analytics queries.
  - Consensus: audit entries can reference consensus round IDs.
  - Federation: audit entries can reference federation event IDs.

Usage:
    from governance.governance_audit import GovernanceAudit, AuditEntry

    audit = GovernanceAudit()
    entry = await audit.record(
        action="peer_join_approved",
        actor="did:asim:govnode1",
        resource="federation",
        details={"proposal_id": "...", "peer_did": "..."},
    )
    chain = await audit.verify_chain()
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Environment defaults
# ---------------------------------------------------------------------------

_AUDIT_DB_PATH = os.environ.get(
    "ASIM_GOV_AUDIT_DB_PATH",
    os.path.join(os.path.expanduser("~"), ".asimnexus", "governance_audit.jsonl"),
)
_AUDIT_MAX_ENTRIES = int(os.environ.get("ASIM_GOV_AUDIT_MAX", "100000"))

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class AuditAction(str, Enum):
    """Categorised governance actions that are audited."""
    # Federation
    PEER_JOIN_PROPOSED = "peer_join_proposed"
    PEER_JOIN_APPROVED = "peer_join_approved"
    PEER_JOIN_REJECTED = "peer_join_rejected"
    PEER_LEFT = "peer_left"
    PEER_EJECTED = "peer_ejected"

    # Governance
    LAW_SUBMITTED = "law_submitted"
    LAW_REVIEWED = "law_reviewed"
    LAW_VETOED = "law_vetoed"
    VETO_ABUSE_DETECTED = "veto_abuse_detected"
    GOVERNANCE_DECISION = "governance_decision"
    CONSTITUTION_ANCHORED = "constitution_anchored"
    CONSTITUTION_VERIFIED = "constitution_verified"

    # Consensus
    CONSENSUS_ROUND_STARTED = "consensus_round_started"
    CONSENSUS_ROUND_COMPLETED = "consensus_round_completed"
    CONSENSUS_VETOED = "consensus_vetoed"
    CONSENSUS_HUMAN_OVERRIDE = "consensus_human_override"

    # Compliance
    COMPLIANCE_POLICY_REGISTERED = "compliance_policy_registered"
    COMPLIANCE_CHECK_PASSED = "compliance_check_passed"
    COMPLIANCE_VIOLATION = "compliance_violation"
    COMPLIANCE_VIOLATION_RESOLVED = "compliance_violation_resolved"
    CROSS_BORDER_DATA_FLOW = "cross_border_data_flow"

    # Government
    GOV_ACTION_SUBMITTED = "gov_action_submitted"
    GOV_ACTION_APPROVED = "gov_action_approved"
    GOV_ACTION_REJECTED = "gov_action_rejected"
    GOV_ACTION_ESCALATED = "gov_action_escalated"

    # System
    SYSTEM_STARTED = "system_started"
    SYSTEM_STOPPED = "system_stopped"
    SYSTEM_CONFIG_CHANGED = "system_config_changed"
    SYSTEM_ERROR = "system_error"

    # General
    CUSTOM = "custom"

class AuditIntegrityStatus(str, Enum):
    """Result of an integrity verification."""
    INTACT = "intact"
    BROKEN = "broken"
    EMPTY = "empty"
    UNKNOWN = "unknown"


@dataclass
class AuditEntry:
    """A single audit record in the tamper-evident chain."""

    entry_id: str = field(default_factory=lambda: uuid.uuid4().hex[:20])
    timestamp: float = field(default_factory=time.time)
    action: str = ""                          # AuditAction value
    actor: str = ""                           # DID or system component name
    resource: str = ""                        # Affected resource (e.g. "federation", "compliance")
    details: Dict[str, Any] = field(default_factory=dict)
    severity: str = "INFO"                    # DEBUG / INFO / WARNING / ERROR / CRITICAL

    # Chain linkage
    previous_hash: str = ""                   # sha256 of the previous entry
    entry_hash: str = ""                      # sha256 of (previous_hash + this entry's data)
    chain_length: int = 0

    # Cross-references
    consensus_round_id: Optional[str] = None
    federation_event_id: Optional[str] = None
    proposal_id: Optional[str] = None

    # Metadata
    node_id: str = ""
    version: int = 1

    def compute_hash(self) -> str:
        """Compute the SHA-256 hash of this entry's content."""
        raw = json.dumps({
            "entry_id": self.entry_id,
            "timestamp": self.timestamp,
            "action": self.action,
            "actor": self.actor,
            "resource": self.resource,
            "details": self.details,
            "severity": self.severity,
            "previous_hash": self.previous_hash,
            "chain_length": self.chain_length,
            "consensus_round_id": self.consensus_round_id,
            "federation_event_id": self.federation_event_id,
            "proposal_id": self.proposal_id,
            "node_id": self.node_id,
            "version": self.version,
        }, sort_keys=True, ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["entry_hash"] = self.entry_hash or self.compute_hash()
        return result

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AuditEntry":
        return cls(
            entry_id=d.get("entry_id", ""),
            timestamp=d.get("timestamp", time.time()),
            action=d.get("action", ""),
            actor=d.get("actor", ""),
            resource=d.get("resource", ""),
            details=d.get("details", {}),
            severity=d.get("severity", "INFO"),
            previous_hash=d.get("previous_hash", ""),
            entry_hash=d.get("entry_hash", ""),
            chain_length=d.get("chain_length", 0),
            consensus_round_id=d.get("consensus_round_id"),
            federation_event_id=d.get("federation_event_id"),
            proposal_id=d.get("proposal_id"),
            node_id=d.get("node_id", ""),
            version=d.get("version", 1),
        )


# ---------------------------------------------------------------------------
# GovernanceAudit
# ---------------------------------------------------------------------------

class GovernanceAudit:
    """
    Tamper-evident governance audit trail.

    Each record is hashed and linked to the previous record, forming a
    hash chain.  The chain can be verified at any time to detect
    tampering.

    Thread-safe via asyncio.Lock.  Persisted via JSONL.

    Usage::

        audit = GovernanceAudit(db_path="/path/to/audit.jsonl")
        entry = await audit.record(
            action=AuditAction.PEER_JOIN_APPROVED,
            actor="did:asim:govnode",
            resource="federation",
            details={"peer_did": "did:asim:peer1"},
        )
        report = await audit.verify_chain()
    """

    def __init__(
        self,
        db_path: str = _AUDIT_DB_PATH,
        max_entries: int = _AUDIT_MAX_ENTRIES,
        node_id: str = "",
        oltp_engine: Optional[Any] = None,
        clickhouse_engine: Optional[Any] = None,
    ) -> None:
        self._db_path = db_path
        self._max_entries = max_entries
        self._node_id = node_id or os.environ.get("ASIM_FED_NODE_ID", "")
        self._oltp = oltp_engine
        self._clickhouse = clickhouse_engine

        self._lock = asyncio.Lock()
        self._entries: List[AuditEntry] = []
        self._dirty = False

        # Ensure directory exists
        db_dir = os.path.dirname(self._db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

        # Load existing entries
        self._load_from_db()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def record(
        self,
        action: str,
        actor: str,
        resource: str = "",
        details: Optional[Dict[str, Any]] = None,
        severity: str = "INFO",
        consensus_round_id: Optional[str] = None,
        federation_event_id: Optional[str] = None,
        proposal_id: Optional[str] = None,
    ) -> AuditEntry:
        """Record a new audit entry in the chain."""
        async with self._lock:
            previous_hash = self._entries[-1].entry_hash if self._entries else ""
            chain_length = len(self._entries) + 1

            entry = AuditEntry(
                action=action,
                actor=actor,
                resource=resource,
                details=details or {},
                severity=severity.upper(),
                previous_hash=previous_hash,
                chain_length=chain_length,
                consensus_round_id=consensus_round_id,
                federation_event_id=federation_event_id,
                proposal_id=proposal_id,
                node_id=self._node_id,
            )
            entry.entry_hash = entry.compute_hash()

            self._entries.append(entry)
            self._dirty = True

            # Trim if over max
            if len(self._entries) > self._max_entries:
                overflow = self._entries[:-self._max_entries]
                self._entries = self._entries[-self._max_entries:]
                logger.info("Audit: trimmed %d old entries", len(overflow))

            # Persist immediately
            self._persist_entry(entry)

            # Also persist to OLTP/ClickHouse if available
            if self._oltp is not None:
                await self._persist_to_oltp(entry)
            if self._clickhouse is not None:
                await self._persist_to_clickhouse(entry)

            logger.debug(
                "Audit: recorded %s by %s on %s (chain=%d)",
                action, actor, resource, chain_length,
            )
            return entry

    async def get_entry(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """Get a single audit entry by ID."""
        for entry in self._entries:
            if entry.entry_id == entry_id:
                return entry.to_dict()
        return None

    async def query(
        self,
        action: Optional[str] = None,
        actor: Optional[str] = None,
        resource: Optional[str] = None,
        severity: Optional[str] = None,
        since: Optional[float] = None,
        until: Optional[float] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Query audit entries with optional filters.

        Returns entries sorted by timestamp (newest first).
        """
        filtered = list(self._entries)

        if action:
            filtered = [e for e in filtered if e.action == action]
        if actor:
            filtered = [e for e in filtered if e.actor == actor]
        if resource:
            filtered = [e for e in filtered if e.resource == resource]
        if severity:
            filtered = [e for e in filtered if e.severity == severity.upper()]
        if since is not None:
            filtered = [e for e in filtered if e.timestamp >= since]
        if until is not None:
            filtered = [e for e in filtered if e.timestamp <= until]

        filtered.sort(key=lambda e: e.timestamp, reverse=True)
        return [e.to_dict() for e in filtered[offset:offset + limit]]

    async def verify_chain(self) -> Dict[str, Any]:
        """Verify the integrity of the entire hash chain.

        Returns a report with status and details of any break.
        """
        async with self._lock:
            if not self._entries:
                return {
                    "status": AuditIntegrityStatus.EMPTY.value,
                    "total_entries": 0,
                    "broken_links": [],
                }

            broken_links: List[Dict[str, Any]] = []
            for i, entry in enumerate(self._entries):
                expected_hash = entry.compute_hash()
                if entry.entry_hash != expected_hash:
                    broken_links.append({
                        "index": i,
                        "entry_id": entry.entry_id,
                        "expected_hash": expected_hash,
                        "stored_hash": entry.entry_hash,
                        "reason": "entry_hash mismatch (entry content tampered)",
                    })

                # Verify previous_hash link
                if i > 0:
                    if entry.previous_hash != self._entries[i - 1].entry_hash:
                        broken_links.append({
                            "index": i,
                            "entry_id": entry.entry_id,
                            "expected_prev_hash": self._entries[i - 1].entry_hash,
                            "stored_prev_hash": entry.previous_hash,
                            "reason": "previous_hash mismatch (chain broken)",
                        })

            status = (
                AuditIntegrityStatus.INTACT if not broken_links
                else AuditIntegrityStatus.BROKEN
            )
            return {
                "status": status.value,
                "total_entries": len(self._entries),
                "broken_links": broken_links,
                "verified_at": time.time(),
            }

    async def get_stats(self) -> Dict[str, Any]:
        """Return summary statistics about the audit trail."""
        async with self._lock:
            action_counts: Dict[str, int] = {}
            severity_counts: Dict[str, int] = {}
            actor_set: set = set()

            for entry in self._entries:
                action_counts[entry.action] = action_counts.get(entry.action, 0) + 1
                severity_counts[entry.severity] = severity_counts.get(entry.severity, 0) + 1
                actor_set.add(entry.actor)

            return {
                "total_entries": len(self._entries),
                "unique_actions": len(action_counts),
                "unique_actors": len(actor_set),
                "action_counts": action_counts,
                "severity_counts": severity_counts,
                "db_path": self._db_path,
                "max_entries": self._max_entries,
                "chain_integrity": (await self.verify_chain())["status"],
                "oldest_entry": self._entries[0].timestamp if self._entries else None,
                "newest_entry": self._entries[-1].timestamp if self._entries else None,
            }

    async def get_chain(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Return the most recent entries in the chain."""
        async with self._lock:
            return [
                e.to_dict()
                for e in self._entries[-limit:]
            ]

    async def export(self, filepath: str = "") -> bool:
        """Export all audit entries to a JSON file."""
        filepath = filepath or self._db_path.replace(".jsonl", "_export.json")
        try:
            async with self._lock:
                data = [e.to_dict() for e in self._entries]
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info("Audit exported %d entries to %s", len(data), filepath)
            return True
        except Exception as exc:
            logger.error("Audit export failed: %s", exc)
            return False

    async def clear(self) -> None:
        """Clear all audit entries (for testing)."""
        async with self._lock:
            self._entries.clear()
            self._dirty = True
            # Truncate the database file
            try:
                with open(self._db_path, "w", encoding="utf-8") as f:
                    f.write("")
            except Exception as exc:
                logger.warning("Failed to clear audit db: %s", exc)

    # ------------------------------------------------------------------
    # Persistence (JSONL)
    # ------------------------------------------------------------------

    def _persist_entry(self, entry: AuditEntry) -> None:
        """Append a single entry to the JSONL database."""
        try:
            with open(self._db_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")
        except Exception as exc:
            logger.error("Failed to persist audit entry: %s", exc)

    def _load_from_db(self) -> None:
        """Load all entries from the JSONL database."""
        if not os.path.exists(self._db_path):
            return
        try:
            with open(self._db_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        entry = AuditEntry.from_dict(data)
                        self._entries.append(entry)
                    except json.JSONDecodeError:
                        logger.warning("Skipping malformed audit entry")
                        continue
            logger.info("GovernanceAudit: loaded %d entries from %s",
                        len(self._entries), self._db_path)
        except Exception as exc:
            logger.warning("Failed to load audit db: %s", exc)

    # ------------------------------------------------------------------
    # OLTP / ClickHouse persistence
    # ------------------------------------------------------------------

    async def _persist_to_oltp(self, entry: AuditEntry) -> None:
        """Persist an audit entry to the OLTP engine."""
        if self._oltp is None:
            return
        try:
            await self._oltp.execute(
                """INSERT INTO governance_decisions
                   (id, entry_id, action, actor, resource, details, severity,
                    previous_hash, entry_hash, chain_length, timestamp, node_id)
                   VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9, :10, :11, :12)""",
                (
                    uuid.uuid4().hex[:16],
                    entry.entry_id,
                    entry.action,
                    entry.actor,
                    entry.resource,
                    json.dumps(entry.details),
                    entry.severity,
                    entry.previous_hash,
                    entry.entry_hash,
                    entry.chain_length,
                    entry.timestamp,
                    entry.node_id,
                ),
            )
        except Exception as exc:
            logger.warning("Failed to persist audit entry to OLTP: %s", exc)

    async def _persist_to_clickhouse(self, entry: AuditEntry) -> None:
        """Persist an audit entry to the ClickHouse engine."""
        if self._clickhouse is None:
            return
        try:
            await self._clickhouse.insert(
                "governance_audit",
                {
                    "entry_id": entry.entry_id,
                    "action": entry.action,
                    "actor": entry.actor,
                    "resource": entry.resource,
                    "details": json.dumps(entry.details),
                    "severity": entry.severity,
                    "previous_hash": entry.previous_hash,
                    "entry_hash": entry.entry_hash,
                    "chain_length": entry.chain_length,
                    "timestamp": entry.timestamp,
                    "node_id": entry.node_id,
                },
            )
        except Exception as exc:
            logger.warning("Failed to persist audit entry to ClickHouse: %s", exc)


# ---------------------------------------------------------------------------
# Singleton accessor
# ---------------------------------------------------------------------------

_audit_lock = asyncio.Lock()
_audit_instance: Optional[GovernanceAudit] = None


async def get_governance_audit(
    db_path: str = _AUDIT_DB_PATH,
    oltp_engine: Optional[Any] = None,
    clickhouse_engine: Optional[Any] = None,
) -> GovernanceAudit:
    """Get or create the singleton GovernanceAudit."""
    global _audit_instance
    if _audit_instance is None:
        async with _audit_lock:
            if _audit_instance is None:
                _audit_instance = GovernanceAudit(
                    db_path=db_path,
                    oltp_engine=oltp_engine,
                    clickhouse_engine=clickhouse_engine,
                )
    return _audit_instance


def reset_governance_audit() -> None:
    """Reset the singleton (for testing)."""
    global _audit_instance
    _audit_instance = None
