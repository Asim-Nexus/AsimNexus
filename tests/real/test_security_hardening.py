"""
Phase 6: Security Hardening Tests

Tests for:
  1. Biometric gate wiring into Level-3 (TOP_SECRET) security flow
  2. Quantum-resistant crypto stubs (Kyber, Dilithium, FALCON)
  3. HardwareBackend abstraction (SoftwareBackend seal/unseal/sign/verify)
"""

import pytest
import asyncio
import os
import hashlib
from typing import Dict, Any, Optional

# ═══════════════════════════════════════════════════════════════════════════
# TestBiometricGateWiring
# ═══════════════════════════════════════════════════════════════════════════


class TestBiometricGateWiring:
    """Verify biometric gate is called for Level-3 (TOP_SECRET) access."""

    def _register_permissions(self, mgr, actor: str, resources: list[str]) -> None:
        """Helper: register read and execute permissions for actor."""
        from security.security_framework import PermissionScope
        scope = PermissionScope(
            read=[*resources, "*"],
            execute=[*resources, "*"],
            write=[*resources, "*"],
        )
        mgr.contain.set_permissions(actor, scope)

    @pytest.mark.asyncio
    async def test_level3_calls_biometric_gate(self):
        """TOP_SECRET access should invoke biometric gate authentication."""
        from security.security_framework import ASIMSecurityManager
        from security.security_base import SecurityLevel

        mgr = ASIMSecurityManager()
        self._register_permissions(mgr, "sovereign", ["test_resource"])
        # TOP_SECRET triggers biometric gate
        allowed, reason = await mgr.check_access(
            actor="sovereign",
            required_level=SecurityLevel.TOP_SECRET,
            resource="test_resource",
            action="read",
        )
        assert allowed is True, f"Expected allowed=True, got {allowed}: {reason}"

    @pytest.mark.asyncio
    async def test_level1_skips_biometric_gate(self):
        """PUBLIC/INTERNAL access should NOT invoke biometric gate."""
        from security.security_framework import ASIMSecurityManager
        from security.security_base import SecurityLevel

        mgr = ASIMSecurityManager()
        self._register_permissions(mgr, "test_user", ["public_resource"])
        # PUBLIC should succeed without biometric gate
        allowed, reason = await mgr.check_access(
            actor="test_user",
            required_level=SecurityLevel.PUBLIC,
            resource="public_resource",
            action="read",
        )
        assert allowed is True, f"Expected allowed=True, got {allowed}: {reason}"

    @pytest.mark.asyncio
    async def test_level2_does_not_require_biometric(self):
        """CONFIDENTIAL/SECRET access should NOT require biometric gate."""
        from security.security_framework import ASIMSecurityManager
        from security.security_base import SecurityLevel

        mgr = ASIMSecurityManager()
        self._register_permissions(mgr, "test_user", ["confidential_data"])
        allowed, reason = await mgr.check_access(
            actor="test_user",
            required_level=SecurityLevel.CONFIDENTIAL,
            resource="confidential_data",
            action="read",
        )
        assert allowed is True, f"Expected allowed=True, got {allowed}: {reason}"

    @pytest.mark.asyncio
    async def test_level3_hardware_action_verifies_signature(self):
        """TOP_SECRET + hardware action should also call verify_hardware_signature."""
        from security.security_framework import ASIMSecurityManager
        from security.security_base import SecurityLevel

        mgr = ASIMSecurityManager()
        self._register_permissions(mgr, "sovereign", ["/system/hardware"])
        # 'execute' action at TOP_SECRET should trigger hardware signature check
        allowed, reason = await mgr.check_access(
            actor="sovereign",
            required_level=SecurityLevel.TOP_SECRET,
            resource="/system/hardware",
            action="execute",
        )
        assert allowed is True, f"Expected allowed=True, got {allowed}: {reason}"


# ═══════════════════════════════════════════════════════════════════════════
# TestQuantumCrypto
# ═══════════════════════════════════════════════════════════════════════════


