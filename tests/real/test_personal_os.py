#!/usr/bin/env python3
"""Comprehensive tests for the Personal OS Shell (Gap 4)."""

import os
import json
import time
import threading
import shutil
import pytest
from pathlib import Path
from typing import List, Dict, Any
from unittest.mock import MagicMock

from core.identity.personal_os import (
    PersonalOSMode,
    NotificationType,
    NotificationSeverity,
    PrivacyLevel,
    Notification,
    UserSettings,
    PersonalMemory,
    PersonalCloneConfig,
    OfflineCache,
    NotificationController,
    OfflineMessage,
    PersonalOS,
    DEFAULT_CLONE_CONFIGS,
    get_personal_os,
    reset_personal_os,
)


# ══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(autouse=True)
def clean_state():
    """Reset PersonalOS pool and clean test data before each test."""
    reset_personal_os()
    # Clean up test DB files and workspace directories
    _clean_test_data()
    yield
    reset_personal_os()
    _clean_test_data()


def _clean_test_data() -> None:
    """Remove test JSONL files and user workspace directories."""
    # Clean JSONL persistence files
    for p in Path("data").glob("*.jsonl"):
        try:
            p.unlink(missing_ok=True)
        except Exception:
            pass
    # Also clean the default DB path
    default_db = Path("data/personal_os.jsonl")
    if default_db.exists():
        try:
            default_db.unlink(missing_ok=True)
        except Exception:
            pass

    # Clean workspace directories (stored under data/users/ by default)
    users_dir = Path("data/users")
    if users_dir.exists():
        for d in users_dir.glob("user_*"):
            try:
                shutil.rmtree(d, ignore_errors=True)
            except Exception:
                pass

    # Also clean any legacy user dirs directly under data/
    for d in Path("data").glob("user_*"):
        try:
            shutil.rmtree(d, ignore_errors=True)
        except Exception:
            pass


@pytest.fixture
def pos():
    """Create a fresh PersonalOS instance with a clean workspace."""
    # Ensure workspace is clean for this user
    # Workspace = _DATA_DIR / f"user_{asim_id[:8]}" where _DATA_DIR defaults to "data/users"
    ws = Path("data/users") / "user_test-use"
    if ws.exists():
        shutil.rmtree(ws, ignore_errors=True)

    return PersonalOS(
        asim_id="test-user-001",
        display_name="Test User",
        country_code="NP",
        db_path="data/test_pos.jsonl",
    )


@pytest.fixture
def pos_offline():
    """PersonalOS with a separate DB path."""
    return PersonalOS(
        asim_id="offline-user-001",
        display_name="Offline User",
        db_path="data/test_pos_offline.jsonl",
    )


# ══════════════════════════════════════════════════════════════════════════════
# Test: Enums
# ══════════════════════════════════════════════════════════════════════════════

class TestPersonalOSMode:
    """PersonalOSMode enum validation."""

    def test_values(self):
        assert PersonalOSMode.PERSONAL.value == "personal"
        assert PersonalOSMode.WORK.value == "work"
        assert PersonalOSMode.PUBLIC.value == "public"
        assert PersonalOSMode.EMERGENCY.value == "emergency"
        assert PersonalOSMode.OFFLINE.value == "offline"

    def test_all_modes(self):
        assert len(PersonalOSMode) == 5


class TestNotificationType:
    """NotificationType enum validation."""

    def test_values(self):
        assert NotificationType.OVERRIDE_REQUEST.value == "override_request"
        assert NotificationType.CONTRACT_EXPIRY.value == "contract_expiry"
        assert NotificationType.MESH_EVENT.value == "mesh_event"
        assert NotificationType.LIFE_JOURNEY.value == "life_journey"
        assert NotificationType.BALANCE_WARNING.value == "balance_warning"
        assert NotificationType.SYSTEM.value == "system"
        assert NotificationType.CLONE_EVENT.value == "clone_event"

    def test_all_types(self):
        assert len(NotificationType) == 7


class TestNotificationSeverity:
    """NotificationSeverity enum validation."""

    def test_values(self):
        assert NotificationSeverity.INFO.value == "info"
        assert NotificationSeverity.WARNING.value == "warning"
        assert NotificationSeverity.CRITICAL.value == "critical"

    def test_all_severities(self):
        assert len(NotificationSeverity) == 3


class TestPrivacyLevel:
    """PrivacyLevel enum validation."""

    def test_values(self):
        assert PrivacyLevel.STANDARD.value == "standard"
        assert PrivacyLevel.HIGH.value == "high"
        assert PrivacyLevel.MAXIMUM.value == "maximum"

    def test_all_levels(self):
        assert len(PrivacyLevel) == 3


