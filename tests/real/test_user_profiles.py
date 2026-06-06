#!/usr/bin/env python3
"""
ASIMNEXUS User Profile & Teams Tests
=====================================
Tests for UserProfileManager (unit) and user profile/team routes (integration).
Covers: profile CRUD, team CRUD, member management, permissions, edge cases.
"""
import os
import gc
import time
import json
import pytest
import sqlite3
import tempfile
import secrets
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from backend.user_profiles import (
    UserProfileManager,
    setup_user_profile_routes,
    UpdateProfileRequest,
    CreateTeamRequest,
    UpdateTeamRequest,
    InviteMemberRequest,
    ChangeMemberRoleRequest,
)


# ═══════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def temp_db():
    """Create temporary SQLite database for testing."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    Path(path).unlink(missing_ok=True)

    # Create users table matching simple_backend schema
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
            created_at TEXT DEFAULT (datetime('now')),
            bio TEXT DEFAULT '',
            avatar_url TEXT DEFAULT '',
            last_login TEXT DEFAULT '',
            trust_level REAL DEFAULT 0.0,
            role TEXT DEFAULT 'user'
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS active_sessions (
            token TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
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
def profile_manager(temp_db):
    """Create a UserProfileManager with temp DB."""
    return UserProfileManager(temp_db)


@pytest.fixture
def test_users(temp_db):
    """Create test users in the database and return their IDs."""
    conn = sqlite3.connect(temp_db)
    users = {}
    for name, email in [
        ("alice", "alice@test.com"),
        ("bob", "bob@test.com"),
        ("charlie", "charlie@test.com"),
    ]:
        uid = f"user_{secrets.token_hex(8)}"
        conn.execute(
            "INSERT INTO users (id, email, display_name, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (uid, email, name.capitalize(), "hash", "user", datetime.now(timezone.utc).isoformat())
        )
        users[name] = uid
    conn.commit()
    conn.close()
    return users


@pytest.fixture
def auth_tokens(temp_db, test_users):
    """Create valid auth session tokens for all test users."""
    conn = sqlite3.connect(temp_db)
    tokens = {}
    for name, uid in test_users.items():
        token = f"test_token_{secrets.token_hex(16)}"
        conn.execute(
            "INSERT INTO active_sessions (token, user_id) VALUES (?, ?)",
            (token, uid)
        )
        tokens[name] = token
    conn.commit()
    conn.close()
    return tokens


# ═══════════════════════════════════════════════════════════════════════════
# Unit Tests: UserProfileManager
# ═══════════════════════════════════════════════════════════════════════════

class TestUserProfileManager:
    """Unit tests for UserProfileManager class."""

    # ── Profile Tests ──────────────────────────────────────────────────────

    def test_get_profile(self, profile_manager, test_users):
        """Get full profile for existing user."""
        profile = profile_manager.get_profile(test_users["alice"])
        assert profile["id"] == test_users["alice"]
        assert profile["email"] == "alice@test.com"
        assert profile["display_name"] == "Alice"
        assert "bio" in profile
        assert "avatar_url" in profile
        assert "trust_level" in profile
        assert "created_at" in profile

    def test_get_profile_nonexistent_user(self, profile_manager):
        """Get profile for non-existent user raises ValueError."""
        with pytest.raises(ValueError, match="User not found"):
            profile_manager.get_profile("nonexistent_id")

    def test_update_profile(self, profile_manager, test_users):
        """Update multiple profile fields."""
        req = UpdateProfileRequest(
            display_name="Alice Updated",
            bio="Hello, I am Alice!",
            avatar_url="https://example.com/avatar.jpg",
            country_code="US"
        )
        result = profile_manager.update_profile(test_users["alice"], req)
        assert result["display_name"] == "Alice Updated"
        assert result["bio"] == "Hello, I am Alice!"
        assert result["avatar_url"] == "https://example.com/avatar.jpg"
        assert result["country_code"] == "US"

        # Verify persistence
        profile = profile_manager.get_profile(test_users["alice"])
        assert profile["bio"] == "Hello, I am Alice!"

    def test_update_profile_partial(self, profile_manager, test_users):
        """Update only some profile fields."""
        req = UpdateProfileRequest(bio="Just my bio")
        result = profile_manager.update_profile(test_users["alice"], req)
        assert result["bio"] == "Just my bio"
        assert result["display_name"] == "Alice"  # unchanged

    def test_update_profile_no_fields(self, profile_manager, test_users):
        """Update with no fields raises error."""
        req = UpdateProfileRequest()
        with pytest.raises(ValueError, match="No fields to update"):
            profile_manager.update_profile(test_users["alice"], req)

    def test_get_public_profile(self, profile_manager, test_users):
        """Get public profile (limited fields)."""
        profile = profile_manager.get_public_profile(test_users["alice"])
        assert profile["id"] == test_users["alice"]
        assert profile["display_name"] == "Alice"
        # Public profile should not include email or role
        assert "email" not in profile
        assert "role" not in profile

    def test_get_public_profile_nonexistent(self, profile_manager):
        """Get public profile for non-existent user raises error."""
        with pytest.raises(ValueError, match="User not found"):
            profile_manager.get_public_profile("nonexistent_id")

    # ── Team Tests ─────────────────────────────────────────────────────────

    def test_create_team(self, profile_manager, test_users):
        """Create a new team and verify owner membership."""
        req = CreateTeamRequest(name="Test Team", description="A test team")
        team = profile_manager.create_team(test_users["alice"], req)
        assert team["name"] == "Test Team"
        assert team["description"] == "A test team"
        assert team["owner_id"] == test_users["alice"]
        assert team["member_role"] == "owner"
        assert team["member_count"] == 1

    def test_list_teams(self, profile_manager, test_users):
        """List teams for a user."""
        profile_manager.create_team(test_users["alice"], CreateTeamRequest(name="Team A"))
        profile_manager.create_team(test_users["alice"], CreateTeamRequest(name="Team B"))
        teams = profile_manager.list_teams(test_users["alice"])
        assert len(teams) == 2
        names = [t["name"] for t in teams]
        assert "Team A" in names
        assert "Team B" in names
        for t in teams:
            assert t["member_role"] == "owner"
            assert t["member_count"] == 1

    def test_get_team(self, profile_manager, test_users):
        """Get team details as a member."""
        team = profile_manager.create_team(test_users["alice"], CreateTeamRequest(name="My Team"))
        result = profile_manager.get_team(team["id"], test_users["alice"])
        assert result["id"] == team["id"]
        assert result["name"] == "My Team"
        assert result["member_role"] == "owner"

    def test_get_team_not_member(self, profile_manager, test_users):
        """Non-member cannot access team."""
        team = profile_manager.create_team(test_users["alice"], CreateTeamRequest(name="Private"))
        with pytest.raises(PermissionError, match="Not a member"):
            profile_manager.get_team(team["id"], test_users["bob"])

    def test_get_team_nonexistent(self, profile_manager, test_users):
        """Get non-existent team raises error."""
        with pytest.raises(ValueError, match="Team not found"):
            profile_manager.get_team("nonexistent_team", test_users["alice"])

    def test_update_team(self, profile_manager, test_users):
        """Update team settings as admin/owner."""
        team = profile_manager.create_team(test_users["alice"], CreateTeamRequest(name="Original"))
        req = UpdateTeamRequest(name="Updated", description="New description")
        result = profile_manager.update_team(team["id"], test_users["alice"], req)
        assert result["name"] == "Updated"
        assert result["description"] == "New description"

    def test_update_team_not_admin(self, profile_manager, test_users):
        """Non-admin cannot update team."""
        team = profile_manager.create_team(test_users["alice"], CreateTeamRequest(name="Team"))
        with pytest.raises(PermissionError, match="Only team admins"):
            profile_manager.update_team(team["id"], test_users["bob"], UpdateTeamRequest(name="Hacked"))

    # ── Member Tests ──────────────────────────────────────────────────────

    def test_invite_member(self, profile_manager, test_users):
        """Invite a user to join a team."""
        team = profile_manager.create_team(test_users["alice"], CreateTeamRequest(name="Team"))
        result = profile_manager.invite_member(
            team["id"], test_users["alice"],
            InviteMemberRequest(user_id=test_users["bob"], role="member")
        )
        assert result["success"] is True
        assert result["user_id"] == test_users["bob"]
        assert result["display_name"] == "Bob"

    def test_invite_duplicate(self, profile_manager, test_users):
        """Invite an existing member raises error."""
        team = profile_manager.create_team(test_users["alice"], CreateTeamRequest(name="Team"))
        profile_manager.invite_member(team["id"], test_users["alice"],
            InviteMemberRequest(user_id=test_users["bob"]))
        with pytest.raises(ValueError, match="already a team member"):
            profile_manager.invite_member(team["id"], test_users["alice"],
                InviteMemberRequest(user_id=test_users["bob"]))

    def test_invite_nonexistent_user(self, profile_manager, test_users):
        """Invite non-existent user raises error."""
        team = profile_manager.create_team(test_users["alice"], CreateTeamRequest(name="Team"))
        with pytest.raises(ValueError, match="Target user not found"):
            profile_manager.invite_member(team["id"], test_users["alice"],
                InviteMemberRequest(user_id="nonexistent_id"))

    def test_invite_by_email(self, profile_manager, test_users):
        """Invite a user by email."""
        team = profile_manager.create_team(test_users["alice"], CreateTeamRequest(name="Team"))
        result = profile_manager.invite_member(
            team["id"], test_users["alice"],
            InviteMemberRequest(email="bob@test.com", role="member")
        )
        assert result["success"] is True
        assert result["user_id"] == test_users["bob"]

    def test_invite_not_admin(self, profile_manager, test_users):
        """Non-admin cannot invite members."""
        team = profile_manager.create_team(test_users["alice"], CreateTeamRequest(name="Team"))
        # Invite bob as member (not admin)
        profile_manager.invite_member(team["id"], test_users["alice"],
            InviteMemberRequest(user_id=test_users["bob"], role="member"))
        # Bob (a regular member) tries to invite charlie - should fail
        with pytest.raises(PermissionError, match="Only team admins"):
            profile_manager.invite_member(team["id"], test_users["bob"],
                InviteMemberRequest(user_id=test_users["charlie"]))

    def test_list_members(self, profile_manager, test_users):
        """List all members of a team."""
        team = profile_manager.create_team(test_users["alice"], CreateTeamRequest(name="Team"))
        profile_manager.invite_member(team["id"], test_users["alice"],
            InviteMemberRequest(user_id=test_users["bob"]))
        members = profile_manager.list_members(team["id"], test_users["alice"])
        assert len(members) == 2
        member_ids = [m["id"] for m in members]
        assert test_users["alice"] in member_ids
        assert test_users["bob"] in member_ids

    def test_list_members_not_member(self, profile_manager, test_users):
        """Non-member cannot list members."""
        team = profile_manager.create_team(test_users["alice"], CreateTeamRequest(name="Team"))
        with pytest.raises(PermissionError, match="Not a member"):
            profile_manager.list_members(team["id"], test_users["bob"])

    def test_remove_member(self, profile_manager, test_users):
        """Remove a member from a team."""
        team = profile_manager.create_team(test_users["alice"], CreateTeamRequest(name="Team"))
        profile_manager.invite_member(team["id"], test_users["alice"],
            InviteMemberRequest(user_id=test_users["bob"]))
        result = profile_manager.remove_member(team["id"], test_users["bob"], test_users["alice"])
        assert result["success"] is True
        members = profile_manager.list_members(team["id"], test_users["alice"])
        assert len(members) == 1

    def test_remove_self_forbidden(self, profile_manager, test_users):
        """Cannot remove yourself from a team."""
        team = profile_manager.create_team(test_users["alice"], CreateTeamRequest(name="Team"))
        with pytest.raises(ValueError, match="Cannot remove yourself"):
            profile_manager.remove_member(team["id"], test_users["alice"], test_users["alice"])

    def test_remove_not_admin(self, profile_manager, test_users):
        """Non-admin cannot remove members."""
        team = profile_manager.create_team(test_users["alice"], CreateTeamRequest(name="Team"))
        profile_manager.invite_member(team["id"], test_users["alice"],
            InviteMemberRequest(user_id=test_users["bob"], role="member"))
        with pytest.raises(PermissionError, match="Only team admins"):
            profile_manager.remove_member(team["id"], test_users["alice"], test_users["bob"])

    def test_remove_nonexistent_member(self, profile_manager, test_users):
        """Remove non-existent member raises error."""
        team = profile_manager.create_team(test_users["alice"], CreateTeamRequest(name="Team"))
        with pytest.raises(ValueError, match="not a team member"):
            profile_manager.remove_member(team["id"], "nonexistent_id", test_users["alice"])

    def test_change_member_role(self, profile_manager, test_users):
        """Change a member's role."""
        team = profile_manager.create_team(test_users["alice"], CreateTeamRequest(name="Team"))
        profile_manager.invite_member(team["id"], test_users["alice"],
            InviteMemberRequest(user_id=test_users["bob"]))
        result = profile_manager.change_member_role(
            team["id"], test_users["bob"], test_users["alice"], "admin")
        assert result["success"] is True
        assert result["new_role"] == "admin"

        # Verify by listing members
        members = profile_manager.list_members(team["id"], test_users["alice"])
        bob = [m for m in members if m["id"] == test_users["bob"]][0]
        assert bob["role"] == "admin"

    def test_change_member_role_invalid(self, profile_manager, test_users):
        """Change to invalid role raises error."""
        team = profile_manager.create_team(test_users["alice"], CreateTeamRequest(name="Team"))
        profile_manager.invite_member(team["id"], test_users["alice"],
            InviteMemberRequest(user_id=test_users["bob"]))
        with pytest.raises(ValueError, match="Invalid role"):
            profile_manager.change_member_role(
                team["id"], test_users["bob"], test_users["alice"], "superadmin")

    def test_change_member_role_not_admin(self, profile_manager, test_users):
        """Non-admin (regular member) cannot change roles."""
        team = profile_manager.create_team(test_users["alice"], CreateTeamRequest(name="Team"))
        # Invite bob as regular member
        profile_manager.invite_member(team["id"], test_users["alice"],
            InviteMemberRequest(user_id=test_users["bob"], role="member"))
        # Bob (a member) tries to change alice's role - should fail
        with pytest.raises(PermissionError, match="Only team admins"):
            profile_manager.change_member_role(
                team["id"], test_users["alice"], test_users["bob"], "admin")

    def test_get_permissions(self, profile_manager, test_users):
        """Get permissions for a user."""
        perms = profile_manager.get_permissions(test_users["alice"])
        assert perms["user_id"] == test_users["alice"]
        assert perms["global_role"] == "user"
        assert perms["can_create_teams"] is True
        assert "teams" in perms

    def test_full_team_flow(self, profile_manager, test_users):
        """Complete team lifecycle: create, invite, list, change role, remove."""
        # 1. Create team
        team = profile_manager.create_team(test_users["alice"],
            CreateTeamRequest(name="Flow Test"))
        assert team["member_count"] == 1

        # 2. Invite members
        profile_manager.invite_member(team["id"], test_users["alice"],
            InviteMemberRequest(user_id=test_users["bob"]))
        profile_manager.invite_member(team["id"], test_users["alice"],
            InviteMemberRequest(user_id=test_users["charlie"], role="viewer"))

        # 3. List members
        members = profile_manager.list_members(team["id"], test_users["alice"])
        assert len(members) == 3

        # 4. Change role
        profile_manager.change_member_role(
            team["id"], test_users["bob"], test_users["alice"], "admin")

        # 5. List teams for bob
        bob_teams = profile_manager.list_teams(test_users["bob"])
        assert len(bob_teams) == 1
        assert bob_teams[0]["member_role"] == "admin"

        # 6. Remove charlie
        profile_manager.remove_member(team["id"], test_users["charlie"], test_users["alice"])
        members = profile_manager.list_members(team["id"], test_users["alice"])
        assert len(members) == 2

        # 7. Check permissions
        perms = profile_manager.get_permissions(test_users["alice"])
        assert len(perms["teams"]) == 1


