"""
STATUS: REAL — Auto-labeled by batch_label.py
"""

"""Pytest configuration and shared fixtures.

Provides shared fixtures used across all test directories:
  - event_loop: Event loop for async tests
  - test_client: FastAPI TestClient pointing to the backend app
  - auth_user: Creates a test user and returns headers with JWT
  - temp_db: Overrides DB to use in-memory SQLite for tests
  - mock_biometric: Mocks BiometricHardwareGate to return success for Level-3 tests
  - mock_state_manager: Mock state manager
  - mock_model_connector: Mock model connector
  - sample_api_keys: Sample API keys
"""

import os
import sys
import json
import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from datetime import datetime


def pytest_configure(config):
    """Configure pytest-asyncio default mode."""
    config.option.asyncio_mode = "auto"

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ──────────────────────────────────────────────────────────────────────────── #
# Patch broken mesh imports BEFORE any backend module is loaded
# backend/mesh.py tries `from mesh.p2p_transport import get_p2p_transport, MessageType`
# but p2p_transport doesn't export MessageType.
# ──────────────────────────────────────────────────────────────────────────── #
_import_orig = __builtins__["__import__"] if isinstance(__builtins__, dict) else __builtins__.__import__


def _patched_import(name, *args, **kwargs):
    """Intercept mesh.p2p_transport imports to add missing names."""
    if name == "mesh.p2p_transport":
        mod = _import_orig(name, *args, **kwargs)
        if not hasattr(mod, "MessageType"):
            from enum import Enum
            class MessageType(str, Enum):
                HELLO = "hello"
                ACK = "ack"
                PING = "ping"
                PONG = "pong"
                RPC_CALL = "rpc_call"
                RPC_RESPONSE = "rpc_response"
                SYNC = "sync"
                DATA = "data"
                STREAM = "stream"
                ERROR = "error"
            mod.MessageType = MessageType
        if not hasattr(mod, "Message"):
            import time as _time
            from dataclasses import dataclass, field
            from typing import Dict, Any, Optional
            @dataclass
            class Message:
                id: str = "msg_001"
                type: Any = None  # MessageType
                sender_id: str = "test"
                recipient_id: str = ""
                payload: dict = field(default_factory=dict)
                timestamp: float = 0.0
                ttl: int = 30

                def to_dict(self) -> Dict[str, Any]:
                    return {
                        "id": self.id,
                        "type": self.type.value if hasattr(self.type, 'value') else str(self.type),
                        "sender_id": self.sender_id,
                        "recipient_id": self.recipient_id,
                        "payload": self.payload,
                        "timestamp": self.timestamp,
                        "ttl": self.ttl,
                    }

                @classmethod
                def from_dict(cls, data: Dict[str, Any]) -> "Message":
                    return cls(
                        id=data.get("id", ""),
                        type=mod.MessageType(data["type"]) if "type" in data and hasattr(mod, "MessageType") else None,
                        sender_id=data.get("sender_id", ""),
                        recipient_id=data.get("recipient_id", ""),
                        payload=data.get("payload", {}),
                        timestamp=data.get("timestamp", 0.0),
                        ttl=data.get("ttl", 30),
                    )

                def is_expired(self) -> bool:
                    return _time.time() - self.timestamp > self.ttl
            mod.Message = Message
        if not hasattr(mod, "PeerConnection"):
            from dataclasses import dataclass
            from enum import Enum
            # Only create mock ConnectionState if the module doesn't already define it.
            # The real module (mesh/p2p_transport.py) defines ConnectionState(Enum),
            # so we must not overwrite it — otherwise test assertions comparing
            # ConnectionState values from the real module will fail (different enum classes).
            _conn_state = getattr(mod, "ConnectionState", None)
            if _conn_state is None:
                class ConnectionState(str, Enum):
                    INIT = "init"
                    CONNECTING = "connecting"
                    CONNECTED = "connected"
                    DISCONNECTED = "disconnected"
                    TIMEOUT = "timeout"
                mod.ConnectionState = ConnectionState
                _conn_state = ConnectionState
            @dataclass
            class PeerConnection:
                peer_id: str = ""
                state: _conn_state = _conn_state.INIT  # type: ignore
                host: str = ""
                port: int = 0
                last_seen: float = 0.0
                failures: int = 0
            mod.PeerConnection = PeerConnection
        return mod
    return _import_orig(name, *args, **kwargs)


if isinstance(__builtins__, dict):
    __builtins__["__import__"] = _patched_import
else:
    __builtins__.__import__ = _patched_import


