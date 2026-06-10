"""
User Profile & Teams Management Module
Provides CRUD operations for user profiles, teams, team membership, and permissions.
All endpoints require JWT authentication via _get_token_user().
"""
import sqlite3
import secrets
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from fastapi import APIRouter, Request, HTTPException

logger = logging.getLogger(__name__)

# ── Pydantic Models ──────────────────────────────────────────────────────────

class UpdateProfileRequest(BaseModel):
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    country_code: Optional[str] = None

class CreateTeamRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = ""
    icon: Optional[str] = "👥"

class UpdateTeamRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    icon: Optional[str] = None

class InviteMemberRequest(BaseModel):
    email: Optional[str] = None
    user_id: Optional[str] = None
    role: str = "member"

class ChangeMemberRoleRequest(BaseModel):
    user_id: str
    role: str = Field(..., pattern="^(admin|member|viewer|owner)$")

# ── Token Auth Dependency ───────────────────────────────────────────────────

def _get_token_user(request: Request) -> Dict:
    """Extract and verify JWT user from request Authorization header.
    Returns dict with user_id, role, mode.
    Raises HTTPException(401) if missing/invalid.
    """
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    token = auth.split(" ", 1)[1]
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")
    try:
        # Use simple_backend's verify token logic
        from simple_backend import _get_user_from_token as verify_token
        user = verify_token(token)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        return {"user_id": user["id"], "role": user.get("role", "user"), "mode": user.get("universe_mode", "personal")}
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Token verification failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")


# ── UserProfileManager ──────────────────────────────────────────────────────

