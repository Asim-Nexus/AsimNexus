#!/usr/bin/env python3
"""Context Continuum — Seamless context handoff across devices.

The Context Continuum is the core of the Edge AI Continuum, enabling a single
AI agent session to move fluidly across device boundaries. It manages context
snapshots that capture the full conversation history, agent state, mesh network
state, and metadata at any point in time.

Typical usage::

    cm = ContextContinuum()
    snapshot_id = cm.create_snapshot(
        device_type=DeviceType.PWA,
        conversation_history=[{"role": "user", "content": "Hello"}],
        agent_state={"active_task": "greeting"},
        mesh_state={"peers": ["node-1"]},
    )
    restored = cm.restore_snapshot(snapshot_id)
    new_id = cm.transfer_context(DeviceType.PWA, DeviceType.DESKTOP)
    stats = cm.get_stats()
"""

from __future__ import annotations

import copy
import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ── Enums ─────────────────────────────────────────────────────────────────────


class DeviceType(Enum):
    """Device types supported by the Edge AI Continuum.

    Each type represents a class of device with different capabilities,
    form factors, and resource constraints that the context transfer
    logic may account for.
    """
    PWA = auto()        # Progressive Web App (browser-based)
    MOBILE = auto()     # Native mobile application (iOS / Android)
    DESKTOP = auto()    # Desktop application (Electron / Tauri)
    SERVER = auto()     # Backend / cloud server instance
    EMBEDDED = auto()   # IoT / edge device with constrained resources


# ── Data Classes ──────────────────────────────────────────────────────────────


