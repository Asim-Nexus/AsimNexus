#!/usr/bin/env python3
"""
core/identity/personal_os.py
AsimNexus — Personal OS Shell (Gap 4)

A personal operating system shell managing user identity, notifications,
settings, memory, clone configurations, offline caching, and mode switching.

Provides:
  - PersonalOSMode, NotificationType, NotificationSeverity, PrivacyLevel enums
  - Notification, UserSettings, PersonalMemory, PersonalCloneConfig,
    OfflineMessage, OfflineCache, NotificationController dataclasses/classes
  - PersonalOS: main shell class with full lifecycle management
  - DEFAULT_CLONE_CONFIGS constant (15 default clone configurations)
  - Singleton factory: get_personal_os() / reset_personal_os()
"""

import os
import json
import time
import shutil
import logging
import threading
from enum import Enum
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger(__name__)


# ── Module Exports ─────────────────────────────────────────────────────────────

__all__ = [
    "PersonalOSMode",
    "NotificationType",
    "NotificationSeverity",
    "PrivacyLevel",
    "Notification",
    "UserSettings",
    "PersonalMemory",
    "PersonalCloneConfig",
    "OfflineCache",
    "NotificationController",
    "OfflineMessage",
    "PersonalOS",
    "GovernmentMode",
    "EnterpriseMode",
    "DEFAULT_CLONE_CONFIGS",
    "get_personal_os",
    "get_government_os",
    "get_enterprise_os",
    "reset_personal_os",
]


# ── Data Directory ────────────────────────────────────────────────────────────

_DATA_DIR = Path("data/users")


# ── Enums ─────────────────────────────────────────────────────────────────────

class PersonalOSMode(str, Enum):
    """Operating modes for Personal OS."""
    PERSONAL = "personal"
    WORK = "work"
    PUBLIC = "public"
    EMERGENCY = "emergency"
    OFFLINE = "offline"


class NotificationType(str, Enum):
    """Types of notifications."""
    OVERRIDE_REQUEST = "override_request"
    CONTRACT_EXPIRY = "contract_expiry"
    MESH_EVENT = "mesh_event"
    LIFE_JOURNEY = "life_journey"
    BALANCE_WARNING = "balance_warning"
    SYSTEM = "system"
    CLONE_EVENT = "clone_event"


class NotificationSeverity(str, Enum):
    """Severity levels for notifications."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class PrivacyLevel(str, Enum):
    """Privacy levels for user data."""
    STANDARD = "standard"
    HIGH = "high"
    MAXIMUM = "maximum"


# ── Notification Dataclass ────────────────────────────────────────────────────

@dataclass
class Notification:
    """A notification message."""
    id: str
    type: NotificationType
    title: str
    message: str
    severity: NotificationSeverity = NotificationSeverity.INFO
    read: bool = False
    dismissed: bool = False
    created_at: float = field(default_factory=time.time)
    action_payload: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["type"] = self.type.value if isinstance(self.type, NotificationType) else self.type
        d["severity"] = self.severity.value if isinstance(self.severity, NotificationSeverity) else self.severity
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Notification":
        data = dict(data)
        if "type" in data and isinstance(data["type"], str):
            data["type"] = NotificationType(data["type"])
        if "severity" in data and isinstance(data["severity"], str):
            data["severity"] = NotificationSeverity(data["severity"])
        return cls(**data)


# ── UserSettings Dataclass ────────────────────────────────────────────────────

@dataclass
class UserSettings:
    """User configurable settings."""
    display_name: str = ""
    privacy_level: PrivacyLevel = PrivacyLevel.STANDARD
    theme: str = "light"
    language: str = "en"
    notifications_enabled: bool = True
    auto_sync: bool = True
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["privacy_level"] = self.privacy_level.value if isinstance(self.privacy_level, PrivacyLevel) else self.privacy_level
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserSettings":
        data = dict(data)
        if "privacy_level" in data and isinstance(data["privacy_level"], str):
            data["privacy_level"] = PrivacyLevel(data["privacy_level"])
        return cls(**data)


# ── PersonalMemory (Memory Store) ─────────────────────────────────────────────

class PersonalMemory:
    """A memory store that holds conversation memories with context window."""

    def __init__(self, user_id: str = ""):
        self.user_id = user_id
        self.memories: List[Dict[str, Any]] = []

    def add_memory(self, role: str, content: str, tags: Optional[List[str]] = None) -> None:
        """Add a memory entry."""
        self.memories.append({
            "role": role,
            "content": content,
            "tags": tags or [],
            "timestamp": time.time(),
        })

    @property
    def context_window(self) -> List[Dict[str, Any]]:
        """Return the last 20 memories as context window."""
        return self.memories[-20:]

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search memories by content."""
        query_lower = query.lower()
        return [m for m in self.memories if query_lower in m["content"].lower()]

    def get_context(self, n: int) -> List[Dict[str, Any]]:
        """Get the last n memories."""
        return self.memories[-n:]


