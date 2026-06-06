-- =============================================================================
-- ASIMNEXUS ClickHouse — DDL for Analytics Tables
-- =============================================================================
-- Auto-generated from storage/schemas/clickhouse_tables.py
-- These tables store time-series analytics data: auth events, routing metrics,
-- network latency, mesh events, websocket events, and UI telemetry.
-- =============================================================================

-- ─────────────────────────────────────────────────────────────────────────────
-- 1. auth_events — Authentication & authorisation audit trail
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS auth_events (
    event_id UUID DEFAULT generateUUIDv4(),
    timestamp DateTime DEFAULT now(),
    user_id String,
    action LowCardinality(String),
    ip_address String,
    user_agent String,
    success UInt8,
    error_code Nullable(String),
    risk_score Float32 DEFAULT 0,
    device_id Nullable(String),
    session_id Nullable(String),
    auth_method LowCardinality(String),
    region LowCardinality(String)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (timestamp, user_id)
TTL timestamp + INTERVAL 12 MONTH
SETTINGS index_granularity = 8192;

-- ─────────────────────────────────────────────────────────────────────────────
-- 2. routing_metrics — AI routing decisions & model performance
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS routing_metrics (
    timestamp DateTime DEFAULT now(),
    source_node String,
    target_node String,
    mesh_type LowCardinality(String),
    latency_ms Float32,
    hops UInt8,
    packet_loss Float32,
    bandwidth_kbps Float32,
    rtt_ms Float32,
    success UInt8,
    error_type Nullable(String),
    protocol LowCardinality(String)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (timestamp, source_node)
TTL timestamp + INTERVAL 6 MONTH;

-- ─────────────────────────────────────────────────────────────────────────────
-- 3. latency_data — Network latency & bandwidth monitoring
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS latency_data (
    timestamp DateTime DEFAULT now(),
    source_id String,
    target_id String,
    route_hash String,
    latency_ms Float32,
    jitter_ms Float32,
    packet_loss_pct Float32,
    bandwidth_estimate Float32,
    connection_type LowCardinality(String),
    mesh_type LowCardinality(String)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (timestamp, source_id)
TTL timestamp + INTERVAL 3 MONTH;

-- ─────────────────────────────────────────────────────────────────────────────
-- 4. mesh_events — P2P mesh network topology & data-transfer events
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS mesh_events (
    event_id UUID DEFAULT generateUUIDv4(),
    timestamp DateTime DEFAULT now(),
    event_type LowCardinality(String),
    node_id String,
    peer_id Nullable(String),
    mesh_type LowCardinality(String),
    direction LowCardinality(String),
    bytes_transferred UInt64 DEFAULT 0,
    status LowCardinality(String),
    detail Nullable(String),
    session_id Nullable(String),
    error_message Nullable(String)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (timestamp, event_type)
TTL timestamp + INTERVAL 6 MONTH;

-- ─────────────────────────────────────────────────────────────────────────────
-- 5. websocket_events — WebSocket connection lifecycle & messaging
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS websocket_events (
    event_id UUID DEFAULT generateUUIDv4(),
    timestamp DateTime DEFAULT now(),
    connection_id String,
    user_id Nullable(String),
    event_type LowCardinality(String),
    message_size UInt32,
    direction LowCardinality(String),
    latency_ms Float32,
    success UInt8,
    error_code Nullable(String),
    protocol_version String
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (timestamp, connection_id)
TTL timestamp + INTERVAL 6 MONTH;

-- ─────────────────────────────────────────────────────────────────────────────
-- 6. ui_telemetry — Front-end user interaction telemetry
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ui_telemetry (
    event_id UUID DEFAULT generateUUIDv4(),
    timestamp DateTime DEFAULT now(),
    session_id String,
    user_id Nullable(String),
    event_type LowCardinality(String),
    component String,
    action String,
    value Float32,
    page String,
    browser LowCardinality(String),
    device_type LowCardinality(String),
    os LowCardinality(String),
    screen_resolution String,
    duration_ms Float32,
    success UInt8
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (timestamp, event_type)
TTL timestamp + INTERVAL 12 MONTH;

-- =============================================================================
-- Materialized Views
-- =============================================================================

-- ─────────────────────────────────────────────────────────────────────────────
-- MV 1: hourly_mesh_stats — Aggregates mesh_events by hour
-- ─────────────────────────────────────────────────────────────────────────────
CREATE MATERIALIZED VIEW IF NOT EXISTS hourly_mesh_stats
ENGINE = AggregatingMergeTree()
PARTITION BY toYYYYMM(hour)
ORDER BY (hour, event_type, status)
AS SELECT
    toStartOfHour(timestamp) AS hour,
    event_type,
    status,
    mesh_type,
    count() AS event_count,
    sum(bytes_transferred) AS total_bytes,
    countIf(success > 0) AS success_count,
    countIf(success = 0) AS failure_count
FROM mesh_events
GROUP BY hour, event_type, status, mesh_type;

-- ─────────────────────────────────────────────────────────────────────────────
-- MV 2: daily_routing_summary — Aggregates routing_metrics by day
-- ─────────────────────────────────────────────────────────────────────────────
CREATE MATERIALIZED VIEW IF NOT EXISTS daily_routing_summary
ENGINE = AggregatingMergeTree()
PARTITION BY toYYYYMM(day)
ORDER BY (day, mesh_type, protocol)
AS SELECT
    toStartOfDay(timestamp) AS day,
    mesh_type,
    protocol,
    count() AS route_count,
    avg(latency_ms) AS avg_latency_ms,
    avg(rtt_ms) AS avg_rtt_ms,
    avg(packet_loss) AS avg_packet_loss,
    sum(bandwidth_kbps) AS total_bandwidth_kbps,
    countIf(success > 0) AS success_count,
    countIf(success = 0) AS failure_count,
    countIf(error_type IS NOT NULL) AS error_count
FROM routing_metrics
GROUP BY day, mesh_type, protocol;
