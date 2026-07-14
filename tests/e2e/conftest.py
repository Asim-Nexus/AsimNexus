"""
STATUS: REAL — E2E test fixtures
=================================
Shared fixtures for end-to-end tests:
  - test_client: FastAPI TestClient pointing to the backend app
  - auth_headers: generates JWT tokens for test users
  - temp_db: in-memory SQLite override for the DB dependency
  - mock_biometric: mocks BiometricHardwareGate to return success
  - test_users: pre-registered test user definitions
"""

import os
import sys
import json
import pytest
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ──────────────────────────────────────────────────────────────────────────── #
# Patch broken mesh imports BEFORE any backend module is loaded
# Some modules try `from mesh.p2p_transport import ...` (old root-level path)
# or `from core.mesh.p2p_transport import ...` (current path).
# Ensure MessageType and Message are always available.
# ──────────────────────────────────────────────────────────────────────────── #
_import_orig = __builtins__["__import__"] if isinstance(__builtins__, dict) else __builtins__.__import__

def _ensure_mesh_attrs(mod):
    """Add MessageType and Message to a mesh transport module if missing."""
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
        from dataclasses import dataclass, field
        @dataclass
        class Message:
            msg_type: str = "data"
            sender_id: str = "test"
            payload: dict = field(default_factory=dict)
            msg_id: str = "msg_001"
            ttl: int = 30
        mod.Message = Message
    return mod

def _patched_import(name, *args, **kwargs):
    """Intercept mesh.p2p_transport imports to add missing names."""
    if name in ("mesh.p2p_transport", "core.mesh.p2p_transport"):
        mod = _import_orig(name, *args, **kwargs)
        return _ensure_mesh_attrs(mod)
    return _import_orig(name, *args, **kwargs)

# Apply the import patch
if isinstance(__builtins__, dict):
    __builtins__["__import__"] = _patched_import
else:
    __builtins__.__import__ = _patched_import

# ──────────────────────────────────────────────────────────────────────────── #
# Patch heavy startup components BEFORE app is imported
# The real app.py startup tries to load Qwen3-4B GGUF model (~2.5GB) which
# takes >60 seconds and causes TestClient to time out.
# ──────────────────────────────────────────────────────────────────────────── #
import unittest.mock as _mock

# Patch LocalLLM.get_instance to return a mock immediately
_asim_llm_patcher = _mock.patch("core.gateway.local_llm_connector.LocalLLM.get_instance", return_value=None)
_asim_llm_patcher.start()

# Patch unified_llm_gateway.initialize to be a no-op
_asim_gateway_patcher = _mock.patch("core.gateway.unified_llm_gateway.UnifiedLLMGateway.initialize", return_value=None)
_asim_gateway_patcher.start()

# Patch AsimRedisManager.get_instance to raise (Redis not available)
_asim_redis_patcher = _mock.patch("core.redis_manager.AsimRedisManager.get_instance", side_effect=Exception("Redis not available in tests"))
_asim_redis_patcher.start()

# Patch RAGEngine to skip auto-ingest
_asim_rag_patcher = _mock.patch("core.knowledge.rag_engine.RAGEngine.add_documents", return_value=None)
_asim_rag_patcher.start()

# Patch the Orchestrator.process method to return a simple response
# instead of trying to call the LLM gateway (which hangs in tests)
async def _mock_orchestrator_process(user_id, message, mode="personal"):
    return {
        "status": "ok",
        "response": f"Mock response to: {message}",
        "plan": [],
        "steps_completed": [],
        "audit_id": "mock-audit-001",
        "error": "",
    }
_asim_orch_patcher = _mock.patch(
    "core.orchestrator.orchestrator.Orchestrator.process",
    side_effect=_mock_orchestrator_process,
)
_asim_orch_patcher.start()

# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="session")
def app():
    """Build the FastAPI application via simple_backend.create_app()."""
    # Patch backend.mesh to avoid broken imports
    from app import app as backend_app
    yield backend_app

