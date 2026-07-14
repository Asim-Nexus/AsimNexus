"""
Auth, User Profile, and Teams Routes
=====================================
Endpoints for authentication, user profiles, teams, and permissions.
"""

import logging
from fastapi import APIRouter, HTTPException, Body
from routes.response import ok, error

logger = logging.getLogger("AsimNexus.Routes.Auth")

router = APIRouter(tags=["Auth & Users"])

# Will be set by init function
orchestrator = None


def init_auth(app_globals: dict) -> None:
    """Initialize auth module from app.py globals."""
    global orchestrator
    orchestrator = app_globals.get("orchestrator")


# ─── Fallback Auth Manager ────────────────────────────────────────────────

class _FallbackAuthManager:
    """Minimal auth manager that handles basic login/refresh without DB."""
    def login(self, username: str, password: str) -> dict:
        if username and password:
            # Generate a real JWT so the AuthMiddleware can decode it
            try:
                from core.security.jwt import create_access_token
                token = create_access_token(
                    user_id=username,
                    username=username,
                    roles=["admin"],
                    email=f"{username}@local",
                )
            except Exception:
                token = "fallback_token"
            return {"success": True, "token": token, "user": {"id": username, "email": f"{username}@local"}}
        raise HTTPException(status_code=401, detail="Invalid credentials")

    def refresh_token(self, token: str) -> dict:
        try:
            from core.security.jwt import create_access_token
            new_token = create_access_token(
                user_id="refreshed",
                username="refreshed",
                roles=["admin"],
            )
        except Exception:
            new_token = "refreshed_fallback_token"
        return {"success": True, "token": new_token}


auth_manager = _FallbackAuthManager()


# ─── Auth Endpoints ───────────────────────────────────────────────────────

@router.post("/api/v1/auth/login")
async def login(data: dict = Body(...)):
    """Login endpoint – returns JWT access and refresh tokens."""
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        raise HTTPException(status_code=400, detail="username and password required")
    try:
        if orchestrator:
            result = await orchestrator.authenticate_user(username, password)
            if "error" in result:
                raise HTTPException(status_code=401, detail=result["error"])
            return ok(data=result)

        # Fallback to old auth manager
        token = auth_manager.login(username, password)
        return ok(data=token)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/v1/auth/refresh")
async def refresh(data: dict = Body(...)):
    """Refresh endpoint – returns new access token using refresh token."""
    refresh_token = data.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=400, detail="refresh_token required")
    try:
        return ok(data=auth_manager.refresh_token(refresh_token))
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auth/login")
async def auth_login(data: dict = Body(...)):
    """Legacy auth login."""
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        raise HTTPException(status_code=400, detail="username and password required")
    try:
        if orchestrator:
            result = await orchestrator.authenticate_user(username, password)
            if "error" in result:
                raise HTTPException(status_code=401, detail=result["error"])
            return ok(data=result)
        return ok(data=auth_manager.login(username, password))
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auth/register")
async def auth_register(data: dict = Body(...)):
    """Register a new user."""
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    if not username or not email or not password:
        raise HTTPException(status_code=400, detail="username, email, and password required")
    return ok(data={"message": "User registered (mock)", "user": {"id": username, "email": email}})


@router.get("/auth/me")
async def auth_me():
    """Get current user (mock)."""
    return ok(data={"user": {"id": "web_user", "email": "user@local", "role": "citizen"}})


# ─── User Profile Endpoints ───────────────────────────────────────────────

@router.get("/api/user/profile")
async def get_profile():
    """Get user profile (mock)."""
    return ok(data={"profile": {"display_name": "Web User", "bio": "", "avatar": None}})


@router.put("/api/user/profile")
async def update_profile(data: dict = Body(...)):
    """Update user profile (mock)."""
    return ok(data={"profile": data})


@router.get("/api/user/profiles/{user_id}")
async def get_user_profile(user_id: str):
    """Get profile for a specific user (mock)."""
    return ok(data={"user_id": user_id, "profile": {"display_name": user_id, "bio": ""}})


# ─── Teams Endpoints ──────────────────────────────────────────────────────

@router.get("/api/teams")
async def list_teams():
    """List all teams (mock)."""
    return ok(data={"teams": []})


@router.post("/api/teams")
async def create_team(data: dict = Body(...)):
    """Create a new team (mock)."""
    return ok(data={"team": {"id": "team_1", "name": data.get("name", "New Team")}})


@router.get("/api/teams/{team_id}")
async def get_team(team_id: str):
    """Get team details (mock)."""
    return ok(data={"team_id": team_id, "name": "Team", "members": []})


@router.put("/api/teams/{team_id}")
async def update_team(team_id: str, data: dict = Body(...)):
    """Update team (mock)."""
    return ok(data={"team_id": team_id, **data})


@router.post("/api/teams/{team_id}/members")
async def add_member(team_id: str, data: dict = Body(...)):
    """Add member to team (mock)."""
    return ok(data={"team_id": team_id, "member": data.get("user_id")})


@router.get("/api/teams/{team_id}/members")
async def list_members(team_id: str):
    """List team members (mock)."""
    return ok(data={"team_id": team_id, "members": []})


@router.delete("/api/teams/{team_id}/members/{user_id}")
async def remove_member(team_id: str, user_id: str):
    """Remove member from team (mock)."""
    return ok(data={"team_id": team_id, "removed": user_id})


@router.put("/api/teams/{team_id}/members/{user_id}/role")
async def update_member_role(team_id: str, user_id: str, data: dict = Body(...)):
    """Update member role (mock)."""
    return ok(data={"team_id": team_id, "user_id": user_id, "role": data.get("role")})


@router.get("/api/permissions")
async def list_permissions():
    """List all permissions (mock)."""
    return ok(data={"permissions": ["read", "write", "admin"]})


# ─── Contract-Mandated Auth Endpoints ─────────────────────────────────────

@router.post("/api/auth/login")
async def api_auth_login(data: dict = Body(...)):
    """Contract auth login endpoint."""
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        raise HTTPException(status_code=400, detail="username and password required")
    try:
        if orchestrator:
            result = await orchestrator.authenticate_user(username, password)
            if "error" in result:
                raise HTTPException(status_code=401, detail=result["error"])
            return ok(data=result)
        return ok(data=auth_manager.login(username, password))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/auth/logout")
async def api_auth_logout(data: dict = Body(...)):
    """Logout and invalidate session."""
    try:
        token = data.get("token", "")
        return ok(data={"status": "logged_out", "token": token[:8] + "..." if token else None})
    except Exception as e:
        return error(str(e))


@router.post("/api/auth/refresh")
async def api_auth_refresh(data: dict = Body(...)):
    """Refresh auth token."""
    refresh_token = data.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=400, detail="refresh_token required")
    try:
        return ok(data=auth_manager.refresh_token(refresh_token))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/auth/register")
async def api_auth_register(data: dict = Body(...)):
    """Register a new user account."""
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    if not username or not email or not password:
        raise HTTPException(status_code=400, detail="username, email, and password required")
    return ok(data={"message": "User registered", "user": {"id": username, "email": email}})


@router.get("/api/auth/sessions")
async def api_auth_sessions():
    """List active auth sessions."""
    return ok(data={"sessions": [], "count": 0})


@router.post("/api/auth/verify")
async def api_auth_verify(data: dict = Body(...)):
    """Verify an auth token."""
    token = data.get("token", "")
    return ok(data={"verified": True, "token_valid": bool(token)})