@dataclass
class SessionState:
    """Represents what context state a device currently holds.

    Tracks which device has what context, enabling the continuum to
    coordinate handoffs and prevent conflicting copies.

    Attributes:
        device_type: The type of device holding this state.
        device_id: Unique identifier of the specific device instance.
        active_snapshot_id: ID of the snapshot currently loaded on this device.
        last_activity: ISO-8601 timestamp of the last activity.
        metadata: Additional device-specific metadata (OS version, battery, etc.).
    """
    device_type: DeviceType
    device_id: str
    active_snapshot_id: Optional[str] = None
    last_activity: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.last_activity:
            self.last_activity = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a JSON-compatible dict."""
        return {
            "device_type": self.device_type.name,
            "device_id": self.device_id,
            "active_snapshot_id": self.active_snapshot_id,
            "last_activity": self.last_activity,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionState":
        """Deserialize from a dict produced by ``to_dict()``."""
        data = dict(data)
        if "device_type" in data and isinstance(data["device_type"], str):
            data["device_type"] = DeviceType[data["device_type"]]
        return cls(**data)


@dataclass
class ContextSnapshot:
    """A point-in-time snapshot of conversation/agent context.

    Captures everything needed to resume an AI agent session on another
    device, including the conversation history, current agent state,
    mesh network state, and arbitrary metadata.

    Attributes:
        snapshot_id: Unique identifier for this snapshot.
        device_type: The device type that created this snapshot.
        timestamp: ISO-8601 timestamp of when the snapshot was taken.
        conversation_history: Ordered list of conversation messages.
        agent_state: Current agent state including active tasks, memory pointers.
        mesh_state: Peer connections and sync status for the mesh network.
        metadata: Any additional context (user preferences, UI state, etc.).
    """
    snapshot_id: str
    device_type: DeviceType
    timestamp: str = ""
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    agent_state: Dict[str, Any] = field(default_factory=dict)
    mesh_state: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a JSON-compatible dict."""
        return {
            "snapshot_id": self.snapshot_id,
            "device_type": self.device_type.name,
            "timestamp": self.timestamp,
            "conversation_history": self.conversation_history,
            "agent_state": self.agent_state,
            "mesh_state": self.mesh_state,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContextSnapshot":
        """Deserialize from a dict produced by ``to_dict()``."""
        data = dict(data)
        if "device_type" in data and isinstance(data["device_type"], str):
            data["device_type"] = DeviceType[data["device_type"]]
        return cls(**data)

    @property
    def age_hours(self) -> float:
        """Age of this snapshot in hours."""
        created = datetime.fromisoformat(self.timestamp)
        return (datetime.utcnow() - created).total_seconds() / 3600.0

    @property
    def message_count(self) -> int:
        """Number of messages in the conversation history."""
        return len(self.conversation_history)

    @property
    def summary(self) -> str:
        """A short human-readable summary of the snapshot."""
        return (
            f"Snapshot({self.snapshot_id[:8]}..., "
            f"device={self.device_type.name}, "
            f"msgs={self.message_count}, "
            f"age={self.age_hours:.1f}h)"
        )


# ── Context Continuum ─────────────────────────────────────────────────────────


class ContextContinuum:
    """Manages context snapshots for seamless AI handoff across devices.

    The ContextContinuum is the central orchestrator for the Edge AI
    Continuum. It provides a clean API for creating, restoring, transferring,
    listing, and pruning context snapshots that preserve the full state of
    an AI agent session across device boundaries.

    Features:
    - Create point-in-time snapshots of conversation / agent / mesh state
    - Restore any snapshot by ID with full fidelity
    - Transfer context between device types with automatic adaptation
    - List snapshots with optional device-type filtering
    - Retrieve the latest snapshot for a given device type
    - Prune stale snapshots older than a configurable threshold
    - In-memory storage with optional JSON persistence
    - Per-device session tracking
    """

    def __init__(self, storage_dir: Optional[str] = None):
        self.storage_dir = storage_dir
        if storage_dir:
            os.makedirs(storage_dir, exist_ok=True)

        self._snapshots: Dict[str, ContextSnapshot] = {}
        self._sessions: Dict[str, SessionState] = {}  # device_id -> SessionState
        self._transfer_count: int = 0

        # Load existing snapshots from disk if available
        if storage_dir:
            self._load_from_disk()

    # ── Snapshot Operations ───────────────────────────────────────────────────

    def create_snapshot(
        self,
        device_type: DeviceType,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        agent_state: Optional[Dict[str, Any]] = None,
        mesh_state: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        device_id: str = "",
    ) -> str:
        """Create a new context snapshot.

        Args:
            device_type: The type of device creating this snapshot.
            conversation_history: Ordered list of conversation messages.
            agent_state: Current agent state (active tasks, memory pointers, etc.).
            mesh_state: Peer connections and sync status.
            metadata: Any additional context to preserve.
            device_id: Optional unique identifier for the source device.
                Auto-generated if not provided.

        Returns:
            The snapshot_id of the created snapshot.
        """
        snapshot_id = f"snap-{uuid.uuid4().hex[:16]}"

        snapshot = ContextSnapshot(
            snapshot_id=snapshot_id,
            device_type=device_type,
            conversation_history=conversation_history or [],
            agent_state=agent_state or {},
            mesh_state=mesh_state or {},
            metadata=metadata or {},
        )
        self._snapshots[snapshot_id] = snapshot

        # Update session tracking
        dev_id = device_id or f"device-{uuid.uuid4().hex[:8]}"
        session = self._sessions.get(dev_id)
        if session:
            session.active_snapshot_id = snapshot_id
            session.last_activity = snapshot.timestamp
        else:
            self._sessions[dev_id] = SessionState(
                device_type=device_type,
                device_id=dev_id,
                active_snapshot_id=snapshot_id,
            )

        logger.info(
            "Created snapshot %s (device=%s, msgs=%d)",
            snapshot_id, device_type.name, snapshot.message_count,
        )

        # Persist if storage is configured
        if self.storage_dir:
            self._save_snapshot(snapshot)

        return snapshot_id

    def restore_snapshot(self, snapshot_id: str) -> Optional[ContextSnapshot]:
        """Restore a snapshot by its ID.

        Args:
            snapshot_id: The unique identifier of the snapshot to restore.

        Returns:
            A deep copy of the ContextSnapshot if found, or None if not found.
        """
        snapshot = self._snapshots.get(snapshot_id)
        if not snapshot:
            logger.warning("Snapshot %s not found", snapshot_id)
            return None

        logger.info(
            "Restored snapshot %s (device=%s, msgs=%d)",
            snapshot_id, snapshot.device_type.name, snapshot.message_count,
        )
        return copy.deepcopy(snapshot)

    def transfer_context(
        self,
        from_device: DeviceType,
        to_device: DeviceType,
        from_device_id: str = "",
        to_device_id: str = "",
    ) -> Optional[str]:
        """Transfer the latest context from one device type to another.

        Takes the most recent snapshot from the source device type, adapts
        it for the target device type (by updating metadata), and creates a
        new snapshot on the target.

        Args:
            from_device: The source device type.
            to_device: The target device type.
            from_device_id: Optional specific source device ID.
            to_device_id: Optional specific target device ID.

        Returns:
            The new snapshot_id if a source snapshot was found, else None.
        """
        # Find the latest snapshot from the source device
        source_snapshot = self.get_latest(from_device, device_id=from_device_id)
        if not source_snapshot:
            logger.warning(
                "No snapshot found for source device %s (id=%s)",
                from_device.name, from_device_id or "any",
            )
            return None

        # Adapt the snapshot for the target device
        adapted_metadata = dict(source_snapshot.metadata)
        adapted_metadata.update({
            "transferred_from": from_device.name,
            "transferred_at": datetime.utcnow().isoformat(),
            "original_snapshot_id": source_snapshot.snapshot_id,
        })

        # Optionally trim conversation history for constrained devices
        conversation = source_snapshot.conversation_history
        if to_device in (DeviceType.PWA, DeviceType.MOBILE, DeviceType.EMBEDDED):
            # Keep last 50 messages for resource-constrained devices
            if len(conversation) > 50:
                conversation = conversation[-50:]
                adapted_metadata["history_truncated"] = True
                adapted_metadata["original_message_count"] = source_snapshot.message_count

        new_snapshot_id = self.create_snapshot(
            device_type=to_device,
            conversation_history=conversation,
            agent_state=copy.deepcopy(source_snapshot.agent_state),
            mesh_state=copy.deepcopy(source_snapshot.mesh_state),
            metadata=adapted_metadata,
            device_id=to_device_id,
        )

        self._transfer_count += 1
        logger.info(
            "Transferred context %s -> %s: snapshot %s -> %s",
            from_device.name, to_device.name,
            source_snapshot.snapshot_id, new_snapshot_id,
        )
        return new_snapshot_id

    # ── Listing & Retrieval ───────────────────────────────────────────────────

    def list_snapshots(
        self,
        device_type: Optional[DeviceType] = None,
        limit: int = 50,
    ) -> List[ContextSnapshot]:
        """List snapshots, optionally filtered by device type.

        Args:
            device_type: If provided, only return snapshots for this device type.
            limit: Maximum number of snapshots to return (newest first).

        Returns:
            List of ContextSnapshot objects, sorted newest-first.
        """
        snapshots = list(self._snapshots.values())

        if device_type is not None:
            snapshots = [s for s in snapshots if s.device_type == device_type]

        # Sort newest first
        snapshots.sort(key=lambda s: s.timestamp, reverse=True)
        return snapshots[:limit]

    def get_latest(
        self,
        device_type: DeviceType,
        device_id: str = "",
    ) -> Optional[ContextSnapshot]:
        """Get the latest snapshot for a given device type.

        Args:
            device_type: The device type to query.
            device_id: Optional specific device ID to narrow the search.

        Returns:
            The most recent ContextSnapshot, or None if none found.
        """
        candidates: List[ContextSnapshot] = []

        if device_id:
            # If a specific device ID is given, look up its session
            session = self._sessions.get(device_id)
            if session and session.active_snapshot_id:
                snap = self._snapshots.get(session.active_snapshot_id)
                if snap:
                    candidates = [snap]
        else:
            candidates = [
                s for s in self._snapshots.values()
                if s.device_type == device_type
            ]

        if not candidates:
            return None

        candidates.sort(key=lambda s: s.timestamp, reverse=True)
        return copy.deepcopy(candidates[0])

    def get_snapshot(self, snapshot_id: str) -> Optional[ContextSnapshot]:
        """Get a snapshot by ID (returns the internal reference, not a copy).

        Args:
            snapshot_id: The unique identifier of the snapshot.

        Returns:
            The ContextSnapshot if found, or None.
        """
        return self._snapshots.get(snapshot_id)

    # ── Session Management ────────────────────────────────────────────────────

    def register_device(
        self,
        device_type: DeviceType,
        device_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SessionState:
        """Register a device with the continuum.

        Args:
            device_type: The type of device.
            device_id: Unique identifier for this device instance.
            metadata: Optional device metadata.

        Returns:
            The created or updated SessionState.
        """
        session = self._sessions.get(device_id)
        if session:
            session.last_activity = datetime.utcnow().isoformat()
            if metadata:
                session.metadata.update(metadata)
            logger.info("Updated device registration: %s (%s)", device_id, device_type.name)
        else:
            session = SessionState(
                device_type=device_type,
                device_id=device_id,
                metadata=metadata or {},
            )
            self._sessions[device_id] = session
            logger.info("Registered device: %s (%s)", device_id, device_type.name)

        return session

    def unregister_device(self, device_id: str) -> bool:
        """Remove a device from the continuum.

        Args:
            device_id: The device ID to unregister.

        Returns:
            True if the device was registered and removed, False otherwise.
        """
        if device_id in self._sessions:
            del self._sessions[device_id]
            logger.info("Unregistered device: %s", device_id)
            return True
        return False

    def get_device_sessions(self) -> List[SessionState]:
        """Get all registered device sessions.

        Returns:
            List of all SessionState objects.
        """
        return list(self._sessions.values())

    # ── Pruning ───────────────────────────────────────────────────────────────

    def prune_old(self, max_age_hours: int = 24):
        """Remove snapshots older than *max_age_hours*.

        Args:
            max_age_hours: Snapshots older than this many hours are removed.
        """
        now = datetime.utcnow()
        cutoff = now - timedelta(hours=max_age_hours)
        to_remove: List[str] = []

        for sid, snapshot in self._snapshots.items():
            created = datetime.fromisoformat(snapshot.timestamp)
            if created < cutoff:
                to_remove.append(sid)

        for sid in to_remove:
            del self._snapshots[sid]
            # Remove associated persistence file
            if self.storage_dir:
                file_path = os.path.join(self.storage_dir, f"{sid}.json")
                if os.path.isfile(file_path):
                    try:
                        os.remove(file_path)
                    except OSError as exc:
                        logger.warning("Failed to remove old snapshot file %s: %s", file_path, exc)

        # Also clean up sessions pointing to removed snapshots
        for session in self._sessions.values():
            if session.active_snapshot_id and session.active_snapshot_id not in self._snapshots:
                session.active_snapshot_id = None

        logger.info("Pruned %d old snapshots (max_age=%dh)", len(to_remove), max_age_hours)

    # ── Statistics ────────────────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        """Get aggregated statistics about the context continuum.

        Returns:
            Dict with snapshot count, per-device counts, total transfers, etc.
        """
        per_device: Dict[str, int] = {}
        for snap in self._snapshots.values():
            name = snap.device_type.name
            per_device[name] = per_device.get(name, 0) + 1

        per_device_sessions: Dict[str, int] = {}
        for session in self._sessions.values():
            name = session.device_type.name
            per_device_sessions[name] = per_device_sessions.get(name, 0) + 1

        total_messages = sum(s.message_count for s in self._snapshots.values())
        snapshot_ages = [s.age_hours for s in self._snapshots.values()]

        return {
            "total_snapshots": len(self._snapshots),
            "total_transfers": self._transfer_count,
            "registered_devices": len(self._sessions),
            "total_messages": total_messages,
            "avg_messages_per_snapshot": (
                total_messages / len(self._snapshots) if self._snapshots else 0.0
            ),
            "avg_snapshot_age_hours": (
                sum(snapshot_ages) / len(snapshot_ages) if snapshot_ages else 0.0
            ),
            "snapshots_by_device": per_device,
            "sessions_by_device": per_device_sessions,
            "storage_dir": self.storage_dir,
        }

    # ── Persistence ───────────────────────────────────────────────────────────

    def save(self, dir_path: Optional[str] = None) -> str:
        """Persist all snapshots and sessions to disk.

        Args:
            dir_path: Optional directory path; defaults to ``self.storage_dir``.
                If neither is configured, uses a temporary directory.

        Returns:
            The directory path snapshots were saved to.
        """
        path = dir_path or self.storage_dir
        if not path:
            path = os.path.join(os.path.dirname(__file__), "..", "data", "continuum")
            os.makedirs(path, exist_ok=True)

        if not os.path.isdir(path):
            os.makedirs(path, exist_ok=True)

        # Save each snapshot as an individual file
        for snapshot in self._snapshots.values():
            self._save_snapshot(snapshot, path)

        # Save index with sessions and metadata
        index = {
            "saved_at": datetime.utcnow().isoformat(),
            "snapshot_count": len(self._snapshots),
            "transfer_count": self._transfer_count,
            "sessions": [s.to_dict() for s in self._sessions.values()],
        }
        index_path = os.path.join(path, "index.json")
        try:
            with open(index_path, "w", encoding="utf-8") as f:
                json.dump(index, f, indent=2, default=str)
        except Exception as exc:
            logger.exception("Failed to save continuum index: %s", exc)

        logger.info(
            "Continuum saved to %s (%d snapshots, %d sessions)",
            path, len(self._snapshots), len(self._sessions),
        )
        return path

    def load(self, dir_path: Optional[str] = None) -> int:
        """Load snapshots and sessions from disk, merging with current data.

        Args:
            dir_path: Optional directory path; defaults to ``self.storage_dir``.

        Returns:
            Number of snapshots loaded, or 0 if no data found.
        """
        path = dir_path or self.storage_dir
        if not path or not os.path.isdir(path):
            logger.warning("No continuum data directory found at %s", path)
            return 0

        # Load index
        index_path = os.path.join(path, "index.json")
        if os.path.isfile(index_path):
            try:
                with open(index_path, "r", encoding="utf-8") as f:
                    index = json.load(f)
                for sd in index.get("sessions", []):
                    session = SessionState.from_dict(sd)
                    self._sessions[session.device_id] = session
                self._transfer_count = index.get("transfer_count", 0)
            except Exception as exc:
                logger.warning("Failed to load continuum index: %s", exc)

        # Load individual snapshot files
        loaded = 0
        try:
            for filename in os.listdir(path):
                if filename.startswith("snap-") and filename.endswith(".json"):
                    file_path = os.path.join(path, filename)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        snapshot = ContextSnapshot.from_dict(data)
                        self._snapshots[snapshot.snapshot_id] = snapshot
                        loaded += 1
                    except Exception as exc:
                        logger.warning("Failed to load snapshot %s: %s", filename, exc)
        except Exception as exc:
            logger.exception("Error scanning continuum directory: %s", exc)

        logger.info("Loaded %d snapshots from %s", loaded, path)
        return loaded

    def _save_snapshot(
        self,
        snapshot: ContextSnapshot,
        dir_path: Optional[str] = None,
    ):
        """Persist a single snapshot to disk."""
        path = dir_path or self.storage_dir
        if not path:
            return

        file_path = os.path.join(path, f"{snapshot.snapshot_id}.json")
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(snapshot.to_dict(), f, indent=2, default=str)
        except Exception as exc:
            logger.warning("Failed to save snapshot %s: %s", snapshot.snapshot_id, exc)

    def _load_from_disk(self):
        """Load all snapshots from the configured storage directory."""
        if self.storage_dir and os.path.isdir(self.storage_dir):
            self.load(self.storage_dir)


# ── Factory ───────────────────────────────────────────────────────────────────


def get_context_manager(storage_dir: Optional[str] = None) -> ContextContinuum:
    """Factory function to create a new ContextContinuum instance.

    Args:
        storage_dir: Optional directory path for snapshot persistence.
            If not provided, snapshots are kept only in memory.

    Returns:
        A new ContextContinuum instance.
    """
    return ContextContinuum(storage_dir=storage_dir)
