"""
JWT Utilities for AsimNexus – HSM‑aware token creation and verification.

Supports two modes:
  * **HS256 (symmetric)** – default fallback using ``JWT_SECRET``.
  * **ES256/RS256 (asymmetric)** – when ``JWT_USE_HSM=true``, signing happens
    inside the HSM and verification uses the exported public key (PEM).

STATUS: REAL — Core security component
"""

import base64
import json
import logging
import os
from datetime import datetime, timedelta
from typing import List, Optional

import jwt as pyjwt
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration — loaded once at module import
# ---------------------------------------------------------------------------
SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

USE_HSM = os.getenv("JWT_USE_HSM", "false").lower() == "true"

# Lazy HSM initialisation — only when needed
_hsm_client = None
_public_key_pem: Optional[str] = None


def _get_hsm_client():
    """Return the module‑level HSMClient singleton, creating it on first call."""
    global _hsm_client
    if _hsm_client is None:
        from .hsm_client import HSMClient
        _hsm_client = HSMClient()
    return _hsm_client


def _get_public_key_pem() -> str:
    """Load the PEM public key from env‑var or file (cached)."""
    global _public_key_pem
    if _public_key_pem is None:
        # Try inline PEM first, then file path
        _public_key_pem = os.getenv("JWT_PUBLIC_KEY_PEM", "")
        if not _public_key_pem:
            pem_file = os.getenv("JWT_PUBLIC_KEY_PEM_FILE", "public_key.pem")
            if os.path.exists(pem_file):
                with open(pem_file, "r") as fh:
                    _public_key_pem = fh.read()
                logger.info("Loaded public key from %s", pem_file)
            else:
                logger.warning("No public key found at %s", pem_file)
    return _public_key_pem


# ---------------------------------------------------------------------------
# Base64‑URL helper (RFC 7515 §2)
# ---------------------------------------------------------------------------

def _b64url(data: bytes) -> str:
    """Return unpadded Base64‑URL encoding of *data*.

    This is the encoding mandated by the JWS specification (RFC 7515 §2):
    standard Base64 with ``+`` → ``-``, ``/`` → ``_``, and trailing ``=``
    removed.
    """
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    """Decode an unpadded Base64‑URL string back to bytes."""
    # Re‑add padding so Python's decoder is happy
    s += "=" * (4 - len(s) % 4)
    return base64.urlsafe_b64decode(s)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

class TokenData(BaseModel):
    """Data extracted from a JWT after verification."""

    user_id: str
    username: str
    roles: List[str]
    org_id: Optional[str] = None
    permissions: Optional[List[str]] = None
    email: Optional[str] = None
    exp: datetime


# ---------------------------------------------------------------------------
# Payload builder
# ---------------------------------------------------------------------------

def _build_payload(
    user_id: str,
    username: str,
    roles: List[str],
    token_type: str,
    expires: datetime,
    org_id: Optional[str] = None,
    permissions: Optional[List[str]] = None,
    email: Optional[str] = None,
) -> dict:
    """Assemble the JWT claims dictionary."""
    payload = {
        "user_id": user_id,
        "username": username,
        "roles": roles,
        "type": token_type,
        "exp": expires.timestamp(),  # numeric epoch for JSON serialisation
        "iat": datetime.utcnow().timestamp(),
    }
    if org_id is not None:
        payload["org_id"] = org_id
    if permissions is not None:
        payload["permissions"] = permissions
    if email is not None:
        payload["email"] = email
    return payload


# ---------------------------------------------------------------------------
# Token creation
# ---------------------------------------------------------------------------

def _sign_with_hsm(payload: dict) -> str:
    """Build a JWS token whose signature is produced by the HSM."""
    hsm = _get_hsm_client()
    header = {"alg": "RS256", "typ": "JWT"}
    header_b64 = _b64url(json.dumps(header, separators=(",", ":")).encode())
    payload_b64 = _b64url(json.dumps(payload, separators=(",", ":")).encode())
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    signature = _b64url(hsm.sign(signing_input))
    return f"{header_b64}.{payload_b64}.{signature}"