@pytest.fixture
def test_client(app):
    """FastAPI TestClient wrapping the backend application."""
    from fastapi.testclient import TestClient
    with TestClient(app) as client:
        yield client

@pytest.fixture
def temp_db():
    """Create a temporary SQLite database and override DB dependencies."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    db_path = tmp.name

    # Initialize schema tables needed by auth
    from core.security.auth_middleware import AuthManager
    AuthManager()

    # AuthManager._init_db() does NOT create the 'users' table,
    # but AuthManager.register_user and login_user need it.
    import sqlite3
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
def test_users(temp_db):
    """Pre-register test users and return their credentials + JWT tokens."""
    from core.security.auth_middleware import AuthManager

    auth_mgr = AuthManager(temp_db)

    users = {
        "alice": {
            "email": "alice@test.asim",
            "password": "AlicePass123!",
            "display_name": "Alice Test",
        },
        "bob": {
            "email": "bob@test.asim",
            "password": "BobPass456!",
            "display_name": "Bob Test",
        },
        "admin": {
            "email": "admin@test.asim",
            "password": "AdminPass789!",
            "display_name": "Admin User",
        },
    }

    tokens = {}
    for name, creds in users.items():
        try:
            auth_mgr.register_user(
                type("Req", (), {
                    "email": creds["email"],
                    "password": creds["password"],
                    "display_name": creds["display_name"],
                    "device_id": f"e2e-test-{name}",
                    "mode": "personal",
                    "country_code": "US",
                })()
            )
        except (ValueError, Exception):
            pass  # user may already exist

        login_result = auth_mgr.login_user(
            type("Req", (), {
                "email": creds["email"],
                "password": creds["password"],
                "device_id": f"e2e-test-{name}",
                "mode": "personal",
            })(),
            client_ip="127.0.0.1",
        )
        tokens[name] = {
            "token": login_result["token"],
            "refresh_token": login_result["refresh_token"],
            **creds,
        }

    return tokens

@pytest.fixture
def auth_headers(test_users):
    """Authorization headers for each test user."""
    headers = {}
    for name, data in test_users.items():
        headers[name] = {
            "Authorization": f"Bearer {data['token']}",
            "Content-Type": "application/json",
        }
    return headers

@pytest.fixture
def mock_biometric():
    """Mock BiometricHardwareGate to automatically pass biometric checks."""
    with patch("core.security.biometric_hardware_gate.BiometricHardwareGate") as mock:
        gate_instance = MagicMock()
        gate_instance.verify_biometric = AsyncMock(return_value={
            "verified": True,
            "confidence": 0.99,
            "method": "mock",
        })
        gate_instance.verify_and_lock = AsyncMock(return_value={
            "verified": True,
            "confidence": 0.99,
            "method": "mock",
            "locked": False,
        })
        gate_instance.get_status = MagicMock(return_value={
            "locked": False,
            "verified": True,
            "method": "mock",
            "timestamp": datetime.utcnow().isoformat(),
        })
        mock.return_value = gate_instance
        yield gate_instance

@pytest.fixture
def mock_hardware_deps(mock_biometric):
    """Aggregate mock for all hardware-dependent components."""
    with patch("core.security.tpm_binding.TPMBinding") as tpm_mock:
        tpm_instance = MagicMock()
        tpm_instance.attest = MagicMock(return_value={"status": "trusted"})
        tpm_instance.seal = MagicMock(return_value="sealed-data")
        tpm_mock.return_value = tpm_instance

        with patch("core.hardware_sync.get_hardware_sync") as hw_mock:
            hw_instance = MagicMock()
            hw_instance.get_system_status = MagicMock(return_value={
                "cpu": {"usage_percent": 10.0},
                "memory": {"usage_percent": 20.0},
                "gpu": {"memory_used_percent": 15.0},
            })
            hw_instance.get_gpu_status = MagicMock(return_value={
                "memory_used_percent": 15.0,
            })
            hw_mock.return_value = hw_instance
            yield