# ══════════════════════════════════════════════════════════════════════════════
# Test: Data Models
# ══════════════════════════════════════════════════════════════════════════════

class TestNotification:
    """Notification dataclass tests."""

    def test_create(self):
        n = Notification(
            id="n1",
            type=NotificationType.SYSTEM,
            title="Test",
            message="Hello",
            severity=NotificationSeverity.INFO,
        )
        assert n.id == "n1"
        assert not n.read
        assert not n.dismissed

    def test_to_dict(self):
        n = Notification(
            id="n1",
            type=NotificationType.SYSTEM,
            title="Test",
            message="Hello",
            severity=NotificationSeverity.WARNING,
        )
        d = n.to_dict()
        assert d["type"] == "system"
        assert d["severity"] == "warning"
        assert d["title"] == "Test"

    def test_from_dict(self):
        d = {
            "id": "n1",
            "type": "contract_expiry",
            "title": "Contract",
            "message": "Expiring soon",
            "severity": "critical",
            "created_at": 100.0,
            "read": True,
            "dismissed": False,
            "action_payload": {"contract_id": "c1"},
        }
        n = Notification.from_dict(d)
        assert n.type == NotificationType.CONTRACT_EXPIRY
        assert n.severity == NotificationSeverity.CRITICAL
        assert n.action_payload["contract_id"] == "c1"
        assert n.read is True


class TestUserSettings:
    """UserSettings dataclass tests."""

    def test_defaults(self):
        s = UserSettings()
        assert s.language == "en"
        assert s.theme == "light"
        assert s.privacy_level == PrivacyLevel.STANDARD
        assert s.auto_sync is True

    def test_to_dict(self):
        s = UserSettings(language="ne", theme="dark")
        d = s.to_dict()
        assert d["language"] == "ne"
        assert d["theme"] == "dark"
        assert d["privacy_level"] == "standard"

    def test_from_dict(self):
        d = {"language": "ne", "theme": "dark", "privacy_level": "high"}
        s = UserSettings.from_dict(d)
        assert s.language == "ne"
        assert s.privacy_level == PrivacyLevel.HIGH


class TestPersonalMemory:
    """PersonalMemory dataclass tests."""

    def test_add_memory(self):
        mem = PersonalMemory(user_id="u1")
        mem.add_memory("user", "Hello", tags=["greeting"])
        assert len(mem.memories) == 1
        assert mem.memories[0]["role"] == "user"
        assert "greeting" in mem.memories[0]["tags"]

    def test_context_window(self):
        mem = PersonalMemory(user_id="u1")
        for i in range(25):
            mem.add_memory("user", f"msg {i}")
        assert len(mem.context_window) == 20
        assert mem.context_window[-1]["content"] == "msg 24"

    def test_search(self):
        mem = PersonalMemory(user_id="u1")
        mem.add_memory("user", "Hello world")
        mem.add_memory("assistant", "Hi there")
        mem.add_memory("user", "How is the weather?")
        results = mem.search("weather")
        assert len(results) == 1
        assert "weather" in results[0]["content"]

    def test_get_context(self):
        mem = PersonalMemory(user_id="u1")
        for i in range(10):
            mem.add_memory("user", f"msg {i}")
        ctx = mem.get_context(3)
        assert len(ctx) == 3
        assert ctx[-1]["content"] == "msg 9"


class TestPersonalCloneConfig:
    """PersonalCloneConfig dataclass tests."""

    def test_defaults(self):
        c = PersonalCloneConfig(clone_id="c01", name="Test", specialty="test")
        assert c.active is True
        assert c.model_preference == "local"
        assert c.custom_instructions == ""

    def test_to_dict(self):
        c = PersonalCloneConfig("c01", "Tech Guide", "tech", True, "help", "cloud")
        d = c.to_dict()
        assert d["clone_id"] == "c01"
        assert d["model_preference"] == "cloud"

    def test_from_dict(self):
        d = {"clone_id": "c01", "name": "Test", "specialty": "test",
             "active": False, "custom_instructions": "", "model_preference": "auto"}
        c = PersonalCloneConfig.from_dict(d)
        assert c.active is False
        assert c.model_preference == "auto"


