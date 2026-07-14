"""
AsimNexus Biometric Gate Module (Consolidated)
===============================================
Consolidated from: biometric_hardware_gate.py, hardware_dna.py

Re-exports all biometric/hardware auth classes from the primary implementations.
"""

# Re-export from biometric_hardware_gate.py (651 lines, primary implementation)
from core.security.biometric_hardware_gate import (
    BiometricHardwareGate, get_biometric_gate, reset_biometric_gate,
    BiometricGateState,
)

# Re-export from hardware_dna.py (68 lines)
from core.security.hardware_dna import (
    HardwareDNA, get_hardware_dna, DeviceDNA,
)

__all__ = [
    "BiometricHardwareGate", "get_biometric_gate", "reset_biometric_gate",
    "BiometricGateState",
    "HardwareDNA", "get_hardware_dna", "DeviceDNA",
]