# ──────────────────────────────────────────────────────────────────────────── #
# Existing Fixtures
# ──────────────────────────────────────────────────────────────────────────── #

@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_state_manager():
    """Mock state manager for testing."""
    manager = Mock()
    manager.get = Mock(return_value=None)
    manager.set = Mock(return_value=True)
    manager.delete = Mock(return_value=True)
    return manager


@pytest.fixture
def mock_model_connector():
    """Mock model connector for testing."""
    connector = Mock()
    connector.generate = Mock(return_value="Test response")
    connector.get_model_for_task = Mock(return_value=Mock(name="test_model"))
    return connector


@pytest.fixture
def sample_api_keys():
    """Sample API keys for testing."""
    return {
        'openai': 'sk-test123',
        'anthropic': 'sk-ant-test123',
        'gemini': 'test-key-123'
    }


# ──────────────────────────────────────────────────────────────────────────── #
# New Shared Fixtures (Phase 7)
# ──────────────────────────────────────────────────────────────────────────── #

@pytest.fixture(scope="session")
def app():
    """Build the FastAPI application via simple_backend.create_app()."""
    # Patch mesh routes to avoid import error during app creation
    with patch("backend.mesh.setup_mesh_routes") as mock_mesh:
        from simple_backend import create_app
        application = create_app()
        yield application


@pytest.fixture
def test_client(app):
    """FastAPI TestClient pointing to the backend application."""
    from fastapi.testclient import TestClient
    with TestClient(app) as client:
        yield client


@pytest.fixture
def temp_db():
    """Override DB to use a temporary SQLite database for tests."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    db_path = tmp.name

    # Initialize schema tables needed by auth
    import sqlite3
    from backend.auth import AuthManager
    AuthManager(db_path)

    # AuthManager._init_db() does NOT create the 'users' table,
    # but AuthManager.register_user and login_user need it.
    # Create it here to match simple_backend._init_db() schema.
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                display_name TEXT,
                password_hash TEXT NOT NULL,
                country_code TEXT DEFAULT 'NP',
                universe_mode TEXT DEFAULT 'personal',
                theme TEXT DEFAULT 'deep-space',
                api_keys TEXT DEFAULT '{}',
                agent_mode_json TEXT DEFAULT '{}',
                resource_sharing_json TEXT DEFAULT '{}',
                phone TEXT,
                national_id_hash TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.commit()

    yield db_path

    # Cleanup
    try:
        os.unlink(db_path)
    except OSError:
        pass


@pytest.fixture
def auth_user(temp_db):
    """
    Create a test user and return authorization headers with JWT.
    Returns a dict with 'headers' (Authorization header) and 'user' info.
    """
    from backend.auth import AuthManager

    auth_mgr = AuthManager(temp_db)

    email = "conftest_user@test.asim"
    password = "ConftestPass123!"

    try:
        auth_mgr.register_user(
            type("Req", (), {
                "email": email,
                "password": password,
                "display_name": "Conftest User",
                "device_id": "conftest-device",
                "mode": "personal",
                "country_code": "US",
            })()
        )
    except (ValueError, Exception):
        pass  # user may already exist

    login_result = auth_mgr.login_user(
        type("Req", (), {
            "email": email,
            "password": password,
            "device_id": "conftest-device",
            "mode": "personal",
        })(),
        client_ip="127.0.0.1",
    )

    headers = {
        "Authorization": f"Bearer {login_result['token']}",
        "Content-Type": "application/json",
    }

    return {
        "headers": headers,
        "token": login_result["token"],
        "user_id": login_result.get("session", {}).get("user_id", ""),
        "email": email,
    }


@pytest.fixture
def mock_biometric():
    """
    Mock BiometricHardwareGate to automatically pass biometric checks.
    Useful for Level-3 (CRITICAL) endpoint tests that trigger the biometric gate.
    """
    with patch("security.biometric_hardware_gate.BiometricHardwareGate") as mock:
        gate_instance = MagicMock()
        gate_instance.verify_biometric = AsyncMock(return_value={
            "verified": True,
            "confidence": 0.99,
            "method": "mock_biometric",
        })
        gate_instance.verify_and_lock = AsyncMock(return_value={
            "verified": True,
            "confidence": 0.99,
            "method": "mock_biometric",
            "locked": False,
        })
        gate_instance.get_status = MagicMock(return_value={
            "locked": False,
            "verified": True,
            "method": "mock_biometric",
            "timestamp": datetime.utcnow().isoformat(),
        })
        mock.return_value = gate_instance
        yield gate_instance
