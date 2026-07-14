"""
Unit tests for AsimNexus JWT utilities and HSM client.

Covers both HSM‑enabled (mock) and symmetric (HS256) fallback paths.

Run with:
    pytest tests/security/test_jwt.py -v
"""

import hashlib
import json
import os
import sys
import time
from datetime import datetime, timedelta
from unittest import mock

import pytest

# ---------------------------------------------------------------------------
# Ensure the project root is importable
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ═══════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture(autouse=True)
def _reset_jwt_module():
    """Force a fresh import of the jwt module for every test so that
    module‑level globals (USE_HSM, SECRET_KEY, etc.) reflect the
    environment variables set by each test.
    """
    mods_to_remove = [k for k in sys.modules if k.startswith("core.security")]
    for mod in mods_to_remove:
        del sys.modules[mod]
    yield
    mods_to_remove = [k for k in sys.modules if k.startswith("core.security")]
    for mod in mods_to_remove:
        del sys.modules[mod]

@pytest.fixture
def fallback_env(monkeypatch):
    """Configure env for HS256 (symmetric) fallback path."""
    monkeypatch.setenv("JWT_USE_HSM", "false")
    monkeypatch.setenv("JWT_SECRET", "test-secret-key-for-unit-tests")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15")
    monkeypatch.setenv("REFRESH_TOKEN_EXPIRE_DAYS", "1")

@pytest.fixture
def hsm_env(monkeypatch):
    """Configure env for HSM (mock) path."""
    monkeypatch.setenv("JWT_USE_HSM", "true")
    monkeypatch.setenv("JWT_SECRET", "unused-in-hsm-mode")
    monkeypatch.setenv("JWT_PUBLIC_KEY_PEM", "")  # mock doesn't need PEM
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15")
    monkeypatch.setenv("REFRESH_TOKEN_EXPIRE_DAYS", "1")

# ═══════════════════════════════════════════════════════════════════════════
# Helper — import after env is set
# ═══════════════════════════════════════════════════════════════════════════

def _import_jwt():
    """Import the jwt module lazily (after env‑vars are configured)."""
    from core.security import jwt as jwt_mod  # noqa: F811
    return jwt_mod

def _import_hsm():
    """Import the HSMClient class lazily."""
    from core.security.hsm_client import HSMClient
    return HSMClient

# ═══════════════════════════════════════════════════════════════════════════
# 1. Base64‑URL encoder tests
# ═══════════════════════════════════════════════════════════════════════════

class TestB64URL:
    """Validate the RFC 7515 §2 Base64‑URL encoder/decoder."""

    def test_b64url_roundtrip(self, fallback_env):
        jwt_mod = _import_jwt()
        data = b"Hello, AsimNexus!"
        encoded = jwt_mod._b64url(data)
        decoded = jwt_mod._b64url_decode(encoded)
        assert decoded == data

    def test_b64url_no_padding(self, fallback_env):
        jwt_mod = _import_jwt()
        encoded = jwt_mod._b64url(b"test")
        assert "=" not in encoded

    def test_b64url_url_safe(self, fallback_env):
        jwt_mod = _import_jwt()
        # Use bytes that would produce + and / in standard Base64
        data = b"\xfb\xff\xfe"
        encoded = jwt_mod._b64url(data)
        assert "+" not in encoded
        assert "/" not in encoded

# ═══════════════════════════════════════════════════════════════════════════
# 2. Token creation – symmetric fallback (HS256)
# ═══════════════════════════════════════════════════════════════════════════

class TestCreateTokenFallback:
    """Test token creation when HSM is disabled (HS256 symmetric)."""

    def test_create_access_token(self, fallback_env):
        jwt_mod = _import_jwt()
        token = jwt_mod.create_access_token(
            user_id="user_001",
            username="testuser",
            roles=["citizen"],
            org_id="org_nepal",
            permissions=["tax:read", "profile:write"],
            email="test@asimnexus.ai",
        )
        assert isinstance(token, str)
        assert len(token.split(".")) == 3

    def test_create_refresh_token(self, fallback_env):
        jwt_mod = _import_jwt()
        token = jwt_mod.create_refresh_token(
            user_id="user_001",
            username="testuser",
            roles=["citizen"],
        )
        assert isinstance(token, str)
        assert len(token.split(".")) == 3

    def test_access_token_contains_claims(self, fallback_env):
        jwt_mod = _import_jwt()
        token = jwt_mod.create_access_token(
            user_id="u42",
            username="ram",
            roles=["admin", "developer"],
            org_id="gov_np",
            permissions=["all"],
            email="ram@gov.np",
        )
        data = jwt_mod.decode_token(token)
        assert data.user_id == "u42"
        assert data.username == "ram"
        assert "admin" in data.roles
        assert data.org_id == "gov_np"
        assert data.email == "ram@gov.np"
        assert "all" in data.permissions

    def test_custom_expiry(self, fallback_env):
        jwt_mod = _import_jwt()
        token = jwt_mod.create_access_token(
            user_id="u1",
            username="short",
            roles=["guest"],
            expires_minutes=1,
        )
        data = jwt_mod.decode_token(token)
        # Expiry should be within ~2 minutes from now
        delta = data.exp - datetime.utcnow()
        assert delta.total_seconds() < 120