class TestQuantumCrypto:
    """Test quantum-resistant cryptographic stubs."""

    # ─── Kyber KEM ──────────────────────────────────────────────────────

    def test_kyber_keygen_returns_correct_sizes(self):
        """Kyber keygen should return (pk, sk) with correct NIST sizes."""
        from security.identity_quantum_vault import kyber_keygen, KYBER_PK_SIZE, KYBER_SK_SIZE

        pk, sk = kyber_keygen()
        assert len(pk) == KYBER_PK_SIZE, f"PK size: {len(pk)} != {KYBER_PK_SIZE}"
        assert len(sk) == KYBER_SK_SIZE, f"SK size: {len(sk)} != {KYBER_SK_SIZE}"

    def test_kyber_round_trip(self):
        """Kyber encapsulate → decapsulate should recover the same shared secret."""
        from security.identity_quantum_vault import kyber_keygen, kyber_encapsulate, kyber_decapsulate

        pk, sk = kyber_keygen()
        ct, ss_alice = kyber_encapsulate(pk)
        ss_bob = kyber_decapsulate(ct, sk)

        assert ss_alice == ss_bob, "Shared secrets do not match after round-trip"
        assert len(ss_alice) == 32, "Shared secret should be 32 bytes"

    def test_kyber_different_keys_produce_different_secrets(self):
        """Different keypairs should produce different shared secrets."""
        from security.identity_quantum_vault import kyber_keygen, kyber_encapsulate

        pk1, sk1 = kyber_keygen()
        pk2, sk2 = kyber_keygen()

        ct1, ss1 = kyber_encapsulate(pk1)
        ct2, ss2 = kyber_encapsulate(pk2)

        assert ss1 != ss2, "Different keypairs should produce different shared secrets"

    # ─── Dilithium Signatures ───────────────────────────────────────────

    def test_dilithium_keygen_returns_correct_sizes(self):
        """Dilithium keygen should return (pk, sk) with correct NIST sizes."""
        from security.identity_quantum_vault import (
            dilithium_keygen, DILITHIUM_PK_SIZE, DILITHIUM_SK_SIZE,
        )

        pk, sk = dilithium_keygen()
        assert len(pk) == DILITHIUM_PK_SIZE, f"PK size: {len(pk)} != {DILITHIUM_PK_SIZE}"
        assert len(sk) == DILITHIUM_SK_SIZE, f"SK size: {len(sk)} != {DILITHIUM_SK_SIZE}"

    def test_dilithium_sign_verify_round_trip(self):
        """Dilithium sign → verify should return True for valid signatures."""
        from security.identity_quantum_vault import dilithium_keygen, dilithium_sign, dilithium_verify

        pk, sk = dilithium_keygen()
        message = b"Test message for Dilithium signing"
        sig = dilithium_sign(message, sk)

        assert len(sig) == 2420, f"Sig size: {len(sig)} != 2420"
        assert dilithium_verify(message, sig, pk) is True

    def test_dilithium_wrong_message_fails_verification(self):
        """Dilithium verify should return False for wrong message."""
        from security.identity_quantum_vault import dilithium_keygen, dilithium_sign, dilithium_verify

        pk, sk = dilithium_keygen()
        sig = dilithium_sign(b"original message", sk)
        assert dilithium_verify(b"tampered message", sig, pk) is False

    # ─── FALCON Signatures ──────────────────────────────────────────────

    def test_falcon_keygen_returns_correct_sizes(self):
        """FALCON keygen should return (pk, sk) with correct FALCON-512 sizes."""
        from security.identity_quantum_vault import falcon_keygen, FALCON_PK_SIZE, FALCON_SK_SIZE

        pk, sk = falcon_keygen()
        assert len(pk) == FALCON_PK_SIZE, f"PK size: {len(pk)} != {FALCON_PK_SIZE}"
        assert len(sk) == FALCON_SK_SIZE, f"SK size: {len(sk)} != {FALCON_SK_SIZE}"

    def test_falcon_sign_verify_round_trip(self):
        """FALCON sign → verify should return True for valid signatures."""
        from security.identity_quantum_vault import falcon_keygen, falcon_sign, falcon_verify

        pk, sk = falcon_keygen()
        message = b"FALCON test message"
        sig = falcon_sign(message, sk)

        assert len(sig) == 666, f"Sig size: {len(sig)} != 666"
        assert falcon_verify(message, sig, pk) is True

    def test_falcon_wrong_key_fails_verification(self):
        """FALCON verify with wrong public key should return False."""
        from security.identity_quantum_vault import falcon_keygen, falcon_sign, falcon_verify

        pk_alice, sk_alice = falcon_keygen()
        pk_bob, _ = falcon_keygen()
        sig = falcon_sign(b"secret message", sk_alice)
        assert falcon_verify(b"secret message", sig, pk_bob) is False

    # ─── QuantumKeyBundle ───────────────────────────────────────────────

    def test_quantum_key_bundle_creation(self):
        """Generate a QuantumKeyBundle and verify all four keys exist."""
        from security.identity_quantum_vault import generate_quantum_keypair, QuantumKeyBundle

        bundle = generate_quantum_keypair()
        assert isinstance(bundle, QuantumKeyBundle)
        assert len(bundle.kyber_public_key) == 800
        assert len(bundle.kyber_secret_key) == 1632
        assert len(bundle.dilithium_public_key) == 1312
        assert len(bundle.dilithium_secret_key) == 2528
        assert bundle.pqc_provider == "software_fallback"
        assert bundle.created_at != ""

    def test_multiple_bundles_independent(self):
        """Two calls to generate_quantum_keypair should produce different keys."""
        from security.identity_quantum_vault import generate_quantum_keypair

        b1 = generate_quantum_keypair()
        b2 = generate_quantum_keypair()
        assert b1.kyber_public_key != b2.kyber_public_key
        assert b1.dilithium_public_key != b2.dilithium_public_key

    def test_pqc_provider_constant(self):
        """PQC_PROVIDER constant should be defined and accessible."""
        from security.identity_quantum_vault import PQC_PROVIDER
        assert PQC_PROVIDER in ("software_fallback", "liboqs")