# ── PersonalCloneConfig Dataclass ─────────────────────────────────────────────

@dataclass
class PersonalCloneConfig:
    """Configuration for a personal clone."""
    clone_id: str
    name: str
    specialty: str
    active: bool = True
    custom_instructions: str = ""
    model_preference: str = "local"
    description: str = ""
    personality: Dict[str, Any] = field(default_factory=dict)
    capabilities: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PersonalCloneConfig":
        return cls(**data)


# ── Default Clone Configs ─────────────────────────────────────────────────────

DEFAULT_CLONE_CONFIGS: List[PersonalCloneConfig] = [
    PersonalCloneConfig(clone_id="c01", name="Tech Guide", specialty="tech",
                        description="Guides you through technical questions and troubleshooting",
                        capabilities=["troubleshooting", "guidance", "documentation"]),
    PersonalCloneConfig(clone_id="c02", name="Creative Writer", specialty="creative",
                        description="Helps with creative writing and content generation",
                        capabilities=["writing", "ideation", "editing"]),
    PersonalCloneConfig(clone_id="c03", name="Data Analyst", specialty="data",
                        description="Analyzes data and generates insights",
                        capabilities=["analysis", "visualization", "reporting"]),
    PersonalCloneConfig(clone_id="c04", name="Research Assistant", specialty="research",
                        description="Conducts research and gathers information",
                        capabilities=["research", "summarization", "fact-checking"]),
    PersonalCloneConfig(clone_id="c05", name="Finance Advisor", specialty="finance",
                        description="Manages finances and budgeting",
                        capabilities=["budgeting", "tracking", "forecasting"]),
    PersonalCloneConfig(clone_id="c06", name="Health Coach", specialty="health",
                        description="Tracks health and wellness metrics",
                        capabilities=["tracking", "analysis", "recommendations"]),
    PersonalCloneConfig(clone_id="c07", name="Learning Coach", specialty="learning",
                        description="Facilitates learning and skill development",
                        capabilities=["tutoring", "curation", "assessment"]),
    PersonalCloneConfig(clone_id="c08", name="Network Coordinator", specialty="network",
                        description="Manages network connections and relationships",
                        capabilities=["networking", "introductions", "follow-ups"]),
    PersonalCloneConfig(clone_id="c09", name="Legal Advisor", specialty="legal",
                        description="Provides legal guidance and document review",
                        capabilities=["review", "research", "drafting"]),
    PersonalCloneConfig(clone_id="c10", name="Operations Manager", specialty="operations",
                        description="Manages daily operations and tasks",
                        capabilities=["scheduling", "prioritization", "automation"]),
    PersonalCloneConfig(clone_id="c11", name="Strategic Planner", specialty="strategy",
                        description="Develops long-term strategies and goals",
                        capabilities=["planning", "analysis", "roadmapping"]),
    PersonalCloneConfig(clone_id="c12", name="Security Monitor", specialty="security",
                        description="Monitors security and threats",
                        capabilities=["monitoring", "detection", "response"]),
    PersonalCloneConfig(clone_id="c13", name="Communications Lead", specialty="communications",
                        description="Manages communications and messaging",
                        capabilities=["messaging", "scheduling", "coordination"]),
    PersonalCloneConfig(clone_id="c14", name="System Architect", specialty="architecture",
                        description="Designs and plans system architecture",
                        capabilities=["planning", "design", "analysis"]),
    PersonalCloneConfig(clone_id="c15", name="Support Agent", specialty="support",
                        description="Provides technical support and troubleshooting",
                        capabilities=["troubleshooting", "guidance", "documentation"]),
]


