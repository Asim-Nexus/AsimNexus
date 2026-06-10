"""
ASIMNEXUS Economy + Identity/DID API Endpoints
===============================================
Split into modular files under core/api_endpoints/.
This shim re-exports from the new package for backward compatibility.
"""

from core.api_endpoints import router, register_economy_routes
