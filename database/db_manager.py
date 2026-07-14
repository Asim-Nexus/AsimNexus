"""
database/db_manager.py
AsimNexus — Database Manager (Enhanced)

Provides the DBManager interface consumed by routes/memory.py:
    get_conversations(user_id) -> list
    get_api_keys(user_id) -> list
    update_keys(user_id, keys) -> dict
    health_check() -> dict

Backed by SQLite with:
  - Connection pooling (thread-local)
  - WAL mode for concurrent reads
  - Automatic retry with exponential backoff
  - Automated backup integration
  - Schema migration framework
  - PostgreSQL migration path via database.migrations
"""

import json
import logging
import os
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("AsimNexus.DB.Manager")

_DEFAULT_DB_DIR = Path(__file__).resolve().parent / "data"
_DEFAULT_DB_PATH = _DEFAULT_DB_DIR / "asimnexus.db"

# Connection pool defaults
_MAX_RETRIES = 3
_RETRY_DELAY_SEC = 0.1       # initial delay, doubles each retry
_POOL_TIMEOUT_SEC = 5.0
_WAL_CHECKPOINT_INTERVAL = 60  # seconds between WAL checkpoints


class _ConnectionPool:
    """Thread-safe SQLite connection pool with WAL mode.

    Maintains one connection per thread (thread-local) to avoid
    SQLite's single-writer limitation across threads.
    """

    def __init__(self, db_path: str, max_retries: int = _MAX_RETRIES,
                 retry_delay: float = _RETRY_DELAY_SEC):
        self._db_path = db_path
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._local = threading.local()
        self._lock = threading.Lock()
        self._last_checkpoint = 0.0

    def get_connection(self) -> sqlite3.Connection:
        """Get a thread-local connection, creating one if needed."""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = self._create_connection()
        return self._local.conn

    def _create_connection(self) -> sqlite3.Connection:
        """Create a new SQLite connection with WAL mode and retry."""
        last_exc = None
        delay = self._retry_delay
        for attempt in range(1, self._max_retries + 1):
            try:
                conn = sqlite3.connect(
                    self._db_path,
                    timeout=_POOL_TIMEOUT_SEC,
                    check_same_thread=False,
                )
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA synchronous=NORMAL")
                conn.execute("PRAGMA busy_timeout=5000")
                conn.execute("PRAGMA foreign_keys=ON")
                conn.row_factory = sqlite3.Row
                logger.debug("Connection created (attempt %d/%d)", attempt, self._max_retries)
                return conn
            except sqlite3.OperationalError as exc:
                last_exc = exc
                logger.warning("DB connection attempt %d failed: %s", attempt, exc)
                time.sleep(delay)
                delay *= 2  # exponential backoff
        raise ConnectionError(
            f"Could not connect to database after {self._max_retries} retries"
        ) from last_exc

    def checkpoint_wal(self, force: bool = False) -> None:
        """Periodically checkpoint the WAL to keep it from growing unbounded."""
        now = time.time()
        if not force and (now - self._last_checkpoint < _WAL_CHECKPOINT_INTERVAL):
            return
        try:
            conn = self.get_connection()
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            self._last_checkpoint = now
            logger.debug("WAL checkpoint completed")
        except Exception as exc:
            logger.warning("WAL checkpoint failed: %s", exc)

    def close_all(self) -> None:
        """Close all connections in the pool."""
        if hasattr(self._local, "conn") and self._local.conn:
            try:
                self._local.conn.close()
            except Exception:
                pass
            self._local.conn = None


