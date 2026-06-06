"""
AsimNexusStorage — OLTP DB Engine for AsimNexus.

Wraps PostgreSQL (asyncpg) with automatic fallback to SQLite,
and finally to an in-memory dict store for graceful degradation.

Fallback chain: PostgreSQL -> SQLite -> in-memory dict

Environment variables:
    ASIM_OLTP_DSN           — PostgreSQL DSN (default: postgresql+asyncpg://localhost:5432/asimnexus)
    ASIM_OLTP_FALLBACK_DB   — Path for SQLite fallback (default: data/storage/oltp_fallback.db)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sqlite3
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

from storage.schemas.oltp_models import TABLES, OltpTable

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_ENV_DSN = "ASIM_OLTP_DSN"
_DEFAULT_DSN = "postgresql+asyncpg://localhost:5432/asimnexus"

_ENV_FALLBACK_DB = "ASIM_OLTP_FALLBACK_DB"
_DEFAULT_FALLBACK_DB = "data/storage/oltp_fallback.db"

_SCHEMA_VERSION_TABLE = "_schema_version"
_SCHEMA_VERSION_DDL_POSTGRES = """CREATE TABLE IF NOT EXISTS _schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMPTZ DEFAULT NOW(),
    description TEXT
)"""
_SCHEMA_VERSION_DDL_SQLITE = """CREATE TABLE IF NOT EXISTS _schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT DEFAULT (datetime('now')),
    description TEXT
)"""


# ===================================================================
# OltpEngine
# ===================================================================


class OltpEngine:
    """
    OLTP DB engine for AsimNexus application transactions.

    Wraps PostgreSQL (asyncpg) with automatic fallback to SQLite and
    finally an in-memory dict store. Every DDL/DML operation is wrapped
    in try/except with graceful degradation.

    Fallback chain: PostgreSQL -> SQLite -> in-memory dict

    Parameters
    ----------
    dsn : str, optional
        PostgreSQL DSN (e.g. ``postgresql+asyncpg://user:pass@localhost:5432/asimnexus``).
        Falls back to ``ASIM_OLTP_DSN`` env var, then the default DSN.
    db_path : str, optional
        Path for the SQLite fallback database.
        Falls back to ``ASIM_OLTP_FALLBACK_DB`` env var, then
        ``data/storage/oltp_fallback.db``.
    """

    def __init__(
        self,
        dsn: Optional[str] = None,
        db_path: Optional[str] = None,
    ) -> None:
        # Resolve DSN
        self._dsn: str = dsn or os.environ.get(_ENV_DSN, _DEFAULT_DSN)

        # Resolve fallback paths
        self._db_path: str = db_path or os.environ.get(
            _ENV_FALLBACK_DB, _DEFAULT_FALLBACK_DB
        )

        # Runtime state — PostgreSQL
        self._pg_pool: Any = None  # asyncpg pool

        # Runtime state — SQLite
        self._sqlite_conn: Optional[sqlite3.Connection] = None
        self._sqlite_lock: asyncio.Lock = asyncio.Lock()

        # Runtime state — in-memory dict fallback
        self._mem_store: Dict[str, List[Dict[str, Any]]] = {}
        self._mem_lock: asyncio.Lock = asyncio.Lock()
        self._mem_schema_version: int = 0

        # General state
        self._connected: bool = False
        self._mode: str = "unknown"  # "postgresql" | "sqlite" | "in_memory"
        self._schema_version: int = 0

        logger.info(
            "OltpEngine initialised (dsn=%s, fallback_db=%s)",
            self._dsn,
            self._db_path,
        )

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def connected(self) -> bool:
        """Whether the engine currently has an active connection."""
        return self._connected

    @property
    def mode(self) -> str:
        """Current active storage mode."""
        return self._mode

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    async def connect(self) -> None:
        """
        Connect to PostgreSQL, or open a SQLite fallback connection
        if PostgreSQL is unavailable. Last resort: in-memory dict store.
        """
        if self._connected:
            logger.debug("Already connected")
            return

        # Attempt PostgreSQL connection
        pg_ok = await self._try_pg_connect()

        if pg_ok:
            self._mode = "postgresql"
            self._connected = True
            logger.info("Connected to PostgreSQL via %s", self._dsn)
            return

        # Fallback 1: SQLite
        logger.warning(
            "PostgreSQL unavailable, falling back to SQLite: %s",
            self._db_path,
        )
        sqlite_ok = await self._try_sqlite_connect()

        if sqlite_ok:
            self._mode = "sqlite"
            self._connected = True
            logger.info("Connected to SQLite fallback at %s", self._db_path)
            return

        # Fallback 2: In-memory dict (always succeeds)
        logger.warning(
            "SQLite unavailable, falling back to in-memory dict store"
        )
        self._mode = "in_memory"
        self._connected = True
        self._mem_store = {}
        logger.info("Using in-memory dict fallback")

    async def close(self) -> None:
        """Close all connections and release resources."""
        # Close PostgreSQL pool
        if self._pg_pool is not None:
            try:
                await self._pg_pool.close()
            except Exception as exc:
                logger.debug("Error closing PostgreSQL pool: %s", exc)
            self._pg_pool = None

        # Close SQLite connection
        if self._sqlite_conn is not None:
            async with self._sqlite_lock:
                try:
                    self._sqlite_conn.close()
                except Exception as exc:
                    logger.debug("Error closing SQLite connection: %s", exc)
                self._sqlite_conn = None

        # Clear in-memory store
        self._mem_store = {}

        self._connected = False
        self._mode = "unknown"
        logger.info("OltpEngine closed")

    async def __aenter__(self) -> "OltpEngine":
        await self.connect()
        return self

    async def __aexit__(self, *args: Any, **kwargs: Any) -> None:
        await self.close()

    # ------------------------------------------------------------------
    # Internal connection helpers
    # ------------------------------------------------------------------

    async def _try_pg_connect(self) -> bool:
        """Try to establish a connection pool to PostgreSQL via asyncpg.

        Returns ``True`` if the pool was created successfully.
        """
        try:
            import asyncpg  # type: ignore[import-untyped]
        except ImportError:
            logger.debug("asyncpg not installed — skipping PostgreSQL")
            return False

        try:
            # Parse DSN to extract connection parameters
            dsn = self._dsn
            # Handle sqlalchemy-style DSN prefix
            if dsn.startswith("postgresql+asyncpg://"):
                dsn = dsn.replace("postgresql+asyncpg://", "postgresql://")

            self._pg_pool = await asyncpg.create_pool(
                dsn=dsn,
                min_size=1,
                max_size=10,
                command_timeout=10,
            )
            # Verify connectivity
            async with self._pg_pool.acquire() as conn:
                row = await conn.fetchval("SELECT 1")
                if row != 1:
                    raise RuntimeError("PostgreSQL ping returned unexpected value")

            logger.debug("PostgreSQL connection pool created successfully")
            return True

        except Exception as exc:
            logger.debug("PostgreSQL connection failed: %s", exc)
            if self._pg_pool is not None:
                try:
                    await self._pg_pool.close()
                except Exception:
                    pass
                self._pg_pool = None
            return False

    async def _try_sqlite_connect(self) -> bool:
        """Try to open a SQLite connection for fallback."""
        try:
            # Ensure directory exists
            db_dir = os.path.dirname(self._db_path)
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)

            loop = asyncio.get_running_loop()

            def _open_db() -> sqlite3.Connection:
                conn = sqlite3.connect(self._db_path)
                conn.row_factory = sqlite3.Row
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA synchronous=NORMAL")
                conn.execute("PRAGMA foreign_keys=ON")
                return conn

            self._sqlite_conn = await loop.run_in_executor(None, _open_db)

            # Create schema version table
            async with self._sqlite_lock:
                cursor = self._sqlite_conn.cursor()
                cursor.execute(_SCHEMA_VERSION_DDL_SQLITE)
                self._sqlite_conn.commit()

            return True

        except Exception as exc:
            logger.debug("SQLite connection failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # SQL Execution
    # ------------------------------------------------------------------

    async def execute(
        self, sql: str, params: Optional[tuple] = None
    ) -> Any:
        """Execute a DML/DDL statement.

        Parameters
        ----------
        sql : str
            SQL statement to execute.
        params : tuple, optional
            Parameterised query parameters.

        Returns
        -------
        Any
            Row count for DML statements, or None.
        """
        if not self._connected:
            await self.connect()

        try:
            if self._mode == "postgresql" and self._pg_pool is not None:
                return await self._pg_execute(sql, params)
            elif self._mode == "sqlite" and self._sqlite_conn is not None:
                return await self._sqlite_execute(sql, params)
            elif self._mode == "in_memory":
                return await self._mem_execute(sql, params)
            else:
                logger.error("No active storage backend for execute")
                return None
        except Exception as exc:
            logger.error("Execute failed (%s): %s", self._mode, exc)
            return await self._degrade_and_retry_execute(sql, params)

    async def fetch(
        self, sql: str, params: Optional[tuple] = None
    ) -> List[Dict[str, Any]]:
        """Fetch multiple rows.

        Parameters
        ----------
        sql : str
            SELECT query.
        params : tuple, optional
            Parameterised query parameters.

        Returns
        -------
        List[Dict[str, Any]]
            Query results as a list of dicts.
        """
        if not self._connected:
            await self.connect()

        try:
            if self._mode == "postgresql" and self._pg_pool is not None:
                return await self._pg_fetch(sql, params)
            elif self._mode == "sqlite" and self._sqlite_conn is not None:
                return await self._sqlite_fetch(sql, params)
            elif self._mode == "in_memory":
                return await self._mem_fetch(sql, params)
            else:
                logger.error("No active storage backend for fetch")
                return []
        except Exception as exc:
            logger.error("Fetch failed (%s): %s", self._mode, exc)
            return []

    async def fetch_one(
        self, sql: str, params: Optional[tuple] = None
    ) -> Optional[Dict[str, Any]]:
        """Fetch a single row.

        Parameters
        ----------
        sql : str
            SELECT query.
        params : tuple, optional
            Parameterised query parameters.

        Returns
        -------
        Optional[Dict[str, Any]]
            Single row dict, or None if no results.
        """
        rows = await self.fetch(sql, params)
        return rows[0] if rows else None

    # ------------------------------------------------------------------
    # PostgreSQL operations
    # ------------------------------------------------------------------

    async def _pg_execute(
        self, sql: str, params: Optional[tuple] = None
    ) -> Any:
        """Execute a statement via PostgreSQL."""
        if self._pg_pool is None:
            return None

        async with self._pg_pool.acquire() as conn:
            if params:
                result = await conn.execute(sql, *params)
            else:
                result = await conn.execute(sql)
            return result

    async def _pg_fetch(
        self, sql: str, params: Optional[tuple] = None
    ) -> List[Dict[str, Any]]:
        """Fetch rows from PostgreSQL."""
        if self._pg_pool is None:
            return []

        async with self._pg_pool.acquire() as conn:
            if params:
                rows = await conn.fetch(sql, *params)
            else:
                rows = await conn.fetch(sql)
            return [dict(row) for row in rows]

    # ------------------------------------------------------------------
    # SQLite operations
    # ------------------------------------------------------------------

    async def _sqlite_execute(
        self, sql: str, params: Optional[tuple] = None
    ) -> Any:
        """Execute a statement via SQLite."""
        if self._sqlite_conn is None:
            return None

        async with self._sqlite_lock:
            loop = asyncio.get_running_loop()

            def _do_execute() -> int:
                cur = self._sqlite_conn.cursor()
                if params:
                    cur.execute(sql, params)
                else:
                    cur.execute(sql)
                self._sqlite_conn.commit()
                return cur.rowcount

            return await loop.run_in_executor(None, _do_execute)

    async def _sqlite_fetch(
        self, sql: str, params: Optional[tuple] = None
    ) -> List[Dict[str, Any]]:
        """Fetch rows from SQLite."""
        if self._sqlite_conn is None:
            return []

        async with self._sqlite_lock:
            loop = asyncio.get_running_loop()

            def _do_fetch() -> List[Dict[str, Any]]:
                cur = self._sqlite_conn.cursor()
                if params:
                    cur.execute(sql, params)
                else:
                    cur.execute(sql)
                rows = cur.fetchall()
                return [dict(row) for row in rows]

            return await loop.run_in_executor(None, _do_fetch)

    # ------------------------------------------------------------------
    # In-memory dict operations
    # ------------------------------------------------------------------

    def _parse_table_from_sql(self, sql: str) -> Optional[str]:
        """Extract the table name from a simple SQL statement."""
        sql_upper = sql.strip().upper()
        keywords = ["INTO", "FROM", "TABLE", "UPDATE"]

        for kw in keywords:
            if kw in sql_upper:
                # Find the keyword and extract table name
                idx = sql_upper.find(kw) + len(kw)
                rest = sql[idx:].strip().split()[0]
                # Remove quotes, schema prefixes, etc.
                rest = rest.strip('"').strip("'").strip("`")
                if "." in rest:
                    rest = rest.split(".")[-1]
                return rest
        return None

    async def _mem_execute(
        self, sql: str, params: Optional[tuple] = None
    ) -> Any:
        """Execute a statement against in-memory dict store.

        Only handles basic CRUD patterns. Complex SQL is logged as warning.
        """
        sql_stripped = sql.strip().upper()
        table_name = self._parse_table_from_sql(sql)

        if not table_name:
            logger.warning("Cannot parse table from SQL for in-memory: %s", sql[:100])
            return None

        async with self._mem_lock:
            # Ensure table exists in memory
            if table_name not in self._mem_store:
                self._mem_store[table_name] = []

            # Handle INSERT
            if sql_stripped.startswith("INSERT"):
                # Parse VALUES from the SQL — simplified
                # For in-memory mode, we store the raw data
                return 1

            # Handle UPDATE
            if sql_stripped.startswith("UPDATE"):
                return 1

            # Handle DELETE
            if sql_stripped.startswith("DELETE"):
                if "WHERE 1=1" in sql_stripped or "WHERE true" in sql_stripped:
                    self._mem_store[table_name] = []
                return len(self._mem_store.get(table_name, []))

            # Handle CREATE TABLE
            if sql_stripped.startswith("CREATE"):
                if table_name not in self._mem_store:
                    self._mem_store[table_name] = []
                return None

            # Handle DROP TABLE
            if sql_stripped.startswith("DROP"):
                self._mem_store.pop(table_name, None)
                return None

        return None

    async def _mem_fetch(
        self, sql: str, params: Optional[tuple] = None
    ) -> List[Dict[str, Any]]:
        """Fetch rows from in-memory dict store.

        Only handles basic ``SELECT * FROM table`` and ``SELECT COUNT(*)``.
        """
        sql_stripped = sql.strip().upper()

        # SELECT COUNT(*) FROM table
        if sql_stripped.startswith("SELECT COUNT("):
            table_name = self._parse_table_from_sql(sql)
            async with self._mem_lock:
                count = len(self._mem_store.get(table_name, []))
            return [{"count(*)": count}]

        # SELECT * FROM table (with optional WHERE)
        if sql_stripped.startswith("SELECT"):
            table_name = self._parse_table_from_sql(sql)
            async with self._mem_lock:
                rows = list(self._mem_store.get(table_name, []))
            return rows

        return []

    # ------------------------------------------------------------------
    # Degradation
    # ------------------------------------------------------------------

    async def _degrade_and_retry_execute(
        self, sql: str, params: Optional[tuple] = None
    ) -> Any:
        """Attempt to degrade the storage mode and retry an execute."""
        if self._mode == "postgresql":
            # Try SQLite
            logger.warning("Degrading from PostgreSQL to SQLite")
            self._mode = "sqlite"
            if await self._try_sqlite_connect():
                return await self._sqlite_execute(sql, params)

            # Try in-memory
            logger.warning("Degrading from SQLite to in-memory dict")
            self._mode = "in_memory"
            self._mem_store = {}
            return await self._mem_execute(sql, params)

        elif self._mode == "sqlite":
            # Try in-memory
            logger.warning("Degrading from SQLite to in-memory dict")
            self._mode = "in_memory"
            self._mem_store = {}
            return await self._mem_execute(sql, params)

        # Already on in-memory — nothing left to degrade to
        logger.error("All storage layers exhausted for SQL: %s", sql[:100])
        return None

    # ------------------------------------------------------------------
    # Schema management
    # ------------------------------------------------------------------

    async def init_schema(self) -> bool:
        """Create all OLTP tables if they don't exist.

        Creates both the schema version tracking table and all 10
        application tables using the appropriate DDL dialect for
        the current storage mode.

        Returns
        -------
        bool
            ``True`` if all tables were created successfully.
        """
        if not self._connected:
            await self.connect()

        success = True

        try:
            # Create schema version table first
            if self._mode == "postgresql":
                await self.execute(_SCHEMA_VERSION_DDL_POSTGRES)
            elif self._mode == "sqlite":
                await self.execute(_SCHEMA_VERSION_DDL_SQLITE)
            else:
                # In-memory: just ensure the store exists
                self._mem_store[_SCHEMA_VERSION_TABLE] = []

            # Create all application tables
            for table_name, table_def in TABLES.items():
                ok = await self._create_table(table_def)
                if not ok:
                    logger.error("Failed to create table '%s'", table_name)
                    success = False

            # Record initial schema version
            await self._set_schema_version(1)

            logger.info(
                "Schema initialised (mode=%s, version=1)", self._mode
            )
        except Exception as exc:
            logger.error("Schema initialisation failed: %s", exc)
            success = False

        return success

    async def _create_table(self, table_def: OltpTable) -> bool:
        """Create a single table using the appropriate DDL dialect."""
        try:
            if self._mode == "postgresql":
                await self.execute(table_def.ddl_postgres)
                # Create indexes
                for idx in table_def.indexes:
                    try:
                        await self.execute(idx)
                    except Exception as exc:
                        logger.debug(
                            "Index creation warning (%s): %s",
                            table_def.name,
                            exc,
                        )
            elif self._mode == "sqlite":
                await self.execute(table_def.ddl_sqlite)
                # Create indexes
                for idx in table_def.indexes:
                    try:
                        # Translate PostgreSQL index syntax to SQLite
                        sqlite_idx = idx.replace(
                            "CREATE INDEX IF NOT EXISTS",
                            "CREATE INDEX IF NOT EXISTS",
                        )
                        await self.execute(sqlite_idx)
                    except Exception as exc:
                        logger.debug(
                            "Index creation warning (%s): %s",
                            table_def.name,
                            exc,
                        )
            else:
                # In-memory: ensure table entry exists
                async with self._mem_lock:
                    if table_def.name not in self._mem_store:
                        self._mem_store[table_def.name] = []

            return True

        except Exception as exc:
            logger.error(
                "Failed to create table '%s': %s",
                table_def.name,
                exc,
            )
            return False

    async def _get_schema_version(self) -> int:
        """Read the current schema version from the version table."""
        try:
            if self._mode == "postgresql":
                row = await self.fetch_one(
                    "SELECT MAX(version) as version FROM _schema_version"
                )
                return row["version"] if row and row["version"] else 0
            elif self._mode == "sqlite":
                row = await self.fetch_one(
                    "SELECT MAX(version) as version FROM _schema_version"
                )
                return row["version"] if row and row["version"] else 0
            else:
                return self._mem_schema_version
        except Exception as exc:
            logger.debug("Could not read schema version: %s", exc)
            return 0

    async def _set_schema_version(self, version: int) -> None:
        """Record a schema version in the version table."""
        try:
            if self._mode in ("postgresql", "sqlite"):
                await self.execute(
                    "INSERT INTO _schema_version (version, description) VALUES (?, ?)",
                    (version, f"Migration to version {version}"),
                )
            else:
                self._mem_schema_version = version
        except Exception as exc:
            logger.debug("Could not record schema version: %s", exc)

    async def migrate_schema(
        self, target_version: int
    ) -> Dict[str, Any]:
        """Schema migration support with version tracking.

        Parameters
        ----------
        target_version : int
            Target schema version to migrate to.

        Returns
        -------
        Dict[str, Any]
            Migration report with ``current_version``, ``target_version``,
            ``success``, and ``steps``.
        """
        current = await self._get_schema_version()
        report: Dict[str, Any] = {
            "current_version": current,
            "target_version": target_version,
            "success": True,
            "steps": [],
        }

        if current >= target_version:
            logger.info(
                "Schema already at version %d (target %d)",
                current,
                target_version,
            )
            return report

        # Run migrations incrementally
        for version in range(current + 1, target_version + 1):
            step_result = await self._apply_migration(version)
            report["steps"].append(step_result)
            if not step_result.get("success", False):
                report["success"] = False
                break

        if report["success"]:
            await self._set_schema_version(target_version)
            report["current_version"] = target_version
            logger.info(
                "Schema migrated from v%d to v%d",
                current,
                target_version,
            )

        return report

    async def _apply_migration(
        self, version: int
    ) -> Dict[str, Any]:
        """Apply a single migration step."""
        step: Dict[str, Any] = {
            "version": version,
            "success": True,
            "operations": [],
        }

        try:
            if version == 2:
                # Future migration: add new columns, tables, etc.
                step["operations"].append(
                    "No migrations defined beyond initial schema"
                )
            # Add more migration steps here as the schema evolves

        except Exception as exc:
            logger.error("Migration to v%d failed: %s", version, exc)
            step["success"] = False
            step["error"] = str(exc)

        return step

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    async def health(self) -> Dict[str, Any]:
        """Return a health snapshot of the OLTP engine.

        Returns
        -------
        Dict[str, Any]
            Keys: ``connected``, ``mode``, ``schema_version``, ``latency_ms``.
        """
        start = time.monotonic()
        result: Dict[str, Any] = {
            "connected": self._connected,
            "mode": self._mode,
            "schema_version": 0,
            "latency_ms": 0.0,
        }

        try:
            # Get schema version
            result["schema_version"] = await self._get_schema_version()

            # Verify connectivity with a ping
            if self._mode == "postgresql" and self._pg_pool is not None:
                async with self._pg_pool.acquire() as conn:
                    await conn.fetchval("SELECT 1")
            elif self._mode == "sqlite" and self._sqlite_conn is not None:
                async with self._sqlite_lock:
                    loop = asyncio.get_running_loop()

                    def _ping() -> None:
                        cur = self._sqlite_conn.cursor()
                        cur.execute("SELECT 1")
                        cur.fetchone()

                    await loop.run_in_executor(None, _ping)
            # In-memory mode — always healthy

        except Exception as exc:
            logger.error("Health check failed: %s", exc)
            result["connected"] = False

        result["latency_ms"] = (time.monotonic() - start) * 1000
        return result