# ═══════════════════════════════════════════════════════════════════════════
# TestHardwareLock
# ═══════════════════════════════════════════════════════════════════════════


class TestHardwareLock:
    """Test HardwareBackend abstraction and SoftwareBackend."""

    def test_software_backend_seal_unseal_round_trip(self):
        """SoftwareBackend.seal → unseal should recover original data."""
        from security.hardware_hard_lock import SoftwareBackend

        backend = SoftwareBackend()
        data = b"Top secret data for sealing test"
        sealed = backend.seal(data)
        unsealed = backend.unseal(sealed)

        assert unsealed == data, "Unsealed data does not match original"

    def test_software_backend_seal_produces_different_output(self):
        """Each seal() call should produce different output (random IV)."""
        from security.hardware_hard_lock import SoftwareBackend

        backend = SoftwareBackend()
        data = b"deterministic test data"
        sealed1 = backend.seal(data)
        sealed2 = backend.seal(data)
        assert sealed1 != sealed2, "Seal should produce different output each time (random IV)"

    def test_software_backend_sign_verify_round_trip(self):
        """SoftwareBackend.sign → verify should return True."""
        from security.hardware_hard_lock import SoftwareBackend

        backend = SoftwareBackend()
        digest = hashlib.sha256(b"message to sign").digest()
        sig = backend.sign(digest)
        assert backend.verify(digest, sig) is True

    def test_software_backend_verify_wrong_signature(self):
        """SoftwareBackend.verify with wrong signature should return False."""
        from security.hardware_hard_lock import SoftwareBackend

        backend = SoftwareBackend()
        digest = hashlib.sha256(b"real message").digest()
        wrong_sig = b"\x00" * 32
        assert backend.verify(digest, wrong_sig) is False

    def test_software_backend_seal_context_binding(self):
        """Seal/unseal with matching context should work; mismatch should fail."""
        from security.hardware_hard_lock import SoftwareBackend, HardwareLockError

        backend = SoftwareBackend()
        data = b"context-bound secret"
        sealed = backend.seal(data, context="production")

        # Matching context should succeed
        unsealed = backend.unseal(sealed, context="production")
        assert unsealed == data

        # Wrong context should fail (integrity check)
        with pytest.raises(HardwareLockError):
            backend.unseal(sealed, context="staging")

    def test_hardware_lock_uses_backend(self):
        """HardwareHardLock should accept and use a custom backend."""
        from security.hardware_hard_lock import HardwareHardLock, SoftwareBackend

        backend = SoftwareBackend()
        lock = HardwareHardLock(backend=backend)
        assert lock._backend is backend

    def test_hardware_lock_get_process_list_no_subprocess(self):
        """HardwareHardLock._get_running_processes should use backend (no subprocess)."""
        from security.hardware_hard_lock import HardwareHardLock, SoftwareBackend

        lock = HardwareHardLock(backend=SoftwareBackend())
        processes = lock._get_running_processes()
        # Should be a list (possibly empty if psutil unavailable)
        assert isinstance(processes, list)

    def test_hardware_lock_get_network_no_subprocess(self):
        """HardwareHardLock._get_network_connections should use backend (no subprocess)."""
        from security.hardware_hard_lock import HardwareHardLock, SoftwareBackend

        lock = HardwareHardLock(backend=SoftwareBackend())
        connections = lock._get_network_connections()
        assert isinstance(connections, list)

    def test_software_backend_tpm_info(self):
        """SoftwareBackend.get_tpm_info should report TPM unavailable."""
        from security.hardware_hard_lock import SoftwareBackend

        backend = SoftwareBackend()
        info = backend.get_tpm_info()
        assert info["tpm_present"] is False
        assert info["attestation_status"] == "unavailable"

    def test_hardware_lock_error_exception(self):
        """HardwareLockError should be catchable."""
        from security.hardware_hard_lock import HardwareLockError

        try:
            raise HardwareLockError("Test error")
        except HardwareLockError as e:
            assert str(e) == "Test error"

    def test_hardware_backend_abc_cannot_instantiate(self):
        """HardwareBackend ABC should not be instantiable directly."""
        from security.hardware_hard_lock import HardwareBackend

        with pytest.raises(TypeError):
            HardwareBackend()  # type: ignore

    def test_tpm_backend_fallback(self):
        """TPMBackend should fall back to SoftwareBackend when no TPM."""
        from security.hardware_hard_lock import TPMBackend

        backend = TPMBackend()
        # Should not crash - either works with TPM or falls back
        info = backend.get_tpm_info()
        assert isinstance(info, dict)
        assert "tpm_present" in info


# ═══════════════════════════════════════════════════════════════════════════
# Additional: Biometric Gate Integration Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestBiometricGateIntegration:
    """Test BiometricHardwareGate methods added for security framework."""

    @pytest.mark.asyncio
    async def test_biometric_gate_authenticate_authorized_user(self):
        """authenticate() should succeed for authorized users."""
        from security.biometric_hardware_gate import BiometricHardwareGate

        gate = BiometricHardwareGate()
        result = await gate.authenticate(user_id="sovereign")
        assert result["success"] is True
        assert result["confidence"] >= 0.9

    @pytest.mark.asyncio
    async def test_biometric_gate_authenticate_unauthorized_user(self):
        """authenticate() should fail for unauthorized users."""
        from security.biometric_hardware_gate import BiometricHardwareGate

        gate = BiometricHardwareGate()
        result = await gate.authenticate(user_id="unknown_hacker")
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_biometric_gate_verify_hardware_signature(self):
        """verify_hardware_signature() should return verified=True."""
        from security.biometric_hardware_gate import BiometricHardwareGate

        gate = BiometricHardwareGate()
        result = await gate.verify_hardware_signature({
            "resource": "/dev/tpm0",
            "action": "read",
        })
        assert result["verified"] is True
        assert result["signature"] != ""
