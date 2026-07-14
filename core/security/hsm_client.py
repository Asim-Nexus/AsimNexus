"""
HSM Client — Hardware Security Module interface.
==================================================
Provides a client for interacting with PKCS#11-compatible Hardware Security
Modules (HSMs). Supports mock mode for testing and real mode for production.

Exports:
    HSMClient — main class for HSM operations
"""

import hashlib
import logging
import os
from typing import Optional, Tuple

logger = logging.getLogger("AsimNexus.Security.HSM")


class HSMClient:
    """Client for Hardware Security Module operations.

    Supports two modes:
        - mock=True: In-memory simulation for testing
        - mock=False: Real PKCS#11 HSM interaction
    """

    def __init__(self, mock: bool = False):
        """Initialize the HSM client.

        Args:
            mock: If True, use in-memory mock mode. If False, connect to real HSM.

        Raises:
            FileNotFoundError: If mock=False and PKCS#11 library not found
        """
        self.mock = mock
        self.session = None
        self._mock_keys: dict = {}

        if not mock:
            self._init_real_mode()

    def _init_real_mode(self) -> None:
        """Initialize real PKCS#11 HSM mode."""
        lib_path = os.environ.get("PKCS11_LIB_PATH", "")
        if not lib_path:
            logger.warning("PKCS11_LIB_PATH not set, defaulting to mock mode")
            self.mock = True
            return

        if not os.path.isfile(lib_path):
            raise FileNotFoundError(f"PKCS#11 library not found at: {lib_path}")

        # In a real implementation, this would initialize the PKCS#11 interface
        # using a library like python-pkcs11 or PyKCS11.
        # For now, we log the initialization attempt.
        logger.info(f"HSM initialized with PKCS#11 library: {lib_path}")

    def sign(self, data: bytes) -> bytes:
        """Sign data using the HSM.

        Args:
            data: The data bytes to sign

        Returns:
            Signature bytes
        """
        if self.mock:
            # Mock: use SHA-256 hash as a simulated signature
            return hashlib.sha256(data).digest()
        else:
            # Real mode would use PKCS#11 C_Sign
            raise NotImplementedError("Real HSM signing not implemented")

    def verify(self, data: bytes, signature: bytes, **kwargs) -> bool:
        """Verify a signature against data using the HSM.

        Args:
            data: The original data bytes
            signature: The signature bytes to verify
            **kwargs: Additional keyword arguments (e.g., public_key) accepted for
                      compatibility with callers that pass extra parameters.

        Returns:
            True if signature is valid, False otherwise
        """
        if self.mock:
            # Mock: verify by re-computing the hash
            expected = hashlib.sha256(data).digest()
            return signature == expected
        else:
            # Real mode would use PKCS#11 C_Verify
            raise NotImplementedError("Real HSM verification not implemented")

    def generate_rsa_keypair(self, label: str) -> Tuple[Optional[bytes], Optional[bytes]]:
        """Generate an RSA key pair on the HSM.

        Args:
            label: The label/identifier for the key pair

        Returns:
            Tuple of (public_key, private_key) or (None, None) in mock mode
        """
        if self.mock:
            # Mock: return None for both keys
            return None, None
        else:
            # Real mode would use PKCS#11 C_GenerateKeyPair
            raise NotImplementedError("Real HSM key generation not implemented")
