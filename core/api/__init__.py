"""
AsimNexus API Module
====================
Core API endpoints for system introspection, government, real-time data, and WebSocket.
"""

from .core_kernel_api import router as core_kernel_router
from .gov_routes import router as gov_router
from .real_time_api import router as real_time_router
from .ws_routes import router as ws_router, ConnectionManager

__all__ = [
    "core_kernel_router",
    "gov_router",
    "real_time_router",
    "ws_router",
    "ConnectionManager",
]