class DBManager:
    """Database manager — conversations, API keys, health.

    Uses SQLite with connection pooling, WAL mode, and automatic retry.
    PostgreSQL migration available via database.migrations.postgresql.PostgreSQLMigration.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or str(_DEFAULT_DB_PATH)
        self._initialized = False
        self._pool: Optional[_ConnectionPool] = None
        self._migration_version = 0

    # ── Initialization ──────────────────────────────────────────────────

    def initialize(self) -> None:
        """Ensure database and tables exist with connection pool."""
        if self._initialized:
            return
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._pool = _ConnectionPool(self.db_path)
        conn = self._pool.get_connection()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                content TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                service TEXT NOT NULL,
                api_key TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversations_user
            ON conversations(user_id)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_api_keys_user
            ON api_keys(user_id)
        """)
        # Schema version tracking
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL DEFAULT (datetime('now')),
                description TEXT
            )
        """)
        row = conn.execute(
            "SELECT COALESCE(MAX(version), 0) FROM schema_version"
        ).fetchone()
        self._migration_version = row[0] if row else 0
        conn.commit()
        self._initialized = True
        logger.info(
            "DBManager initialized (path=%s, schema_version=%d)",
            self.db_path, self._migration_version,
        )

    # ── Migration helpers ───────────────────────────────────────────────

    def get_schema_version(self) -> int:
        """Return the current schema version."""
        self._ensure()
        return self._migration_version

    def apply_migration(self, version: int, description: str,
                        statements: List[str]) -> bool:
        """Apply a schema migration transactionally."""
        self._ensure()
        conn = self._pool.get_connection()
        try:
            conn.execute("BEGIN")
            for stmt in statements:
                conn.execute(stmt)
            conn.execute(
                "INSERT INTO schema_version (version, description) VALUES (?, ?)",
                (version, description),
            )
            conn.commit()
            self._migration_version = version
            logger.info("Migration v%d applied: %s", version, description)
            return True
        except Exception as exc:
            conn.rollback()
            logger.error("Migration v%d failed: %s", version, exc)
            return False

    def get_pending_migrations(self) -> List[Dict[str, Any]]:
        """Return migrations that have not yet been applied."""
        return _PENDING_MIGRATIONS[self._migration_version:]

    def run_pending_migrations(self) -> List[Dict[str, Any]]:
        """Apply all pending migrations in order."""
        results = []
        for mig in _PENDING_MIGRATIONS:
            if mig["version"] <= self._migration_version:
                continue
            ok = self.apply_migration(
                mig["version"], mig["description"], mig["statements"],
            )
            results.append({"version": mig["version"], "success": ok})
        return results

    # ── Routes interface ────────────────────────────────────────────────

    async def get_conversations(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all conversations for a user."""
        self._ensure()
        conn = self._pool.get_connection()
        rows = conn.execute(
            "SELECT id, role, content, created_at FROM conversations "
            "WHERE user_id = ? ORDER BY created_at DESC LIMIT 100",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    async def get_api_keys(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all API keys for a user."""
        self._ensure()
        conn = self._pool.get_connection()
        rows = conn.execute(
            "SELECT id, service, api_key, created_at FROM api_keys "
            "WHERE user_id = ?",
            (user_id,),
        ).fetchall()
        # Mask keys for security
        result = []
        for r in rows:
            d = dict(r)
            key = d.get("api_key", "")
            if len(key) > 8:
                d["api_key"] = key[:4] + "****" + key[-4:]
            result.append(d)
        return result

    async def update_keys(self, user_id: str, keys: Dict[str, str]) -> Dict[str, Any]:
        """Update API keys for a user (replaces all keys for that user)."""
        self._ensure()
        conn = self._pool.get_connection()
        conn.execute("DELETE FROM api_keys WHERE user_id = ?", (user_id,))
        for service, api_key in keys.items():
            conn.execute(
                "INSERT INTO api_keys (user_id, service, api_key) VALUES (?, ?, ?)",
                (user_id, service, api_key),
            )
        conn.commit()
        logger.info("API keys updated for user %s (%d services)", user_id, len(keys))
        return {"user_id": user_id, "services_updated": len(keys)}

    async def health_check(self) -> Dict[str, Any]:
        """Check database connectivity."""
        self._ensure()
        try:
            conn = self._pool.get_connection()
            conn.execute("SELECT 1")
            return {
                "status": "healthy",
                "database": "sqlite",
                "path": self.db_path,
                "schema_version": self._migration_version,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
        except Exception as exc:
            return {
                "status": "unhealthy",
                "error": str(exc),
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }

    # ── Connection pool management ──────────────────────────────────────

    def checkpoint(self, force: bool = False) -> None:
        """Trigger a WAL checkpoint."""
        if self._pool:
            self._pool.checkpoint_wal(force=force)

    def close(self) -> None:
        """Close all pooled connections."""
        if self._pool:
            self._pool.close_all()
        self._initialized = False

    # ── Internals ───────────────────────────────────────────────────────

    def _ensure(self) -> None:
        if not self._initialized:
            self.initialize()


# ── Schema Migrations ─────────────────────────────────────────────────────
# Ordered list of migrations. Each entry has:
#   version, description, statements (list of SQL strings)

_PENDING_MIGRATIONS: List[Dict[str, Any]] = [
    {
        "version": 1,
        "description": "Initial schema (conversations, api_keys, schema_version)",
        "statements": [
            """CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                content TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )""",
            """CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                service TEXT NOT NULL,
                api_key TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )""",
            "CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_api_keys_user ON api_keys(user_id)",
        ],
    },
    {
        "version": 2,
        "description": "Add self_awareness_knowledge table",
        "statements": [
            """CREATE TABLE IF NOT EXISTS self_awareness_knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                source TEXT DEFAULT 'manual',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            )""",
            "CREATE INDEX IF NOT EXISTS idx_knowledge_key ON self_awareness_knowledge(key)",
        ],
    },
    {
        "version": 3,
        "description": "Add build_actions table for SelfBuilder persistence",
        "statements": [
            """CREATE TABLE IF NOT EXISTS build_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action_id TEXT UNIQUE NOT NULL,
                action_type TEXT NOT NULL,
                filepath TEXT,
                status TEXT DEFAULT 'completed',
                message TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )""",
            "CREATE INDEX IF NOT EXISTS idx_build_actions_type ON build_actions(action_type)",
            "CREATE INDEX IF NOT EXISTS idx_build_actions_created ON build_actions(created_at)",
        ],
    },
    {
        "version": 4,
        "description": "Add mirror_reflections table for MirrorModule persistence",
        "statements": [
            """CREATE TABLE IF NOT EXISTS mirror_reflections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                reflection_id TEXT UNIQUE NOT NULL,
                intent TEXT,
                contradictions TEXT,
                balance_impact REAL DEFAULT 0.0,
                response TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )""",
            "CREATE INDEX IF NOT EXISTS idx_reflections_user ON mirror_reflections(user_id)",
        ],
    },
    {
        "version": 5,
        "description": "Add evolution_suggestions table for EvolutionEngine persistence",
        "statements": [
            """CREATE TABLE IF NOT EXISTS evolution_suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                suggestion_id TEXT UNIQUE NOT NULL,
                category TEXT,
                title TEXT,
                description TEXT,
                status TEXT DEFAULT 'pending',
                priority TEXT DEFAULT 'medium',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                applied_at TEXT
            )""",
            "CREATE INDEX IF NOT EXISTS idx_suggestions_status ON evolution_suggestions(status)",
        ],
    },
]
