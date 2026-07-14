"""
AsimNexus Route Modules
=======================
Package that registers all route modules with the FastAPI app.
Each module is a self-contained router with its own prefix and tags.
"""

import logging
from fastapi import FastAPI

logger = logging.getLogger("AsimNexus.Routes")


def register_routes(app: FastAPI) -> None:
    """Register all route modules with the FastAPI application.

    Each module is imported and registered in its own try/except block
    so that a single broken module does not prevent all routes from loading.
    """
    _route_modules = [
        "nepal",
        "chat",
        "auth",
        "marketplace",
        "mesh",
        "os_control",
        "identity",
        "consensus",
        "analytics",
        "memory",
        "mcp",
        "healing",
        "universal",
        "sovereignty",
        "infrastructure",
        "finance",
        "government",
        "governance",
        "enterprise",
        "security",
        "learning",
        "observability",
        "registry",
        "deploy",
        "push",
        "bugs",
        "clones",
        "offline",
        "override",
        "router",
        "health",
        "rbe",
        "depin",
        "blockchain_identity",
        "jobs",
        "pwa",
        "release",
        "self_awareness",
        "stakeholder",
        "arvr",
        "soul_key",
        "mirror",
        "dreaming",
        "evolution",
        "universe",
        "dharma",
        "founder_clones",
    ]

    registered = 0
    failed = 0
    for module_name in _route_modules:
        try:
            mod = __import__(f"routes.{module_name}", fromlist=["router"])
            router = getattr(mod, "router")
            app.include_router(router)
            registered += 1
        except Exception as e:
            logger.warning("Route module 'routes.%s' skipped: %s", module_name, e)
            failed += 1

    logger.info(
        "Route registration complete: %d registered, %d failed (total %d routes)",
        registered, failed, len(app.routes),
    )