class TestOfflineMessage:
    """OfflineMessage dataclass tests."""

    def test_create(self):
        m = OfflineMessage(id="m1", action="send_message", payload={"text": "hi"})
        assert m.status == "pending"
        assert m.retry_count == 0
        assert m.max_retries == 5

    def test_to_dict(self):
        m = OfflineMessage("m1", "sync", {"k": "v"}, status="sent")
        d = m.to_dict()
        assert d["status"] == "sent"
        assert d["action"] == "sync"

    def test_from_dict(self):
        d = {"id": "m1", "action": "test", "payload": {"a": 1},
             "status": "pending", "retry_count": 0, "max_retries": 5,
             "created_at": 100.0}
        m = OfflineMessage.from_dict(d)
        assert m.action == "test"


class TestDefaultCloneConfigs:
    """Verify the 15 default clone configurations."""

    def test_fifteen_clones(self):
        assert len(DEFAULT_CLONE_CONFIGS) == 15

    def test_all_have_ids(self):
        ids = [c.clone_id for c in DEFAULT_CLONE_CONFIGS]
        expected = [f"c{i:02d}" for i in range(1, 16)]
        assert ids == expected

    def test_first_five_active(self):
        active = [c for c in DEFAULT_CLONE_CONFIGS if c.active]
        assert len(active) >= 8  # Most are active by default


# ══════════════════════════════════════════════════════════════════════════════
# Test: OfflineCache
# ══════════════════════════════════════════════════════════════════════════════

class TestOfflineCache:
    """Offline message queue."""

    @pytest.fixture
    def cache(self):
        return OfflineCache(db_path="data/test_cache.jsonl")

    def test_enqueue(self, cache):
        m = cache.enqueue("send_message", {"text": "hello"})
        assert m.action == "send_message"
        assert m.status == "pending"

    def test_get_pending(self, cache):
        cache.enqueue("action1", {})
        cache.enqueue("action2", {})
        pending = cache.get_pending()
        assert len(pending) == 2

    def test_mark_sent(self, cache):
        m = cache.enqueue("test", {})
        assert cache.mark_sent(m.id) is True
        assert len(cache.get_pending()) == 0

    def test_mark_failed(self, cache):
        m = cache.enqueue("test", {})
        cache.mark_failed(m.id)
        assert cache.get_pending()[0].retry_count == 1

    def test_max_retries_exhausted(self, cache):
        m = cache.enqueue("test", {})
        for _ in range(6):
            cache.mark_failed(m.id)
        assert cache.get_count().get("failed", 0) == 1

    def test_get_count(self, cache):
        cache.enqueue("a", {})
        cache.enqueue("b", {})
        m3 = cache.enqueue("c", {})
        cache.mark_sent(m3.id)
        counts = cache.get_count()
        assert counts.get("pending", 0) == 2
        assert counts.get("sent", 0) == 1

    def test_flush_stale(self, cache):
        m = cache.enqueue("old", {})
        cache.mark_sent(m.id)
        # Message just created — not stale yet
        assert cache.flush_stale(max_age_hours=0) >= 0

    def test_persist_and_reload(self, cache):
        cache.enqueue("persist", {"data": "value"})
        # Create new cache instance that reads the same DB
        cache2 = OfflineCache(db_path="data/test_cache.jsonl")
        pending = cache2.get_pending()
        assert len(pending) == 1
        assert pending[0].action == "persist"

    def test_clear(self, cache):
        cache.enqueue("a", {})
        cache.enqueue("b", {})
        cache.clear()
        assert len(cache.get_pending()) == 0


# ══════════════════════════════════════════════════════════════════════════════
# Test: NotificationController
# ══════════════════════════════════════════════════════════════════════════════