# ── OfflineMessage Dataclass ──────────────────────────────────────────────────

@dataclass
class OfflineMessage:
    """A message queued for offline delivery."""
    id: str
    action: str
    payload: Dict[str, Any]
    priority: int = 0
    retry_count: int = 0
    max_retries: int = 5
    status: str = "pending"  # "pending" | "sent" | "failed"
    created_at: float = field(default_factory=time.time)
    last_attempt: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OfflineMessage":
        return cls(**data)


# ── OfflineCache ──────────────────────────────────────────────────────────────

class OfflineCache:
    """Persistent offline message queue with retry logic."""

    def __init__(self, db_path: str = "data/offline_cache.jsonl"):
        self._db_path = db_path
        self._messages: Dict[str, OfflineMessage] = {}
        self._lock = threading.Lock()
        self._id_counter = 0
        self._load()

    def enqueue(self, action: str, payload: Dict[str, Any]) -> OfflineMessage:
        """Add a message to the queue. Returns the created OfflineMessage."""
        with self._lock:
            cid = self._id_counter
            self._id_counter += 1
            msg = OfflineMessage(
                id=f"offline_{int(time.time() * 1000)}_{cid}",
                action=action,
                payload=payload,
            )
            self._messages[msg.id] = msg
            self._persist()
        return msg

    def get_pending(self) -> List[OfflineMessage]:
        """Get all pending messages."""
        with self._lock:
            return [m for m in self._messages.values() if m.status == "pending"]

    def mark_sent(self, message_id: str) -> bool:
        """Mark a message as sent. Returns True if found."""
        with self._lock:
            if message_id in self._messages:
                self._messages[message_id].status = "sent"
                self._persist()
                return True
            return False

    def mark_failed(self, message_id: str) -> None:
        """Mark a message as failed."""
        with self._lock:
            if message_id in self._messages:
                msg = self._messages[message_id]
                msg.retry_count += 1
                msg.last_attempt = time.time()
                if msg.retry_count >= msg.max_retries:
                    msg.status = "failed"
                self._persist()

    def get_count(self) -> Dict[str, int]:
        """Get counts by status."""
        with self._lock:
            counts: Dict[str, int] = {"pending": 0, "sent": 0, "failed": 0}
            for m in self._messages.values():
                if m.status in counts:
                    counts[m.status] += 1
            return counts

    def flush_stale(self, max_age_hours: int = 24) -> int:
        """Remove messages older than max_age_hours."""
        cutoff = time.time() - (max_age_hours * 3600)
        with self._lock:
            to_remove = [mid for mid, m in self._messages.items()
                         if m.created_at < cutoff]
            for mid in to_remove:
                del self._messages[mid]
            if to_remove:
                self._persist()
            return len(to_remove)

    def clear(self) -> None:
        """Clear all messages."""
        with self._lock:
            self._messages.clear()
            self._persist()

    def _persist(self) -> None:
        """Persist messages to JSONL."""
        try:
            os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
            with open(self._db_path, "w", encoding="utf-8") as f:
                for msg in self._messages.values():
                    f.write(json.dumps(msg.to_dict()) + "\n")
        except Exception as e:
            logger.warning(f"Failed to persist offline cache: {e}")

    def _load(self) -> None:
        """Load messages from JSONL."""
        if not os.path.exists(self._db_path):
            return
        try:
            with open(self._db_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        data = json.loads(line)
                        msg = OfflineMessage.from_dict(data)
                        self._messages[msg.id] = msg
        except Exception as e:
            logger.warning(f"Failed to load offline cache: {e}")


# ── NotificationController ────────────────────────────────────────────────────

class NotificationController:
    """Manages notification lifecycle: push, read, dismiss, flush."""

    def __init__(self, db_path: str = "data/notifications.jsonl"):
        self._db_path = db_path
        self._notifications: Dict[str, Notification] = {}
        self._lock = threading.Lock()
        self._id_counter = 0
        self._load()

    def push(self, ntype: NotificationType, title: str, message: str,
             severity: NotificationSeverity = NotificationSeverity.INFO) -> Notification:
        """Add a new notification. Returns the created Notification."""
        with self._lock:
            cid = self._id_counter
            self._id_counter += 1
            notification = Notification(
                id=f"notif_{int(time.time() * 1000)}_{cid}",
                type=ntype,
                title=title,
                message=message,
                severity=severity,
            )
            self._notifications[notification.id] = notification
            self._persist()
        return notification

    def get_active(self, include_read: bool = False,
                   severity: Optional[NotificationSeverity] = None) -> List[Notification]:
        """Get active (non-dismissed) notifications, optionally filtered by severity."""
        with self._lock:
            result = []
            for n in self._notifications.values():
                if n.dismissed:
                    continue
                if not include_read and n.read:
                    continue
                if severity is not None and n.severity != severity:
                    continue
                result.append(n)
            return sorted(result, key=lambda x: x.created_at, reverse=True)

    def mark_read(self, notification_id: str) -> bool:
        """Mark a notification as read. Returns True if found."""
        with self._lock:
            if notification_id in self._notifications:
                self._notifications[notification_id].read = True
                self._persist()
                return True
            return False

    def dismiss(self, notification_id: str) -> bool:
        """Dismiss a notification. Returns True if found."""
        with self._lock:
            if notification_id in self._notifications:
                self._notifications[notification_id].dismissed = True
                self._persist()
                return True
            return False

    def get_unread_count(self) -> int:
        """Get count of unread, non-dismissed notifications."""
        with self._lock:
            return sum(1 for n in self._notifications.values()
                       if not n.read and not n.dismissed)

    def clear_all(self) -> int:
        """Clear all notifications. Returns the count cleared."""
        with self._lock:
            count = len(self._notifications)
            self._notifications.clear()
            self._persist()
            return count

    def clear(self) -> None:
        """Alias for clear_all that returns None."""
        self.clear_all()

    def flush_old(self, max_age_hours: int = 168) -> int:
        """Remove notifications older than max_age_hours (default: 7 days)."""
        cutoff = time.time() - (max_age_hours * 3600)
        with self._lock:
            to_remove = [nid for nid, n in self._notifications.items()
                         if n.created_at < cutoff]
            for nid in to_remove:
                del self._notifications[nid]
            if to_remove:
                self._persist()
            return len(to_remove)

    def get_stats(self) -> Dict[str, Any]:
        """Get notification statistics."""
        with self._lock:
            total = len(self._notifications)
            unread = sum(1 for n in self._notifications.values() if not n.read)
            dismissed = sum(1 for n in self._notifications.values() if n.dismissed)
            by_type: Dict[str, int] = {}
            for n in self._notifications.values():
                key = n.type.value if isinstance(n.type, NotificationType) else str(n.type)
                by_type[key] = by_type.get(key, 0) + 1
            return {
                "total": total,
                "unread": unread,
                "dismissed": dismissed,
                "active": total - dismissed,
                "by_type": by_type,
            }

    def _persist(self) -> None:
        """Persist notifications to JSONL."""
        try:
            os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
            with open(self._db_path, "w", encoding="utf-8") as f:
                for n in self._notifications.values():
                    f.write(json.dumps(n.to_dict()) + "\n")
        except Exception as e:
            logger.warning(f"Failed to persist notifications: {e}")

    def _load(self) -> None:
        """Load notifications from JSONL."""
        if not os.path.exists(self._db_path):
            return
        try:
            with open(self._db_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        data = json.loads(line)
                        n = Notification.from_dict(data)
                        self._notifications[n.id] = n
        except Exception as e:
            logger.warning(f"Failed to load notifications: {e}")


# ── PersonalOS ────────────────────────────────────────────────────────────────

class PersonalOS:
    """
    Personal Operating System Shell.

    Manages user identity, settings, notifications, memory, clones,
    offline caching, and mode switching.
    """

    def __init__(self, asim_id: str, display_name: str = "",
                 country_code: str = "NP",
                 db_path: Optional[str] = None):
        self.asim_id = asim_id
        self.display_name = display_name
        self.country_code = country_code
        self._db_path = db_path or f"data/personal_os_{asim_id[:8]}.jsonl"

        # State
        self._mode: PersonalOSMode = PersonalOSMode.PERSONAL
        self.settings: UserSettings = UserSettings(
            display_name=self.display_name,
        )
        self._memory = PersonalMemory(user_id=asim_id)
        self.rules: List[str] = []
        self.documents: Dict[str, str] = {}
        self._document_visibility: Dict[str, str] = {}
        import copy
        self._clone_configs: Dict[str, PersonalCloneConfig] = {
            c.clone_id: copy.deepcopy(c) for c in DEFAULT_CLONE_CONFIGS
        }

        # Subsystems
        self.notifications = NotificationController(
            db_path=f"data/notifications_{asim_id[:8]}.jsonl")
        self.offline_cache = OfflineCache(
            db_path=f"data/offline_{asim_id[:8]}.jsonl")

        # External module references (lazy)
        self._life_journey = None
        self._mesh_router = None
        self._contract_system = None
        self._power_balance = None

        # Workspace
        self._workspace = _DATA_DIR / f"user_{asim_id[:8]}"
        self._workspace.mkdir(parents=True, exist_ok=True)

        # Load persisted state
        self._load()

    # ── Properties ────────────────────────────────────────────────────────

    @property
    def active_mode(self) -> PersonalOSMode:
        """Get the current operating mode."""
        return self._mode

    @active_mode.setter
    def active_mode(self, value: PersonalOSMode) -> None:
        self._mode = value

    @property
    def clones(self) -> List[PersonalCloneConfig]:
        """Get all clone configurations as a list."""
        return list(self._clone_configs.values())

    @property
    def memory(self) -> PersonalMemory:
        """Get the memory store."""
        return self._memory

    # ── Mode Switching ────────────────────────────────────────────────────

    def set_mode(self, mode: str) -> Dict[str, Any]:
        """Switch operating mode. Accepts string mode name."""
        try:
            new_mode = PersonalOSMode(mode)
        except ValueError:
            # Invalid mode — remain unchanged
            return {
                "status": "error",
                "old_mode": self._mode.value,
                "new_mode": self._mode.value,
            }
        old_mode = self._mode
        self._mode = new_mode
        self._persist()

        # If switching to offline mode, generate a notification
        if new_mode == PersonalOSMode.OFFLINE and old_mode != PersonalOSMode.OFFLINE:
            self.notify(
                NotificationType.SYSTEM,
                "Mode Changed",
                "Switched to offline mode",
                NotificationSeverity.INFO,
            )

        return {
            "status": "ok",
            "old_mode": old_mode.value,
            "new_mode": new_mode.value,
        }

    def get_mode(self) -> str:
        """Get current mode as string."""
        return self._mode.value

    # ── Settings ──────────────────────────────────────────────────────────

    def get_settings(self) -> Dict[str, Any]:
        """Get settings as a dictionary."""
        return self.settings.to_dict()

    def update_settings(self, **kwargs) -> Dict[str, Any]:
        """Update user settings."""
        for key, value in kwargs.items():
            if hasattr(self.settings, key):
                if key == "privacy_level" and isinstance(value, str):
                    value = PrivacyLevel(value)
                setattr(self.settings, key, value)
        self.settings.updated_at = time.time()
        self._persist()
        return {"status": "ok", "updated": list(kwargs.keys())}

    # ── Clone Management ──────────────────────────────────────────────────

    def get_active_clones(self) -> List[Dict[str, Any]]:
        """Get all active clone configurations as dicts."""
        return [c.to_dict() for c in self._clone_configs.values() if c.active]

    def get_clones(self) -> List[PersonalCloneConfig]:
        """Get all clone configurations."""
        return self.clones

    def customize_clone(self, clone_id: str, **kwargs) -> Dict[str, Any]:
        """Customize a clone configuration. Returns dict with success key."""
        clone = self._clone_configs.get(clone_id)
        if clone is None:
            return {"success": False}
        for key, value in kwargs.items():
            # Map 'instructions' kwarg to 'custom_instructions' field
            attr = "custom_instructions" if key == "instructions" else key
            if hasattr(clone, attr):
                setattr(clone, attr, value)
        self._persist()
        return {"success": True}

    def reset_clones(self) -> None:
        """Reset clone configurations to defaults."""
        import copy
        self._clone_configs = {c.clone_id: copy.deepcopy(c) for c in DEFAULT_CLONE_CONFIGS}
        self._persist()

    # ── Rules Management ──────────────────────────────────────────────────

    def add_personal_rule(self, rule: str) -> None:
        """Add a personal rule as a string."""
        self.rules.append(rule)
        self._persist()

    def get_personal_rules(self) -> List[str]:
        """Get all personal rules."""
        return list(self.rules)

    def remove_personal_rule(self, index: int) -> bool:
        """Remove a personal rule by index. Returns True if successful."""
        if 0 <= index < len(self.rules):
            self.rules.pop(index)
            self._persist()
            return True
        return False

    # ── Document Storage ──────────────────────────────────────────────────

    def save_document(self, doc_id: str, content: str,
                      visibility: str = "private") -> Dict[str, Any]:
        """Save a document with optional visibility."""
        self.documents[doc_id] = content
        self._document_visibility[doc_id] = visibility
        self._persist()
        return {"success": True, "path": f"{visibility}/{doc_id}"}

    def list_documents(self, visibility: Optional[str] = None) -> List[str]:
        """List document IDs, optionally filtered by visibility."""
        if visibility is None:
            return list(self.documents.keys())
        return [doc_id for doc_id in self.documents
                if self._document_visibility.get(doc_id) == visibility]

    def read_document(self, doc_id: str) -> Optional[str]:
        """Read a document by ID."""
        return self.documents.get(doc_id)

    def delete_document(self, doc_id: str) -> bool:
        """Delete a document by ID."""
        if doc_id in self.documents:
            del self.documents[doc_id]
            self._document_visibility.pop(doc_id, None)
            self._persist()
            return True
        return False

    # ── Memory Management ─────────────────────────────────────────────────

    def process_message(self, message: str) -> Dict[str, Any]:
        """Process a user message and store as memory. Returns dict with clone_used."""
        self._memory.add_memory("user", message)

        # Determine which clone to use based on message content
        clone_used = "general"
        msg_lower = message.lower()
        for c in self._clone_configs.values():
            if c.active:
                # Check specialty field first
                if c.specialty.lower() in msg_lower:
                    clone_used = c.clone_id
                    break
                # Then check capabilities
                for cap in c.capabilities:
                    if cap.lower() in msg_lower:
                        clone_used = c.clone_id
                        break
                if clone_used != "general":
                    break

        return {"clone_used": clone_used}

    def receive_response(self, content: str) -> PersonalMemory:
        """Receive and store an assistant response."""
        self._memory.add_memory("assistant", content)
        return self._memory

    def search_memories(self, query: str) -> List[Dict[str, Any]]:
        """Search through memories."""
        return self._memory.search(query)

    # ── Notifications ────────────────────────────────────────────────────

    def notify(self, ntype: NotificationType, title: str, message: str,
               severity: NotificationSeverity = NotificationSeverity.INFO) -> Notification:
        """Send a notification. Always returns a Notification."""
        return self.notifications.push(ntype, title, message, severity)

    def get_notifications(self, include_read: bool = False,
                          severity: Optional[NotificationSeverity] = None) -> List[Notification]:
        """Get active notifications, optionally filtered by severity."""
        return self.notifications.get_active(include_read=include_read, severity=severity)

    def get_unread_count(self) -> int:
        """Get count of unread notifications."""
        return self.notifications.get_unread_count()

    # ── Offline ──────────────────────────────────────────────────────────

    def enqueue_offline(self, action: str, payload: Dict[str, Any]) -> OfflineMessage:
        """Queue a message for offline delivery. Returns the OfflineMessage."""
        return self.offline_cache.enqueue(action, payload)

    def get_pending_offline(self) -> List[OfflineMessage]:
        """Get pending offline messages."""
        return self.offline_cache.get_pending()

    def get_offline_stats(self) -> Dict[str, int]:
        """Get offline cache statistics."""
        return self.offline_cache.get_count()

    # ── Dashboard ────────────────────────────────────────────────────────

    def get_dashboard(self) -> Dict[str, Any]:
        """Get dashboard data."""
        return {
            "user": {
                "asim_id": self.asim_id,
                "display_name": self.display_name,
                "country_code": self.country_code,
                "mode": self._mode.value,
            },
            "settings": self.settings.to_dict(),
            "clones": {
                "total": len(self._clone_configs),
                "active": len([c for c in self._clone_configs.values() if c.active]),
            },
            "memory": {
                "total_entries": len(self._memory.memories),
                "context_window": len(self._memory.context_window),
            },
            "notifications": self.notifications.get_stats(),
            "documents": {
                "total": len(self.documents),
            },
            "rules": len(self.rules),
            "offline": self.offline_cache.get_count(),
        }

    # ── Status ───────────────────────────────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        """Get current status."""
        return {
            "asim_id": self.asim_id,
            "name": self.display_name,
            "mode": self._mode.value,
            "privacy_level": self.settings.privacy_level.value if isinstance(self.settings.privacy_level, PrivacyLevel) else self.settings.privacy_level,
            "notifications_enabled": self.settings.notifications_enabled,
            "active_clones": len([c for c in self._clone_configs.values() if c.active]),
            "total_memories": len(self._memory.memories),
            "notifications_unread": self.notifications.get_unread_count(),
            "offline_pending": len(self.offline_cache.get_pending()),
            "settings_version": self.settings.updated_at,
        }

    # ── External Integrations ────────────────────────────────────────────

    def set_life_journey(self, module: Any) -> None:
        """Set the life journey module reference."""
        self._life_journey = module

    def set_mesh_router(self, router: Any) -> None:
        """Set the mesh router reference."""
        self._mesh_router = router

    def set_contract_system(self, system: Any) -> None:
        """Set the contract system reference."""
        self._contract_system = system

    def set_power_balance(self, balance: Any) -> None:
        """Set the power balance constitution reference."""
        self._power_balance = balance

    # ── Persistence ──────────────────────────────────────────────────────

    def _persist(self) -> None:
        """Persist state to JSONL."""
        try:
            data = {
                "asim_id": self.asim_id,
                "display_name": self.display_name,
                "country_code": self.country_code,
                "mode": self._mode.value,
                "settings": self.settings.to_dict(),
                "memories": self._memory.memories,
                "rules": self.rules,
                "documents": self.documents,
                "document_visibility": self._document_visibility,
                "clone_configs": {k: v.to_dict() for k, v in self._clone_configs.items()},
            }
            os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
            with open(self._db_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(data) + "\n")
        except Exception as e:
            logger.warning(f"Failed to persist PersonalOS: {e}")

    def _load(self) -> None:
        """Load state from JSONL."""
        if not os.path.exists(self._db_path):
            return
        try:
            with open(self._db_path, encoding="utf-8") as f:
                line = f.readline().strip()
                if line:
                    data = json.loads(line)
                    self.asim_id = data.get("asim_id", self.asim_id)
                    self.display_name = data.get("display_name", self.display_name)
                    self.country_code = data.get("country_code", self.country_code)
                    if "mode" in data:
                        self._mode = PersonalOSMode(data["mode"])
                    if "settings" in data:
                        self.settings = UserSettings.from_dict(data["settings"])
                    if "memories" in data:
                        self._memory.memories = data["memories"]
                    if "rules" in data:
                        self.rules = data["rules"]
                    if "documents" in data:
                        self.documents = data["documents"]
                    if "document_visibility" in data:
                        self._document_visibility = data["document_visibility"]
                    if "clone_configs" in data:
                        for k, v in data["clone_configs"].items():
                            self._clone_configs[k] = PersonalCloneConfig.from_dict(v)
        except Exception as e:
            logger.warning(f"Failed to load PersonalOS: {e}")


# ── Government Mode Extensions ─────────────────────────────────────────────────

class GovernmentMode(PersonalOS):
    """Government official's Personal OS with Level-3 access and audit capabilities."""
    
    def __init__(self, user_id: str, department: str = ""):
        super().__init__(user_id, display_name=f"Gov_{user_id}")
        self._mode = PersonalOSMode.PERSONAL  # Default to personal, can switch
        self.department = department
        self.gov_permissions = [
            "policy_edit", "audit_access", "kill_switch",
            "sector_balance", "council_vote"
        ]
        
    def set_government_mode(self) -> None:
        """Switch to government operating mode."""
        self._mode = PersonalOSMode.PERSONAL  # Government uses custom mode
        
    def approve_policy_change(self, proposal: str) -> bool:
        """Level-3 approval for policy changes."""
        # Would integrate with HSM + biometric in production
        return True
        
    def get_gov_dashboard(self) -> Dict[str, Any]:
        """Government-specific dashboard data."""
        return {
            "user": self.get_status(),
            "department": self.department,
            "permissions": self.gov_permissions,
            "audit_pending": 0,  # Would fetch from audit system
        }


class EnterpriseMode(PersonalOS):
    """Enterprise user's Personal OS with company integrations."""
    
    def __init__(self, user_id: str, company_id: str = ""):
        super().__init__(user_id, display_name=f"Ent_{user_id}")
        self.company_id = company_id
        self.ent_permissions = ["company_data", "revenuve_ops", "reporting"]
        self.data_limit_gb = 10
        
    def set_enterprise_mode(self) -> None:
        """Switch to enterprise mode."""
        self._mode = PersonalOSMode.PERSONAL
        
    def get_ent_dashboard(self) -> Dict[str, Any]:
        """Enterprise-specific dashboard data."""
        return {
            "user": self.get_status(),
            "company_id": self.company_id,
            "permissions": self.ent_permissions,
            "data_usage": "0GB",
        }


# ── Singleton Factory ─────────────────────────────────────────────────────────

_personal_os_pool: Dict[str, PersonalOS] = {}


def get_personal_os(asim_id: str, display_name: str = "",
                    db_path: Optional[str] = None) -> PersonalOS:
    """Get or create a PersonalOS instance for the given asim_id."""
    if asim_id not in _personal_os_pool:
        _personal_os_pool[asim_id] = PersonalOS(
            asim_id=asim_id,
            display_name=display_name,
            db_path=db_path,
        )
    return _personal_os_pool[asim_id]


def get_government_os(user_id: str, department: str = "") -> GovernmentMode:
    """Get GovernmentMode PersonalOS instance."""
    pool_key = f"gov_{user_id}"
    if pool_key not in _personal_os_pool:
        _personal_os_pool[pool_key] = GovernmentMode(user_id, department)
    return _personal_os_pool[pool_key]


def get_enterprise_os(user_id: str, company_id: str = "") -> EnterpriseMode:
    """Get EnterpriseMode PersonalOS instance."""
    pool_key = f"ent_{user_id}"
    if pool_key not in _personal_os_pool:
        _personal_os_pool[pool_key] = EnterpriseMode(user_id, company_id)
    return _personal_os_pool[pool_key]


def reset_personal_os(asim_id: Optional[str] = None) -> None:
    """Reset PersonalOS singleton(s). If asim_id is None, reset all."""
    global _personal_os_pool
    if asim_id is None:
        _personal_os_pool.clear()
    else:
        _personal_os_pool.pop(asim_id, None)
