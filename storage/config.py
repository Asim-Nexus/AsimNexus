"""
AsimNexus Storage Configuration Loader.

Reads ``config/storage.yaml`` and provides typed dataclass access to all
4-layer storage configuration values, with ``${VAR:-default}`` environment
variable substitution.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import yaml


# ---------------------------------------------------------------------------
# Environment variable substitution
# ---------------------------------------------------------------------------

_ENV_VAR_PATTERN = re.compile(r"\$\{(?P<name>[^:}-]+)(?::-(?P<default>[^}]*))?\}")


def _substitute_env_vars(value: str) -> str:
    """Replace ``${VAR:-default}`` patterns with environment variable values.

    If the environment variable is set (even to empty string), the env value
    is used.  Otherwise the ``:-default`` fallback is substituted.  If no
    default is provided and the variable is unset, the pattern is left as-is.
    """
    def _replacer(match: re.Match) -> str:
        var_name = match.group("name")
        default = match.group("default")
        env_value = os.environ.get(var_name)
        if env_value is not None:
            return env_value
        if default is not None:
            return default
        # Variable not set and no default — return the raw placeholder
        return match.group(0)

    return _ENV_VAR_PATTERN.sub(_replacer, value)


def _walk_and_substitute(obj: Any) -> Any:
    """Recursively walk a parsed YAML object and substitute env vars in strings."""
    if isinstance(obj, str):
        # Only process if the string actually contains a placeholder
        if "${" in obj:
            return _substitute_env_vars(obj)
        return obj
    if isinstance(obj, dict):
        return {k: _walk_and_substitute(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_walk_and_substitute(item) for item in obj]
    return obj


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class ClickHouseTableConfig:
    """Configuration for a single ClickHouse table."""
    ttl: Optional[str] = None
    partition: Optional[str] = None


@dataclass
class ClickHouseFallbackConfig:
    """ClickHouse fallback (SQLite or JSONL) configuration."""
    type: str = "sqlite"  # sqlite | jsonl
    path: str = "data/storage/clickhouse_fallback.db"


@dataclass
class ClickHouseConfig:
    """ClickHouse layer configuration."""
    enabled: bool = True
    dsn: str = "clickhouse://localhost:9000/asimnexus"
    http_port: int = 8123
    user: str = "default"
    password: str = ""
    database: str = "asimnexus"
    connect_timeout: int = 10
    query_timeout: int = 30
    pool_size: int = 10
    tables: Dict[str, ClickHouseTableConfig] = field(default_factory=dict)
    fallback: ClickHouseFallbackConfig = field(default_factory=ClickHouseFallbackConfig)


@dataclass
class OltpFallbackConfig:
    """OLTP fallback (SQLite) configuration."""
    type: str = "sqlite"
    path: str = "data/storage/oltp_fallback.db"


@dataclass
class OltpConfig:
    """OLTP (PostgreSQL) layer configuration."""
    enabled: bool = True
    dsn: str = "postgresql+asyncpg://localhost:5432/asimnexus"
    user: str = "asimnexus"
    password: str = ""
    database: str = "asimnexus"
    pool_size: int = 20
    max_overflow: int = 10
    schema_version: int = 1
    tables: List[str] = field(default_factory=list)
    fallback: OltpFallbackConfig = field(default_factory=OltpFallbackConfig)


@dataclass
class ObjectStoreFallbackConfig:
    """Object store fallback (local filesystem) configuration."""
    type: str = "local"
    path: str = "data/object_store"


@dataclass
class ObjectStoreConfig:
    """Object store (S3/MinIO) layer configuration."""
    enabled: bool = True
    endpoint: str = "http://localhost:9000"
    access_key: str = "minioadmin"
    secret_key: str = "minioadmin"
    region: str = "auto"
    bucket_prefix: str = "asimnexus"
    buckets: List[str] = field(default_factory=list)
    fallback: ObjectStoreFallbackConfig = field(default_factory=ObjectStoreFallbackConfig)


@dataclass
class VectorCollectionConfig:
    """Configuration for a single VectorStore collection."""
    ttl: Optional[int] = None  # seconds, None = no expiry
    dimension: int = 384
    hnsw_space: str = "cosine"


@dataclass
class EmbeddingConfig:
    """Embedding model configuration."""
    model: str = "all-MiniLM-L6-v2"
    dimension: int = 384
    cache_size: int = 10000


@dataclass
class VectorDBFallbackConfig:
    """Vector DB fallback (SQLite) configuration."""
    type: str = "sqlite"
    path: str = "data/storage/vector_fallback.db"


@dataclass
class VectorDBConfig:
    """Vector DB (ChromaDB) layer configuration."""
    enabled: bool = True
    provider: str = "chromadb"  # chromadb | sqlite | memory
    path: str = "data/chromadb"
    collections: Dict[str, VectorCollectionConfig] = field(default_factory=dict)
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    fallback: VectorDBFallbackConfig = field(default_factory=VectorDBFallbackConfig)


@dataclass
class MigrationSourceConfig:
    """Glob patterns for legacy JSONL sources."""
    jsonl_audit: str = "data/audit/*.jsonl"
    jsonl_telemetry: str = "data/telemetry/*.jsonl"
    jsonl_governance: str = "data/governance/*.jsonl"
    jsonl_mesh: str = "data/mesh/*.jsonl"
    jsonl_power_balance: str = "data/power_balance/*.jsonl"
    jsonl_personal_os: str = "data/personal_os/*.jsonl"


@dataclass
class MigrationConfig:
    """Migration orchestrator configuration."""
    batch_size: int = 1000
    dual_write: bool = False
    auto_migrate: bool = False
    sources: MigrationSourceConfig = field(default_factory=MigrationSourceConfig)


@dataclass
class LoggingConfig:
    """Storage-layer logging configuration."""
    level: str = "INFO"
    slow_query_threshold_ms: int = 500
    connection_errors: bool = True


@dataclass
class StorageConfig:
    """Top-level AsimNexus 4-layer storage configuration."""
    version: str = "1.0"
    clickhouse: ClickHouseConfig = field(default_factory=ClickHouseConfig)
    oltp: OltpConfig = field(default_factory=OltpConfig)
    object_store: ObjectStoreConfig = field(default_factory=ObjectStoreConfig)
    vector_db: VectorDBConfig = field(default_factory=VectorDBConfig)
    migration: MigrationConfig = field(default_factory=MigrationConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)


# ---------------------------------------------------------------------------
# Build helpers
# ---------------------------------------------------------------------------

def _build_clickhouse(raw: dict) -> ClickHouseConfig:
    tables_raw = raw.get("tables", {})
    tables: Dict[str, ClickHouseTableConfig] = {}
    for name, tbl in tables_raw.items():
        tables[name] = ClickHouseTableConfig(
            ttl=tbl.get("ttl"),
            partition=tbl.get("partition"),
        )

    fb_raw = raw.get("fallback", {})
    fallback = ClickHouseFallbackConfig(
        type=fb_raw.get("type", "sqlite"),
        path=fb_raw.get("path", "data/storage/clickhouse_fallback.db"),
    )

    return ClickHouseConfig(
        enabled=bool(raw.get("enabled", True)),
        dsn=str(raw.get("dsn", "clickhouse://localhost:9000/asimnexus")),
        http_port=int(raw.get("http_port", 8123)),
        user=str(raw.get("user", "default")),
        password=str(raw.get("password", "")),
        database=str(raw.get("database", "asimnexus")),
        connect_timeout=int(raw.get("connect_timeout", 10)),
        query_timeout=int(raw.get("query_timeout", 30)),
        pool_size=int(raw.get("pool_size", 10)),
        tables=tables,
        fallback=fallback,
    )


def _build_oltp(raw: dict) -> OltpConfig:
    fb_raw = raw.get("fallback", {})
    fallback = OltpFallbackConfig(
        type=fb_raw.get("type", "sqlite"),
        path=fb_raw.get("path", "data/storage/oltp_fallback.db"),
    )

    return OltpConfig(
        enabled=bool(raw.get("enabled", True)),
        dsn=str(raw.get("dsn", "postgresql+asyncpg://localhost:5432/asimnexus")),
        user=str(raw.get("user", "asimnexus")),
        password=str(raw.get("password", "")),
        database=str(raw.get("database", "asimnexus")),
        pool_size=int(raw.get("pool_size", 20)),
        max_overflow=int(raw.get("max_overflow", 10)),
        schema_version=int(raw.get("schema_version", 1)),
        tables=list(raw.get("tables", [])),
        fallback=fallback,
    )


def _build_object_store(raw: dict) -> ObjectStoreConfig:
    fb_raw = raw.get("fallback", {})
    fallback = ObjectStoreFallbackConfig(
        type=fb_raw.get("type", "local"),
        path=fb_raw.get("path", "data/object_store"),
    )

    return ObjectStoreConfig(
        enabled=bool(raw.get("enabled", True)),
        endpoint=str(raw.get("endpoint", "http://localhost:9000")),
        access_key=str(raw.get("access_key", "minioadmin")),
        secret_key=str(raw.get("secret_key", "minioadmin")),
        region=str(raw.get("region", "auto")),
        bucket_prefix=str(raw.get("bucket_prefix", "asimnexus")),
        buckets=list(raw.get("buckets", [])),
        fallback=fallback,
    )


def _build_vector_db(raw: dict) -> VectorDBConfig:
    collections_raw = raw.get("collections", {})
    collections: Dict[str, VectorCollectionConfig] = {}
    for name, col in collections_raw.items():
        collections[name] = VectorCollectionConfig(
            ttl=col.get("ttl"),
            dimension=int(col.get("dimension", 384)),
            hnsw_space=str(col.get("hnsw_space", "cosine")),
        )

    emb_raw = raw.get("embedding", {})
    embedding = EmbeddingConfig(
        model=str(emb_raw.get("model", "all-MiniLM-L6-v2")),
        dimension=int(emb_raw.get("dimension", 384)),
        cache_size=int(emb_raw.get("cache_size", 10000)),
    )

    fb_raw = raw.get("fallback", {})
    fallback = VectorDBFallbackConfig(
        type=fb_raw.get("type", "sqlite"),
        path=fb_raw.get("path", "data/storage/vector_fallback.db"),
    )

    return VectorDBConfig(
        enabled=bool(raw.get("enabled", True)),
        provider=str(raw.get("provider", "chromadb")),
        path=str(raw.get("path", "data/chromadb")),
        collections=collections,
        embedding=embedding,
        fallback=fallback,
    )


def _build_migration(raw: dict) -> MigrationConfig:
    src_raw = raw.get("sources", {})
    sources = MigrationSourceConfig(
        jsonl_audit=str(src_raw.get("jsonl_audit", "data/audit/*.jsonl")),
        jsonl_telemetry=str(src_raw.get("jsonl_telemetry", "data/telemetry/*.jsonl")),
        jsonl_governance=str(src_raw.get("jsonl_governance", "data/governance/*.jsonl")),
        jsonl_mesh=str(src_raw.get("jsonl_mesh", "data/mesh/*.jsonl")),
        jsonl_power_balance=str(src_raw.get("jsonl_power_balance", "data/power_balance/*.jsonl")),
        jsonl_personal_os=str(src_raw.get("jsonl_personal_os", "data/personal_os/*.jsonl")),
    )

    return MigrationConfig(
        batch_size=int(raw.get("batch_size", 1000)),
        dual_write=bool(raw.get("dual_write", False)),
        auto_migrate=bool(raw.get("auto_migrate", False)),
        sources=sources,
    )


def _build_logging(raw: dict) -> LoggingConfig:
    return LoggingConfig(
        level=str(raw.get("level", "INFO")),
        slow_query_threshold_ms=int(raw.get("slow_query_threshold_ms", 500)),
        connection_errors=bool(raw.get("connection_errors", True)),
    )


# ---------------------------------------------------------------------------
# Public loader
# ---------------------------------------------------------------------------


def load_storage_config(path: str = "config/storage.yaml") -> StorageConfig:
    """Load and parse storage configuration with env var substitution.

    Parameters
    ----------
    path : str
        Path to the YAML configuration file (default ``config/storage.yaml``).

    Returns
    -------
    StorageConfig
        A fully-populated ``StorageConfig`` dataclass tree with environment
        variables resolved.
    """
    with open(path, "r", encoding="utf-8") as f:
        raw: Dict[str, Any] = yaml.safe_load(f)

    if not raw:
        raw = {}

    # Substitute environment variables in all string values
    raw = _walk_and_substitute(raw)

    ch_raw = raw.get("clickhouse", {})
    ol_raw = raw.get("oltp", {})
    os_raw = raw.get("object_store", {})
    vd_raw = raw.get("vector_db", {})
    mg_raw = raw.get("migration", {})
    lg_raw = raw.get("logging", {})

    return StorageConfig(
        version=str(raw.get("version", "1.0")),
        clickhouse=_build_clickhouse(ch_raw),
        oltp=_build_oltp(ol_raw),
        object_store=_build_object_store(os_raw),
        vector_db=_build_vector_db(vd_raw),
        migration=_build_migration(mg_raw),
        logging=_build_logging(lg_raw),
    )