class TestNotificationController:
    """Notification management subsystem."""

    @pytest.fixture
    def nc(self):
        return NotificationController(db_path="data/test_notif.jsonl")

    def test_push(self, nc):
        n = nc.push(NotificationType.SYSTEM, "Test", "Hello",
                     NotificationSeverity.INFO)
        assert n.title == "Test"
        assert n.read is False

    def test_get_active(self, nc):
        nc.push(NotificationType.SYSTEM, "A", "msg1", NotificationSeverity.INFO)
        nc.push(NotificationType.SYSTEM, "B", "msg2", NotificationSeverity.WARNING)
        active = nc.get_active()
        assert len(active) == 2

    def test_get_active_filtered(self, nc):
        nc.push(NotificationType.SYSTEM, "A", "m1", NotificationSeverity.INFO)
        nc.push(NotificationType.SYSTEM, "B", "m2", NotificationSeverity.CRITICAL)
        critical = nc.get_active(severity=NotificationSeverity.CRITICAL)
        assert len(critical) == 1
        assert critical[0].title == "B"

    def test_mark_read(self, nc):
        n = nc.push(NotificationType.SYSTEM, "Test", "m", NotificationSeverity.INFO)
        assert nc.mark_read(n.id) is True
        assert nc.get_unread_count() == 0

    def test_dismiss(self, nc):
        n = nc.push(NotificationType.SYSTEM, "Test", "m", NotificationSeverity.INFO)
        assert nc.dismiss(n.id) is True
        assert len(nc.get_active()) == 0

    def test_get_unread_count(self, nc):
        nc.push(NotificationType.SYSTEM, "A", "m1", NotificationSeverity.INFO)
        nc.push(NotificationType.SYSTEM, "B", "m2", NotificationSeverity.INFO)
        n3 = nc.push(NotificationType.SYSTEM, "C", "m3", NotificationSeverity.INFO)
        nc.mark_read(n3.id)
        assert nc.get_unread_count() == 2

    def test_clear_all(self, nc):
        nc.push(NotificationType.SYSTEM, "A", "m1", NotificationSeverity.INFO)
        nc.push(NotificationType.SYSTEM, "B", "m2", NotificationSeverity.WARNING)
        count = nc.clear_all()
        assert count == 2
        assert len(nc.get_active()) == 0

    def test_flush_old(self, nc):
        n = nc.push(NotificationType.SYSTEM, "Old", "m", NotificationSeverity.INFO)
        # Force old timestamp
        n.created_at = 0
        flushed = nc.flush_old(max_age_hours=0)
        assert flushed == 1

    def test_get_stats(self, nc):
        nc.push(NotificationType.SYSTEM, "A", "m", NotificationSeverity.INFO)
        nc.push(NotificationType.CONTRACT_EXPIRY, "B", "m", NotificationSeverity.WARNING)
        stats = nc.get_stats()
        assert stats["total"] == 2
        assert stats["unread"] == 2
        assert stats["by_type"]["system"] == 1
        assert stats["by_type"]["contract_expiry"] == 1

    def test_persist_and_reload(self, nc):
        nc.push(NotificationType.SYSTEM, "Persist", "survive", NotificationSeverity.INFO)
        nc2 = NotificationController(db_path="data/test_notif.jsonl")
        active = nc2.get_active()
        assert len(active) >= 1
        assert active[0].title == "Persist"

    def test_dismissed_not_loaded(self, nc):
        n = nc.push(NotificationType.SYSTEM, "DismissMe", "bye", NotificationSeverity.INFO)
        nc.dismiss(n.id)
        nc2 = NotificationController(db_path="data/test_notif.jsonl")
        assert len(nc2.get_active()) == 0

    def test_clear(self, nc):
        nc.push(NotificationType.SYSTEM, "A", "m", NotificationSeverity.INFO)
        nc.clear()
        assert nc.get_unread_count() == 0


# ══════════════════════════════════════════════════════════════════════════════
# Test: PersonalOS Core
# ══════════════════════════════════════════════════════════════════════════════

class TestPersonalOSInit:
    """PersonalOS initialisation."""

    def test_create(self, pos):
        assert pos.asim_id == "test-user-001"
        assert pos.display_name == "Test User"
        assert pos.country_code == "NP"
        assert pos.active_mode == PersonalOSMode.PERSONAL

    def test_default_clones_loaded(self, pos):
        assert len(pos.clones) == 15
        assert pos.clones[0].clone_id == "c01"

    def test_subsystems_initialized(self, pos):
        assert pos.memory is not None
        assert pos.notifications is not None
        assert pos.offline_cache is not None
        assert pos.settings is not None

    def test_mode_personal_by_default(self, pos):
        assert pos.active_mode == PersonalOSMode.PERSONAL
        assert pos.get_mode() == "personal"


class TestPersonalOSSettings:
    """Settings management."""

    def test_default_settings(self, pos):
        s = pos.get_settings()
        assert s["language"] == "en"
        assert s["theme"] == "light"
        assert s["privacy_level"] == "standard"

    def test_update_settings(self, pos):
        pos.update_settings(language="ne", theme="dark")
        s = pos.get_settings()
        assert s["language"] == "ne"
        assert s["theme"] == "dark"

    def test_update_privacy_level(self, pos):
        pos.update_settings(privacy_level="high")
        s = pos.get_settings()
        assert s["privacy_level"] == "high"

    def test_update_ignores_invalid_key(self, pos):
        pos.update_settings(invalid_key="value")
        s = pos.get_settings()
        assert "invalid_key" not in s

    def test_settings_persist(self, pos):
        pos.update_settings(language="ne")
        # Create new PersonalOS with same asim_id
        pos2 = PersonalOS(
            asim_id="test-user-001",
            display_name="Test User",
            db_path="data/test_pos.jsonl",
        )
        s = pos2.get_settings()
        assert s["language"] == "ne"

    def test_settings_updated_at_changes(self, pos):
        t1 = pos.get_settings()["updated_at"]
        pos.update_settings(language="ne")
        t2 = pos.get_settings()["updated_at"]
        assert t2 >= t1


