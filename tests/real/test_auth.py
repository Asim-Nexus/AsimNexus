#!/usr/bin/env python3
"""
STATUS: REAL — Production-grade authentication tests
ASIMNEXUS Authentication Tests
==============================
"""

import os
import gc
import time
import pytest
import sqlite3
import tempfile
from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient
from backend.auth import AuthManager, setup_auth_routes, RegisterRequest, LoginRequest

class TestAuthManager:
    """Test suite for AuthManager class."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        Path(path).unlink(missing_ok=True)
        
        # Initialize users table to match simple_backend layout
        conn = sqlite3.connect(path)
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
        conn.close()

        yield path

        gc.collect()
        for _ in range(5):
            try:
                Path(path).unlink(missing_ok=True)
                break
            except PermissionError:
                time.sleep(0.1)

    @pytest.fixture
    def auth_manager(self, temp_db):
        return AuthManager(temp_db)

    def test_user_registration_and_login(self, auth_manager):
        # Register
        reg_req = RegisterRequest(
            email="founder_test@asimnexus.com",
            password="securePassword123!",
            display_name="Founder Test",
            country_code="NP"
        )
        user = auth_manager.register_user(reg_req)
        assert user["email"] == "founder_test@asimnexus.com"
        assert user["display_name"] == "Founder Test"

        # Login
        login_req = LoginRequest(
            email="founder_test@asimnexus.com",
            password="securePassword123!",
            device_id="device_hash_12345",
            mode="company"
        )
        login_res = auth_manager.login_user(login_req, "127.0.0.1")
        assert login_res["success"] is True
        assert "token" in login_res
        assert login_res["session"]["role"] == "founder"
        assert login_res["session"]["mode"] == "company"
        assert login_res["session"]["device_trust"] == "trusted"
        assert login_res["session"]["risk_score"] < 0.5
        assert "read_codebase" in login_res["session"]["consent_scope"]
        assert login_res["session"]["jurisdiction"] == "NP"

    def test_duplicate_registration_failure(self, auth_manager):
        reg_req = RegisterRequest(
            email="dup@test.com",
            password="password",
            display_name="Dup"
        )
        auth_manager.register_user(reg_req)
        with pytest.raises(ValueError, match="Email already registered"):
            auth_manager.register_user(reg_req)

    def test_login_invalid_credentials(self, auth_manager):
        reg_req = RegisterRequest(
            email="wrong@test.com",
            password="correct_password"
        )
        auth_manager.register_user(reg_req)

        login_req = LoginRequest(
            email="wrong@test.com",
            password="wrong_password"
        )
        with pytest.raises(ValueError, match="Invalid credentials"):
            auth_manager.login_user(login_req, "127.0.0.1")

    def test_lockout_mechanism(self, auth_manager):
        reg_req = RegisterRequest(
            email="lockout@test.com",
            password="correct"
        )
        auth_manager.register_user(reg_req)

        login_req = LoginRequest(
            email="lockout@test.com",
            password="wrong"
        )
        # Attempt 5 failed logins
        for _ in range(5):
            try:
                auth_manager.login_user(login_req, "127.0.0.1")
            except ValueError:
                pass

        # 6th attempt should trigger lockout check
        with pytest.raises(PermissionError, match="Account locked"):
            auth_manager.login_user(login_req, "127.0.0.1")

    def test_token_verification_and_hijack_prevention(self, auth_manager):
        reg_req = RegisterRequest(
            email="verify@test.com",
            password="password"
        )
        auth_manager.register_user(reg_req)

        login_req = LoginRequest(
            email="verify@test.com",
            password="password",
            device_id="dev_trust_1",
            mode="personal"
        )
        login_res = auth_manager.login_user(login_req, "127.0.0.1")
        token = login_res["token"]

        # Verify token successfully
        ver_res = auth_manager.verify_token(token, "127.0.0.1")
        assert ver_res["valid"] is True
        assert ver_res["mode"] == "personal"

        # Verify token with IP mismatch (Hijack attempt)
        with pytest.raises(ValueError, match="Client IP mismatch"):
            auth_manager.verify_token(token, "192.168.1.50")

    def test_session_revocation(self, auth_manager):
        reg_req = RegisterRequest(
            email="rev@test.com",
            password="password"
        )
        auth_manager.register_user(reg_req)

        login_req = LoginRequest(
            email="rev@test.com",
            password="password"
        )
        login_res = auth_manager.login_user(login_req, "127.0.0.1")
        token = login_res["token"]

        # Verify first
        ver = auth_manager.verify_token(token, "127.0.0.1")
        assert ver["valid"] is True

        # Revoke session
        revoked = auth_manager.revoke_session(token)
        assert revoked is True

        # Verify after revocation (should fail)
        with pytest.raises(ValueError, match="Session not found"):
            auth_manager.verify_token(token, "127.0.0.1")


class TestAuthRoutes:
    """Test suite for integrated API auth routes."""

    @pytest.fixture
    def temp_db(self):
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        Path(path).unlink(missing_ok=True)
        
        conn = sqlite3.connect(path)
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
        conn.close()

        yield path

        gc.collect()
        for _ in range(5):
            try:
                Path(path).unlink(missing_ok=True)
                break
            except PermissionError:
                time.sleep(0.1)

    @pytest.fixture
    def app(self, temp_db):
        app = FastAPI()
        setup_auth_routes(app, temp_db)
        return app

    @pytest.fixture
    def client(self, app):
        return TestClient(app)

    def test_routes_integration_flow(self, client):
        # 1. Register via API
        reg_resp = client.post("/api/auth/register", json={
            "email": "route_admin@asimnexus.com",
            "password": "password123",
            "display_name": "Route Admin",
            "country_code": "NP"
        })
        assert reg_resp.status_code == 200
        assert reg_resp.json()["email"] == "route_admin@asimnexus.com"

        # 2. Login via API
        login_resp = client.post("/api/auth/login", json={
            "email": "route_admin@asimnexus.com",
            "password": "password123",
            "device_id": "route_dev_hash",
            "mode": "company"
        })
        assert login_resp.status_code == 200
        data = login_resp.json()
        token = data["token"]
        assert "token" in data
        assert data["session"]["role"] == "founder"

        # 3. Verify via API
        ver_resp = client.post("/api/auth/verify", headers={"Authorization": f"Bearer {token}"})
        assert ver_resp.status_code == 200
        assert ver_resp.json()["valid"] is True
        assert ver_resp.json()["mode"] == "company"

        # 4. Get active sessions
        sess_resp = client.get("/api/auth/sessions", headers={"Authorization": f"Bearer {token}"})
        assert sess_resp.status_code == 200
        assert len(sess_resp.json()) == 1
        assert sess_resp.json()[0]["mode_boundary"] == "company"

        # 5. Logout
        logout_resp = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
        assert logout_resp.status_code == 200
        assert logout_resp.json()["success"] is True

        # 6. Verify again should fail
        ver_resp = client.post("/api/auth/verify", headers={"Authorization": f"Bearer {token}"})
        assert ver_resp.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