# ═══════════════════════════════════════════════════════════════════════════
# Integration Tests: Routes
# ═══════════════════════════════════════════════════════════════════════════

class TestUserProfileRoutes:
    """Integration tests for user profile and team routes."""

    @pytest.fixture(autouse=True)
    def _setup(self, temp_db, test_users, auth_tokens):
        """Set up test app and client with mocked auth dependency."""
        self.temp_db = temp_db
        self.test_users = test_users
        self.auth_tokens = auth_tokens

        # Create the FastAPI test app
        self.app = FastAPI()
        setup_user_profile_routes(self.app, temp_db)

        # Patch _get_token_user globally for all route tests
        # This patcher remains active throughout the test session
        self._patcher = patch("backend.user_profiles._get_token_user")
        mock_get_token_user = self._patcher.start()

        def side_effect(request):
            auth = request.headers.get("Authorization", "")
            token = auth.replace("Bearer ", "") if auth.startswith("Bearer ") else ""
            # Map tokens to users
            for name, t in self.auth_tokens.items():
                if t == token:
                    return {"user_id": self.test_users[name], "role": "user", "mode": "personal"}
            raise HTTPException(status_code=401, detail="Invalid token")

        mock_get_token_user.side_effect = side_effect
        self.client = TestClient(self.app)

    def teardown_method(self):
        if hasattr(self, '_patcher'):
            self._patcher.stop()

    def _auth_header(self, user="alice"):
        return {"Authorization": f"Bearer {self.auth_tokens[user]}"}

    # ── Profile Routes ─────────────────────────────────────────────────────

    def test_get_profile_route(self):
        """GET /api/user/profile returns profile."""
        resp = self.client.get("/api/user/profile", headers=self._auth_header("alice"))
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["success"] is True
        assert data["profile"]["display_name"] == "Alice"

    def test_get_profile_unauthorized(self):
        """GET /api/user/profile without auth returns 401."""
        resp = self.client.get("/api/user/profile")
        assert resp.status_code == 401

    def test_update_profile_route(self):
        """PUT /api/user/profile updates and returns profile."""
        resp = self.client.put(
            "/api/user/profile",
            json={"display_name": "Alice New", "bio": "Updated bio"},
            headers=self._auth_header("alice")
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["success"] is True
        assert data["profile"]["display_name"] == "Alice New"
        assert data["profile"]["bio"] == "Updated bio"

    def test_get_public_profile_route(self):
        """GET /api/user/profiles/{user_id} returns public profile."""
        # Get alice's profile first to know her ID
        resp = self.client.get("/api/user/profile", headers=self._auth_header("alice"))
        alice_id = resp.json()["profile"]["id"]

        resp = self.client.get(f"/api/user/profiles/{alice_id}", headers=self._auth_header("bob"))
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["success"] is True
        assert data["profile"]["display_name"] == "Alice"
        assert "email" not in data["profile"]

    def test_get_public_profile_nonexistent(self):
        """GET /api/user/profiles/nonexistent returns 404."""
        resp = self.client.get("/api/user/profiles/nonexistent_id", headers=self._auth_header("alice"))
        assert resp.status_code == 404

    # ── Team Routes ────────────────────────────────────────────────────────

    def test_create_team_route(self):
        """POST /api/teams creates a new team."""
        resp = self.client.post(
            "/api/teams",
            json={"name": "Test Team", "description": "A test team"},
            headers=self._auth_header("alice")
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["success"] is True
        assert data["team"]["name"] == "Test Team"
        assert data["team"]["member_role"] == "owner"

    def test_list_teams_route(self):
        """GET /api/teams lists user's teams."""
        # Create a team first
        self.client.post("/api/teams", json={"name": "My Team"}, headers=self._auth_header("alice"))
        resp = self.client.get("/api/teams", headers=self._auth_header("alice"))
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["success"] is True
        assert len(data["teams"]) >= 1

    def test_get_team_route(self):
        """GET /api/teams/{team_id} returns team details."""
        create_resp = self.client.post(
            "/api/teams", json={"name": "Detail Test"}, headers=self._auth_header("alice"))
        team_id = create_resp.json()["team"]["id"]

        resp = self.client.get(f"/api/teams/{team_id}", headers=self._auth_header("alice"))
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["team"]["name"] == "Detail Test"

    def test_update_team_route(self):
        """PUT /api/teams/{team_id} updates team settings."""
        create_resp = self.client.post(
            "/api/teams", json={"name": "Original"}, headers=self._auth_header("alice"))
        team_id = create_resp.json()["team"]["id"]

        resp = self.client.put(
            f"/api/teams/{team_id}",
            json={"name": "Updated", "description": "New desc"},
            headers=self._auth_header("alice")
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["team"]["name"] == "Updated"

    # ── Member Routes ──────────────────────────────────────────────────────

    def test_invite_member_route(self):
        """POST /api/teams/{team_id}/members invites a user."""
        create_resp = self.client.post(
            "/api/teams", json={"name": "Invite Test"}, headers=self._auth_header("alice"))
        team_id = create_resp.json()["team"]["id"]

        resp = self.client.post(
            f"/api/teams/{team_id}/members",
            json={"email": "bob@test.com", "role": "member"},
            headers=self._auth_header("alice")
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["success"] is True

    def test_list_members_route(self):
        """GET /api/teams/{team_id}/members lists members."""
        create_resp = self.client.post(
            "/api/teams", json={"name": "Members List"}, headers=self._auth_header("alice"))
        team_id = create_resp.json()["team"]["id"]

        # Invite bob
        self.client.post(
            f"/api/teams/{team_id}/members",
            json={"email": "bob@test.com", "role": "member"},
            headers=self._auth_header("alice")
        )

        resp = self.client.get(f"/api/teams/{team_id}/members", headers=self._auth_header("alice"))
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert len(data["members"]) == 2

    def test_remove_member_route(self):
        """DELETE /api/teams/{team_id}/members/{user_id} removes member."""
        create_resp = self.client.post(
            "/api/teams", json={"name": "Remove Test"}, headers=self._auth_header("alice"))
        team_id = create_resp.json()["team"]["id"]

        # Invite bob
        self.client.post(
            f"/api/teams/{team_id}/members",
            json={"email": "bob@test.com", "role": "member"},
            headers=self._auth_header("alice")
        )

        resp = self.client.delete(
            f"/api/teams/{team_id}/members/{self.test_users['bob']}",
            headers=self._auth_header("alice")
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["success"] is True

    def test_change_member_role_route(self):
        """PUT /api/teams/{team_id}/members/{user_id}/role changes role."""
        create_resp = self.client.post(
            "/api/teams", json={"name": "Role Test"}, headers=self._auth_header("alice"))
        team_id = create_resp.json()["team"]["id"]

        # Invite bob
        self.client.post(
            f"/api/teams/{team_id}/members",
            json={"email": "bob@test.com", "role": "member"},
            headers=self._auth_header("alice")
        )

        resp = self.client.put(
            f"/api/teams/{team_id}/members/{self.test_users['bob']}/role",
            json={"user_id": self.test_users["bob"], "role": "admin"},
            headers=self._auth_header("alice")
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["success"] is True
        assert data["new_role"] == "admin"

    def test_change_member_role_invalid_route(self):
        """PUT with invalid role returns 400 (ValueError caught in route handler)."""
        create_resp = self.client.post(
            "/api/teams", json={"name": "Invalid Role"}, headers=self._auth_header("alice"))
        team_id = create_resp.json()["team"]["id"]

        self.client.post(
            f"/api/teams/{team_id}/members",
            json={"email": "bob@test.com", "role": "member"},
            headers=self._auth_header("alice")
        )

        resp = self.client.put(
            f"/api/teams/{team_id}/members/{self.test_users['bob']}/role",
            json={"user_id": self.test_users["bob"], "role": "superadmin"},
            headers=self._auth_header("alice")
        )
        assert resp.status_code == 400  # ValueError caught and returned as 400 by route handler

    def test_get_permissions_route(self):
        """GET /api/permissions returns permissions."""
        resp = self.client.get("/api/permissions", headers=self._auth_header("alice"))
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["success"] is True
        assert data["permissions"]["can_create_teams"] is True

    def test_unauthorized_access_all_endpoints(self):
        """All endpoints return 401 without auth."""
        endpoints = [
            ("GET", "/api/user/profile"),
            ("PUT", "/api/user/profile"),
            ("GET", "/api/user/profiles/some_id"),
            ("GET", "/api/teams"),
            ("POST", "/api/teams"),
            ("GET", "/api/teams/some_id"),
            ("PUT", "/api/teams/some_id"),
            ("POST", "/api/teams/some_id/members"),
            ("GET", "/api/teams/some_id/members"),
            ("DELETE", "/api/teams/some_id/members/some_id"),
            ("PUT", "/api/teams/some_id/members/some_id/role"),
            ("GET", "/api/permissions"),
        ]
        for method, path in endpoints:
            resp = self.client.request(method, path)
            assert resp.status_code == 401, f"{method} {path} should return 401"

    def test_duplicate_invite_route(self):
        """Inviting an existing member returns 400."""
        create_resp = self.client.post(
            "/api/teams", json={"name": "Duplicate"}, headers=self._auth_header("alice"))
        team_id = create_resp.json()["team"]["id"]

        # First invite - should succeed
        resp1 = self.client.post(
            f"/api/teams/{team_id}/members",
            json={"email": "bob@test.com", "role": "member"},
            headers=self._auth_header("alice")
        )
        assert resp1.status_code == 200

        # Second invite - should fail
        resp2 = self.client.post(
            f"/api/teams/{team_id}/members",
            json={"email": "bob@test.com", "role": "member"},
            headers=self._auth_header("alice")
        )
        assert resp2.status_code == 400

    def test_unauthorized_team_access(self):
        """Non-member cannot access team details."""
        create_resp = self.client.post(
            "/api/teams", json={"name": "Private"}, headers=self._auth_header("alice"))
        team_id = create_resp.json()["team"]["id"]

        # Bob tries to access alice's team
        resp = self.client.get(f"/api/teams/{team_id}", headers=self._auth_header("bob"))
        assert resp.status_code == 403
