"""
Hardware DNA
============
Generates unique device fingerprints based on hardware characteristics.
Used for device binding and attestation.
"""

import hashlib
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

_instance = None


@dataclass
class DeviceDNA:
    """Device DNA fingerprint."""
    dna_hash: str
    device_id: str
    dna: str


class HardwareDNA:
    """Generates and manages hardware DNA fingerprints."""

    def __init__(self):
        self._initialized = True

    def generate_device_dna(self) -> dict:
        """Generate a device DNA fingerprint."""
        import platform
        import uuid

        # Collect hardware identifiers
        system = platform.system()
        node = platform.node()
        machine = platform.machine()
        processor = platform.processor()
        mac_hash = hashlib.sha256(str(uuid.getnode()).encode()).hexdigest()[:16]

        # Create DNA hash
        dna_source = f"{system}:{node}:{machine}:{processor}:{mac_hash}"
        dna_hash = hashlib.sha256(dna_source.encode()).hexdigest()
        device_id = f"HDNA-{dna_hash[:12].upper()}"

        return {
            "dna_hash": dna_hash,
            "device_id": device_id,
            "dna": dna_source,
        }


def get_hardware_dna() -> HardwareDNA:
    """Get or create the singleton HardwareDNA instance."""
    global _instance
    if _instance is None:
        _instance = HardwareDNA()
    return _instance


def reset_hardware_dna() -> None:
    """Reset the singleton for testing."""
    global _instance
    _instance = None
