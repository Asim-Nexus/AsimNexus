"""
AsimNexus Storage — ClickHouse Table DDL Definitions.

Defines all table schemas, materialized views, and the ``create_all_tables``
factory that provisions them through an ``AsimNexusEngine`` instance.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from storage.clickhouse_engine import AsimNexusEngine

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Table DDL definitions
# ---------------------------------------------------------------------------

TABLES: Dict[str, Dict[str, Any]] = {
    # ..................................................................
    # auth_events — Authentication & authorisation audit trail
    # ..................................................................
    "auth_events": {
        "ddl": """CREATE TABLE IF NOT EXISTS auth_events (
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
        SETTINGS index_granularity = 8192""",
        "columns": [
            "event_id UUID DEFAULT generateUUIDv4()",
            "timestamp DateTime DEFAULT now()",
            "user_id String",
            "action LowCardinality(String)",
            "ip_address String",
            "user_agent String",
            "success UInt8",
            "error_code Nullable(String)",
            "risk_score Float32 DEFAULT 0",
            "device_id Nullable(String)",
            "session_id Nullable(String)",
            "auth_method LowCardinality(String)",
            "region LowCardinality(String)",
        ],
        "ttl": "12 MONTH",
        "partition": "toYYYYMM(timestamp)",
        "order_by": "(timestamp, user_id)",
        "engine": "MergeTree",
        "description": "Authentication & authorisation audit trail",
    },

    # ..................................................................
    # routing_metrics — AI routing decisions & model performance
    # ..................................................................
    "routing_metrics": {
        "ddl": """CREATE TABLE IF NOT EXISTS routing_metrics (
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
        TTL timestamp + INTERVAL 6 MONTH""",
        "columns": [
            "timestamp DateTime DEFAULT now()",
            "source_node String",
            "target_node String",
            "mesh_type LowCardinality(String)",
            "latency_ms Float32",
            "hops UInt8",
            "packet_loss Float32",
            "bandwidth_kbps Float32",
            "rtt_ms Float32",
            "success UInt8",
            "error_type Nullable(String)",
            "protocol LowCardinality(String)",
        ],
        "ttl": "6 MONTH",
        "partition": "toYYYYMM(timestamp)",
        "order_by": "(timestamp, source_node)",
        "engine": "MergeTree",
        "description": "AI routing decisions & network metrics",
    },

    # ..................................................................
    # latency_data — Network latency & bandwidth monitoring
    # ..................................................................
    "latency_data": {
        "ddl": """CREATE TABLE IF NOT EXISTS latency_data (
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
        TTL timestamp + INTERVAL 3 MONTH""",
        "columns": [
            "timestamp DateTime DEFAULT now()",
            "source_id String",
            "target_id String",
            "route_hash String",
            "latency_ms Float32",
            "jitter_ms Float32",
            "packet_loss_pct Float32",
            "bandwidth_estimate Float32",
            "connection_type LowCardinality(String)",
            "mesh_type LowCardinality(String)",
        ],
        "ttl": "3 MONTH",
        "partition": "toYYYYMM(timestamp)",
        "order_by": "(timestamp, source_id)",
        "engine": "MergeTree",
        "description": "Network latency, jitter & bandwidth monitoring",
    },

    # ..................................................................
    # mesh_events — P2P mesh network topology & data-transfer events
    # ..................................................................
    "mesh_events": {
        "ddl": """CREATE TABLE IF NOT EXISTS mesh_events (
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
        TTL timestamp + INTERVAL 6 MONTH""",
        "columns": [
            "event_id UUID DEFAULT generateUUIDv4()",
            "timestamp DateTime DEFAULT now()",
            "event_type LowCardinality(String)",
            "node_id String",
            "peer_id Nullable(String)",
            "mesh_type LowCardinality(String)",
            "direction LowCardinality(String)",
            "bytes_transferred UInt64 DEFAULT 0",
            "status LowCardinality(String)",
            "detail Nullable(String)",
            "session_id Nullable(String)",
            "error_message Nullable(String)",
        ],
        "ttl": "6 MONTH",
        "partition": "toYYYYMM(timestamp)",
        "order_by": "(timestamp, event_type)",
        "engine": "MergeTree",
        "description": "P2P mesh topology & data-transfer events",
    },

    # ..................................................................
    # websocket_events — WebSocket connection lifecycle & messaging
    # ..................................................................
    "websocket_events": {
        "ddl": """CREATE TABLE IF NOT EXISTS websocket_events (
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
        TTL timestamp + INTERVAL 6 MONTH""",
        "columns": [
            "event_id UUID DEFAULT generateUUIDv4()",
            "timestamp DateTime DEFAULT now()",
            "connection_id String",
            "user_id Nullable(String)",
            "event_type LowCardinality(String)",
            "message_size UInt32",
            "direction LowCardinality(String)",
            "latency_ms Float32",
            "success UInt8",
            "error_code Nullable(String)",
            "protocol_version String",
        ],
        "ttl": "6 MONTH",
        "partition": "toYYYYMM(timestamp)",
        "order_by": "(timestamp, connection_id)",
        "engine": "MergeTree",
        "description": "WebSocket connection lifecycle & messaging",
    },

    # ..................................................................
    # ui_telemetry — Front-end user interaction telemetry
    # ..................................................................
    "ui_telemetry": {
        "ddl": """CREATE TABLE IF NOT EXISTS ui_telemetry (
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
        TTL timestamp + INTERVAL 12 MONTH""",
        "columns": [
            "event_id UUID DEFAULT generateUUIDv4()",
            "timestamp DateTime DEFAULT now()",
            "session_id String",
            "user_id Nullable(String)",
            "event_type LowCardinality(String)",
            "component String",
            "action String",
            "value Float32",
            "page String",
            "browser LowCardinality(String)",
            "device_type LowCardinality(String)",
            "os LowCardinality(String)",
            "screen_resolution String",
            "duration_ms Float32",
            "success UInt8",
        ],
        "ttl": "12 MONTH",
        "partition": "toYYYYMM(timestamp)",
        "order_by": "(timestamp, event_type)",
        "engine": "MergeTree",
        "description": "Front-end user interaction telemetry",
    },
}


# ---------------------------------------------------------------------------
# Materialized Views
# ---------------------------------------------------------------------------

MATERIALIZED_VIEWS: Dict[str, Dict[str, Any]] = {
    # ..................................................................
    # hourly_mesh_stats — Aggregates mesh_events by hour
    # ..................................................................
    "hourly_mesh_stats": {
        "target_table": "hourly_mesh_stats",
        "ddl": """CREATE MATERIALIZED VIEW IF NOT EXISTS hourly_mesh_stats
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
GROUP BY hour, event_type, status, mesh_type""",
        "source_table": "mesh_events",
        "description": "Hourly aggregation of mesh events by type and status",
    },

    # ..................................................................
    # daily_routing_summary — Aggregates routing_metrics by day
    # ..................................................................
    "daily_routing_summary": {
        "target_table": "daily_routing_summary",
        "ddl": """CREATE MATERIALIZED VIEW IF NOT EXISTS daily_routing_summary
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
GROUP BY day, mesh_type, protocol""",
        "source_table": "routing_metrics",
        "description": "Daily aggregation of routing metrics by mesh and protocol",
    },
}


# ---------------------------------------------------------------------------
# create_all_tables
# ---------------------------------------------------------------------------


async def create_all_tables(engine: AsimNexusEngine) -> Dict[str, bool]:
    """Create all ClickHouse tables and materialized views.

    Executes each DDL statement through the provided engine.
    Tables that already exist (``IF NOT EXISTS``) will be left untouched.

    Parameters
    ----------
    engine : AsimNexusEngine
        An initialised engine instance with an active connection.

    Returns
    -------
    Dict[str, bool]
        Mapping of table/view name to success status.
    """
    results: Dict[str, bool] = {}

    # --- Create base tables ---
    for table_name, table_def in TABLES.items():
        ddl = table_def["ddl"]
        try:
            result = await engine.query(ddl)
            results[table_name] = True
            logger.info("Table '%s' created successfully", table_name)
        except Exception as exc:
            logger.error("Failed to create table '%s': %s", table_name, exc)
            results[table_name] = False

    # --- Create materialized views ---
    for view_name, view_def in MATERIALIZED_VIEWS.items():
        ddl = view_def["ddl"]
        try:
            result = await engine.query(ddl)
            results[view_name] = True
            logger.info("Materialized view '%s' created successfully", view_name)
        except Exception as exc:
            logger.error(
                "Failed to create materialized view '%s': %s",
                view_name,
                exc,
            )
            results[view_name] = False

    return results
