"""OS Control Layer — Hardware and system-level control interface.

Provides a secure microkernel interface for:
- Hardware status monitoring (CPU, memory, disk, network, GPU)
- Hardware control (power management, device control)
- Driver management (install, update, verify)
- System-level operations (shutdown, restart, sleep)

All operations go through the Gateway for authorization.
"""

from os_control.microkernel import MicroKernelInterface

__all__ = ["MicroKernelInterface"]