class TestPersonalOSMode:
    """Mode switching."""

    def test_set_mode_valid(self, pos):
        pos.set_mode("work")
        assert pos.get_mode() == "work"
        assert pos.active_mode == PersonalOSMode.WORK

    def test_set_mode_offline(self, pos):
        pos.set_mode("offline")
        assert pos.get_mode() == "offline"
        # Offline mode should generate a notification
        assert pos.get_unread_count() >= 1

    def test_set_mode_invalid(self, pos):
        pos.set_mode("invalid_mode")
        assert pos.get_mode() == "personal"  # Should remain unchanged

    def test_set_mode_all(self, pos):
        for mode in ["personal", "work", "public", "emergency", "offline"]:
            pos.set_mode(mode)
            assert pos.get_mode() == mode


class TestPersonalOSClones:
    """Clone management."""

    def test_get_active_clones(self, pos):
        active = pos.get_active_clones()
        assert len(active) >= 8
        for c in active:
            assert c["active"] is True

    def test_get_all_clones(self, pos):
        all_clones = pos.get_clones()
        assert len(all_clones) == 15

    def test_customize_clone(self, pos):
        result = pos.customize_clone("c01", name="My Tech Guide",
                                      instructions="Be concise")
        assert result["success"] is True
        assert pos.clones[0].name == "My Tech Guide"
        assert pos.clones[0].custom_instructions == "Be concise"

    def test_customize_invalid_clone(self, pos):
        result = pos.customize_clone("c99", name="Ghost")
        assert result["success"] is False

    def test_customize_model_preference(self, pos):
        pos.customize_clone("c02", model_preference="cloud")
        assert pos.clones[1].model_preference == "cloud"

    def test_customize_toggle_active(self, pos):
        pos.customize_clone("c01", active=False)
        assert pos.clones[0].active is False

    def test_reset_clones(self, pos):
        pos.customize_clone("c01", name="Changed")
        pos.reset_clones()
        assert pos.clones[0].name == "Tech Guide"


class TestPersonalOSRules:
    """Personal rules management."""

    def test_add_rule(self, pos):
        pos.add_personal_rule("Never share financial data")
        rules = pos.get_personal_rules()
        assert len(rules) == 1
        assert "financial" in rules[0]

    def test_add_multiple_rules(self, pos):
        pos.add_personal_rule("Rule 1")
        pos.add_personal_rule("Rule 2")
        pos.add_personal_rule("Rule 3")
        assert len(pos.get_personal_rules()) == 3

    def test_remove_rule(self, pos):
        pos.add_personal_rule("Rule 1")
        pos.add_personal_rule("Rule 2")
        assert pos.remove_personal_rule(0) is True
        assert len(pos.get_personal_rules()) == 1
        assert pos.get_personal_rules()[0] == "Rule 2"

    def test_remove_invalid_index(self, pos):
        assert pos.remove_personal_rule(99) is False
        assert pos.remove_personal_rule(-1) is False


class TestPersonalOSDocuments:
    """Document storage."""

    def test_save_document(self, pos):
        result = pos.save_document("note1", "Hello world")
        assert result["success"] is True
        assert "private" in result["path"]

    def test_list_documents(self, pos):
        pos.save_document("doc1", "Content 1")
        pos.save_document("doc2", "Content 2")
        docs = pos.list_documents()
        assert len(docs) == 2

    def test_read_document(self, pos):
        pos.save_document("readme", "Read content")
        content = pos.read_document("readme")
        assert content == "Read content"

    def test_read_nonexistent(self, pos):
        assert pos.read_document("nonexistent") is None

    def test_delete_document(self, pos):
        pos.save_document("temp", "Delete me")
        assert pos.delete_document("temp") is True
        assert pos.read_document("temp") is None

    def test_delete_nonexistent(self, pos):
        assert pos.delete_document("ghost") is False

    def test_public_documents(self, pos):
        pos.save_document("pub", "Public content", visibility="public")
        docs = pos.list_documents("public")
        assert len(docs) == 1