def create_access_token(
    user_id: str,
    username: str,
    roles: List[str],
    org_id: Optional[str] = None,
    permissions: Optional[List[str]] = None,
    email: Optional[str] = None,
    expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES,
) -> str:
    """Generate a signed JWT access token.

    Uses HSM for signing when ``JWT_USE_HSM=true``; otherwise falls back to
    symmetric HS256.
    """
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    payload = _build_payload(
        user_id=user_id,
        username=username,
        roles=roles,
        token_type="access",
        expires=expire,
        org_id=org_id,
        permissions=permissions,
        email=email,
    )

    if USE_HSM:
        return _sign_with_hsm(payload)

    # Symmetric fallback — use datetime object (PyJWT handles conversion)
    payload["exp"] = expire
    payload["iat"] = datetime.utcnow()
    return pyjwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(
    user_id: str,
    username: str,
    roles: List[str],
    org_id: Optional[str] = None,
    permissions: Optional[List[str]] = None,
    email: Optional[str] = None,
    expires_days: int = REFRESH_TOKEN_EXPIRE_DAYS,
) -> str:
    """Generate a signed JWT refresh token."""
    expire = datetime.utcnow() + timedelta(days=expires_days)
    payload = _build_payload(
        user_id=user_id,
        username=username,
        roles=roles,
        token_type="refresh",
        expires=expire,
        org_id=org_id,
        permissions=permissions,
        email=email,
    )

    if USE_HSM:
        return _sign_with_hsm(payload)

    payload["exp"] = expire
    payload["iat"] = datetime.utcnow()
    return pyjwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# ---------------------------------------------------------------------------
# Token decoding / verification
# ---------------------------------------------------------------------------

def _extract_token_data(payload: dict) -> TokenData:
    """Convert a raw claims dict into a ``TokenData`` instance."""
    exp_val = payload.get("exp")
    if isinstance(exp_val, (int, float)):
        exp_dt = datetime.utcfromtimestamp(exp_val)
    elif isinstance(exp_val, datetime):
        exp_dt = exp_val
    else:
        exp_dt = datetime.utcnow()

    return TokenData(
        user_id=payload["user_id"],
        username=payload["username"],
        roles=payload.get("roles", []),
        org_id=payload.get("org_id"),
        permissions=payload.get("permissions"),
        email=payload.get("email"),
        exp=exp_dt,
    )


def decode_token(token: str) -> TokenData:
    """Decode and validate a JWT.

    Supports both HS256 (symmetric) and RS256 (asymmetric via HSM).

    Raises:
        pyjwt.ExpiredSignatureError: if the token has expired.
        pyjwt.InvalidTokenError: for any other validation failure.
    """
    if not USE_HSM:
        # ---- Symmetric path ----
        payload = pyjwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return _extract_token_data(payload)

    # ---- Asymmetric (HSM) path ----
    parts = token.split(".")
    if len(parts) != 3:
        raise pyjwt.InvalidTokenError("JWT must contain exactly 3 parts")

    header_b64, payload_b64, sig_b64 = parts
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    signature = _b64url_decode(sig_b64)

    hsm = _get_hsm_client()
    pub_key = _get_public_key_pem()

    if not hsm.verify(signing_input, signature, public_key=pub_key or None):
        raise pyjwt.InvalidSignatureError("HSM signature verification failed")

    # Decode & validate expiry
    payload = json.loads(_b64url_decode(payload_b64))
    exp_val = payload.get("exp")
    if isinstance(exp_val, (int, float)):
        if datetime.utcfromtimestamp(exp_val) < datetime.utcnow():
            raise pyjwt.ExpiredSignatureError("Token has expired")

    return _extract_token_data(payload)
