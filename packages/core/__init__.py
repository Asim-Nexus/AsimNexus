
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""Core Module"""

from .kernel.microkernel import (
    ASIMMicrokernel as Microkernel,
    Capability,
)

# Lazy singletons for microkernel access
_microkernel_instance = None

def get_microkernel():
    global _microkernel_instance
    if _microkernel_instance is None:
        from .kernel.microkernel import ASIMMicrokernel
        _microkernel_instance = ASIMMicrokernel()
    return _microkernel_instance

def get_kernel_sync():
    return get_microkernel()

__all__ = [
    'Microkernel',
    'Capability',
    'get_microkernel',
    'get_kernel_sync',
]