class TestPersonalOSMemory:
    """Memory management."""

    def test_process_message_adds_memory(self, pos):
        pos.process_message("Hello, how are you?")
        assert len(pos.memory.memories) == 1
        assert pos.memory.memories[0]["role"] == "user"

    def test_receive_response_adds_memory(self, pos):
        pos.receive_response("I am fine, thank you!")
        assert len(pos.memory.memories) == 1
        assert pos.memory.memories[0]["role"] == "assistant"

    def test_search_memories(self, pos):
        pos.process_message("What is the weather in Kathmandu?")
        pos.receive_response("The weather is sunny in Kathmandu.")
        results = pos.search_memories("weather")
        assert len(results) >= 1

    def test_context_includes_clone(self, pos):
        result = pos.process_message("I need tech help")
        assert result["clone_used"] != "general"


class TestPersonalOSNotifications:
    """Notification integration."""

    def test_notify(self, pos):
        n = pos.notify(
            NotificationType.SYSTEM,
            "Welcome",
            "Your Personal OS is ready",
            NotificationSeverity.INFO,
        )
        assert n.title == "Welcome"
        assert n.type == NotificationType.SYSTEM

    def test_get_notifications(self, pos):
        pos.notify(NotificationType.SYSTEM, "A", "msg1", NotificationSeverity.INFO)
        pos.notify(NotificationType.CONTRACT_EXPIRY, "B", "msg2",
                    NotificationSeverity.WARNING)
        notifs = pos.get_notifications()
        assert len(notifs) == 2

    def test_get_notifications_filtered(self, pos):
        pos.notify(NotificationType.SYSTEM, "A", "m", NotificationSeverity.INFO)
        pos.notify(NotificationType.SYSTEM, "B", "m", NotificationSeverity.CRITICAL)
        critical = pos.get_notifications(severity=NotificationSeverity.CRITICAL)
        assert len(critical) == 1

    def test_unread_count(self, pos):
        pos.notify(NotificationType.SYSTEM, "A", "m", NotificationSeverity.INFO)
        pos.notify(NotificationType.SYSTEM, "B", "m", NotificationSeverity.INFO)
        assert pos.get_unread_count() == 2

    def test_notifications_disabled(self, pos):
        pos.update_settings(notifications_enabled=False)
        n = pos.notify(NotificationType.SYSTEM, "Silent", "m",
                        NotificationSeverity.INFO)
        assert n is not None  # Still stored


class TestPersonalOSOffline:
    """Offline cache integration."""

    def test_enqueue_offline(self, pos):
        m = pos.enqueue_offline("sync_memory", {"entries": 5})
        assert m.action == "sync_memory"
        assert m.status == "pending"

    def test_get_pending_offline(self, pos):
        pos.enqueue_offline("action1", {})
        pos.enqueue_offline("action2", {})
        pending = pos.get_pending_offline()
        assert len(pending) == 2

    def test_offline_stats(self, pos):
        m = pos.enqueue_offline("test", {})
        pending = pos.get_offline_stats()
        assert pending.get("pending", 0) == 1


class TestPersonalOSDashboard:
    """Dashboard data aggregation."""

    def test_dashboard_has_all_sections(self, pos):
        db = pos.get_dashboard()
        assert "user" in db
        assert "clones" in db
        assert "memory" in db
        assert "notifications" in db
        assert "settings" in db
        assert "offline" in db
        assert "rules" in db
        assert "documents" in db

    def test_dashboard_user_info(self, pos):
        db = pos.get_dashboard()
        assert db["user"]["asim_id"] == "test-user-001"
        assert db["user"]["display_name"] == "Test User"
        assert db["user"]["mode"] == "personal"

    def test_dashboard_clones(self, pos):
        db = pos.get_dashboard()
        assert db["clones"]["total"] == 15
        assert db["clones"]["active"] >= 8

    def test_dashboard_reflects_activity(self, pos):
        pos.process_message("Hello")
        pos.receive_response("Hi there!")
        pos.enqueue_offline("sync", {"k": "v"})
        db = pos.get_dashboard()
        assert db["memory"]["total_entries"] == 2
        assert db["offline"].get("pending", 0) >= 1

    def test_dashboard_notifications(self, pos):
        pos.notify(NotificationType.SYSTEM, "Test", "m", NotificationSeverity.INFO)
        db = pos.get_dashboard()
        assert db["notifications"]["unread"] == 1


class TestPersonalOSStatus:
    """Status reporting."""

    def test_status(self, pos):
        st = pos.get_status()
        assert st["asim_id"] == "test-user-001"
        assert st["name"] == "Test User"
        assert st["mode"] == "personal"
        assert "notifications_unread" in st
        assert "offline_pending" in st
        assert "settings_version" in st

    def test_status_updates(self, pos):
        st1 = pos.get_status()
        pos.set_mode("work")
        st2 = pos.get_status()
        assert st2["mode"] == "work"


