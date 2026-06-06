"""
AsimNexusEngine — Primary warehouse engine for AsimNexus.

Wraps ClickHouse with connection pooling, async inserts,
query templating, and graceful fallback.

Fallback chain: ClickHouse -> SQLite -> JSONL append

Uses ClickHouse HTTP interface (port 8123) via aiohttp
for maximum portability without native client libraries.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sqlite3
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import aiofiles
import aiohttp

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_CLICKHOUSE_DEFAULT_DSN = "clickhouse://localhost:9000/asimnexus"
_ENV_DSN = "ASIM_CLICKHOUSE_DSN"
_ENV_FALLBACK_DB = "ASIM_STORAGE_FALLBACK_DB"
_DEFAULT_FALLBACK_DB = "data/storage/clickhouse_fallback.db"
_DEFAULT_FALLBACK_JSONL = "data/storage/clickhouse_fallback.jsonl"
_CLICKHOUSE_HTTP_PORT = 8123


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class ClickHouseConfig:
    """Parsed ClickHouse connection parameters."""

    host: str = "localhost"
    port: int = _CLICKHOUSE_HTTP_PORT
    database: str = "asimnexus"
    user: str = "default"
    password: str = ""
    secure: bool = False


@dataclass
class EngineHealth:
    """Snapshot of engine health at a point in time."""

    connected: bool = False
    mode: str = "unknown"  # "clickhouse" | "sqlite" | "jsonl"
    tables: int = 0
    latency_ms: float = 0.0
    fallback_active: bool = False


# ---------------------------------------------------------------------------
# DSN parser
# ---------------------------------------------------------------------------


def _parse_clickhouse_dsn(dsn: str) -> ClickHouseConfig:
    """Parse a ``clickhouse://`` DSN string into a ``ClickHouseConfig``.

    Supports the following forms::

        clickhouse://localhost:9000/asimnexus
        clickhouse://user:password@localhost:9000/asimnexus
        clickhouse://host:port/database?secure=1
    """
    cfg = ClickHouseConfig()
    if not dsn:
        return cfg

    parsed = urlparse(dsn)
    if parsed.scheme not in ("clickhouse", "http", "https"):
        logger.warning("Unrecognised DSN scheme '%s', falling back to defaults", parsed.scheme)
        return cfg

    cfg.host = parsed.hostname or "localhost"
    if parsed.port:
        cfg.port = parsed.port
    else:
        cfg.port = _CLICKHOUSE_HTTP_PORT

    if parsed.path:
        # Strip leading '/'
        db = parsed.path.lstrip("/")
        if db:
            cfg.database = db

    if parsed.username:
        cfg.user = parsed.username
    if parsed.password:
        cfg.password = parsed.password

    cfg.secure = parsed.scheme == "https"

    # Override port to HTTP port if native TCP port (9000) was provided
    if cfg.port == 9000:
        cfg.port = _CLICKHOUSE_HTTP_PORT

    return cfg


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sqlite_table_exists(cursor: sqlite3.Cursor, table: str) -> bool:
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    )
    return cursor.fetchone() is not None


def _sqlite_ensure_table(cursor: sqlite3.Cursor, table: str, columns: Dict[str, str]) -> None:
    """Create a SQLite table if it does not exist, inferring column types."""
    if _sqlite_table_exists(cursor, table):
        return
    col_defs = ", ".join(f"{col} {typ}" for col, typ in columns.items())
    cursor.execute(f"CREATE TABLE IF NOT EXISTS {table} ({col_defs})")


# Maps ClickHouse types -> SQLite types for fallback table creation
_CH_TO_SQLITE_TYPE: Dict[str, str] = {
    "UUID": "TEXT",
    "String": "TEXT",
    "Nullable(String)": "TEXT",
    "LowCardinality(String)": "TEXT",
    "DateTime": "TEXT",
    "DateTime64(3)": "TEXT",
    "Date": "TEXT",
    "UInt8": "INTEGER",
    "UInt16": "INTEGER",
    "UInt32": "INTEGER",
    "UInt64": "INTEGER",
    "Int8": "INTEGER",
    "Int16": "INTEGER",
    "Int32": "INTEGER",
    "Int64": "INTEGER",
    "Float32": "REAL",
    "Float64": "REAL",
    "Float32 DEFAULT 0": "REAL DEFAULT 0",
    "Float64 DEFAULT 0": "REAL DEFAULT 0",
    "UInt8 DEFAULT 0": "INTEGER DEFAULT 0",
}


def _infer_sqlite_type(ch_type: str) -> str:
    """Best-effort conversion from a ClickHouse column type to SQLite."""
    # Strip DEFAULT expressions for matching
    stripped = ch_type.split(" DEFAULT")[0].strip()
    if stripped in _CH_TO_SQLITE_TYPE:
        base = _CH_TO_SQLITE_TYPE[stripped]
    elif "Int" in stripped or "UInt" in stripped:
        base = "INTEGER"
    elif "Float" in stripped or "Decimal" in stripped:
        base = "REAL"
    else:
        base = "TEXT"
    # Re-append DEFAULT if present
    if "DEFAULT" in ch_type and base:
        default_val = ch_type.split("DEFAULT", 1)[1].strip()
        return f"{base} DEFAULT {default_val}"
    return base


# ---------------------------------------------------------------------------
# Column schemas for fallback table creation
# ---------------------------------------------------------------------------

_FALLBACK_COLUMNS: Dict[str, Dict[str, str]] = {
    "auth_events": {
        "event_id": "TEXT",
        "timestamp": "TEXT",
        "user_id": "TEXT",
        "action": "TEXT",
        "ip_address": "TEXT",
        "user_agent": "TEXT",
        "success": "INTEGER",
        "error_code": "TEXT",
        "risk_score": "REAL",
        "device_id": "TEXT",
        "session_id": "TEXT",
        "auth_method": "TEXT",
        "region": "TEXT",
        "_detail": "TEXT",
    },
    "routing_metrics": {
        "timestamp": "TEXT",
        "source_node": "TEXT",
        "target_node": "TEXT",
        "mesh_type": "TEXT",
        "latency_ms": "REAL",
        "hops": "INTEGER",
        "packet_loss": "REAL",
        "bandwidth_kbps": "REAL",
        "rtt_ms": "REAL",
        "success": "INTEGER",
        "error_type": "TEXT",
        "protocol": "TEXT",
        "_detail": "TEXT",
    },
    "latency_data": {
        "timestamp": "TEXT",
        "source_id": "TEXT",
        "target_id": "TEXT",
        "route_hash": "TEXT",
        "latency_ms": "REAL",
        "jitter_ms": "REAL",
        "packet_loss_pct": "REAL",
        "bandwidth_estimate": "REAL",
        "connection_type": "TEXT",
        "mesh_type": "TEXT",
        "_detail": "TEXT",
    },
    "mesh_events": {
        "event_id": "TEXT",
        "timestamp": "TEXT",
        "event_type": "TEXT",
        "node_id": "TEXT",
        "peer_id": "TEXT",
        "mesh_type": "TEXT",
        "direction": "TEXT",
        "bytes_transferred": "INTEGER",
        "status": "TEXT",
        "detail": "TEXT",
        "session_id": "TEXT",
        "error_message": "TEXT",
        "_detail": "TEXT",
    },
    "websocket_events": {
        "event_id": "TEXT",
        "timestamp": "TEXT",
        "connection_id": "TEXT",
        "user_id": "TEXT",
        "event_type": "TEXT",
        "message_size": "INTEGER",
        "direction": "TEXT",
        "latency_ms": "REAL",
        "success": "INTEGER",
        "error_code": "TEXT",
        "protocol_version": "TEXT",
        "_detail": "TEXT",
    },
    "ui_telemetry": {
        "event_id": "TEXT",
        "timestamp": "TEXT",
        "session_id": "TEXT",
        "user_id": "TEXT",
        "event_type": "TEXT",
        "component": "TEXT",
        "action": "TEXT",
        "value": "REAL",
        "page": "TEXT",
        "browser": "TEXT",
        "device_type": "TEXT",
        "os": "TEXT",
        "screen_resolution": "TEXT",
        "duration_ms": "REAL",
        "success": "INTEGER",
        "_detail": "TEXT",
    },
}


# ===================================================================
# AsimNexusEngine
# ===================================================================


class AsimNexusEngine:
    """
    Primary warehouse engine for AsimNexus.

    Wraps ClickHouse with connection pooling, async inserts,
    query templating, and graceful fallback.

    Fallback chain: ClickHouse -> SQLite -> JSONL append

    Parameters
    ----------
    dsn : str, optional
        ClickHouse DSN (e.g. ``clickhouse://localhost:9000/asimnexus``).
        Falls back to ``ASIM_CLICKHOUSE_DSN`` env var, then the default DSN.
    db_path : str, optional
        Path for the SQLite fallback database.
        Falls back to ``ASIM_STORAGE_FALLBACK_DB`` env var, then
        ``data/storage/clickhouse_fallback.db``.
    """

    def __init__(
        self,
        dsn: Optional[str] = None,
        db_path: Optional[str] = None,
    ) -> None:
        # Resolve DSN
        dsn = dsn or os.environ.get(_ENV_DSN, _CLICKHOUSE_DEFAULT_DSN)
        self._ch_config: ClickHouseConfig = _parse_clickhouse_dsn(dsn)

        # Resolve fallback paths
        self._db_path: str = db_path or os.environ.get(
            _ENV_FALLBACK_DB, _DEFAULT_FALLBACK_DB
        )
        self._jsonl_path: str = _DEFAULT_FALLBACK_JSONL

        # Runtime state
        self._http_session: Optional[aiohttp.ClientSession] = None
        self._sqlite_conn: Optional[sqlite3.Connection] = None
        self._sqlite_lock: asyncio.Lock = asyncio.Lock()
        self._jsonl_lock: asyncio.Lock = asyncio.Lock()
        self._write_lock: asyncio.Lock = asyncio.Lock()

        self._connected: bool = False
        self._mode: str = "unknown"  # "clickhouse" | "sqlite" | "jsonl"

        # Track known tables for health checks
        self._known_tables: List[str] = list(_FALLBACK_COLUMNS.keys())

        logger.info(
            "AsimNexusEngine initialised (dsn=%s, fallback_db=%s)",
            dsn,
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
        Connect to ClickHouse via HTTP interface, or open a SQLite
        fallback connection if ClickHouse is unavailable.
        """
        if self._connected:
            logger.debug("Already connected")
            return

        # Attempt ClickHouse connection
        ch_ok = await self._try_clickhouse_connect()

        if ch_ok:
            self._mode = "clickhouse"
            self._connected = True
            logger.info("Connected to ClickHouse at %s:%d/%s",
                        self._ch_config.host, self._ch_config.port,
                        self._ch_config.database)
            return

        # Fallback 1: SQLite
        logger.warning("ClickHouse unavailable, falling back to SQLite: %s",
                       self._db_path)
        sqlite_ok = await self._try_sqlite_connect()

        if sqlite_ok:
            self._mode = "sqlite"
            self._connected = True
            logger.info("Connected to SQLite fallback at %s", self._db_path)
            return

        # Fallback 2: JSONL (always succeeds)
        logger.warning("SQLite unavailable, falling back to JSONL: %s",
                       self._jsonl_path)
        self._mode = "jsonl"
        self._connected = True
        logger.info("Using JSONL fallback at %s", self._jsonl_path)

    async def close(self) -> None:
        """Close all connections and release resources."""
        if self._http_session and not self._http_session.closed:
            await self._http_session.close()
            self._http_session = None

        if self._sqlite_conn:
            async with self._sqlite_lock:
                self._sqlite_conn.close()
                self._sqlite_conn = None

        self._connected = False
        self._mode = "unknown"
        logger.info("AsimNexusEngine closed")

    async def __aenter__(self) -> "AsimNexusEngine":
        await self.connect()
        return self

    async def __aexit__(self, *args: Any, **kwargs: Any) -> None:
        await self.close()

    # ------------------------------------------------------------------
    # Internal connection helpers
    # ------------------------------------------------------------------

    async def _try_clickhouse_connect(self) -> bool:
        """Try to establish a connection to ClickHouse via HTTP.

        Returns ``True`` if the ping succeeded.
        """
        try:
            cfg = self._ch_config
            scheme = "https" if cfg.secure else "http"
            base_url = f"{scheme}://{cfg.host}:{cfg.port}"

            self._http_session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10),
                headers={"Content-Type": "text/plain"},
            )

            # Ping with a simple query
            ping_sql = "SELECT 1"
            params = {
                "database": cfg.database,
                "user": cfg.user,
            }
            if cfg.password:
                params["password"] = cfg.password

            async with self._http_session.post(
                base_url + "/",
                params=params,
                data=ping_sql,
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    logger.debug("ClickHouse ping failed: HTTP %d - %s",
                                 resp.status, text[:200])
                    await self._http_session.close()
                    self._http_session = None
                    return False

                result_text = await resp.text()
                if "1" in result_text.strip():
                    logger.debug("ClickHouse ping succeeded")
                    return True

            await self._http_session.close()
            self._http_session = None
            return False

        except (aiohttp.ClientError, asyncio.TimeoutError, OSError) as exc:
            logger.debug("ClickHouse connection failed: %s", exc)
            if self._http_session and not self._http_session.closed:
                await self._http_session.close()
                self._http_session = None
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
                return conn

            self._sqlite_conn = await loop.run_in_executor(None, _open_db)

            # Create fallback tables
            async with self._sqlite_lock:
                cursor = self._sqlite_conn.cursor()
                for table, columns in _FALLBACK_COLUMNS.items():
                    _sqlite_ensure_table(cursor, table, columns)
                self._sqlite_conn.commit()

            return True

        except Exception as exc:
            logger.debug("SQLite connection failed: %s", exc)
            return False

    def _ch_base_url(self) -> str:
        """Build the ClickHouse HTTP base URL."""
        cfg = self._ch_config
        scheme = "https" if cfg.secure else "http"
        return f"{scheme}://{cfg.host}:{cfg.port}"

    def _ch_params(self) -> Dict[str, str]:
        """Build query parameters for ClickHouse HTTP requests."""
        cfg = self._ch_config
        params: Dict[str, str] = {
            "database": cfg.database,
            "user": cfg.user,
        }
        if cfg.password:
            params["password"] = cfg.password
        return params

    # ------------------------------------------------------------------
    # Insert operations
    # ------------------------------------------------------------------

    async def insert(self, table: str, data: Dict[str, Any]) -> bool:
        """Insert a single row into *table*.

        Falls back gracefully through the chain:
        ClickHouse -> SQLite -> JSONL.

        Parameters
        ----------
        table : str
            Target table name.
        data : Dict[str, Any]
            Column-value mapping for the row.

        Returns
        -------
        bool
            ``True`` if the insert succeeded.
        """
        async with self._write_lock:
            try:
                if self._mode == "clickhouse" and self._http_session:
                    return await self._ch_insert(table, data)
                elif self._mode == "clickhouse":
                    # ClickHouse mode but no session → degrade
                    self._mode = "sqlite"
                    await self._try_sqlite_connect()
                    return await self._sqlite_insert(table, data)
                elif self._mode == "sqlite" and self._sqlite_conn:
                    return await self._sqlite_insert(table, data)
                else:
                    return await self._jsonl_insert(table, data)
            except Exception as exc:
                logger.error("Insert into %s failed (%s): %s",
                             table, self._mode, exc)
                # Attempt degradation
                return await self._degrade_and_retry_insert(table, data)

    async def insert_batch(self, table: str, data: List[Dict[str, Any]]) -> int:
        """Insert multiple rows into *table* in a single batch.

        Parameters
        ----------
        table : str
            Target table name.
        data : List[Dict[str, Any]]
            List of row dicts.

        Returns
        -------
        int
            Number of rows successfully inserted.
        """
        if not data:
            return 0

        inserted = 0
        async with self._write_lock:
            try:
                if self._mode == "clickhouse" and self._http_session:
                    inserted = await self._ch_insert_batch(table, data)
                elif self._mode == "sqlite" and self._sqlite_conn:
                    inserted = await self._sqlite_insert_batch(table, data)
                else:
                    # Fall back to individual JSONL inserts
                    for row in data:
                        ok = await self._jsonl_insert(table, row)
                        if ok:
                            inserted += 1
            except Exception as exc:
                logger.error("Batch insert into %s failed (%s): %s",
                             table, self._mode, exc)
                # Degrade and retry one by one
                for row in data:
                    try:
                        ok = await self._degrade_and_retry_insert(table, row)
                        if ok:
                            inserted += 1
                    except Exception:
                        pass

        return inserted

    async def _ch_insert(self, table: str, data: Dict[str, Any]) -> bool:
        """Execute a single-row INSERT via ClickHouse HTTP."""
        cols = list(data.keys())
        vals = list(data.values())
        placeholders = ", ".join(cols)
        sql = f"INSERT INTO {table} ({placeholders}) VALUES"

        async with self._http_session.post(
            self._ch_base_url() + "/",
            params=self._ch_params(),
            data=self._build_ch_values(sql, [vals]),
        ) as resp:
            if resp.status != 200:
                text = await resp.text()
                logger.error("ClickHouse INSERT failed: HTTP %d - %s",
                             resp.status, text[:200])
                return False
            return True

    async def _ch_insert_batch(self, table: str, data: List[Dict[str, Any]]) -> int:
        """Execute a batch INSERT via ClickHouse HTTP."""
        if not data:
            return 0

        cols = list(data[0].keys())
        placeholders = ", ".join(cols)
        sql = f"INSERT INTO {table} ({placeholders}) VALUES"
        values = [list(row.values()) for row in data]

        async with self._http_session.post(
            self._ch_base_url() + "/",
            params=self._ch_params(),
            data=self._build_ch_values(sql, values),
        ) as resp:
            if resp.status != 200:
                text = await resp.text()
                logger.error("ClickHouse batch INSERT failed: HTTP %d - %s",
                             resp.status, text[:200])
                return 0
            return len(data)

    @staticmethod
    def _build_ch_values(sql: str, rows: List[List[Any]]) -> str:
        """Build the VALUES clause for ClickHouse SQL.

        Handles proper quoting of string values.
        """
        parts: List[str] = []
        for row in rows:
            val_strs: List[str] = []
            for v in row:
                if v is None:
                    val_strs.append("NULL")
                elif isinstance(v, (int, float)):
                    val_strs.append(str(v))
                elif isinstance(v, bool):
                    val_strs.append("1" if v else "0")
                elif isinstance(v, uuid.UUID):
                    val_strs.append(f"'{v}'")
                else:
                    # Escape single quotes
                    escaped = str(v).replace("'", "\\'")
                    val_strs.append(f"'{escaped}'")
            parts.append(f"({', '.join(val_strs)})")

        return sql + "\n" + ",\n".join(parts)

    # ------------------------------------------------------------------
    # SQLite operations
    # ------------------------------------------------------------------

    async def _sqlite_insert(self, table: str, data: Dict[str, Any]) -> bool:
        """Insert a single row into SQLite."""
        if not self._sqlite_conn:
            return False

        async with self._sqlite_lock:
            try:
                cols = list(data.keys())
                placeholders = ", ".join(["?" for _ in cols])
                col_names = ", ".join(cols)
                vals = [
                    json.dumps(data.get("_detail"))
                    if k == "_detail" and isinstance(data.get("_detail"), dict)
                    else str(v) if isinstance(v, uuid.UUID)
                    else v
                    for k, v in zip(cols, [data.get(c) for c in cols])
                ]
                # Actually, let's rebuild properly
                row_vals = []
                for c in cols:
                    v = data[c]
                    if isinstance(v, uuid.UUID):
                        row_vals.append(str(v))
                    elif isinstance(v, dict):
                        row_vals.append(json.dumps(v))
                    else:
                        row_vals.append(v)

                loop = asyncio.get_running_loop()

                def _do_insert() -> None:
                    cur = self._sqlite_conn.cursor()
                    cur.execute(
                        f"INSERT OR REPLACE INTO {table} ({col_names}) VALUES ({placeholders})",
                        row_vals,
                    )
                    self._sqlite_conn.commit()

                await loop.run_in_executor(None, _do_insert)
                return True

            except Exception as exc:
                logger.error("SQLite insert failed: %s", exc)
                return False

    async def _sqlite_insert_batch(
        self, table: str, data: List[Dict[str, Any]]
    ) -> int:
        """Batch insert into SQLite."""
        if not data or not self._sqlite_conn:
            return 0

        async with self._sqlite_lock:
            try:
                cols = list(data[0].keys())
                col_names = ", ".join(cols)
                placeholders = ", ".join(["?" for _ in cols])

                rows: List[List[Any]] = []
                for row in data:
                    row_vals = []
                    for c in cols:
                        v = row.get(c)
                        if isinstance(v, uuid.UUID):
                            row_vals.append(str(v))
                        elif isinstance(v, dict):
                            row_vals.append(json.dumps(v))
                        else:
                            row_vals.append(v)
                    rows.append(row_vals)

                loop = asyncio.get_running_loop()

                def _do_batch() -> int:
                    cur = self._sqlite_conn.cursor()
                    cur.executemany(
                        f"INSERT OR REPLACE INTO {table} ({col_names}) VALUES ({placeholders})",
                        rows,
                    )
                    self._sqlite_conn.commit()
                    return len(rows)

                return await loop.run_in_executor(None, _do_batch)

            except Exception as exc:
                logger.error("SQLite batch insert failed: %s", exc)
                return 0

    # ------------------------------------------------------------------
    # JSONL operations
    # ------------------------------------------------------------------

    async def _jsonl_insert(self, table: str, data: Dict[str, Any]) -> bool:
        """Append a single row as a JSONL line."""
        async with self._jsonl_lock:
            try:
                jsonl_dir = os.path.dirname(self._jsonl_path)
                if jsonl_dir:
                    os.makedirs(jsonl_dir, exist_ok=True)

                # Per-table JSONL files
                table_path = self._jsonl_path.replace(
                    ".jsonl", f"_{table}.jsonl"
                )

                # Serialise data, converting UUIDs etc.
                serialised: Dict[str, Any] = {}
                for k, v in data.items():
                    if isinstance(v, uuid.UUID):
                        serialised[k] = str(v)
                    elif isinstance(v, (set, frozenset)):
                        serialised[k] = list(v)
                    else:
                        serialised[k] = v

                line = json.dumps(serialised, default=str)
                async with aiofiles.open(table_path, mode="a", encoding="utf-8") as f:
                    await f.write(line + "\n")

                return True

            except Exception as exc:
                logger.error("JSONL insert failed: %s", exc)
                return False

    # ------------------------------------------------------------------
    # Degradation
    # ------------------------------------------------------------------

    async def _degrade_and_retry_insert(
        self, table: str, data: Dict[str, Any]
    ) -> bool:
        """Attempt to degrade the storage mode and retry an insert."""
        if self._mode == "clickhouse":
            # Try SQLite
            logger.warning("Degrading from ClickHouse to SQLite")
            self._mode = "sqlite"
            if await self._try_sqlite_connect():
                return await self._sqlite_insert(table, data)

            # Try JSONL
            logger.warning("Degrading from SQLite to JSONL")
            self._mode = "jsonl"
            return await self._jsonl_insert(table, data)

        elif self._mode == "sqlite":
            # Try JSONL
            logger.warning("Degrading from SQLite to JSONL")
            self._mode = "jsonl"
            return await self._jsonl_insert(table, data)

        # Already on JSONL — nothing left to degrade to
        logger.error("All storage layers exhausted for table %s", table)
        return False

    # ------------------------------------------------------------------
    # Query operations
    # ------------------------------------------------------------------

    async def query(
        self, sql: str, params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute a query against the active storage layer.

        For ClickHouse, native SQL is used.
        For SQLite fallback, basic SQL translation is attempted.
        For JSONL, queries are not supported (returns empty list).

        Parameters
        ----------
        sql : str
            SQL query string.
        params : Dict[str, Any], optional
            Query parameters (for ClickHouse).

        Returns
        -------
        List[Dict[str, Any]]
            Query results as a list of row dicts.
        """
        if not self._connected:
            await self.connect()

        try:
            if self._mode == "clickhouse" and self._http_session:
                return await self._ch_query(sql, params)
            elif self._mode == "sqlite" and self._sqlite_conn:
                return await self._sqlite_query(sql)
            else:
                logger.warning("Query not supported in JSONL mode")
                return []
        except Exception as exc:
            logger.error("Query failed (%s): %s", self._mode, exc)
            # If ClickHouse query fails, try SQLite
            if self._mode == "clickhouse":
                try:
                    return await self._sqlite_query(sql)
                except Exception:
                    pass
            return []

    async def _ch_query(
        self, sql: str, params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute a query via ClickHouse HTTP interface, returning JSON."""
        cfg = self._ch_config
        scheme = "https" if cfg.secure else "http"
        url = f"{scheme}://{cfg.host}:{cfg.port}/"
        query_params = self._ch_params()
        query_params["default_format"] = "JSONCompact"

        if params:
            # Build query with parameter substitution for ClickHouse
            for key, val in params.items():
                if isinstance(val, str):
                    sql = sql.replace(f"{{{key}}}", f"'{val.replace(chr(39), chr(39)*2)}'")
                elif isinstance(val, (int, float)):
                    sql = sql.replace(f"{{{key}}}", str(val))
                else:
                    sql = sql.replace(f"{{{key}}}", str(val))

        async with self._http_session.post(
            url,
            params=query_params,
            data=sql,
        ) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise RuntimeError(f"ClickHouse query failed (HTTP {resp.status}): {text[:500]}")

            content_type = resp.headers.get("Content-Type", "")
            text = await resp.text()

            if "application/json" in content_type or text.strip().startswith("{"):
                result = json.loads(text)
                rows = result.get("data", [])
                meta = result.get("meta", [])
                col_names = [m["name"] for m in meta]
                return [dict(zip(col_names, row)) for row in rows]
            else:
                # Tab-separated fallback
                lines = text.strip().split("\n")
                if not lines:
                    return []
                col_names = lines[0].split("\t")
                result_rows = []
                for line in lines[1:]:
                    if line.strip():
                        vals = line.split("\t")
                        result_rows.append(dict(zip(col_names, vals)))
                return result_rows

    async def _sqlite_query(self, sql: str) -> List[Dict[str, Any]]:
        """Execute a query against the SQLite fallback."""
        if not self._sqlite_conn:
            return []

        # Basic SQL translation: ClickHouse-specific syntax -> SQLite
        sql = self._translate_sql_for_sqlite(sql)

        async with self._sqlite_lock:
            try:
                loop = asyncio.get_running_loop()

                def _do_query() -> List[Dict[str, Any]]:
                    cur = self._sqlite_conn.cursor()
                    cur.execute(sql)
                    rows = cur.fetchall()
                    return [dict(row) for row in rows]

                return await loop.run_in_executor(None, _do_query)

            except Exception as exc:
                logger.error("SQLite query failed: %s", exc)
                return []

    @staticmethod
    def _translate_sql_for_sqlite(sql: str) -> str:
        """Translate basic ClickHouse SQL dialect to SQLite-compatible SQL.

        This handles common patterns; complex queries may need manual
        adjustment.
        """
        translated = sql

        # Remove MATERIALIZED VIEW DDL (SQLite doesn't support it)
        if "MATERIALIZED VIEW" in translated.upper():
            translated = "-- SQLite does not support materialized views"

        # Replace toStartOfMonth, toStartOfDay, toStartOfHour with strftime
        import re

        # toStartOfHour(timestamp) -> strftime('%Y-%m-%d %H:00:00', timestamp)
        translated = re.sub(
            r"toStartOfHour\((\w+)\)",
            r"strftime('%Y-%m-%d %H:00:00', \1)",
            translated,
        )
        translated = re.sub(
            r"toStartOfDay\((\w+)\)",
            r"strftime('%Y-%m-%d 00:00:00', \1)",
            translated,
        )
        translated = re.sub(
            r"toStartOfMonth\((\w+)\)",
            r"strftime('%Y-%m-01 00:00:00', \1)",
            translated,
        )

        # Replace toYYYYMM(timestamp) -> strftime('%Y%m', timestamp)
        translated = re.sub(
            r"toYYYYMM\((\w+)\)",
            r"strftime('%Y%m', \1)",
            translated,
        )

        # Replace LowCardinality(String) -> TEXT (in CAST etc.)
        translated = translated.replace("LowCardinality(String)", "TEXT")

        # Replace generateUUIDv4() -> lower(hex(randomblob(16)))
        translated = translated.replace(
            "generateUUIDv4()",
            "lower(hex(randomblob(16)))",
        )

        # Replace now64() or now() with datetime('now')
        translated = re.sub(r"\bnow64\(\)", "datetime('now')", translated)
        translated = re.sub(r"\bnow\(\)", "datetime('now')", translated)

        # Replace quantile(0.95)(col) pattern
        translated = re.sub(
            r"quantile\([\d.]+\)\((\w+)\)",
            r"\1 /* quantile not supported in SQLite */",
            translated,
        )

        # Replace INTERVAL X MONTH/YEAR with SQLite-compatible extensions
        # (this is simplified; actual TTL is handled in app logic)
        translated = re.sub(
            r"INTERVAL\s+(\d+)\s+(MONTH|YEAR|DAY|HOUR)",
            "",  # Remove TTL clauses
            translated,
        )

        return translated

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    async def health(self) -> Dict[str, Any]:
        """Return a health snapshot of the storage engine.

        Returns
        -------
        Dict[str, Any]
            Keys: ``connected``, ``mode``, ``tables``, ``latency_ms``.
        """
        start = time.monotonic()
        result: Dict[str, Any] = {
            "connected": self._connected,
            "mode": self._mode,
            "tables": 0,
            "latency_ms": 0.0,
        }

        try:
            if self._mode == "clickhouse" and self._http_session:
                # Ping ClickHouse
                ping_result = await self._ch_query("SELECT 1")
                result["tables"] = len(self._known_tables) if ping_result else 0
            elif self._mode == "sqlite" and self._sqlite_conn:
                # Count tables in SQLite
                async with self._sqlite_lock:
                    loop = asyncio.get_running_loop()

                    def _count_tables() -> int:
                        cur = self._sqlite_conn.cursor()
                        cur.execute(
                            "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
                        )
                        row = cur.fetchone()
                        return row[0] if row else 0

                    result["tables"] = await loop.run_in_executor(
                        None, _count_tables
                    )
            else:
                # JSONL mode — we can't "count tables"
                result["tables"] = 0

        except Exception as exc:
            logger.error("Health check failed: %s", exc)
            result["connected"] = False

        result["latency_ms"] = (time.monotonic() - start) * 1000
        return result