# ═══════════════════════════════════════════════════════════════════════════
# 3. Token creation – HSM path (mock)
# ═══════════════════════════════════════════════════════════════════════════

class TestCreateTokenHSM:
    """Test token creation when HSM is enabled (uses mock client)."""

    def test_create_access_token_hsm(self, hsm_env):
        jwt_mod = _import_jwt()
        # Patch _get_hsm_client to return a mock‑mode HSMClient
        HSMClient = _import_hsm()
        mock_hsm = HSMClient(mock=True)
        with mock.patch.object(jwt_mod, "_get_hsm_client", return_value=mock_hsm):
            token = jwt_mod.create_access_token(
                user_id="user_hsm",
                username="hsmuser",
                roles=["admin"],
                org_id="org_hsm",
                permissions=["all"],
                email="hsm@test.com",
            )
        assert isinstance(token, str)
        assert len(token.split(".")) == 3

    def test_create_refresh_token_hsm(self, hsm_env):
        jwt_mod = _import_jwt()
        HSMClient = _import_hsm()
        mock_hsm = HSMClient(mock=True)
        with mock.patch.object(jwt_mod, "_get_hsm_client", return_value=mock_hsm):
            token = jwt_mod.create_refresh_token(
                user_id="user_hsm",
                username="hsmuser",
                roles=["citizen"],
            )
        assert isinstance(token, str)
        assert len(token.split(".")) == 3

    def test_hsm_token_header_alg(self, hsm_env):
        """HSM tokens must use RS256 algorithm in the header."""
        jwt_mod = _import_jwt()
        HSMClient = _import_hsm()
        mock_hsm = HSMClient(mock=True)
        with mock.patch.object(jwt_mod, "_get_hsm_client", return_value=mock_hsm):
            token = jwt_mod.create_access_token(
                user_id="u1",
                username="test",
                roles=["guest"],
            )
        header_b64 = token.split(".")[0]
        header = json.loads(jwt_mod._b64url_decode(header_b64))
        assert header["alg"] == "RS256"
        assert header["typ"] == "JWT"

# ═══════════════════════════════════════════════════════════════════════════
# 4. Token decoding – symmetric fallback (HS256)
# ═══════════════════════════════════════════════════════════════════════════

class TestDecodeTokenFallback:
    """Decode/verify tokens using the HS256 symmetric path."""

    def test_decode_valid_token(self, fallback_env):
        jwt_mod = _import_jwt()
        token = jwt_mod.create_access_token(
            user_id="u100",
            username="decode_test",
            roles=["user"],
        )
        data = jwt_mod.decode_token(token)
        assert data.user_id == "u100"
        assert data.username == "decode_test"
        assert "user" in data.roles

    def test_decode_refresh_token(self, fallback_env):
        jwt_mod = _import_jwt()
        token = jwt_mod.create_refresh_token(
            user_id="u200",
            username="refresh_test",
            roles=["citizen"],
            org_id="org_np",
        )
        data = jwt_mod.decode_token(token)
        assert data.user_id == "u200"
        assert data.org_id == "org_np"

    def test_decode_expired_token(self, fallback_env):
        """Expired tokens must raise ExpiredSignatureError."""
        jwt_mod = _import_jwt()
        import jwt as pyjwt

        token = jwt_mod.create_access_token(
            user_id="expired",
            username="old",
            roles=["guest"],
            expires_minutes=-1,  # Already expired
        )
        with pytest.raises(pyjwt.ExpiredSignatureError):
            jwt_mod.decode_token(token)

    def test_decode_invalid_token(self, fallback_env):
        """Garbage tokens must raise an error."""
        jwt_mod = _import_jwt()
        import jwt as pyjwt

        with pytest.raises(pyjwt.exceptions.DecodeError):
            jwt_mod.decode_token("not.a.real.token")

    def test_decode_tampered_token(self, fallback_env):
        """Tampered payload must fail verification."""
        jwt_mod = _import_jwt()
        import jwt as pyjwt

        token = jwt_mod.create_access_token(
            user_id="u1",
            username="legit",
            roles=["user"],
        )
        parts = token.split(".")
        # Tamper with payload
        parts[1] = parts[1][::-1]
        tampered = ".".join(parts)
        with pytest.raises(Exception):
            jwt_mod.decode_token(tampered)