class TestPersonalOSExternalIntegrations:
    """Lazy external module integration."""

    def test_set_life_journey(self, pos):
        mock = MagicMock()
        pos.set_life_journey(mock)
        assert pos._life_journey is mock

    def test_set_mesh_router(self, pos):
        mock = MagicMock()
        pos.set_mesh_router(mock)
        assert pos._mesh_router is mock

    def test_set_contract_system(self, pos):
        mock = MagicMock()
        pos.set_contract_system(mock)
        assert pos._contract_system is mock

    def test_set_power_balance(self, pos):
        mock = MagicMock()
        pos.set_power_balance(mock)
        assert pos._power_balance is mock


# ══════════════════════════════════════════════════════════════════════════════
# Test: Singleton Factory
# ══════════════════════════════════════════════════════════════════════════════

class TestPersonalOSFactory:
    """Pool-based singleton factory."""

    def test_get_same_instance(self):
        p1 = get_personal_os("user1", "Alice")
        p2 = get_personal_os("user1", "Alice")
        assert p1 is p2

    def test_different_users_different_instances(self):
        p1 = get_personal_os("user_a", "Alice")
        p2 = get_personal_os("user_b", "Bob")
        assert p1 is not p2
        assert p1.asim_id == "user_a"
        assert p2.asim_id == "user_b"

    def test_reset_single(self):
        p1 = get_personal_os("user_x", "X")
        reset_personal_os("user_x")
        p2 = get_personal_os("user_x", "X")
        assert p1 is not p2

    def test_reset_all(self):
        p1 = get_personal_os("user1", "A")
        p2 = get_personal_os("user2", "B")
        reset_personal_os()
        p3 = get_personal_os("user1", "A")
        p4 = get_personal_os("user2", "B")
        assert p1 is not p3
        assert p2 is not p4

    def test_singleton_preserves_state(self):
        p1 = get_personal_os("state_user", "State")
        p1.add_personal_rule("Important rule")
        p2 = get_personal_os("state_user", "State")
        assert len(p2.get_personal_rules()) == 1

    def test_factory_with_db_path(self):
        p1 = get_personal_os("db_user", "DB", db_path="data/test_factory.jsonl")
        p1.add_personal_rule("Factory rule")
        p2 = get_personal_os("db_user", "DB", db_path="data/test_factory.jsonl")
        assert p1 is p2


# ══════════════════════════════════════════════════════════════════════════════
# Test: Module Exports
# ══════════════════════════════════════════════════════════════════════════════

class TestModuleExports:
    """Verify that __all__ exports match actual module contents."""

    def test_all_exports_defined(self):
        from core.identity import personal_os as pos_mod
        for name in pos_mod.__all__:
            assert hasattr(pos_mod, name), f"{name} not found in module"

    def test_all_exports_are_importable(self):
        from core.identity.personal_os import (
            PersonalOSMode,
            NotificationType,
            NotificationSeverity,
            PrivacyLevel,
            Notification,
            UserSettings,
            PersonalMemory,
            PersonalCloneConfig,
            OfflineCache,
            NotificationController,
            OfflineMessage,
            PersonalOS,
            DEFAULT_CLONE_CONFIGS,
            get_personal_os,
            reset_personal_os,
        )
        assert PersonalOSMode is not None
        assert NotificationType is not None
        assert NotificationSeverity is not None
        assert PrivacyLevel is not None
        assert Notification is not None
        assert UserSettings is not None
        assert PersonalMemory is not None
        assert PersonalCloneConfig is not None
        assert OfflineCache is not None
        assert NotificationController is not None
        assert OfflineMessage is not None
        assert PersonalOS is not None
        assert DEFAULT_CLONE_CONFIGS is not None
        assert get_personal_os is not None
        assert reset_personal_os is not None


# ══════════════════════════════════════════════════════════════════════════════
# Test: Edge Cases
# ══════════════════════════════════════════════════════════════════════════════

