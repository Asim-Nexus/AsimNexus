# AsimNexus Database Layer
# ======================
# SQLite to PostgreSQL migration + Supabase integration
# Schema migration framework + automated backup system
#
# Usage:
#   from database import get_db, DBManager
#   db = get_db()
#   db.initialize()
#   conversations = db.get_conversations("user_123")

import logging
import threading
from typing import Optional

from .migrations.postgresql import PostgreSQLMigration, get_migration, get_migration_sync
from .migrations.manager import MigrationManager, get_migration_manager, run_pending_migrations
from .db_manager import DBManager

logger = logging.getLogger("AsimNexus.DB")

class DatabaseLayer:
    """Facade over the database subsystem — provides a unified entry point."""
    pass

# ── Singleton DBManager ──────────────────────────────────────────

_db_instance: Optional[DBManager] = None
_db_lock: threading.Lock = threading.Lock()


def get_db() -> DBManager:
    """Get or create the singleton DBManager instance.

    The first call creates and initializes the manager.
    Subsequent calls return the same instance (thread-safe).
    """
    global _db_instance
    if _db_instance is None:
        with _db_lock:
            if _db_instance is None:
                _db_instance = DBManager()
                _db_instance.initialize()
                logger.info("Database layer initialized (singleton)")
    return _db_instance


def reset_db() -> None:
    """Reset the singleton (for testing)."""
    global _db_instance
    with _db_lock:
        _db_instance = None


__all__ = [
    "PostgreSQLMigration",
    "get_migration",
    "get_migration_sync",
    "MigrationManager",
    "get_migration_manager",
    "run_pending_migrations",
    "DBManager",
    "DatabaseLayer",
    "get_db",
    "reset_db",
]