class UserProfileManager:
    """Manages user profiles, teams, and permissions using SQLite storage."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_db(self):
        """Ensure required columns and tables exist."""
        with self._get_conn() as conn:
            # Add profile columns to users table if not present
            for col in ["bio", "avatar_url", "last_login", "trust_level"]:
                try:
                    conn.execute(f"ALTER TABLE users ADD COLUMN {col} TEXT DEFAULT ''")
                except sqlite3.OperationalError:
                    pass  # Column already exists
            try:
                conn.execute("ALTER TABLE users ADD COLUMN trust_level REAL DEFAULT 0.0")
            except sqlite3.OperationalError:
                pass

            # Teams table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS teams (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    icon TEXT DEFAULT '👥',
                    owner_id TEXT NOT NULL,
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (owner_id) REFERENCES users(id)
                )
            """)

            # Team members table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS team_members (
                    team_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'member',
                    invited_by TEXT,
                    joined_at TEXT DEFAULT (datetime('now')),
                    PRIMARY KEY (team_id, user_id),
                    FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            # Notifications table for team invites
            conn.execute("""
                CREATE TABLE IF NOT EXISTS team_notifications (
                    id TEXT PRIMARY KEY,
                    team_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    type TEXT NOT NULL DEFAULT 'invite',
                    message TEXT,
                    read INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

    # ── Profile Methods ─────────────────────────────────────────────────────

    def get_profile(self, user_id: str) -> Dict:
        """Get full profile for the authenticated user."""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT id, email, display_name, bio, avatar_url, country_code, "
                "universe_mode, theme, created_at, last_login, trust_level, role "
                "FROM users WHERE id = ?",
                (user_id,)
            ).fetchone()
            if not row:
                raise ValueError("User not found")
            return dict(row)

    def update_profile(self, user_id: str, req: UpdateProfileRequest) -> Dict:
        """Update profile fields for the authenticated user."""
        fields = req.model_dump(exclude_none=True)
        if not fields:
            raise ValueError("No fields to update")

        set_clause = ", ".join(f"{k} = ?" for k in fields.keys())
        values = list(fields.values()) + [user_id]

        with self._get_conn() as conn:
            conn.execute(
                f"UPDATE users SET {set_clause} WHERE id = ?",
                values
            )
            if conn.total_changes == 0:
                raise ValueError("User not found")
            row = conn.execute(
                "SELECT id, email, display_name, bio, avatar_url, country_code, "
                "universe_mode, theme, created_at, last_login, trust_level, role "
                "FROM users WHERE id = ?",
                (user_id,)
            ).fetchone()
            return dict(row)

    def get_public_profile(self, target_user_id: str) -> Dict:
        """Get a limited public profile for another user."""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT id, display_name, bio, avatar_url, country_code, "
                "created_at, trust_level "
                "FROM users WHERE id = ?",
                (target_user_id,)
            ).fetchone()
            if not row:
                raise ValueError("User not found")
            return dict(row)

    # ── Team Methods ────────────────────────────────────────────────────────

    def create_team(self, owner_id: str, req: CreateTeamRequest) -> Dict:
        """Create a new team. Creator becomes owner."""
        team_id = f"team_{secrets.token_hex(8)}"
        now = datetime.now(timezone.utc).isoformat()

        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO teams (id, name, description, icon, owner_id, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (team_id, req.name, req.description, req.icon, owner_id, now, now)
            )
            conn.execute(
                "INSERT INTO team_members (team_id, user_id, role, invited_by) "
                "VALUES (?, ?, ?, ?)",
                (team_id, owner_id, "owner", owner_id)
            )

        return self.get_team(team_id, owner_id)

    def list_teams(self, user_id: str) -> List[Dict]:
        """List all teams the user is a member of."""
        with self._get_conn() as conn:
            rows = conn.execute("""
                SELECT t.id, t.name, t.description, t.icon, t.owner_id, t.created_at,
                       tm.role as member_role,
                       (SELECT COUNT(*) FROM team_members WHERE team_id = t.id) as member_count
                FROM teams t
                JOIN team_members tm ON t.id = tm.team_id
                WHERE tm.user_id = ?
                ORDER BY t.created_at DESC
            """, (user_id,)).fetchall()
            return [dict(r) for r in rows]

    def get_team(self, team_id: str, user_id: str) -> Dict:
        """Get team details. User must be a member."""
        with self._get_conn() as conn:
            # Check team exists first
            team = conn.execute(
                "SELECT * FROM teams WHERE id = ?", (team_id,)
            ).fetchone()
            if not team:
                raise ValueError("Team not found")

            # Then check membership
            member = conn.execute(
                "SELECT role FROM team_members WHERE team_id = ? AND user_id = ?",
                (team_id, user_id)
            ).fetchone()
            if not member:
                raise PermissionError("Not a member of this team")

            result = dict(team)
            result["member_role"] = member["role"]
            result["member_count"] = conn.execute(
                "SELECT COUNT(*) FROM team_members WHERE team_id = ?",
                (team_id,)
            ).fetchone()[0]
            return result

    def update_team(self, team_id: str, user_id: str, req: UpdateTeamRequest) -> Dict:
        """Update team settings. Only admin/owner can update."""
        fields = req.model_dump(exclude_none=True)
        if not fields:
            raise ValueError("No fields to update")

        with self._get_conn() as conn:
            # Verify admin/owner
            member = conn.execute(
                "SELECT role FROM team_members WHERE team_id = ? AND user_id = ?",
                (team_id, user_id)
            ).fetchone()
            if not member or member["role"] not in ("admin", "owner"):
                raise PermissionError("Only team admins can update team settings")

            set_clause = ", ".join(f"{k} = ?" for k in fields.keys())
            values = list(fields.values()) + [team_id]
            conn.execute(f"UPDATE teams SET {set_clause}, updated_at = datetime('now') WHERE id = ?", values)

        return self.get_team(team_id, user_id)

    # ── Member Methods ──────────────────────────────────────────────────────

    def invite_member(self, team_id: str, inviter_id: str, req: InviteMemberRequest) -> Dict:
        """Invite a user to join a team. Inviter must be admin/owner."""
        # Determine target user
        target_user_id = req.user_id
        if req.email and not target_user_id:
            with self._get_conn() as conn:
                user = conn.execute(
                    "SELECT id, display_name FROM users WHERE email = ?",
                    (req.email,)
                ).fetchone()
                if not user:
                    raise ValueError("No user found with that email")
                target_user_id = user["id"]
                display_name = user["display_name"]

        if not target_user_id:
            raise ValueError("Either user_id or email is required")

        with self._get_conn() as conn:
            # Verify inviter is admin/owner
            inviter = conn.execute(
                "SELECT role FROM team_members WHERE team_id = ? AND user_id = ?",
                (team_id, inviter_id)
            ).fetchone()
            if not inviter or inviter["role"] not in ("admin", "owner"):
                raise PermissionError("Only team admins can invite members")

            # Check if already a member
            existing = conn.execute(
                "SELECT role FROM team_members WHERE team_id = ? AND user_id = ?",
                (team_id, target_user_id)
            ).fetchone()
            if existing:
                raise ValueError("User is already a team member")

            # Get display name
            user = conn.execute(
                "SELECT display_name FROM users WHERE id = ?",
                (target_user_id,)
            ).fetchone()
            if not user:
                raise ValueError("Target user not found")
            display_name = user["display_name"]

            # Add member
            conn.execute(
                "INSERT INTO team_members (team_id, user_id, role, invited_by) VALUES (?, ?, ?, ?)",
                (team_id, target_user_id, req.role, inviter_id)
            )

            # Create notification
            notif_id = f"notif_{secrets.token_hex(8)}"
            conn.execute(
                "INSERT INTO team_notifications (id, team_id, user_id, type, message) VALUES (?, ?, ?, 'invite', ?)",
                (notif_id, team_id, target_user_id, f"You've been invited to join a team")
            )

        return {"success": True, "user_id": target_user_id, "display_name": display_name}

    def remove_member(self, team_id: str, target_user_id: str, requester_id: str) -> Dict:
        """Remove a member from a team. Requester must be admin/owner."""
        if target_user_id == requester_id:
            raise ValueError("Cannot remove yourself. Use leave instead.")

        with self._get_conn() as conn:
            requester = conn.execute(
                "SELECT role FROM team_members WHERE team_id = ? AND user_id = ?",
                (team_id, requester_id)
            ).fetchone()
            if not requester or requester["role"] not in ("admin", "owner"):
                raise PermissionError("Only team admins can remove members")

            target = conn.execute(
                "SELECT role FROM team_members WHERE team_id = ? AND user_id = ?",
                (team_id, target_user_id)
            ).fetchone()
            if not target:
                raise ValueError("User is not a team member")
            if target["role"] == "owner":
                raise ValueError("Cannot remove the team owner")

            conn.execute(
                "DELETE FROM team_members WHERE team_id = ? AND user_id = ?",
                (team_id, target_user_id)
            )

        return {"success": True}

    def list_members(self, team_id: str, user_id: str) -> List[Dict]:
        """List all members of a team. User must be a member."""
        with self._get_conn() as conn:
            member = conn.execute(
                "SELECT role FROM team_members WHERE team_id = ? AND user_id = ?",
                (team_id, user_id)
            ).fetchone()
            if not member:
                raise PermissionError("Not a member of this team")

            rows = conn.execute("""
                SELECT u.id, u.display_name, u.email, tm.role, tm.joined_at
                FROM team_members tm
                JOIN users u ON tm.user_id = u.id
                WHERE tm.team_id = ?
                ORDER BY
                    CASE tm.role
                        WHEN 'owner' THEN 0
                        WHEN 'admin' THEN 1
                        WHEN 'member' THEN 2
                        WHEN 'viewer' THEN 3
                    END, u.display_name
            """, (team_id,)).fetchall()
            return [dict(r) for r in rows]

    def change_member_role(self, team_id: str, target_user_id: str, requester_id: str, new_role: str) -> Dict:
        """Change a member's role. Requester must be admin/owner."""
        if new_role not in ("admin", "member", "viewer", "owner"):
            raise ValueError("Invalid role")

        with self._get_conn() as conn:
            requester = conn.execute(
                "SELECT role FROM team_members WHERE team_id = ? AND user_id = ?",
                (team_id, requester_id)
            ).fetchone()
            if not requester or requester["role"] not in ("admin", "owner"):
                raise PermissionError("Only team admins can change roles")

            target = conn.execute(
                "SELECT role FROM team_members WHERE team_id = ? AND user_id = ?",
                (team_id, target_user_id)
            ).fetchone()
            if not target:
                raise ValueError("User is not a team member")
            if target["role"] == "owner":
                raise ValueError("Cannot change the team owner's role")
            if new_role == "owner":
                raise ValueError("Use transfer_ownership to change owner")

            conn.execute(
                "UPDATE team_members SET role = ? WHERE team_id = ? AND user_id = ?",
                (new_role, team_id, target_user_id)
            )

        return {"success": True, "user_id": target_user_id, "new_role": new_role}

    # ── Permissions ─────────────────────────────────────────────────────────

    def get_permissions(self, user_id: str) -> Dict:
        """Get permissions for the user across all teams."""
        with self._get_conn() as conn:
            user = conn.execute(
                "SELECT role FROM users WHERE id = ?", (user_id,)
            ).fetchone()
            global_role = user["role"] if user else "user"

            teams = conn.execute("""
                SELECT t.id, t.name, tm.role
                FROM teams t
                JOIN team_members tm ON t.id = tm.team_id
                WHERE tm.user_id = ?
            """, (user_id,)).fetchall()

            return {
                "user_id": user_id,
                "global_role": global_role,
                "teams": [dict(t) for t in teams],
                "can_create_teams": True,
                "can_invite_members": global_role in ("admin", "superadmin"),
            }


# ── Route Registration ──────────────────────────────────────────────────────

def setup_user_profile_routes(app, db_path: str):
    """Register all user profile and team endpoints on the FastAPI app."""

    mgr = UserProfileManager(db_path)

    router = APIRouter(prefix="/api", tags=["User Profiles & Teams"])

    # ── Profile Endpoints ───────────────────────────────────────────────────

    @router.get("/user/profile")
    async def get_profile(request: Request):
        """Get full profile for the authenticated user."""
        token_user = _get_token_user(request)
        try:
            profile = mgr.get_profile(token_user["user_id"])
            return {"success": True, "profile": profile}
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

    @router.put("/user/profile")
    async def update_profile(request: Request):
        """Update profile for the authenticated user."""
        token_user = _get_token_user(request)
        try:
            body = await request.json()
            req = UpdateProfileRequest(**body)
            profile = mgr.update_profile(token_user["user_id"], req)
            return {"success": True, "profile": profile}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/user/profiles/{user_id}")
    async def get_public_profile(user_id: str, request: Request):
        """Get a public profile (limited info) for another user."""
        _get_token_user(request)  # Auth required
        try:
            profile = mgr.get_public_profile(user_id)
            return {"success": True, "profile": profile}
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

    # ── Team Endpoints ──────────────────────────────────────────────────────

    @router.get("/teams")
    async def list_teams(request: Request):
        """List all teams the authenticated user belongs to."""
        token_user = _get_token_user(request)
        teams = mgr.list_teams(token_user["user_id"])
        return {"success": True, "teams": teams}

    @router.post("/teams")
    async def create_team(request: Request):
        """Create a new team."""
        token_user = _get_token_user(request)
        try:
            body = await request.json()
            req = CreateTeamRequest(**body)
            team = mgr.create_team(token_user["user_id"], req)
            return {"success": True, "team": team}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/teams/{team_id}")
    async def get_team(team_id: str, request: Request):
        """Get team details."""
        token_user = _get_token_user(request)
        try:
            team = mgr.get_team(team_id, token_user["user_id"])
            return {"success": True, "team": team}
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))

    @router.put("/teams/{team_id}")
    async def update_team(team_id: str, request: Request):
        """Update team settings."""
        token_user = _get_token_user(request)
        try:
            body = await request.json()
            req = UpdateTeamRequest(**body)
            team = mgr.update_team(team_id, token_user["user_id"], req)
            return {"success": True, "team": team}
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    # ── Member Endpoints ────────────────────────────────────────────────────

    @router.post("/teams/{team_id}/members")
    async def invite_member(team_id: str, request: Request):
        """Invite a user to join a team."""
        token_user = _get_token_user(request)
        try:
            body = await request.json()
            req = InviteMemberRequest(**body)
            result = mgr.invite_member(team_id, token_user["user_id"], req)
            return {"success": True, **result}
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/teams/{team_id}/members")
    async def list_members(team_id: str, request: Request):
        """List all members of a team."""
        token_user = _get_token_user(request)
        try:
            members = mgr.list_members(team_id, token_user["user_id"])
            return {"success": True, "members": members}
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))

    @router.delete("/teams/{team_id}/members/{user_id}")
    async def remove_member(team_id: str, user_id: str, request: Request):
        """Remove a member from a team."""
        token_user = _get_token_user(request)
        try:
            result = mgr.remove_member(team_id, user_id, token_user["user_id"])
            return {"success": True, **result}
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.put("/teams/{team_id}/members/{user_id}/role")
    async def change_member_role(team_id: str, user_id: str, request: Request):
        """Change a member's role in a team."""
        token_user = _get_token_user(request)
        try:
            body = await request.json()
            req = ChangeMemberRoleRequest(**body)
            result = mgr.change_member_role(team_id, user_id, token_user["user_id"], req.role)
            return {"success": True, **result}
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    # ── Permissions ─────────────────────────────────────────────────────────

    @router.get("/permissions")
    async def get_permissions(request: Request):
        """Get permissions for the authenticated user."""
        token_user = _get_token_user(request)
        permissions = mgr.get_permissions(token_user["user_id"])
        return {"success": True, "permissions": permissions}

    # Register all routes
    app.include_router(router)
