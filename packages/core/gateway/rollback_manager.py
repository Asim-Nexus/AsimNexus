"""
AsimNexus Policy Gateway: Rollback Manager
===========================================
Manages system snapshots and rollback operations.
Creates point-in-time snapshots of system state.
Allows reverting to a previous safe state if something goes wrong.

Retention Policy:
  - max_snapshots: Hard limit on total snapshots (default: 50)
  - max_age_days: Auto-delete snapshots older than this (default: 30)
  - On overflow: oldest snapshot is evicted first
  - EMERGENCY snapshots are never auto-evicted
  - PRE_UPGRADE snapshots kept for at least 7 days
"""

import hashlib, json, logging, threading, time as _time
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("RollbackManager")

class SnapshotType(Enum):
    AUTO = "AUTO"; MANUAL = "MANUAL"; PRE_UPGRADE = "PRE_UPGRADE"; EMERGENCY = "EMERGENCY"

class SnapshotState(Enum):
    CREATING = "CREATING"; AVAILABLE = "AVAILABLE"; RESTORING = "RESTORING"; CORRUPTED = "CORRUPTED"

@dataclass
class Snapshot:
    snapshot_id: str; snapshot_type: SnapshotType; state: SnapshotState
    description: str; data: Dict[str, Any]; checksum: str; created_by: str
    parent_snapshot_id: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    restored_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Standardized export format for snapshots."""
        return {"snapshot_id": self.snapshot_id, "snapshot_type": self.snapshot_type.value,
                "state": self.state.value, "description": self.description,
                "checksum": self.checksum, "created_by": self.created_by,
                "parent_snapshot_id": self.parent_snapshot_id,
                "timestamp": self.timestamp, "restored_at": self.restored_at}

@dataclass
class RollbackEvent:
    event_id: str; action: str; snapshot_id: str; initiator: str; reason: str
    success: bool; details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Standardized export format for rollback events."""
        return {"event_id": self.event_id, "action": self.action,
                "snapshot_id": self.snapshot_id, "initiator": self.initiator,
                "reason": self.reason, "success": self.success,
                "details": self.details, "timestamp": self.timestamp}