# ═══════════════════════════════════════════════════════════════════════════
# 5. Token decoding – HSM path (mock)
# ═══════════════════════════════════════════════════════════════════════════

class TestDecodeTokenHSM:
    """Decode/verify tokens using the HSM (mock) path."""

    def test_roundtrip_hsm(self, hsm_env):
        """Create and verify a token through the HSM mock path."""
        jwt_mod = _import_jwt()
        HSMClient = _import_hsm()
        mock_hsm = HSMClient(mock=True)

        with mock.patch.object(jwt_mod, "_get_hsm_client", return_value=mock_hsm):
            with mock.patch.object(jwt_mod, "_get_public_key_pem", return_value=""):
                token = jwt_mod.create_access_token(
                    user_id="hsm_roundtrip",
                    username="roundtrip",
                    roles=["admin"],
                    email="rt@test.com",
                )
                data = jwt_mod.decode_token(token)

        assert data.user_id == "hsm_roundtrip"
        assert data.username == "roundtrip"
        assert "admin" in data.roles
        assert data.email == "rt@test.com"

    def test_invalid_signature_hsm(self, hsm_env):
        """A token with a bad signature must be rejected."""
        jwt_mod = _import_jwt()
        import jwt as pyjwt
        HSMClient = _import_hsm()
        mock_hsm = HSMClient(mock=True)

        with mock.patch.object(jwt_mod, "_get_hsm_client", return_value=mock_hsm):
            with mock.patch.object(jwt_mod, "_get_public_key_pem", return_value=""):
                token = jwt_mod.create_access_token(
                    user_id="u1",
                    username="test",
                    roles=["user"],
                )
                # Tamper with signature
                parts = token.split(".")
                parts[2] = "AAAA" + parts[2][4:]
                tampered = ".".join(parts)

                with pytest.raises(pyjwt.InvalidSignatureError):
                    jwt_mod.decode_token(tampered)

    def test_malformed_jwt_hsm(self, hsm_env):
        """Tokens without 3 parts must be rejected."""
        jwt_mod = _import_jwt()
        import jwt as pyjwt
        HSMClient = _import_hsm()
        mock_hsm = HSMClient(mock=True)

        with mock.patch.object(jwt_mod, "_get_hsm_client", return_value=mock_hsm):
            with pytest.raises(pyjwt.InvalidTokenError):
                jwt_mod.decode_token("only.two")

# ═══════════════════════════════════════════════════════════════════════════
# 6. HSMClient unit tests
# ═══════════════════════════════════════════════════════════════════════════

class TestHSMClient:
    """Test the HSMClient class directly."""

    def test_mock_mode_init(self, fallback_env):
        HSMClient = _import_hsm()
        client = HSMClient(mock=True)
        assert client.mock is True
        assert client.session is None

    def test_mock_sign_verify_roundtrip(self, fallback_env):
        HSMClient = _import_hsm()
        client = HSMClient(mock=True)
        data = b"test data to sign"
        sig = client.sign(data)
        assert client.verify(data, sig) is True

    def test_mock_verify_bad_signature(self, fallback_env):
        HSMClient = _import_hsm()
        client = HSMClient(mock=True)
        data = b"some data"
        assert client.verify(data, b"bad_signature") is False

    def test_mock_generate_keypair(self, fallback_env):
        HSMClient = _import_hsm()
        client = HSMClient(mock=True)
        pub, priv = client.generate_rsa_keypair("test-label")
        assert pub is None
        assert priv is None

    def test_real_mode_missing_lib(self, fallback_env, monkeypatch):
        """Real mode must fail if PKCS#11 library is not found."""
        HSMClient = _import_hsm()
        monkeypatch.setenv("PKCS11_LIB_PATH", "/nonexistent/lib.so")
        with pytest.raises(FileNotFoundError):
            HSMClient(mock=False)

# ═══════════════════════════════════════════════════════════════════════════
# 7. TokenData model tests
# ═══════════════════════════════════════════════════════════════════════════

class TestTokenData:
    """Validate the TokenData Pydantic model."""

    def test_minimal_fields(self, fallback_env):
        jwt_mod = _import_jwt()
        td = jwt_mod.TokenData(
            user_id="u1",
            username="test",
            roles=["guest"],
            exp=datetime.utcnow(),
        )
        assert td.user_id == "u1"
        assert td.org_id is None
        assert td.permissions is None
        assert td.email is None

    def test_all_fields(self, fallback_env):
        jwt_mod = _import_jwt()
        td = jwt_mod.TokenData(
            user_id="u2",
            username="full",
            roles=["admin", "developer"],
            org_id="gov_np",
            permissions=["read", "write", "delete"],
            email="full@gov.np",
            exp=datetime.utcnow() + timedelta(hours=1),
        )
        assert td.org_id == "gov_np"
        assert len(td.permissions) == 3
        assert td.email == "full@gov.np"
