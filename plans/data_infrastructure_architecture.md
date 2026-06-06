# AsimNexus 4-Layer Data Infrastructure Architecture

> **Status:** Planning Document v1.0  
> **Audience:** Engineering Team  
> **Goal:** Define a comprehensive, production-grade multi-layer storage architecture replacing the current ad-hoc persistence with a resilient, scalable, and backward-compatible 4-layer design.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Current State Analysis](#2-current-state-analysis)
3. [Architecture Overview](#3-architecture-overview)
4. [Layer 1: ClickHouse — Primary Warehouse](#4-layer-1-clickhouse--primary-warehouse)
5. [Layer 2: OLTP DB — PostgreSQL-compatible Source of Truth](#5-layer-2-oltp-db--postgresql-compatible-source-of-truth)
6. [Layer 3: Object Storage — S3/MinIO Raw Data Lake](#6-layer-3-object-storage--s3minio-raw-data-lake)
7. [Layer 4: Vector DB — ChromaDB Semantic Memory](#7-layer-4-vector-db--chromadb-semantic-memory)
8. [Configuration & Environment](#8-configuration--environment)
9. [Migration Strategy](#9-migration-strategy)
10. [Docker Compose Infrastructure](#10-docker-compose-infrastructure)
11. [Appendices](#11-appendices)

---

## 1. Executive Summary

AsimNexus currently uses **34 storage mechanisms** across **6 patterns**: in-memory dicts (16), JSONL append files (8), JSON overwrite files (5), SQLite databases (3), ChromaDB (1), and filesystem .txt (1). This fragmentation creates critical risks — financial data in [`economy/nexus_credits.py`](economy/nexus_credits.py:90) lives entirely in RAM, audit trails use append-only JSONL with no query capability, and state snapshots risk data loss on crash.

The recommended architecture replaces these ad-hoc patterns with a **4-layer storage stack**:

```
┌─────────────────────────────────────────────────────────────────┐
│                      APPLICATION LAYER                           │
│  (HybridRouter, DharmaVeto, Federation, Clones, WebSocket, UI)   │
└───────────────────┬──────────────────────────┬──────────────────┘
                    │                          │
        ┌──────────▼──────────┐    ┌──────────▼──────────┐
        │   AsimNexusEngine   │    │     OltpEngine       │
        │  (ClickHouse Client) │    │  (PostgreSQL Client) │
        │  Fallback: SQLite/   │    │  Fallback: SQLite    │
        │  JSONL              │    │                      │
        └──────────┬──────────┘    └──────────┬──────────┘
                   │                          │
        ┌──────────▼──────────┐    ┌──────────▼──────────┐
        │     ClickHouse       │    │     PostgreSQL       │
        │  Time-series + TTL   │    │  ACID + Relations   │
        │  Auth, Route, Mesh,  │    │  Users, Credits,    │
        │  WS, UI Telemetry   │    │  Governance, DIDs   │
        └─────────────────────┘    └─────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      OBJECT STORAGE (S3/MinIO)                   │
│  raw-logs/ │ exports/ │ snapshots/ │ deployments/ │ uploads/   │
│  mesh-offline-buffers/                                           │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   VECTOR DB (ChromaDB)                           │
│  Collection: agent_context │ semantic_memory │ retrieval │ ...  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Current State Analysis

### 2.1 Storage Mechanism Inventory

| # | Pattern | Count | Risk | Examples |
|---|---------|-------|------|---------|
| 1 | **In-memory dict** | 16 | **CRITICAL** — data lost on restart | [`nexus_credits.py`](economy/nexus_credits.py:90), [`BlockchainGovernance.chain`](core/blockchain/governance.py:74), [`DharmaVeto._balances`](security/power_balance_constitution.py:186), [`ASIMNexusIdentityProvider.founder_clones`](auth/identity_provider.py:40) |
| 2 | **JSONL append** | 8 | MEDIUM — no query, no indexing | [`data/telemetry.jsonl`](data/telemetry.jsonl), [`data/audit_bus.jsonl`](data/audit_bus.jsonl), [`data/os_control_audit.jsonl`](data/os_control_audit.jsonl), [`data/dream_log.jsonl`](data/dream_log.jsonl), [`data/clone_silos/*.jsonl`](data/clone_silos/) |
| 3 | **JSON overwrite** | 5 | HIGH — race conditions, partial writes | [`data/node_registry.json`](data/node_registry.json), [`data/federation/*.json`](data/federation/), [`data/quad_mesh/peers.json`](data/quad_mesh/) |
| 4 | **SQLite** | 3 | LOW — adequate but not scalable | [`data/vector_memory.db`](core/vectormemory.py:32), [`data/node_registry.db`](mesh/node_registry.py:81), health probes |
| 5 | **ChromaDB** | 1 | LOW — but single-collection only | [`data/chromadb/`](data/chromadb/) |
| 6 | **Filesystem .txt** | 1 | LOW | Conversation history |

### 2.2 Critical Data at Risk

| Data | Location | Current Storage | Risk Level |
|------|----------|----------------|------------|
| Credits, balances, transactions | [`economy/nexus_credits.py`](economy/nexus_credits.py:90) | In-memory `Dict[str, float]` | 🔴 CRITICAL |
| Blockchain governance chain | [`core/blockchain/governance.py`](core/blockchain/governance.py:74) | In-memory `List[Block]` | 🔴 CRITICAL |
| Dharma veto state + sector balances | [`security/power_balance_constitution.py`](security/power_balance_constitution.py:186) | In-memory `Dict[str, SectorBalance]` | 🟡 HIGH |
| Federation state + CRDT data | [`core/federation/global_federation.py`](core/federation/global_federation.py:225) | JSON files per peer | 🟡 HIGH |
| Auth tokens, founder clones | [`auth/identity_provider.py`](auth/identity_provider.py:40) | In-memory | 🟡 HIGH |
| WebSocket connections state | [`core/system_metrics_websocket.py`](core/system_metrics_websocket.py:23) | In-memory list | 🟢 LOW |
| Mesh switch events | [`mesh/multi_mesh_router.py`](mesh/multi_mesh_router.py:151) | In-memory (if any) | 🟢 LOW |

---

## 3. Architecture Overview

### 3.1 Four-Layer Design

```
                  ┌──────────────────────────────────────────┐
                  │            DATA PRODUCERS                │
                  │  Agents  │  Users  │  Mesh  │  System    │
                  └────┬─────────┬─────────┬────────┬───────┘
                       │         │         │        │
         ┌─────────────┼─────────┼─────────┼────────┼─────────────┐
         │             │         │         │        │             │
         ▼             ▼         ▼         ▼        ▼             │
   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
   │ ClickHouse│ │PostgreSQL│ │ MinIO/S3│ │ ChromaDB │           │
   │ Warehouse│ │  OLTP DB │ │  Object  │ │  Vector  │           │
   │          │ │          │ │  Store   │ │    DB    │           │
   └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘           │
        │            │            │            │                 │
        ▼            ▼            ▼            ▼                 │
   ┌──────────────────────────────────────────────────────┐     │
   │              UNIFIED CONFIG (storage.yaml)           │     │
   │         AsimNexusEngine │ OltpEngine │ ObjectStore   │     │
   │         VectorStore — consolidated wrappers          │     │
   └──────────────────────────────────────────────────────┘     │
                                                                │
   ┌──────────────────────────────────────────────────────────┐ │
   │  GRACEFUL DEGRADATION CHAIN                              │ │
   │  Primary → ClickHouse/PostgreSQL → SQLite → JSONL → nil │ │
   └──────────────────────────────────────────────────────────┘ │
   └────────────────────────────────────────────────────────────┘
```

### 3.2 Data Flow Principles

1. **Write-through:** All writes go to the primary layer (ClickHouse/PostgreSQL/ChromaDB/S3) via wrapper classes
2. **Fallback chain:** If primary is unavailable, degrade to next available layer  
3. **Async by default:** All DB operations use async/await patterns
4. **Idempotent retry:** Writes are idempotent where possible
5. **Observability:** Every wrapper emits metrics on latency, error rate, fallback count

### 3.3 Wrapper Class Architecture

Each layer has a dedicated wrapper class in [`infrastructure/storage/`](infrastructure/storage/) (to be created):

| Wrapper | Primary | Fallback 1 | Fallback 2 |
|---------|---------|------------|------------|
| [`AsimNexusEngine`](#asimnexusengine) | ClickHouse | SQLite | JSONL |
| [`OltpEngine`](#oltpengine) | PostgreSQL | SQLite | JSON |
| [`ObjectStore`](#objectstore) | S3/MinIO | Local filesystem | — |
| [`VectorStore`](#vectorstore) | ChromaDB | SQLite | JSON |

---

## 4. Layer 1: ClickHouse — Primary Warehouse

### 4.1 Purpose

Time-series analytics warehouse for all telemetry, audit, routing, latency, mesh, WebSocket, and UI events. Designed for high-throughput inserts and low-latency analytical queries with automatic TTL-based data lifecycle management.

### 4.2 Connection Details

| Property | Value |
|----------|-------|
| Host | `clickhouse://localhost:9000` (default) |
| Database | `asimnexus` |
| User | `default` |
| Protocol | Native TCP (9000) + HTTP (8123) |
| Async driver | `clickhouse-driver` + `asyncio` |

### 4.3 Table Schemas

All tables use the `ReplicatedMergeTree` (or `MergeTree` for single-node dev) engine with `ORDER BY` timestamp and `PARTITION BY toYYYYMM(timestamp)`.

#### 4.3.1 `auth_events`

```sql
CREATE TABLE asimnexus.auth_events (
    event_id UUID DEFAULT generateUUIDv4(),
    timestamp DateTime64(3) DEFAULT now64(),
    user_id String,
    session_id String,
    event_type Enum('login', 'logout', 'register', 'token_refresh', 'mfa_challenge', 'password_reset', 'session_expire'),
    ip_address String,
    user_agent String,
    auth_method Enum('jwt', 'oauth', 'biometric', 'did', 'hardware_key'),
    success UInt8,
    failure_reason String DEFAULT '',
    metadata JSON,
    trace_id String,
    span_id String
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (timestamp, user_id)
TTL timestamp + INTERVAL 12 MONTH DELETE
SETTINGS index_granularity = 8192;
```

**Source migrations:**
- [`auth/identity_provider.py`](auth/identity_provider.py) — founder clone auth events (currently in-memory)
- [`data/audit_bus.jsonl`](data/audit_bus.jsonl) — all HTTP auth request/response audit
- [`data/os_control_audit.jsonl`](data/os_control_audit.jsonl) — OS-level auth events

#### 4.3.2 `routing_metrics`

```sql
CREATE TABLE asimnexus.routing_metrics (
    event_id UUID DEFAULT generateUUIDv4(),
    timestamp DateTime64(3) DEFAULT now64(),
    intent Enum('health', 'finance', 'legal', 'education', 'government', 'technical',
                 'communication', 'agriculture', 'transport', 'energy', 'security',
                 'commerce', 'research', 'emergency', 'creative', 'personal', 'system_control', 'generic'),
    model_tier Enum('local_fast', 'local_quality', 'cloud_fast', 'cloud_quality', 'cloud_code'),
    model_name String,
    route_score Float32,
    latency_ms Float64,
    requires_veto UInt8,
    requires_human UInt8,
    sector String,
    user_id String,
    session_id String,
    cache_hit UInt8,
    token_count_input UInt32,
    token_count_output UInt32,
    error_code String DEFAULT '',
    metadata JSON
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (timestamp, intent)
TTL timestamp + INTERVAL 6 MONTH DELETE
SETTINGS index_granularity = 8192;
```

**Source migrations:**
- [`core/routing/hybrid_router.py`](core/routing/hybrid_router.py) — [`RouteDecision`](core/routing/hybrid_router.py:59) metrics
- [`data/telemetry.jsonl`](data/telemetry.jsonl) — all routing telemetry events

#### 4.3.3 `latency_data`

```sql
CREATE TABLE asimnexus.latency_data (
    event_id UUID DEFAULT generateUUIDv4(),
    timestamp DateTime64(3) DEFAULT now64(),
    component String,
    endpoint String,
    method Enum('GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'WS'),
    latency_ms Float64,
    status_code UInt16,
    user_id String,
    session_id String,
    trace_id String,
    span_id String,
    cpu_pct Float32,
    memory_mb Float32,
    network_kbps Float32,
    error_flag UInt8 DEFAULT 0,
    error_message String DEFAULT ''
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (timestamp, component)
TTL timestamp + INTERVAL 3 MONTH DELETE
SETTINGS index_granularity = 8192;
```

**Source migrations:**
- All latency fields from [`data/telemetry.jsonl`](data/telemetry.jsonl)
- [`backend/health.py`](backend/health.py) health check response times
- All HTTP request/response latency from audit bus

#### 4.3.4 `mesh_events`

```sql
CREATE TABLE asimnexus.mesh_events (
    event_id UUID DEFAULT generateUUIDv4(),
    timestamp DateTime64(3) DEFAULT now64(),
    event_type Enum('switch', 'discovery', 'connect', 'disconnect', 'sync', 'error',
                     'trust_change', 'suspension', 'ban', 'unban', 'offline_buffer'),
    mesh_type Enum('local', 'personal', 'cloud', 'public'),
    from_mesh Nullable(Enum('local', 'personal', 'cloud', 'public')),
    node_id String,
    peer_node_id String DEFAULT '',
    reason String,
    initiated_by Enum('auto', 'human'),
    success UInt8,
    latency_ms Float64,
    trust_level Enum('unknown', 'untrusted', 'low', 'medium', 'high', 'trusted'),
    data_classification Enum('public', 'internal', 'sensitive', 'secret'),
    bytes_transferred UInt64 DEFAULT 0,
    metadata JSON
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (timestamp, mesh_type, event_type)
TTL timestamp + INTERVAL 12 MONTH DELETE
SETTINGS index_granularity = 8192;
```

**Source migrations:**
- [`mesh/multi_mesh_router.py`](mesh/multi_mesh_router.py:151) — [`MeshSwitchEvent`](mesh/multi_mesh_router.py:151)
- [`mesh/node_registry.py`](mesh/node_registry.py:74) — trust events
- [`mesh/autodiscovery.py`](mesh/autodiscovery.py) — discovery events
- [`mesh/bootstrap.py`](mesh/bootstrap.py) — bootstrap events
- All mesh switch audit from JSONL

#### 4.3.5 `websocket_events`

```sql
CREATE TABLE asimnexus.websocket_events (
    event_id UUID DEFAULT generateUUIDv4(),
    timestamp DateTime64(3) DEFAULT now64(),
    connection_id String,
    session_id String,
    user_id String,
    event_type Enum('connect', 'disconnect', 'message_sent', 'message_received', 'error', 'ping', 'pong'),
    message_size UInt32 DEFAULT 0,
    latency_ms Float64,
    protocol Enum('system_metrics', 'chat', 'mesh_sync', 'governance', 'founder_sync'),
    success UInt8,
    error_message String DEFAULT '',
    metadata JSON
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (timestamp, protocol)
TTL timestamp + INTERVAL 3 MONTH DELETE
SETTINGS index_granularity = 8192;
```

**Source migrations:**
- [`core/system_metrics_websocket.py`](core/system_metrics_websocket.py:23) — WebSocket connection/disconnect events
- All WebSocket events from audit bus

#### 4.3.6 `ui_telemetry`

```sql
CREATE TABLE asimnexus.ui_telemetry (
    event_id UUID DEFAULT generateUUIDv4(),
    timestamp DateTime64(3) DEFAULT now64(),
    session_id String,
    user_id String,
    event_type Enum('page_view', 'click', 'navigation', 'feature_use', 'error', 'search', 'settings_change'),
    page String,
    component String,
    action String,
    duration_ms Float64,
    screen_width UInt16,
    screen_height UInt16,
    user_agent String,
    metadata JSON
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (timestamp, event_type)
TTL timestamp + INTERVAL 6 MONTH DELETE
SETTINGS index_granularity = 8192;
```

**Source migrations:**
- Frontend UI telemetry (currently unlogged or ad-hoc)
- All UI-related events from [`data/telemetry.jsonl`](data/telemetry.jsonl)

#### 4.3.7 Materialized Views

```sql
-- Hourly latency summary by component
CREATE MATERIALIZED VIEW asimnexus.latency_hourly_mv
ENGINE = AggregatingMergeTree()
PARTITION BY toYYYYMM(hour)
ORDER BY (hour, component)
AS SELECT
    toStartOfHour(timestamp) AS hour,
    component,
    count() AS request_count,
    avg(latency_ms) AS avg_latency,
    quantile(0.95)(latency_ms) AS p95_latency,
    quantile(0.99)(latency_ms) AS p99_latency,
    max(latency_ms) AS max_latency,
    sum(error_flag) AS error_count
FROM asimnexus.latency_data
GROUP BY hour, component;

-- Daily routing summary by intent
CREATE MATERIALIZED VIEW asimnexus.routing_daily_mv
ENGINE = AggregatingMergeTree()
PARTITION BY toYYYYMM(day)
ORDER BY (day, intent)
AS SELECT
    toStartOfDay(timestamp) AS day,
    intent,
    count() AS route_count,
    avg(latency_ms) AS avg_latency,
    avg(route_score) AS avg_score,
    sum(requires_veto) AS veto_count,
    sum(cache_hit) AS cache_hits
FROM asimnexus.routing_metrics
GROUP BY day, intent;
```

### 4.4 JSONL Migration Mapping

| Current File | Target Table(s) | Migration Strategy |
|-------------|-----------------|-------------------|
| [`data/telemetry.jsonl`](data/telemetry.jsonl) | `routing_metrics`, `latency_data`, `ui_telemetry` | Bulk insert via ClickHouse HTTP, then daily incremental |
| [`data/audit_bus.jsonl`](data/audit_bus.jsonl) | `auth_events`, `websocket_events`, `mesh_events` | Bulk insert + streaming via audit bus interceptor |
| [`data/os_control_audit.jsonl`](data/os_control_audit.jsonl) | `auth_events` | Bulk insert |
| [`data/dream_log.jsonl`](data/dream_log.jsonl) | New `dream_sessions` table | JSONL → ClickHouse |
| [`data/clone_silos/*.jsonl`](data/clone_silos/) | New `clone_memory_events` table | JSONL → ClickHouse |
| Mesh switch events (in-code) | `mesh_events` | Direct write via `AsimNexusEngine` |

### 4.5 `AsimNexusEngine` Wrapper

```python
# Conceptual design — infrastructure/storage/clickhouse_engine.py (to be created)

class AsimNexusEngine:
    """
    Primary ClickHouse wrapper with automatic fallback chain:
    ClickHouse → SQLite → JSONL append → silent no-op
    """
    
    def __init__(self, config: StorageConfig):
        self.config = config
        self._clickhouse_client = None  # async clickhouse-driver client
        self._sqlite_pool = None        # aiosqlite connection pool
        self._jsonl_writers = {}        # per-table JSONL file handles
        self._fallback_mode = FallbackMode.DISABLED
    
    async def connect(self):
        """Attempt ClickHouse connection, fall back if unavailable."""
        try:
            self._clickhouse_client = await create_clickhouse_client(
                host=self.config.clickhouse.host,
                port=self.config.clickhouse.port,
                database=self.config.clickhouse.database,
                user=self.config.clickhouse.user,
                password=self.config.clickhouse.password,
            )
            self._fallback_mode = FallbackMode.DISABLED
            logger.info("ClickHouse connected")
        except Exception as e:
            logger.warning(f"ClickHouse unavailable ({e}), activating fallback")
            self._fallback_mode = FallbackMode.SQLITE
            await self._init_sqlite_fallback()
    
    async def insert(self, table: str, data: list[dict], template: str = None):
        """
        Insert rows into ClickHouse (or fallback).
        
        Args:
            table: Target table name (e.g., 'auth_events')
            data: List of row dicts
            template: Optional query template name for validation
        """
        if self._fallback_mode == FallbackMode.DISABLED and self._clickhouse_client:
            try:
                await self._clickhouse_client.execute(
                    f"INSERT INTO asimnexus.{table} VALUES", data
                )
                return
            except Exception as e:
                logger.error(f"ClickHouse insert failed: {e}, degrading")
                self._fallback_mode = FallbackMode.SQLITE
                await self._init_sqlite_fallback()
        
        if self._fallback_mode == FallbackMode.SQLITE:
            await self._sqlite_insert(table, data)
        elif self._fallback_mode == FallbackMode.JSONL:
            await self._jsonl_append(table, data)
    
    async def query(self, query: str, params: dict = None) -> list[dict]:
        """Query with fallback."""
        if self._clickhouse_client:
            try:
                return await self._clickhouse_client.execute(query, params)
            except Exception:
                return await self._sqlite_query(query, params)
        return await self._sqlite_query(query, params)
    
    async def health(self) -> dict:
        """Return health status of all layers."""
        return {
            "clickhouse": self._clickhouse_client is not None,
            "sqlite": self._sqlite_pool is not None,
            "fallback_mode": self._fallback_mode.value,
        }
```

---

## 5. Layer 2: OLTP DB — PostgreSQL-compatible Source of Truth

### 5.1 Purpose

ACID-compliant relational database for all application transactions, user data, financial state, governance state, and identity registry. This is the **source of truth** for all critical mutable state.

### 5.2 Connection Details

| Property | Value |
|----------|-------|
| Host | `postgresql://localhost:5432/asimnexus` (default) |
| Driver | `asyncpg` via SQLAlchemy 2.0 async |
| Pool size | 10-50 connections (configurable) |
| Migration tool | Alembic |

### 5.3 SQLAlchemy Model Design

All models inherit from a common `Base` with `id`, `created_at`, `updated_at` mixin.

#### 5.3.1 `User` Model

```python
# Conceptual design — infrastructure/storage/models/user.py

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[UUID] = mapped_column(UUID, primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    role: Mapped[str] = mapped_column(String(50), default="user")  # user, admin, founder
    
    # Security
    two_factor_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
    deleted_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
```

**Source migrations:**
- [`auth/identity_provider.py`](auth/identity_provider.py:40) — in-memory founder clones dict → DB rows
- [`data/users/*.json`](data/users/) — user profile JSON → DB rows
- Existing [`docker/database_schema.sql`](docker/database_schema.sql) `users` table

#### 5.3.2 `Session` Model

```python
class Session(Base):
    __tablename__ = "sessions"
    
    id: Mapped[UUID] = mapped_column(UUID, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True)
    refresh_token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=True)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
```

**Source migrations:**
- In-memory session/token tracking → DB

#### 5.3.3 `Transaction` / `CreditAccount` Models

```python
class CreditAccount(Base):
    """Persistent credit balance — replaces in-memory nexus_credits.py Dict."""
    __tablename__ = "credit_accounts"
    
    id: Mapped[UUID] = mapped_column(UUID, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0.00"))
    lifetime_earned: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0.00"))
    lifetime_spent: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0.00"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

class CreditTransaction(Base):
    """Immutable transaction log."""
    __tablename__ = "credit_transactions"
    
    id: Mapped[UUID] = mapped_column(UUID, primary_key=True, default=uuid4)
    account_id: Mapped[UUID] = mapped_column(ForeignKey("credit_accounts.id"), index=True)
    transaction_type: Mapped[str] = mapped_column(String(50))  # package_purchase, task_reward, payment...
    sender_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    receiver_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    balance_before: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    balance_after: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    zkp_proof_hash: Mapped[str] = mapped_column(String(255), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
```

**Source migrations:**
- **CRITICAL:** [`economy/nexus_credits.py`](economy/nexus_credits.py:90) — entire `NexusCredits` class (in-memory `Dict[str, float]` for balances, `Dict[str, Transaction]` for history)

#### 5.3.4 `GovernanceState` Model

```python
class GovernanceState(Base):
    """Persistent governance state — replaces in-memory governance dicts."""
    __tablename__ = "governance_state"
    
    id: Mapped[UUID] = mapped_column(UUID, primary_key=True, default=uuid4)
    sector: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    control_type: Mapped[str] = mapped_column(String(50))  # public_coordinated, private_operated, mixed
    public_share: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.51"))
    private_share: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.49"))
    public_decisions: Mapped[int] = mapped_column(Integer, default=0)
    private_decisions: Mapped[int] = mapped_column(Integer, default=0)
    total_decisions: Mapped[int] = mapped_column(Integer, default=0)
    last_decision_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

class GovernanceDecision(Base):
    """Immutable governance decision audit log."""
    __tablename__ = "governance_decisions"
    
    id: Mapped[UUID] = mapped_column(UUID, primary_key=True, default=uuid4)
    sector: Mapped[str] = mapped_column(String(100), index=True)
    is_public_decision: Mapped[bool] = mapped_column(Boolean)
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    verdict: Mapped[str] = mapped_column(String(20))  # pass, warn, block
    context_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
```

**Source migrations:**
- [`security/power_balance_constitution.py`](security/power_balance_constitution.py:186) — in-memory `_balances` and `_amendments`
- [`core/blockchain/governance.py`](core/blockchain/governance.py:74) — `chain`, `smart_contracts`, `identities`
- [`core/governance.py`](core/governance.py:67) — `GovernanceLayer` state

#### 5.3.5 `IdentityDID` Model

```python
class IdentityDID(Base):
    """Decentralized identity registry."""
    __tablename__ = "identity_dids"
    
    id: Mapped[UUID] = mapped_column(UUID, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True, nullable=True)
    did_identifier: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    did_document: Mapped[dict] = mapped_column(JSONB)
    network: Mapped[str] = mapped_column(String(50))  # ethereum, polygon, solana
    wallet_address: Mapped[str] = mapped_column(String(255), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verified_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
```

**Source migrations:**
- [`data/identities/`](data/identities/) — DID JSON files → DB rows
- Auth provider founder clone identities
- [`docker/database_schema.sql`](docker/database_schema.sql) `blockchain_dids` table

#### 5.3.6 `NodeRegistry` Model

```python
class NodeRegistry(Base):
    """Persistent mesh node registry — replaces SQLite + JSON dual storage."""
    __tablename__ = "mesh_nodes"
    
    id: Mapped[UUID] = mapped_column(UUID, primary_key=True, default=uuid4)
    node_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hostname: Mapped[str] = mapped_column(String(255))
    ip_address: Mapped[str] = mapped_column(String(45))
    port: Mapped[int] = mapped_column(Integer)
    public_key: Mapped[str] = mapped_column(Text, nullable=True)
    trust_level: Mapped[str] = mapped_column(String(20), default="unknown")
    status: Mapped[str] = mapped_column(String(20), default="online")
    capabilities: Mapped[list] = mapped_column(JSONB, default=list)
    version: Mapped[str] = mapped_column(String(50), default="1.0.0")
    region: Mapped[str] = mapped_column(String(100), nullable=True)
    first_seen: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    last_seen: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

class TrustEvent(Base):
    """Node trust audit trail."""
    __tablename__ = "trust_events"
    
    id: Mapped[UUID] = mapped_column(UUID, primary_key=True, default=uuid4)
    node_id: Mapped[str] = mapped_column(String(255), index=True)
    event_type: Mapped[str] = mapped_column(String(50))  # discovery, trust_change, suspension...
    old_level: Mapped[str] = mapped_column(String(20), nullable=True)
    new_level: Mapped[str] = mapped_column(String(20), nullable=True)
    reason: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
```

**Source migrations:**
- [`mesh/node_registry.py`](mesh/node_registry.py:81) — SQLite `node_registry.db` + in-memory `self.nodes` dict
- [`data/node_registry.json`](data/node_registry.json) — JSON state snapshot
- [`docker/database_schema.sql`](docker/database_schema.sql) `mesh_nodes` table

#### 5.3.7 `FederationState` Model

```python
class FederationState(Base):
    """Persistent federation state — replaces JSON file per peer pattern."""
    __tablename__ = "federation_state"
    
    id: Mapped[UUID] = mapped_column(UUID, primary_key=True, default=uuid4)
    node_id: Mapped[str] = mapped_column(String(255), index=True)
    peer_node_id: Mapped[str] = mapped_column(String(255), index=True)
    federation_level: Mapped[str] = mapped_column(String(20))  # observer, member, admin, founder
    vector_clock: Mapped[dict] = mapped_column(JSONB, default=dict)  # CRDT vector clock
    state_snapshot: Mapped[dict] = mapped_column(JSONB, default=dict)
    last_sync_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    sync_status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        UniqueConstraint("node_id", "peer_node_id", name="uq_node_peer"),
    )
```

**Source migrations:**
- [`data/federation/*.json`](data/federation/) — 60+ JSON files per peer → DB rows
- [`core/federation/global_federation.py`](core/federation/global_federation.py:225) — [`GlobalFederationManager`](core/federation/global_federation.py:225) CRDT state

### 5.4 In-Memory Store Migration Map

| In-Memory Store | File | Target Model(s) | Priority |
|----------------|------|----------------|----------|
| `NexusCredits.credits`, `user_balances`, `transactions` | [`economy/nexus_credits.py:90-93`](economy/nexus_credits.py:90) | `CreditAccount`, `CreditTransaction` | 🔴 P0 |
| `BlockchainGovernance.chain`, `smart_contracts`, `identities` | [`core/blockchain/governance.py:74-77`](core/blockchain/governance.py:74) | `GovernanceState`, `GovernanceDecision`, `IdentityDID` | 🔴 P0 |
| `DharmaVeto._balances`, `_amendments`, `_audit_log` | [`security/power_balance_constitution.py:186-188`](security/power_balance_constitution.py:186) | `GovernanceState`, `GovernanceDecision` | 🟡 P1 |
| `Federation member states` | [`core/federation/global_federation.py`](core/federation/global_federation.py) | `FederationState` | 🟡 P1 |
| `NodeRegistry.nodes`, `trust_events` | [`mesh/node_registry.py:82-83`](mesh/node_registry.py:82) | `NodeRegistry`, `TrustEvent` | 🟡 P1 |
| `ASIMNexusIdentityProvider.founder_clones` | [`auth/identity_provider.py:40`](auth/identity_provider.py:40) | `User` | 🟡 P1 |
| `FounderSyncProtocol.devices` | [`governance/founder_sync_protocol.py`](governance/founder_sync_protocol.py) | New `FounderDevice` model | 🟢 P2 |
| `SystemMetricsWebSocket.active_connections` | [`core/system_metrics_websocket.py:28`](core/system_metrics_websocket.py:28) | Transient — no persistence needed | 🟢 P3 |

### 5.5 `OltpEngine` Wrapper

```python
# Conceptual design — infrastructure/storage/oltp_engine.py (to be created)

class OltpEngine:
    """
    PostgreSQL OLTP engine with SQLAlchemy 2.0 async.
    Fallback chain: PostgreSQL → SQLite → in-memory dict
    """
    
    def __init__(self, config: StorageConfig):
        self.config = config
        self._async_engine = None
        self._async_session_factory = None
        self._sqlite_engine = None
        self._fallback_mode = FallbackMode.DISABLED
    
    async def connect(self):
        """Initialize asyncpg connection pool or fallback."""
        try:
            self._async_engine = create_async_engine(
                self.config.postgres.dsn,
                pool_size=self.config.postgres.pool_size,
                max_overflow=self.config.postgres.max_overflow,
            )
            self._async_session_factory = async_sessionmaker(
                self._async_engine, expire_on_commit=False
            )
            # Run pending migrations
            await self._run_migrations()
            self._fallback_mode = FallbackMode.DISABLED
        except Exception as e:
            logger.warning(f"PostgreSQL unavailable ({e}), falling back to SQLite")
            self._fallback_mode = FallbackMode.SQLITE
            self._sqlite_engine = create_async_engine(f"sqlite+aiosqlite:///{self.config.fallback_db_path}")
            self._async_session_factory = async_sessionmaker(
                self._sqlite_engine, expire_on_commit=False
            )
    
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Context manager for DB session with automatic fallback."""
        async with self._async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    
    async def health(self) -> dict:
        """Return health status."""
        return {
            "postgresql": self._fallback_mode == FallbackMode.DISABLED,
            "fallback_mode": self._fallback_mode.value,
        }
```

---

## 6. Layer 3: Object Storage — S3/MinIO Raw Data Lake

### 6.1 Purpose

Scalable blob/object storage for raw files, logs, exports, snapshots, deployment artifacts, and mesh offline buffers. All data that is not time-series metrics or relational state lives here.

### 6.2 Connection Details

| Property | Value |
|----------|-------|
| Endpoint | `http://localhost:9000` (MinIO default) |
| Region | `us-east-1` (configurable) |
| Access Key | `${AWS_ACCESS_KEY_ID}` env var |
| Secret Key | `${AWS_SECRET_ACCESS_KEY}` env var |
| SDK | `boto3` (S3-compatible) |

### 6.3 Bucket Structure

```
asimnexus-object-store/
├── raw-logs/
│   ├── system/          # Raw system logs (before ClickHouse ETL)
│   ├── mesh/            # Raw mesh packet captures
│   └── audit/           # Raw audit trail archives
├── exports/
│   ├── data/            # Database exports / dumps
│   ├── reports/         # Generated reports (PDF, CSV)
│   └── analytics/       # Pre-computed analytics outputs
├── snapshots/
│   ├── federation/      # Federation state snapshots (periodic)
│   ├── governance/      # Governance state snapshots
│   └── system/          # Full system state snapshots
├── deployment-artifacts/
│   ├── builds/          # CI/CD build artifacts
│   ├── configs/         # Deployment configurations
│   └── models/          # ML model versions
├── user-uploads/
│   ├── avatars/         # User profile images
│   ├── documents/       # User uploaded documents
│   └── media/           # User uploaded media files
└── mesh-offline-buffers/
    ├── pending/         # Outbound data queued for mesh sync
    └── archive/         # Processed offline buffers
```

### 6.4 `ObjectStore` Wrapper

```python
# Conceptual design — infrastructure/storage/object_store.py (to be created)

class ObjectStore:
    """
    S3/MinIO object storage with local filesystem fallback.
    """
    
    def __init__(self, config: StorageConfig):
        self.config = config
        self._s3_client = None
        self._local_root = Path(config.object_store.local_fallback_path)
        self._local_root.mkdir(parents=True, exist_ok=True)
    
    async def connect(self):
        """Initialize boto3 S3 client or use local filesystem."""
        try:
            import boto3
            self._s3_client = boto3.client(
                "s3",
                endpoint_url=self.config.object_store.endpoint_url,
                aws_access_key_id=self.config.object_store.access_key,
                aws_secret_access_key=self.config.object_store.secret_key,
                region_name=self.config.object_store.region,
                config=Config(
                    connect_timeout=5,
                    read_timeout=30,
                    retries={"max_attempts": 3},
                ),
            )
            # Verify connection by listing buckets
            self._s3_client.list_buckets()
            await self._ensure_buckets()
            logger.info("ObjectStore connected to S3/MinIO")
        except Exception as e:
            logger.warning(f"S3 unavailable ({e}), using local filesystem fallback")
            self._s3_client = None
    
    async def upload(self, bucket: str, key: str, data: bytes, content_type: str = None):
        """Upload object. Falls back to local filesystem."""
        if self._s3_client:
            try:
                extra = {"ContentType": content_type} if content_type else {}
                self._s3_client.put_object(Bucket=bucket, Key=key, Body=data, **extra)
                return
            except Exception as e:
                logger.error(f"S3 upload failed: {e}")
        
        # Local fallback
        local_path = self._local_root / bucket / key
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_bytes(data)
    
    async def download(self, bucket: str, key: str) -> Optional[bytes]:
        """Download object from S3 or local fallback."""
        if self._s3_client:
            try:
                response = self._s3_client.get_object(Bucket=bucket, Key=key)
                return response["Body"].read()
            except Exception:
                pass
        
        local_path = self._local_root / bucket / key
        if local_path.exists():
            return local_path.read_bytes()
        return None
    
    async def list_objects(self, bucket: str, prefix: str = "") -> list[str]:
        """List objects with optional prefix."""
        keys = []
        if self._s3_client:
            try:
                paginator = self._s3_client.get_paginator("list_objects_v2")
                for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
                    for obj in page.get("Contents", []):
                        keys.append(obj["Key"])
                return keys
            except Exception:
                pass
        
        # Local fallback
        local_path = self._local_root / bucket / prefix
        if local_path.exists():
            for f in local_path.rglob("*"):
                if f.is_file():
                    keys.append(str(f.relative_to(self._local_root / bucket)))
        return keys
```

---

## 7. Layer 4: Vector DB — ChromaDB Semantic Memory

### 7.1 Purpose

Semantic memory, agent context, retrieval-augmented generation (RAG), and cross-clone memory search. The current ChromaDB integration ([`core/vectormemory.py`](core/vectormemory.py)) already provides a solid foundation — this layer enhances it with multi-collection support and a consolidated `VectorStore` wrapper.

### 7.2 Current State (P4 — Already Complete)

| Feature | Status | Details |
|---------|--------|---------|
| ChromaDB persistent client | ✅ | `data/chromadb/` with HNSW indexing |
| SentenceTransformer embeddings | ✅ | `all-MiniLM-L6-v2` (384d) |
| SQLite metadata mirror | ✅ | `data/vector_memory.db` |
| Memory CRUD | ✅ | Add, get, search, delete, prune |
| Singleton pattern | ✅ | `get_vector_memory()` / `reset_vector_memory()` |
| Embedding cache (LRU) | ✅ | `_EmbeddingCache` with 10K capacity |
| Async embedding queue | ✅ | `_async_embedding_queue` |

### 7.3 Identified Gaps

| Gap | Current | Required |
|-----|---------|----------|
| **Single collection** | Only `asimnexus_memories` | Multi-collection: `agent_context`, `semantic_memory`, `retrieval`, `clone_silos` |
| **No collection isolation** | All memory types in one namespace | Per-collection HNSW config, filtering, stats |
| **No hybrid search wrapper** | Vector-only search | Hybrid search with BM25 + RRF |
| **No collection CRUD in wrapper** | Manual ChromaDB calls | Unified `VectorStore` API |
| **No metric tracking** | No collection-level metrics | Per-collection count, avg distance, cache hit rate |

### 7.4 Multi-Collection Design

The current single-collection `asimnexus_memories` is split into purpose-specific collections:

| Collection Name | Memory Types | Use Case | Retention |
|----------------|-------------|----------|-----------|
| `semantic_memory` | `CHAT`, `USER_MEMORY`, `KNOWLEDGE` | General semantic memory for all users | 90 days |
| `agent_context` | `SYSTEM`, `LESSON` | Agent context, learned lessons, system state | 180 days |
| `retrieval` | `KNOWLEDGE` | RAG pipeline knowledge base | Indefinite |
| `clone_silos` | `CLONE` | Per-clone memory silos (founder clones) | 90 days |

### 7.5 `VectorStore` Wrapper

```python
# Conceptual design — infrastructure/storage/vector_store.py (to be created)

class VectorStore:
    """
    Consolidated vector operations over ChromaDB + SQLite.
    Manages multi-collection lifecycle with unified API.
    """
    
    COLLECTIONS = {
        "semantic_memory": {
            "memory_types": [MemoryType.CHAT, MemoryType.USER_MEMORY, MemoryType.KNOWLEDGE],
            "hnsw_space": "cosine",
            "hnsw_M": 16,
            "hnsw_construction_ef": 100,
        },
        "agent_context": {
            "memory_types": [MemoryType.SYSTEM, MemoryType.LESSON],
            "hnsw_space": "cosine",
            "hnsw_M": 24,
            "hnsw_construction_ef": 150,
        },
        "retrieval": {
            "memory_types": [MemoryType.KNOWLEDGE],
            "hnsw_space": "cosine",
            "hnsw_M": 32,
            "hnsw_construction_ef": 200,
        },
        "clone_silos": {
            "memory_types": [MemoryType.CLONE],
            "hnsw_space": "cosine",
            "hnsw_M": 16,
            "hnsw_construction_ef": 100,
        },
    }
    
    def __init__(self, config: StorageConfig):
        self.config = config
        self._collections: dict[str, ChromaCollection] = {}
        self._sqlite_meta: dict[str, SQLiteMetadataStore] = {}
        self._embedder = None
    
    async def initialize(self):
        """Initialize ChromaDB with all collections."""
        import chromadb
        from chromadb.config import Settings
        
        self._client = chromadb.PersistentClient(
            path=self.config.vector.chroma_path,
            settings=Settings(anonymized_telemetry=False),
        )
        
        for name, cfg in self.COLLECTIONS.items():
            self._collections[name] = self._client.get_or_create_collection(
                name=name,
                metadata={
                    "hnsw:space": cfg["hnsw_space"],
                    "hnsw:M": cfg["hnsw_M"],
                    "hnsw:construction_ef": cfg["hnsw_construction_ef"],
                },
            )
        
        logger.info(f"VectorStore initialized with {len(self._collections)} collections")
    
    async def add_memory(self, collection: str, text: str, memory_type: MemoryType,
                         user_id: str = "anonymous", metadata: dict = None) -> str:
        """Add memory to the appropriate collection."""
        assert collection in self._collections, f"Unknown collection: {collection}"
        
        embedding = self._embed(text)
        mem_id = str(uuid4())
        
        self._collections[collection].add(
            ids=[mem_id],
            embeddings=[embedding],
            metadatas=[{
                "memory_type": memory_type.value,
                "user_id": user_id,
                "content": text[:500],  # Truncated preview
                **(metadata or {}),
            }],
            documents=[text],
        )
        
        # Mirror metadata in SQLite for fast non-vector queries
        await self._sqlite_insert(collection, mem_id, text, memory_type, user_id, metadata)
        
        return mem_id
    
    async def search(self, collection: str, query: str, top_k: int = 10,
                     filter: dict = None) -> list[SearchResult]:
        """Semantic search within a single collection."""
        embedding = self._embed(query)
        
        results = self._collections[collection].query(
            query_embeddings=[embedding],
            n_results=top_k,
            where=filter,
        )
        
        return self._format_results(results)
    
    def get_stats(self) -> dict:
        """Return per-collection statistics."""
        stats = {}
        for name, col in self._collections.items():
            count = col.count()
            stats[name] = {
                "count": count,
                "memory_types": self.COLLECTIONS[name]["memory_types"],
            }
        return stats
```

---

## 8. Configuration & Environment

### 8.1 `config/storage.yaml`

```yaml
# config/storage.yaml — Centralized storage configuration
# All values overridable via environment variables (ASIM_ prefix)

version: "1.0"

clickhouse:
  host: ${ASIM_CLICKHOUSE_HOST:-localhost}
  port: ${ASIM_CLICKHOUSE_PORT:-9000}
  http_port: ${ASIM_CLICKHOUSE_HTTP_PORT:-8123}
  database: ${ASIM_CLICKHOUSE_DB:-asimnexus}
  user: ${ASIM_CLICKHOUSE_USER:-default}
  password: ${ASIM_CLICKHOUSE_PASSWORD:-}
  connect_timeout: ${ASIM_CLICKHOUSE_TIMEOUT:-10}
  
  # TTL configurations (in months)
  ttl:
    auth_events: 12
    routing_metrics: 6
    latency_data: 3
    mesh_events: 12
    websocket_events: 3
    ui_telemetry: 6

postgres:
  host: ${ASIM_POSTGRES_HOST:-localhost}
  port: ${ASIM_POSTGRES_PORT:-5432}
  database: ${ASIM_POSTGRES_DB:-asimnexus}
  user: ${ASIM_POSTGRES_USER:-asimnexus}
  password: ${ASIM_POSTGRES_PASSWORD:-asimnexus}
  dsn: ${ASIM_POSTGRES_DSN:-postgresql+asyncpg://asimnexus:asimnexus@localhost:5432/asimnexus}
  pool_size: ${ASIM_POSTGRES_POOL_SIZE:-10}
  max_overflow: ${ASIM_POSTGRES_MAX_OVERFLOW:-20}
  
  # Migration settings
  migrations_path: ${ASIM_MIGRATIONS_PATH:-./infrastructure/storage/migrations}

object_store:
  endpoint_url: ${ASIM_S3_ENDPOINT:-http://localhost:9000}
  region: ${ASIM_S3_REGION:-us-east-1}
  access_key: ${ASIM_S3_ACCESS_KEY:-minioadmin}
  secret_key: ${ASIM_S3_SECRET_KEY:-minioadmin}
  local_fallback_path: ${ASIM_S3_FALLBACK_PATH:-./data/object_store}
  
  buckets:
    - raw-logs
    - exports
    - snapshots
    - deployment-artifacts
    - user-uploads
    - mesh-offline-buffers

vector:
  chroma_path: ${ASIM_CHROMA_PATH:-./data/chromadb}
  embedding_model: ${ASIM_EMBEDDING_MODEL:-all-MiniLM-L6-v2}
  embedding_dim: ${ASIM_EMBEDDING_DIM:-384}
  cache_size: ${ASIM_EMBEDDING_CACHE_SIZE:-10000}
  
  collections:
    semantic_memory:
      hnsw_space: cosine
      hnsw_M: 16
      hnsw_construction_ef: 100
    agent_context:
      hnsw_space: cosine
      hnsw_M: 24
      hnsw_construction_ef: 150
    retrieval:
      hnsw_space: cosine
      hnsw_M: 32
      hnsw_construction_ef: 200
    clone_silos:
      hnsw_space: cosine
      hnsw_M: 16
      hnsw_construction_ef: 100

# Fallback behavior
fallback:
  enabled: ${ASIM_FALLBACK_ENABLED:-true}
  db_path: ${ASIM_FALLBACK_DB_PATH:-./data/fallback.db}
  jsonl_dir: ${ASIM_FALLBACK_JSONL_DIR:-./data/fallback_jsonl}
```

### 8.2 Environment Variable Overrides (`.env`)

```bash
# .env — Environment variable overrides for storage layer

# ClickHouse
ASIM_CLICKHOUSE_HOST=clickhouse.example.com
ASIM_CLICKHOUSE_PORT=9000
ASIM_CLICKHOUSE_DB=asimnexus_prod
ASIM_CLICKHOUSE_USER=admin
ASIM_CLICKHOUSE_PASSWORD=secure_password_here

# PostgreSQL
ASIM_POSTGRES_DSN=postgresql+asyncpg://user:pass@pg.example.com:5432/asimnexus_prod
ASIM_POSTGRES_POOL_SIZE=50

# Object Store
ASIM_S3_ENDPOINT=https://s3.example.com
ASIM_S3_ACCESS_KEY=your_access_key
ASIM_S3_SECRET_KEY=your_secret_key

# Vector DB
ASIM_CHROMA_PATH=/data/chromadb

# Fallback
ASIM_FALLBACK_ENABLED=true
ASIM_FALLBACK_DB_PATH=/data/fallback.db
```

---

## 9. Migration Strategy

### 9.1 Phase Overview

```
Phase 1 (Weeks 1-3): ClickHouse + OLTP DB
├── Implement AsimNexusEngine wrapper
├── Implement OltpEngine wrapper
├── Create ClickHouse tables (all 6 + materialized views)
├── Create SQLAlchemy models (all 7)
├── Migrate JSONL files → ClickHouse (bulk + incremental)
├── Migrate in-memory stores → PostgreSQL
├── Alembic migration setup
└── Graceful degradation tests

Phase 2 (Weeks 4-5): Object Storage
├── Implement ObjectStore wrapper
├── Set up MinIO in Docker Compose
├── Create bucket initialization script
├── Migrate raw file storage → S3/MinIO
├── Mesh offline buffer integration
└── Local filesystem fallback tests

Phase 3 (Week 6): Vector DB Enhancements
├── Implement multi-collection in VectorStore
├── Migrate existing ChromaDB data to collections
├── Hybrid search (BM25 + RRF) integration
├── Per-collection stats and metrics
└── Backward-compatible VectorMemory wrapper
```

### 9.2 Backward Compatibility Principle

**ALL existing code continues to work without changes.** The wrappers are designed as an additional layer, not a replacement. Existing code paths that write to JSONL, in-memory dicts, or SQLite continue to function. The new wrappers are injected via configuration and may be adopted incrementally.

```
┌─────────────────────────────────────────────┐
│              EXISTING CODE                    │
│  (nexus_credits.py, node_registry.py, etc.)  │
└──────────────────┬──────────────────────────┘
                   │ (unchanged)
                   ▼
┌─────────────────────────────────────────────┐
│         ADAPTER / INTERCEPTOR LAYER           │
│  Wraps existing write methods to also write   │
│  to new storage layer (dual-write mode)       │
└──────────┬─────────────────────┬─────────────┘
           │                     │
           ▼                     ▼
┌──────────────────┐   ┌──────────────────────┐
│   EXISTING PATH   │   │    NEW STORAGE PATH   │
│  JSONL / In-Mem  │   │  ClickHouse/PostgreSQL │
│  / SQLite        │   │  / S3 / ChromaDB      │
└──────────────────┘   └──────────────────────┘
```

### 9.3 Migration Phases Detail

#### Phase 1: ClickHouse + OLTP DB

**Objective:** Replace JSONL audit/telemetry + in-memory state with ClickHouse and PostgreSQL.

Steps:
1. Create [`infrastructure/storage/`](infrastructure/storage/) package directory
2. Implement [`AsimNexusEngine`](#asimnexusengine) with ClickHouse client + SQLite/JSONL fallback
3. Implement [`OltpEngine`](#oltpengine) with asyncpg + SQLAlchemy + SQLite fallback
4. Create CLI tool for bulk migration of existing JSONL data:
   ```bash
   python -m infrastructure.storage.migrate_jsonl \
       --source data/telemetry.jsonl \
       --table routing_metrics \
       --engine clickhouse
   ```
5. Create Alembic migration for all PostgreSQL tables
6. Wire `AsimNexusEngine` into:
   - Audit bus (replace `data/audit_bus.jsonl` writes)
   - Telemetry collector (replace `data/telemetry.jsonl` writes)
   - Mesh event recorder (replace JSON + JSONL writes)
7. Wire `OltpEngine` into:
   - [`NexusCredits`](economy/nexus_credits.py) — add dual-write (in-memory + PostgreSQL)
   - [`BlockchainGovernance`](core/blockchain/governance.py) — add DB persistence
   - [`PowerBalanceConstitution`](security/power_balance_constitution.py) — add DB persistence
   - [`NodeRegistry`](mesh/node_registry.py) — add DB persistence (dual-write with SQLite)
   - [`GlobalFederationManager`](core/federation/global_federation.py) — migrate JSON files to DB

**Dual-write pattern** (enables safe migration):

```python
# Example: CreditAccount dual-write
class NexusCredits:
    async def create_credit(self, user_id: str, amount: float) -> NexusCredit:
        # Existing in-memory path (unchanged)
        credit = NexusCredit(...)
        self.credits[credit.credit_id] = credit
        self.user_balances[user_id] = self.user_balances.get(user_id, 0) + amount
        
        # NEW: Dual-write to OLTP
        if self._oltp_engine:
            try:
                async with self._oltp_engine.session() as session:
                    account = await CreditAccount.get_or_create(session, user_id)
                    account.balance += amount
                    session.add(CreditTransaction(
                        account_id=account.id,
                        amount=amount,
                        ...
                    ))
            except Exception as e:
                logger.warning(f"OLTP dual-write failed: {e}")
        
        return credit
```

#### Phase 2: Object Storage

**Objective:** Replace filesystem raw storage with S3/MinIO.

Steps:
1. Implement [`ObjectStore`](#objectstore) wrapper
2. Add MinIO service to Docker Compose
3. Create bucket initialization script
4. Migrate:
   - Deployment artifacts → `deployment-artifacts/`
   - Federation snapshots → `snapshots/federation/`
   - User uploads → `user-uploads/`
   - Mesh offline buffers → `mesh-offline-buffers/`
   - Raw log archives → `raw-logs/`

#### Phase 3: Vector DB Enhancements

**Objective:** Multi-collection + hybrid search.

Steps:
1. Implement [`VectorStore`](#vectorstore) wrapper
2. Migrate existing single ChromaDB collection into 4 collections
3. Add hybrid search (BM25 + RRF) in RAG pipeline
4. Maintain backward-compatible [`VectorMemory`](core/vectormemory.py) class delegating to `VectorStore`

### 9.4 Graceful Degradation Test Matrix

| Scenario | ClickHouse | PostgreSQL | S3 | ChromaDB | Expected Behavior |
|----------|-----------|-----------|-----|----------|-------------------|
| All available | ✅ | ✅ | ✅ | ✅ | Full performance |
| ClickHouse down | ❌ | ✅ | ✅ | ✅ | AsimNexusEngine → SQLite fallback |
| PostgreSQL down | ✅ | ❌ | ✅ | ✅ | OltpEngine → SQLite fallback |
| S3/MinIO down | ✅ | ✅ | ❌ | ✅ | ObjectStore → local fs fallback |
| ChromaDB down | ✅ | ✅ | ✅ | ❌ | VectorStore → SQLite metadata search |
| All DBs down | ❌ | ❌ | ❌ | ❌ | All wrappers → JSONL/no-op; system in read-only mode |
| Network partition | ✅ | ✅ | ❌ | ✅ | S3 falls back to local; others may have latency |

---

## 10. Docker Compose Infrastructure

### 10.1 `docker-compose.storage.yml`

```yaml
# docker-compose.storage.yml — Storage layer services
# Extends the existing docker-compose.local.yml

version: "3.8"

services:
  # ── ClickHouse ──────────────────────────────────────────────
  clickhouse:
    image: clickhouse/clickhouse-server:24.3-alpine
    container_name: asimnexus-clickhouse
    restart: unless-stopped
    ports:
      - "8123:8123"   # HTTP interface
      - "9000:9000"   # Native TCP
    volumes:
      - clickhouse-data:/var/lib/clickhouse
      - ./docker/clickhouse/init:/docker-entrypoint-initdb.d  # Table DDL
    environment:
      CLICKHOUSE_DB: asimnexus
      CLICKHOUSE_USER: default
      CLICKHOUSE_PASSWORD: ""
    ulimits:
      nofile:
        soft: 262144
        hard: 262144
    healthcheck:
      test: ["CMD", "clickhouse-client", "--query", "SELECT 1"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ── PostgreSQL ──────────────────────────────────────────────
  postgres:
    image: postgres:16-alpine
    container_name: asimnexus-postgres
    restart: unless-stopped
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./docker/postgres/init:/docker-entrypoint-initdb.d
    environment:
      POSTGRES_DB: asimnexus
      POSTGRES_USER: asimnexus
      POSTGRES_PASSWORD: asimnexus
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U asimnexus"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ── MinIO (S3-compatible) ──────────────────────────────────
  minio:
    image: minio/minio:latest
    container_name: asimnexus-minio
    restart: unless-stopped
    ports:
      - "9000:9000"   # API
      - "9001:9001"   # Console
    volumes:
      - minio-data:/data
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    command: server /data --console-address ":9001"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ── Create MinIO buckets (init container) ──────────────────
  minio-init:
    image: minio/mc:latest
    container_name: asimnexus-minio-init
    depends_on:
      minio:
        condition: service_healthy
    entrypoint: >
      /bin/sh -c "
      /usr/bin/mc alias set asimnexus http://minio:9000 minioadmin minioadmin;
      /usr/bin/mc mb asimnexus/raw-logs --ignore-existing;
      /usr/bin/mc mb asimnexus/exports --ignore-existing;
      /usr/bin/mc mb asimnexus/snapshots --ignore-existing;
      /usr/bin/mc mb asimnexus/deployment-artifacts --ignore-existing;
      /usr/bin/mc mb asimnexus/user-uploads --ignore-existing;
      /usr/bin/mc mb asimnexus/mesh-offline-buffers --ignore-existing;
      echo 'MinIO buckets created successfully';
      "

volumes:
  clickhouse-data:
  postgres-data:
  minio-data:
```

### 10.2 ClickHouse Initialization Script

```sql
-- docker/clickhouse/init/01_schema.sql
-- Auto-executed by ClickHouse on first start

CREATE DATABASE IF NOT EXISTS asimnexus;

-- Include all CREATE TABLE statements from Section 4.3
-- (auth_events, routing_metrics, latency_data, mesh_events,
--  websocket_events, ui_telemetry)

-- Include all CREATE MATERIALIZED VIEW from Section 4.3.7
```

### 10.3 PostgreSQL Initialization Script

```sql
-- docker/postgres/init/01_schema.sql
-- Initial schema (Alembic manages future migrations)

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Include all CREATE TABLE statements from Section 5.3
-- (users, sessions, credit_accounts, credit_transactions,
--  governance_state, governance_decisions, identity_dids,
--  mesh_nodes, trust_events, federation_state)
```

---

## 11. Appendices

### A. Package Dependencies

Add to [`requirements.txt`](requirements.txt):

```txt
# Layer 1: ClickHouse
clickhouse-driver>=0.2.6
clickhouse-connect>=0.7.0

# Layer 2: PostgreSQL
asyncpg>=0.29.0
sqlalchemy[asyncio]>=2.0.25
alembic>=1.13.0
psycopg2-binary>=2.9.9  # for sync operations

# Layer 3: Object Storage
boto3>=1.34.0

# Layer 4: Vector DB
chromadb>=0.4.22
sentence-transformers>=2.2.0

# Configuration
pyyaml>=6.0
python-dotenv>=1.0.0
```

### B. File/Directory Structure Additions

```
infrastructure/
└── storage/
    ├── __init__.py
    ├── clickhouse_engine.py      # AsimNexusEngine
    ├── oltp_engine.py            # OltpEngine
    ├── object_store.py           # ObjectStore
    ├── vector_store.py           # VectorStore
    ├── config.py                 # StorageConfig Pydantic model
    ├── models/                   # SQLAlchemy models
    │   ├── __init__.py
    │   ├── user.py
    │   ├── session.py
    │   ├── credit.py
    │   ├── governance.py
    │   ├── identity.py
    │   ├── node.py
    │   └── federation.py
    ├── migrations/               # Alembic migrations
    │   ├── env.py
    │   ├── alembic.ini
    │   └── versions/
    └── migrate/
        ├── jsonl_to_clickhouse.py
        └── json_to_postgres.py

config/
└── storage.yaml                  # Centralized storage config

docker/
├── clickhouse/
│   └── init/
│       └── 01_schema.sql
└── postgres/
    └── init/
        └── 01_schema.sql

docker-compose.storage.yml        # Storage services
```

### C. Key Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Data loss during migration | HIGH | Dual-write pattern; keep old storage intact until Phase 3 validated |
| ClickHouse connection overhead | MEDIUM | Connection pooling; batch inserts (1000+ rows) |
| PostgreSQL schema drift | MEDIUM | Alembic migrations; CI/CD validation |
| S3/MinIO latency for small objects | LOW | Local filesystem fallback for small files (< 1MB) |
| ChromaDB single-collection migration | LOW | Script to split collection; keep old collection as backup |
| Increased memory usage from dual-write | MEDIUM | Configurable dual-write toggle; remove old code path after validation |

### D. Testing Strategy

```
tests/
└── storage/
    ├── test_clickhouse_engine.py    # Unit + integration with mock ClickHouse
    ├── test_oltp_engine.py          # Unit + integration with test PostgreSQL
    ├── test_object_store.py         # Unit + integration with MinIO container
    ├── test_vector_store.py         # Unit + ChromaDB in-memory tests
    ├── test_fallback.py             # Graceful degradation scenarios
    ├── test_migration.py            # JSONL → ClickHouse migration
    └── conftest.py                  # Test fixtures (Docker containers, mocks)
```

---
