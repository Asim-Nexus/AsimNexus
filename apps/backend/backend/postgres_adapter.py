#!/usr/bin/env python3
"""
STATUS: NEW — PostgreSQL Adapter with Row-Level Security
ASIMNEXUS PostgreSQL Adapter
============================
PostgreSQL adapter with row-level security (RLS) for multi-user isolation.
Supports both sync (psycopg2) and async (asyncpg) connections.

Features:
- Row-Level Security policies per table
- Tenant/user isolation via session-level config
- Automatic RLS policy management
- SQLite → PostgreSQL migration
- Connection pooling with SSL support
- Schema version tracking
"""

import os
import json
import time
import logging
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger("AsimNexus.PostgresAdapter")

# ─── Environment Configuration ────────────────────────────────────────────────

_DEFAULT_DB_HOST = os.getenv("ASIM_PG_HOST", "localhost")
_DEFAULT_DB_PORT = int(os.getenv("ASIM_PG_PORT", "5432"))
_DEFAULT_DB_NAME = os.getenv("ASIM_PG_DB", "asimnexus")
_DEFAULT_DB_USER = os.getenv("ASIM_PG_USER", "asimnexus")
_DEFAULT_DB_PASSWORD = os.getenv("ASIM_PG_PASSWORD", "")
_DEFAULT_DB_SSL = os.getenv("ASIM_PG_SSL", "prefer")
_DEFAULT_POOL_SIZE = int(os.getenv("ASIM_PG_POOL_SIZE", "10"))
_DEFAULT_MAX_OVERFLOW = int(os.getenv("ASIM_PG_MAX_OVERFLOW", "20"))


# ─── Enums ────────────────────────────────────────────────────────────────────

class TenantIsolationLevel(Enum):
    """Level of tenant isolation in RLS policies."""
    NONE = "none"              # No RLS — shared data
    USER = "user"              # Per-user isolation (user_id column)
    ROLE = "role"              # Per-role isolation (role column)
    USER_AND_ROLE = "user_and_role"  # Both user and role


class MigrationStatus(Enum):
    """Status of a database migration."""
    PENDING = "pending"
    APPLIED = "applied"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


# ─── Data Classes ─────────────────────────────────────────────────────────────

@dataclass
class RLSConfig:
    """Configuration for a table's row-level security."""
    table_name: str
    isolation_level: TenantIsolationLevel = TenantIsolationLevel.USER
    user_id_column: str = "user_id"
    role_column: str = "role"
    additional_policies: List[str] = field(default_factory=list)
    force_rls: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "table_name": self.table_name,
            "isolation_level": self.isolation_level.value,
            "user_id_column": self.user_id_column,
            "role_column": self.role_column,
            "force_rls": self.force_rls,
        }


@dataclass
class Migration:
    """A database migration step."""
    version: int
    description: str
    sql_up: str
    sql_down: Optional[str] = None
    status: MigrationStatus = MigrationStatus.PENDING
    applied_at: Optional[str] = None