class RollbackManager:
    _id_counter: int = 0

    def __init__(self, max_snapshots: int = 50, max_age_days: int = 30):
        self._snapshots: Dict[str, Snapshot] = {}
        self._events: List[RollbackEvent] = []
        self._max_snapshots = max_snapshots
        self._max_age_days = max_age_days
        self._state_providers: Dict[str, Callable] = {}
        # Start background retention cleanup
        self._retention_thread = threading.Thread(target=self._enforce_retention_policy, daemon=True)
        self._retention_thread.start()

    def _enforce_retention_policy(self):
        """Background thread that enforces snapshot retention policy every 5 minutes."""
        while True:
            _time.sleep(300)  # Check every 5 minutes
            now = datetime.now(timezone.utc)
            cutoff = now - timedelta(days=self._max_age_days)
            emergency_cutoff = now - timedelta(days=7)  # EMERGENCY kept at least 7 days
            to_delete = []
            for sid, snap in self._snapshots.items():
                try:
                    snap_time = datetime.fromisoformat(snap.timestamp)
                    if snap.snapshot_type == SnapshotType.EMERGENCY:
                        if snap_time < emergency_cutoff:
                            to_delete.append(sid)
                    elif snap.snapshot_type == SnapshotType.PRE_UPGRADE:
                        if snap_time < (now - timedelta(days=7)):
                            to_delete.append(sid)
                    elif snap_time < cutoff:
                        to_delete.append(sid)
                except:
                    to_delete.append(sid)  # Invalid timestamp = delete
            for sid in to_delete:
                self._snapshots.pop(sid, None)
                logger.info(f"Retention: deleted snapshot {sid}")
            # Enforce max_snapshots limit
            while len(self._snapshots) > self._max_snapshots:
                oldest = min(self._snapshots.keys(), key=lambda k: self._snapshots[k].timestamp)
                self._snapshots.pop(oldest, None)
                logger.info(f"Retention: evicted oldest snapshot {oldest}")

    def register_state_provider(self, name: str, provider: Callable) -> None:
        self._state_providers[name] = provider

    def create_snapshot(self, snapshot_type: SnapshotType, description: str,
                        created_by: str, data: Optional[Dict[str, Any]] = None) -> Snapshot:
        if len(self._snapshots) >= self._max_snapshots:
            oldest = min(self._snapshots.keys(), key=lambda k: self._snapshots[k].timestamp)
            del self._snapshots[oldest]
        collected = data or {}
        for name, provider in self._state_providers.items():
            try: collected[name] = provider()
            except Exception as e: logger.warning(f"Provider '{name}' failed: {e}")
        raw = json.dumps(collected, sort_keys=True, default=str)
        checksum = hashlib.sha256(raw.encode()).hexdigest()
        parent = max([s for s in self._snapshots.values() if s.state == SnapshotState.AVAILABLE],
                     key=lambda s: s.timestamp, default=None)
        RollbackManager._id_counter += 1
        sid = f"snap-{hashlib.sha256(f'{created_by}:{datetime.now(timezone.utc).isoformat()}:{RollbackManager._id_counter}'.encode()).hexdigest()[:12]}"
        snapshot = Snapshot(snapshot_id=sid, snapshot_type=snapshot_type, state=SnapshotState.AVAILABLE,
            description=description, data=collected, checksum=checksum, created_by=created_by,
            parent_snapshot_id=parent.snapshot_id if parent else None)
        self._snapshots[sid] = snapshot
        logger.info(f"Snapshot {sid} created ({snapshot_type.value})")
        return snapshot

    def restore_snapshot(self, snapshot_id: str, initiator: str, reason: str) -> bool:
        snapshot = self._snapshots.get(snapshot_id)
        if not snapshot or snapshot.state != SnapshotState.AVAILABLE: return False
        raw = json.dumps(snapshot.data, sort_keys=True, default=str)
        if hashlib.sha256(raw.encode()).hexdigest() != snapshot.checksum:
            snapshot.state = SnapshotState.CORRUPTED; return False
        snapshot.state = SnapshotState.RESTORING
        snapshot.restored_at = datetime.now(timezone.utc).isoformat()
        success = True
        for name, provider in self._state_providers.items():
            if name in snapshot.data:
                try: provider(snapshot.data[name])
                except Exception as e:
                    logger.error(f"Restore failed for '{name}': {e}"); success = False
        if success:
            snapshot.state = SnapshotState.AVAILABLE
            logger.info(f"Restored snapshot {snapshot_id}")
        else:
            snapshot.state = SnapshotState.CORRUPTED
            logger.error(f"Restore partially failed for {snapshot_id}")
        self._events.append(RollbackEvent(
            event_id=f"rb-{datetime.now(timezone.utc).timestamp()}",
            action="RESTORE", snapshot_id=snapshot_id, initiator=initiator,
            reason=reason, success=success))
        return success

    def list_snapshots(self, snapshot_type: Optional[SnapshotType] = None) -> List[Snapshot]:
        snaps = list(self._snapshots.values())
        if snapshot_type: snaps = [s for s in snaps if s.snapshot_type == snapshot_type]
        return sorted(snaps, key=lambda s: s.timestamp, reverse=True)

    def get_snapshot(self, snapshot_id: str) -> Optional[Snapshot]:
        return self._snapshots.get(snapshot_id)

    def delete_snapshot(self, snapshot_id: str) -> bool:
        return bool(self._snapshots.pop(snapshot_id, None))

    def export_snapshots(self) -> List[Dict[str, Any]]:
        """Standardized export of all snapshots."""
        return [s.to_dict() for s in self.list_snapshots()]

    def export_events(self) -> List[Dict[str, Any]]:
        """Standardized export of all rollback events."""
        return [e.to_dict() for e in self._events]

    def get_stats(self) -> Dict[str, Any]:
        return {"total_snapshots": len(self._snapshots),
                "available": sum(1 for s in self._snapshots.values() if s.state == SnapshotState.AVAILABLE),
                "corrupted": sum(1 for s in self._snapshots.values() if s.state == SnapshotState.CORRUPTED),
                "total_events": len(self._events),
                "max_snapshots": self._max_snapshots,
                "max_age_days": self._max_age_days}

rollback_manager = RollbackManager()