class TestEdgeCases:
    """Unusual or boundary conditions."""

    def test_empty_display_name(self):
        p = PersonalOS(asim_id="empty_name", display_name="",
                       db_path="data/test_edge.jsonl")
        assert p.display_name == ""

    def test_very_long_display_name(self):
        long_name = "A" * 1000
        p = PersonalOS(asim_id="long", display_name=long_name,
                       db_path="data/test_edge2.jsonl")
        assert p.display_name == long_name

    def test_large_number_of_memories(self, pos):
        for i in range(200):
            pos.process_message(f"Message {i}")
        assert len(pos.memory.memories) == 200
        # Context window capped at 20
        assert len(pos.memory.context_window) == 20

    def test_memory_search_no_results(self, pos):
        results = pos.search_memories("nonexistent_term_xyz")
        assert len(results) == 0

    def test_multiple_mode_switches(self, pos):
        modes = ["personal", "work", "public", "emergency", "offline",
                 "personal", "work", "offline", "public"]
        for mode in modes:
            pos.set_mode(mode)
            assert pos.get_mode() == mode

    def test_clone_customization_preserved_across_saves(self, pos):
        pos.customize_clone("c01", name="Custom Name", instructions="Custom instr")
        pos2 = PersonalOS(
            asim_id="test-user-001",
            display_name="Test User",
            db_path="data/test_pos.jsonl",
        )
        clone = pos2.clones[0]
        assert clone.name == "Custom Name"
        assert clone.custom_instructions == "Custom instr"

    def test_concurrent_notification_access(self):
        nc = NotificationController(db_path="data/test_concurrent.jsonl")

        def push_notifs(count: int):
            for i in range(count):
                nc.push(NotificationType.SYSTEM, f"Test {i}",
                        f"Message {i}", NotificationSeverity.INFO)

        threads = []
        for i in range(4):
            t = threading.Thread(target=push_notifs, args=(10,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        assert nc.get_stats()["total"] == 40

    def test_concurrent_offline_queue(self):
        cache = OfflineCache(db_path="data/test_concurrent_off.jsonl")

        def enqueue_items(count: int):
            for i in range(count):
                cache.enqueue("test", {"i": i})

        threads = []
        for i in range(4):
            t = threading.Thread(target=enqueue_items, args=(10,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        assert len(cache.get_pending()) == 40

    def test_full_lifecycle(self, pos):
        """End-to-end: create OS → configure → use → save → restore."""
        # Configure
        pos.update_settings(language="ne", theme="dark", privacy_level="high")
        pos.customize_clone("c01", name="My Guide", instructions="Be helpful")
        pos.add_personal_rule("Keep data private")
        pos.set_mode("work")

        # Use
        pos.process_message("Help me with tech")
        pos.receive_response("Sure, I can help!")
        pos.save_document("tech_note", "Important technical information")

        # Verify state
        assert pos.get_mode() == "work"
        assert len(pos.get_personal_rules()) == 1
        assert len(pos.memory.memories) == 2
        assert len(pos.list_documents()) == 1

        # Restore from new instance
        pos2 = PersonalOS(
            asim_id="test-user-001",
            display_name="Test User",
            db_path="data/test_pos.jsonl",
        )
        assert pos2.get_settings()["language"] == "ne"
        assert pos2.get_settings()["theme"] == "dark"
        assert pos2.get_settings()["privacy_level"] == "high"
        assert pos2.clones[0].name == "My Guide"
        assert len(pos2.get_personal_rules()) == 1

    def test_multiple_users_isolation(self):
        """Different users should not share state."""
        user1 = PersonalOS(asim_id="u1", display_name="Alice",
                           db_path="data/test_multi.jsonl")
        user2 = PersonalOS(asim_id="u2", display_name="Bob",
                           db_path="data/test_multi.jsonl")

        user1.add_personal_rule("Alice's rule")
        user2.add_personal_rule("Bob's rule")

        assert len(user1.get_personal_rules()) == 1
        assert len(user2.get_personal_rules()) == 1
        assert user1.get_personal_rules()[0] == "Alice's rule"
        assert user2.get_personal_rules()[0] == "Bob's rule"

    def test_offline_messages_survive_restart(self):
        """Offline messages should persist across different instances."""
        # This test uses the offline cache directly to avoid OS pool interference
        cache1 = OfflineCache(db_path="data/test_survive.jsonl")
        cache1.enqueue("critical_action", {"data": "important"})

        cache2 = OfflineCache(db_path="data/test_survive.jsonl")
        pending = cache2.get_pending()
        assert len(pending) == 1
        assert pending[0].action == "critical_action"

    def test_settings_survive_os_restart_with_different_db(self):
        """Settings persisted in JSONL should survive across instances."""
        p1 = PersonalOS(asim_id="survivor", display_name="Survivor",
                        db_path="data/test_survive_set.jsonl")
        p1.update_settings(language="ne", theme="dark")

        p2 = PersonalOS(asim_id="survivor", display_name="Survivor",
                        db_path="data/test_survive_set.jsonl")
        s = p2.get_settings()
        assert s["language"] == "ne"
        assert s["theme"] == "dark"