@dataclass
class PostgresConfig:
    """PostgreSQL connection configuration."""
    host: str = _DEFAULT_DB_HOST
    port: int = _DEFAULT_DB_PORT
    database: str = _DEFAULT_DB_NAME
    user: str = _DEFAULT_DB_USER
    password: str = _DEFAULT_DB_PASSWORD
    ssl_mode: str = _DEFAULT_DB_SSL
    pool_size: int = _DEFAULT_POOL_SIZE
    max_overflow: int = _DEFAULT_MAX_OVERFLOW
    application_name: str = "asimnexus"

    @property
    def sync_url(self) -> str:
        """Get SQLAlchemy sync connection URL."""
        return (
            f"postgresql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )

    @property
    def async_url(self) -> str:
        """Get SQLAlchemy async connection URL."""
        return (
            f"postgresql+asyncpg://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )


# ─── RLS Policy Builder ───────────────────────────────────────────────────────

class RLSPolicyBuilder:
    """
    Builds PostgreSQL Row-Level Security policies for tenant isolation.

    RLS ensures that users can only see/modify rows belonging to their tenant.
    Uses PostgreSQL's `ALTER TABLE ... ENABLE ROW LEVEL SECURITY` and
    `CREATE POLICY` statements.
    """

    @staticmethod
    def enable_rls(table_name: str) -> str:
        """Enable RLS on a table."""
        return f'ALTER TABLE "{table_name}" ENABLE ROW LEVEL SECURITY;'

    @staticmethod
    def force_rls(table_name: str) -> str:
        """Force RLS (deny table-level access to table owner)."""
        return f'ALTER TABLE "{table_name}" FORCE ROW LEVEL SECURITY;'

    @staticmethod
    def user_isolation_policy(
        table_name: str,
        user_id_column: str = "user_id",
        policy_name: str = "user_isolation",
    ) -> str:
        """
        Create a policy that restricts access to rows matching the current user.

        Uses `current_setting('app.current_user_id')` which is set per-session
        by the application layer.
        """
        return f"""
        CREATE POLICY "{policy_name}" ON "{table_name}"
        FOR ALL
        USING ("{user_id_column}" = current_setting('app.current_user_id')::TEXT)
        WITH CHECK ("{user_id_column}" = current_setting('app.current_user_id')::TEXT);
        """

    @staticmethod
    def role_isolation_policy(
        table_name: str,
        role_column: str = "role",
        policy_name: str = "role_isolation",
    ) -> str:
        """
        Create a policy that filters by user role.

        Uses `current_setting('app.current_user_role')`.
        """
        return f"""
        CREATE POLICY "{policy_name}" ON "{table_name}"
        FOR ALL
        USING ("{role_column}" = current_setting('app.current_user_role')::TEXT);
        """

    @staticmethod
    def admin_override_policy(
        table_name: str,
        policy_name: str = "admin_override",
    ) -> str:
        """
        Allow admin users (role='admin') to bypass RLS on a table.

        Relies on `current_setting('app.is_admin')::boolean`.
        """
        return f"""
        CREATE POLICY "{policy_name}" ON "{table_name}"
        FOR ALL
        USING (current_setting('app.is_admin')::BOOLEAN IS TRUE);
        """

    @staticmethod
    def set_session_user(user_id: str, role: str = "user", is_admin: bool = False) -> str:
        """SQL to set session-level user context for RLS."""
        sql = f"""
        SELECT set_config('app.current_user_id', '{user_id}', true);
        SELECT set_config('app.current_user_role', '{role}', true);
        SELECT set_config('app.is_admin', '{str(is_admin).lower()}', true);
        """
        return sql

    @staticmethod
    def reset_session() -> str:
        """Reset session-level user context."""
        return """
        SELECT set_config('app.current_user_id', '', true);
        SELECT set_config('app.current_user_role', '', true);
        SELECT set_config('app.is_admin', 'false', true);
        """


# ─── PostgreSQL Adapter ───────────────────────────────────────────────────────

class PostgresAdapter:
    """
    PostgreSQL adapter with RLS support.

    Provides:
    - Async connection pool management (asyncpg)
    - Sync connections (psycopg2) for migrations
    - RLS policy creation and management
    - Session-level user context for RLS
    - Migration runner
    """

    def __init__(self, config: Optional[PostgresConfig] = None):
        self.config = config or PostgresConfig()
        self._async_pool: Optional[Any] = None
        self._sync_conn: Optional[Any] = None
        self._rls_tables: Dict[str, RLSConfig] = {}
        self._migrations: List[Migration] = []
        self._initialized = False

        logger.info(
            f"🐘 PostgresAdapter initialized — {self.config.host}:{self.config.port}/{self.config.database}"
        )

    # ─── Connection Management ────────────────────────────────────────────────

    async def initialize(self) -> bool:
        """
        Initialize the async connection pool and run pending migrations.
        Returns True if initialization succeeded.
        """
        if self._initialized:
            return True

        try:
            import asyncpg
            self._async_pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.user,
                password=self.config.password,
                min_size=2,
                max_size=self.config.pool_size,
                ssl=self.config.ssl_mode,
                server_settings={
                    "application_name": self.config.application_name,
                },
            )
            logger.info(f"🐘 Async pool created ({self.config.pool_size} connections)")
            self._initialized = True
            return True

        except ImportError:
            logger.warning("asyncpg not installed — async operations unavailable")
            return False
        except Exception as e:
            logger.error(f"🐘 Failed to initialize PostgreSQL pool: {e}")
            return False

    async def close(self) -> None:
        """Close all connections."""
        if self._async_pool:
            await self._async_pool.close()
            self._async_pool = None
        self._initialized = False
        logger.info("🐘 PostgreSQL connections closed")

    def get_sync_connection(self):
        """
        Get a synchronous psycopg2 connection (for migrations).
        Falls back to None if psycopg2 is unavailable.
        """
        try:
            import psycopg2
            if self._sync_conn is None or self._sync_conn.closed:
                self._sync_conn = psycopg2.connect(
                    host=self.config.host,
                    port=self.config.port,
                    dbname=self.config.database,
                    user=self.config.user,
                    password=self.config.password,
                    sslmode=self.config.ssl_mode,
                    application_name=self.config.application_name,
                )
                self._sync_conn.autocommit = True
            return self._sync_conn
        except ImportError:
            logger.warning("psycopg2 not installed — sync operations unavailable")
            return None
        except Exception as e:
            logger.error(f"🐘 Sync connection failed: {e}")
            return None

    # ─── RLS Management ───────────────────────────────────────────────────────

    def register_rls_table(self, config: RLSConfig) -> None:
        """Register a table for RLS enforcement."""
        self._rls_tables[config.table_name] = config
        logger.debug(f"🔒 RLS registered for table: {config.table_name}")

    def register_default_rls_tables(self) -> None:
        """Register common tables with default RLS configs."""
        defaults = [
            RLSConfig("users", TenantIsolationLevel.NONE),
            RLSConfig("profiles", TenantIsolationLevel.USER),
            RLSConfig("memories", TenantIsolationLevel.USER),
            RLSConfig("personal_os_data", TenantIsolationLevel.USER),
            RLSConfig("life_journey", TenantIsolationLevel.USER),
            RLSConfig("agent_contracts", TenantIsolationLevel.USER),
            RLSConfig("notifications", TenantIsolationLevel.USER),
            RLSConfig("hdt_records", TenantIsolationLevel.USER),
            RLSConfig("nexus_credits", TenantIsolationLevel.USER,
                      user_id_column="owner_id"),
            RLSConfig("audit_log", TenantIsolationLevel.ROLE,
                      role_column="actor_role"),
            RLSConfig("governance_records", TenantIsolationLevel.NONE),
            RLSConfig("system_config", TenantIsolationLevel.NONE),
        ]
        for cfg in defaults:
            self.register_rls_table(cfg)

    def apply_rls_policies(self) -> List[str]:
        """
        Generate and execute SQL to apply RLS policies for all registered tables.
        Returns list of SQL statements executed.
        """
        conn = self.get_sync_connection()
        if not conn:
            logger.warning("Cannot apply RLS policies — no sync connection")
            return []

        statements = []
        try:
            cur = conn.cursor()

            for config in self._rls_tables.values():
                table = config.table_name

                # Enable RLS
                stmt = RLSPolicyBuilder.enable_rls(table)
                cur.execute(stmt)
                statements.append(stmt)

                # Force RLS if configured
                if config.force_rls:
                    stmt = RLSPolicyBuilder.force_rls(table)
                    cur.execute(stmt)
                    statements.append(stmt)

                # User isolation policy
                if config.isolation_level in (TenantIsolationLevel.USER,
                                              TenantIsolationLevel.USER_AND_ROLE):
                    stmt = RLSPolicyBuilder.user_isolation_policy(
                        table, config.user_id_column
                    )
                    cur.execute(stmt)
                    statements.append(stmt)

                # Role isolation policy
                if config.isolation_level in (TenantIsolationLevel.ROLE,
                                              TenantIsolationLevel.USER_AND_ROLE):
                    stmt = RLSPolicyBuilder.role_isolation_policy(
                        table, config.role_column
                    )
                    cur.execute(stmt)
                    statements.append(stmt)

                # Admin override
                stmt = RLSPolicyBuilder.admin_override_policy(table)
                cur.execute(stmt)
                statements.append(stmt)

                # Custom policies
                for custom_policy in config.additional_policies:
                    cur.execute(custom_policy)
                    statements.append(custom_policy)

                logger.info(f"🔒 RLS policies applied to table: {table}")

            cur.close()
            logger.info(f"✅ Applied {len(statements)} RLS policy statements")
            return statements

        except Exception as e:
            logger.error(f"🐘 Failed to apply RLS policies: {e}")
            return statements

    def remove_rls_policies(self, table_name: Optional[str] = None) -> List[str]:
        """
        Remove RLS policies from tables.
        If table_name is None, removes from all registered tables.
        """
        conn = self.get_sync_connection()
        if not conn:
            return []

        statements = []
        try:
            cur = conn.cursor()
            tables = [table_name] if table_name else list(self._rls_tables.keys())

            for table in tables:
                # Drop all policies on the table
                stmt = f'DROP POLICY IF EXISTS "user_isolation" ON "{table}";'
                cur.execute(stmt)
                statements.append(stmt)

                stmt = f'DROP POLICY IF EXISTS "role_isolation" ON "{table}";'
                cur.execute(stmt)
                statements.append(stmt)

                stmt = f'DROP POLICY IF EXISTS "admin_override" ON "{table}";'
                cur.execute(stmt)
                statements.append(stmt)

                stmt = f'ALTER TABLE "{table}" DISABLE ROW LEVEL SECURITY;'
                cur.execute(stmt)
                statements.append(stmt)

            cur.close()
            logger.info(f"🔓 RLS policies removed from {len(tables)} tables")
            return statements

        except Exception as e:
            logger.error(f"🐘 Failed to remove RLS policies: {e}")
            return statements

    # ─── Session Context ─────────────────────────────────────────────────────

    async def set_session_context(
        self, user_id: str, role: str = "user", is_admin: bool = False
    ) -> bool:
        """
        Set session-level user context for RLS.
        Must be called after acquiring a connection from the pool.
        """
        if not self._async_pool:
            return False

        try:
            async with self._async_pool.acquire() as conn:
                await conn.execute(
                    "SELECT set_config('app.current_user_id', $1, true)",
                    user_id,
                )
                await conn.execute(
                    "SELECT set_config('app.current_user_role', $1, true)",
                    role,
                )
                await conn.execute(
                    "SELECT set_config('app.is_admin', $1, true)",
                    "true" if is_admin else "false",
                )
            return True
        except Exception as e:
            logger.error(f"Failed to set session context: {e}")
            return False

    async def query(
        self, sql: str, *args, user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a query with optional user context for RLS.

        Args:
            sql: SQL query with $1, $2, etc. placeholders.
            args: Query parameters.
            user_id: If set, executes in the user's RLS context.

        Returns:
            List of rows as dictionaries.
        """
        if not self._async_pool:
            logger.warning("PostgreSQL pool not initialized")
            return []

        try:
            async with self._async_pool.acquire() as conn:
                # Set user context for RLS if provided
                if user_id:
                    await conn.execute(
                        "SELECT set_config('app.current_user_id', $1, true)",
                        user_id,
                    )

                rows = await conn.fetch(sql, *args)
                return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Query failed: {e}")
            return []

    async def execute(
        self, sql: str, *args, user_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Execute a write query with optional user context for RLS.

        Returns status string or None on failure.
        """
        if not self._async_pool:
            return None

        try:
            async with self._async_pool.acquire() as conn:
                if user_id:
                    await conn.execute(
                        "SELECT set_config('app.current_user_id', $1, true)",
                        user_id,
                    )
                await conn.execute(sql, *args)
                return "ok"
        except Exception as e:
            logger.error(f"Execute failed: {e}")
            return None

    # ─── Migrations ──────────────────────────────────────────────────────────

    def register_migration(self, migration: Migration) -> None:
        """Register a migration step."""
        self._migrations.append(migration)
        self._migrations.sort(key=lambda m: m.version)

    def register_default_migrations(self) -> None:
        """Register the default schema migrations."""
        self._migrations = [
            Migration(
                version=1,
                description="Create schema tracking table",
                sql_up="""
                CREATE TABLE IF NOT EXISTS _schema_version (
                    version INTEGER PRIMARY KEY,
                    description TEXT NOT NULL,
                    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    checksum TEXT NOT NULL
                );
                """,
                sql_down="DROP TABLE IF EXISTS _schema_version;",
            ),
            Migration(
                version=2,
                description="Create user and profile tables",
                sql_up="""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT,
                    role TEXT NOT NULL DEFAULT 'user',
                    is_admin BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                CREATE TABLE IF NOT EXISTS profiles (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL REFERENCES users(user_id),
                    display_name TEXT,
                    avatar_url TEXT,
                    preferences JSONB DEFAULT '{}',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_profiles_user ON profiles(user_id);
                """,
                sql_down="""
                DROP TABLE IF EXISTS profiles;
                DROP TABLE IF EXISTS users;
                """,
            ),
            Migration(
                version=3,
                description="Create memories and personal OS tables",
                sql_up="""
                CREATE TABLE IF NOT EXISTS memories (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL REFERENCES users(user_id),
                    memory_type TEXT NOT NULL DEFAULT 'chat',
                    content TEXT NOT NULL,
                    embedding FLOAT[],
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_memories_user ON memories(user_id);
                CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(memory_type);

                CREATE TABLE IF NOT EXISTS personal_os_data (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL REFERENCES users(user_id),
                    data_key TEXT NOT NULL,
                    data_value JSONB NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    UNIQUE(user_id, data_key)
                );
                """,
                sql_down="""
                DROP TABLE IF EXISTS personal_os_data;
                DROP TABLE IF EXISTS memories;
                """,
            ),
            Migration(
                version=4,
                description="Create agent contracts and notifications",
                sql_up="""
                CREATE TABLE IF NOT EXISTS agent_contracts (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL REFERENCES users(user_id),
                    contract_type TEXT NOT NULL,
                    tier TEXT NOT NULL DEFAULT 'trial',
                    status TEXT NOT NULL DEFAULT 'active',
                    duration_days INTEGER NOT NULL DEFAULT 5,
                    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    expires_at TIMESTAMP WITH TIME ZONE,
                    terms JSONB DEFAULT '{}',
                    UNIQUE(user_id, contract_type)
                );
                CREATE TABLE IF NOT EXISTS notifications (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL REFERENCES users(user_id),
                    title TEXT NOT NULL,
                    body TEXT,
                    urgency TEXT DEFAULT 'normal',
                    read BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id);
                """,
                sql_down="""
                DROP TABLE IF EXISTS notifications;
                DROP TABLE IF EXISTS agent_contracts;
                """,
            ),
            Migration(
                version=5,
                description="Create governance and audit tables",
                sql_up="""
                CREATE TABLE IF NOT EXISTS governance_records (
                    id SERIAL PRIMARY KEY,
                    action_type TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    sector TEXT NOT NULL,
                    is_constitutional BOOLEAN DEFAULT TRUE,
                    reason TEXT,
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                CREATE TABLE IF NOT EXISTS audit_log (
                    id SERIAL PRIMARY KEY,
                    actor_role TEXT NOT NULL DEFAULT 'system',
                    action TEXT NOT NULL,
                    resource TEXT,
                    detail JSONB DEFAULT '{}',
                    ip_address TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_audit_actor ON audit_log(actor_role);
                CREATE INDEX IF NOT EXISTS idx_audit_time ON audit_log(created_at);
                """,
                sql_down="""
                DROP TABLE IF EXISTS audit_log;
                DROP TABLE IF EXISTS governance_records;
                """,
            ),
            Migration(
                version=6,
                description="Enable RLS on user-isolated tables",
                sql_up="""
                -- RLS is applied programmatically via apply_rls_policies()
                -- This migration ensures RLS-related config columns exist
                ALTER TABLE profiles ADD COLUMN IF NOT EXISTS rls_enabled BOOLEAN DEFAULT TRUE;
                ALTER TABLE memories ADD COLUMN IF NOT EXISTS rls_enabled BOOLEAN DEFAULT TRUE;
                ALTER TABLE personal_os_data ADD COLUMN IF NOT EXISTS rls_enabled BOOLEAN DEFAULT TRUE;
                ALTER TABLE agent_contracts ADD COLUMN IF NOT EXISTS rls_enabled BOOLEAN DEFAULT TRUE;
                ALTER TABLE notifications ADD COLUMN IF NOT EXISTS rls_enabled BOOLEAN DEFAULT TRUE;
                """,
                sql_down="""
                ALTER TABLE profiles DROP COLUMN IF EXISTS rls_enabled;
                ALTER TABLE memories DROP COLUMN IF EXISTS rls_enabled;
                ALTER TABLE personal_os_data DROP COLUMN IF EXISTS rls_enabled;
                ALTER TABLE agent_contracts DROP COLUMN IF EXISTS rls_enabled;
                ALTER TABLE notifications DROP COLUMN IF EXISTS rls_enabled;
                """,
            ),
        ]

    def run_migrations(self, target_version: Optional[int] = None) -> List[str]:
        """
        Run all pending migrations up to target_version (or all).
        Returns list of migration descriptions applied.
        """
        conn = self.get_sync_connection()
        if not conn:
            logger.warning("Cannot run migrations — no sync connection")
            return []

        applied: List[str] = []
        try:
            cur = conn.cursor()

            # Ensure schema version table exists
            cur.execute("""
                CREATE TABLE IF NOT EXISTS _schema_version (
                    version INTEGER PRIMARY KEY,
                    description TEXT NOT NULL,
                    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    checksum TEXT NOT NULL
                );
            """)

            # Get current version
            cur.execute("SELECT COALESCE(MAX(version), 0) FROM _schema_version;")
            current_version = cur.fetchone()[0]

            # Apply migrations
            for migration in self._migrations:
                if migration.version <= current_version:
                    continue
                if target_version and migration.version > target_version:
                    continue

                try:
                    checksum = hashlib.sha256(
                        migration.sql_up.encode()
                    ).hexdigest()[:16]

                    cur.execute(migration.sql_up)
                    cur.execute(
                        """
                        INSERT INTO _schema_version (version, description, checksum)
                        VALUES (%s, %s, %s)
                        """,
                        (migration.version, migration.description, checksum),
                    )

                    migration.status = MigrationStatus.APPLIED
                    migration.applied_at = datetime.now(timezone.utc).isoformat()
                    applied.append(migration.description)
                    logger.info(
                        f"📦 Migration v{migration.version}: {migration.description}"
                    )

                except Exception as e:
                    migration.status = MigrationStatus.FAILED
                    logger.error(
                        f"❌ Migration v{migration.version} failed: {e}"
                    )
                    raise

            cur.close()
            logger.info(f"✅ Migrations applied: {len(applied)}")
            return applied

        except Exception as e:
            logger.error(f"🐘 Migration run failed: {e}")
            return applied

    # ─── SQLite → PostgreSQL Migration ───────────────────────────────────────

    def migrate_from_sqlite(self, sqlite_path: str, tables: List[str]) -> Dict[str, int]:
        """
        Migrate data from SQLite to PostgreSQL.
        Returns dict with table_name -> row_count mapping.

        Args:
            sqlite_path: Path to SQLite database file.
            tables: List of table names to migrate.
        """
        import sqlite3

        conn = self.get_sync_connection()
        if not conn:
            logger.warning("Cannot migrate — no PostgreSQL connection")
            return {}

        results: Dict[str, int] = {}

        try:
            sqlite_conn = sqlite3.connect(sqlite_path)
            sqlite_conn.row_factory = sqlite3.Row

            for table in tables:
                # Read from SQLite
                sqlite_rows = sqlite_conn.execute(
                    f"SELECT * FROM {table}"
                ).fetchall()

                if not sqlite_rows:
                    results[table] = 0
                    continue

                # Get column names
                columns = [desc[0] for desc in sqlite_conn.execute(
                    f"SELECT * FROM {table} LIMIT 0"
                ).description]

                # Build INSERT statement
                placeholders = ", ".join([f"%({col})s" for col in columns])
                col_names = ", ".join(columns)
                insert_sql = (
                    f"INSERT INTO {table} ({col_names}) "
                    f"VALUES ({placeholders}) "
                    f"ON CONFLICT DO NOTHING"
                )

                # Insert into PostgreSQL
                pg_cur = conn.cursor()
                count = 0
                for row in sqlite_rows:
                    try:
                        pg_cur.execute(insert_sql, dict(row))
                        count += 1
                    except Exception as e:
                        logger.debug(f"Skipping row in {table}: {e}")

                pg_cur.close()
                results[table] = count
                logger.info(
                    f"📋 Migrated {count} rows from SQLite.{table} → PostgreSQL"
                )

            sqlite_conn.close()
            logger.info(f"✅ SQLite → PostgreSQL migration complete: {results}")
            return results

        except Exception as e:
            logger.error(f"🐘 SQLite migration failed: {e}")
            return results

    # ─── Status ──────────────────────────────────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        """Get PostgreSQL adapter status."""
        rls_tables = {
            name: cfg.to_dict() for name, cfg in self._rls_tables.items()
        }
        migration_status = {
            m.version: {
                "description": m.description,
                "status": m.status.value,
                "applied_at": m.applied_at,
            }
            for m in self._migrations
        }

        return {
            "config": {
                "host": self.config.host,
                "port": self.config.port,
                "database": self.config.database,
                "user": self.config.user,
                "pool_size": self.config.pool_size,
            },
            "initialized": self._initialized,
            "rls_tables": rls_tables,
            "migrations": migration_status,
            "async_pool_ready": self._async_pool is not None,
            "sync_conn_ready": self._sync_conn is not None and not (
                hasattr(self._sync_conn, 'closed') and self._sync_conn.closed
            ),
        }


# ─── Singleton ────────────────────────────────────────────────────────────────

_postgres_adapter: Optional[PostgresAdapter] = None


def get_postgres_adapter(config: Optional[PostgresConfig] = None) -> PostgresAdapter:
    """Get or create the global PostgreSQL adapter instance."""
    global _postgres_adapter
    if _postgres_adapter is None:
        _postgres_adapter = PostgresAdapter(config)
    return _postgres_adapter


def reset_postgres_adapter():
    """Reset the global PostgreSQL adapter (for testing)."""
    global _postgres_adapter
    _postgres_adapter = None


__all__ = [
    "PostgresAdapter",
    "PostgresConfig",
    "RLSConfig",
    "RLSPolicyBuilder",
    "Migration",
    "TenantIsolationLevel",
    "MigrationStatus",
    "get_postgres_adapter",
    "reset_postgres_adapter",
]
