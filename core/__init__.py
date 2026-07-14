# core/__init__.py
# AsimNexus — Core Package

import importlib
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Lazy subpackage loading — allows patch('core.orchestrator...') to work
# without eagerly importing the orchestrator module (which has heavy deps).
# Also enables `from core import self_awareness, mesh, evolution` etc.
_SUBPACKAGES = {
    "self_awareness": "core.self_awareness",
    "mesh": "core.mesh",
    "evolution": "core.evolution",
    "dreaming": "core.dreaming",
    "mirror": "core.mirror",
    "dharma_chakra": "core.dharma_chakra",
    "dharma": "core.dharma",
    "federation": "core.federation",
    "governance": "core.governance",
    "economy": "core.economy",
    "finance": "core.finance",
    "agents": "core.agents",
    "agent": "core.agent",
    "identity": "core.identity",
    "knowledge": "core.knowledge",
    "mcp": "core.mcp",
    "policy": "core.policy",
    "risk_management": "core.risk_management",
    "routing": "core.routing",
    "sandbox": "core.sandbox",
    "sync": "core.sync",
    "universal": "core.universal",
    "universe": "core.universe",
    "world": "core.world",
    "depin": "core.depin",
    "nepal": "core.nepal",
    "compliance": "core.compliance",
    "consensus": "core.consensus",
    "analytics": "core.analytics",
    "gateway": "core.gateway",
    "kernel": "core.kernel",
    "lifecycle": "core.lifecycle",
    "network": "core.network",
    "government": "core.government",
    "orchestrator": "core.orchestrator",
    "security": "core.security",
    "api": "core.api",
    "api_endpoints": "core.api_endpoints",
    "asim_brain": "core.asim_brain",
    "data": "core.data",
    "founder_clones": "core.founder_clones",
    "integration": "core.integration",
    "database": "database",
    "infrastructure": "core.infrastructure",
    "monitoring": "core.monitoring",
}


def __getattr__(name):
    if name in _SUBPACKAGES:
        return importlib.import_module(_SUBPACKAGES[name])
    # Convenience: allow `core.get_db()` without importing `core.database` first
    if name in _DATABASE_EXPORTS:
        db_mod = importlib.import_module("database")
        return getattr(db_mod, name)
    raise AttributeError(f"module 'core' has no attribute {name!r}")


# Convenience re-exports for the database layer
# Allows `from core import get_db, DBManager, reset_db` etc.
_DATABASE_EXPORTS = {
    "get_db",
    "reset_db",
    "DBManager",
    "DatabaseLayer",
    "MigrationManager",
    "PostgreSQLMigration",
    "get_migration",
    "get_migration_sync",
    "get_migration_manager",
    "run_pending_migrations",
}


def __dir__():
    """List available subpackages for tab-completion."""
    return list(_SUBPACKAGES.keys()) + [
        "__builtins__", "__cached__", "__doc__", "__file__",
        "__loader__", "__name__", "__package__", "__path__",
        "__spec__", "importlib", "logger",
    ]


__all__ = sorted(_SUBPACKAGES.keys())
