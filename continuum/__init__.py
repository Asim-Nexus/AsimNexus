#!/usr/bin/env python3
"""Edge AI Continuum — Seamless AI across PWA → Mobile → Desktop → Server.

The Edge AI Continuum enables a single AI agent session to move fluidly
across device boundaries: a conversation started on a Progressive Web App
can be handed off to a mobile device, resumed on a desktop, and offloaded
to a server — all with full context preservation.

Core concept:
    A **ContextContinuum** manages context snapshots that capture the
    conversation history, agent state, mesh network state, and metadata
    at any point in time. These snapshots can be transferred between
    device types, restored later, or pruned when stale.

Device types supported:
    - PWA:      Progressive Web App (browser-based)
    - MOBILE:   Native mobile application
    - DESKTOP:  Desktop application (Electron / Tauri)
    - SERVER:   Backend / cloud server instance
    - EMBEDDED: IoT / edge device with constrained resources

Modules:
    context_manager: ContextContinuum implementation with snapshots,
        transfers, persistence, and factory functions.
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)

__all__ = [
    "ContextContinuum",
    "ContextSnapshot",
    "SessionState",
    "DeviceType",
    "get_context_manager",
    "reset_all",
]

# Global singletons
_context_manager: Optional["ContextContinuum"] = None


def get_context_manager(storage_dir: Optional[str] = None) -> "ContextContinuum":
    """Get or create the singleton ContextContinuum instance.

    Args:
        storage_dir: Optional directory for snapshot persistence.
            If not provided, snapshots are kept only in memory.

    Returns:
        The global ContextContinuum instance.
    """
    global _context_manager
    if _context_manager is None:
        from continuum.context_manager import ContextContinuum
        _context_manager = ContextContinuum(storage_dir=storage_dir)
    return _context_manager


def reset_all():
    """Reset all singleton instances (for testing).

    Clears the global context manager so the next call to
    ``get_context_manager()`` creates a fresh instance.
    """
    global _context_manager
    _context_manager = None
    logger.info("Continuum singletons reset")
