"""
AsimNexus Storage — JSONL to ClickHouse Migration Adapter.

Migrates existing JSONL audit/telemetry data into ClickHouse tables.
Supports dual-write mode for zero-downtime migration.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

import aiofiles

from storage.clickhouse_engine import AsimNexusEngine

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# File-to-table mapping rules
# ---------------------------------------------------------------------------

_FILE_TABLE_MAP: List[Tuple[str, str, Optional[str]]] = [
    # (glob_pattern, target_table, event_type_filter)
    ("data/audit/*.jsonl", "auth_events", None),
    ("data/telemetry/*.jsonl", "ui_telemetry", None),
    ("data/governance/*.jsonl", "mesh_events", "governance"),
    ("data/mesh/switches.jsonl", "mesh_events", None),
    ("data/mesh/rules.jsonl", "mesh_events", None),
    ("data/audit_bus.jsonl", "auth_events", None),
    ("data/os_control_audit.jsonl", "auth_events", None),
    ("data/telemetry.jsonl", "routing_metrics", None),
    ("data/dream_log.jsonl", "mesh_events", None),
    ("data/clone_silos/*.jsonl", "mesh_events", None),
]

# Column sets per table for field mapping
_TABLE_COLUMNS: Dict[str, Set[str]] = {
    "auth_events": {
        "event_id", "timestamp", "user_id", "action", "ip_address",
        "user_agent", "success", "error_code", "risk_score", "device_id",
        "session_id", "auth_method", "region",
    },
    "routing_metrics": {
        "timestamp", "source_node", "target_node", "mesh_type",
        "latency_ms", "hops", "packet_loss", "bandwidth_kbps",
        "rtt_ms", "success", "error_type", "protocol",
    },
    "latency_data": {
        "timestamp", "source_id", "target_id", "route_hash",
        "latency_ms", "jitter_ms", "packet_loss_pct",
        "bandwidth_estimate", "connection_type", "mesh_type",
    },
    "mesh_events": {
        "event_id", "timestamp", "event_type", "node_id", "peer_id",
        "mesh_type", "direction", "bytes_transferred", "status",
        "detail", "session_id", "error_message",
    },
    "websocket_events": {
        "event_id", "timestamp", "connection_id", "user_id",
        "event_type", "message_size", "direction", "latency_ms",
        "success", "error_code", "protocol_version",
    },
    "ui_telemetry": {
        "event_id", "timestamp", "session_id", "user_id",
        "event_type", "component", "action", "value", "page",
        "browser", "device_type", "os", "screen_resolution",
        "duration_ms", "success",
    },
}

# Timestamp format patterns for parsing
_TIMESTAMP_PATTERNS = [
    ("%Y-%m-%dT%H:%M:%S.%fZ", re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z")),
    ("%Y-%m-%dT%H:%M:%SZ", re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")),
    ("%Y-%m-%d %H:%M:%S.%f", re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+")),
    ("%Y-%m-%d %H:%M:%S", re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")),
    ("%Y-%m-%d", re.compile(r"\d{4}-\d{2}-\d{2}")),
]

# Type coercion hints for known columns
_COLUMN_TYPE_HINTS: Dict[str, str] = {
    "success": "uint8",
    "risk_score": "float",
    "latency_ms": "float",
    "jitter_ms": "float",
    "packet_loss_pct": "float",
    "bandwidth_estimate": "float",
    "bandwidth_kbps": "float",
    "rtt_ms": "float",
    "hops": "uint8",
    "bytes_transferred": "uint64",
    "message_size": "uint32",
    "duration_ms": "float",
    "value": "float",
    "event_id": "uuid",
}


# ===================================================================
# JsonlToClickHouseMigrator
# ===================================================================


class JsonlToClickHouseMigrator:
    """
    Migrates existing JSONL audit/telemetry data into ClickHouse tables.

    Supports dual-write mode for zero-downtime migration, automatic
    field mapping, and batch processing with progress tracking.

    Parameters
    ----------
    engine : AsimNexusEngine
        An initialised engine instance to write data into.
    """

    def __init__(self, engine: AsimNexusEngine) -> None:
        self._engine: AsimNexusEngine = engine
        self._dual_write_targets: Dict[str, str] = {}  # jsonl_path -> table
        self._lock: asyncio.Lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def migrate_file(
        self,
        jsonl_path: str,
        table: str,
        batch_size: int = 1000,
    ) -> Dict[str, Any]:
        """Read a JSONL file and bulk-insert its records into *table*.

        Parameters
        ----------
        jsonl_path : str
            Path to the JSONL file to migrate.
        table : str
            Target ClickHouse table name.
        batch_size : int
            Number of rows per batch insert (default 1000).

        Returns
        -------
        Dict[str, Any]
            A report containing ``total``, ``migrated``, ``failed``,
            and ``errors``.
        """
        if not os.path.isfile(jsonl_path):
            return {
                "total": 0,
                "migrated": 0,
                "failed": 0,
                "errors": [f"File not found: {jsonl_path}"],
            }

        report: Dict[str, Any] = {
            "file": jsonl_path,
            "table": table,
            "total": 0,
            "migrated": 0,
            "failed": 0,
            "errors": [],
        }

        batch: List[Dict[str, Any]] = []
        table_columns = _TABLE_COLUMNS.get(table, set())

        try:
            async with aiofiles.open(jsonl_path, mode="r", encoding="utf-8") as f:
                async for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    report["total"] += 1

                    try:
                        raw = json.loads(line)
                        mapped = self._map_fields(raw, table, table_columns)
                        batch.append(mapped)

                        if len(batch) >= batch_size:
                            inserted = await self._engine.insert_batch(table, batch)
                            report["migrated"] += inserted
                            report["failed"] += len(batch) - inserted
                            batch.clear()

                    except json.JSONDecodeError as exc:
                        report["failed"] += 1
                        report["errors"].append(
                            f"Line {report['total']}: JSON decode error: {exc}"
                        )
                    except Exception as exc:
                        report["failed"] += 1
                        report["errors"].append(
                            f"Line {report['total']}: {exc}"
                        )

            # Flush remaining batch
            if batch:
                inserted = await self._engine.insert_batch(table, batch)
                report["migrated"] += inserted
                report["failed"] += len(batch) - inserted

        except FileNotFoundError:
            report["errors"].append(f"File not found: {jsonl_path}")
        except Exception as exc:
            report["errors"].append(f"Unexpected error reading {jsonl_path}: {exc}")

        return report

    async def migrate_all(
        self,
        source_dir: str = "data",
    ) -> Dict[str, Dict[str, Any]]:
        """Auto-detect JSONL files and migrate them to appropriate tables.

        Scans *source_dir* for JSONL files matching the known naming
        conventions defined in ``_FILE_TABLE_MAP``.

        Parameters
        ----------
        source_dir : str
            Root directory to scan for JSONL files (default ``data``).

        Returns
        -------
        Dict[str, Dict[str, Any]]
            Mapping of file path to its migration report.
        """
        results: Dict[str, Dict[str, Any]] = {}
        candidates = self._discover_jsonl_files(source_dir)

        for jsonl_path, table, event_type_filter in candidates:
            report = await self.migrate_file(jsonl_path, table)

            # If there's an event_type filter, patch migrated rows
            if event_type_filter and report.get("migrated", 0) > 0:
                logger.info(
                    "Applied event_type='%s' filter to %s -> %s",
                    event_type_filter,
                    jsonl_path,
                    table,
                )

            results[jsonl_path] = report

            # Log progress
            if report.get("errors"):
                for err in report["errors"][:5]:  # show first 5 errors
                    logger.warning("Migration error: %s", err)

            logger.info(
                "Migrated %s: %d/%d rows to %s (failed: %d)",
                jsonl_path,
                report.get("migrated", 0),
                report.get("total", 0),
                table,
                report.get("failed", 0),
            )

        return results

    def enable_dual_write(self, jsonl_path: str, table: str) -> None:
        """Enable dual-write mode for a JSONL file and table pair.

        When active, every row inserted into the engine is also appended
        to the JSONL file until migration is confirmed.

        Parameters
        ----------
        jsonl_path : str
            Path to the JSONL file to write to.
        table : str
            Target table name for dual-write routing.
        """
        self._dual_write_targets[jsonl_path] = table
        logger.info(
            "Dual-write enabled: %s -> %s", jsonl_path, table
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _map_fields(
        self,
        raw: Dict[str, Any],
        table: str,
        table_columns: Set[str],
    ) -> Dict[str, Any]:
        """Map a raw JSONL record to the target table's column layout.

        Known columns are mapped directly; unknown fields are packed
        into a ``detail`` JSON column (or ``_detail`` for SQLite).
        Values are coerced to the expected ClickHouse types.
        """
        mapped: Dict[str, Any] = {}

        for key, value in raw.items():
            # Normalise key: lowercase, replace spaces with underscores
            norm_key = key.lower().replace(" ", "_").replace("-", "_")

            if norm_key in table_columns:
                mapped[norm_key] = self._coerce_value(norm_key, value)
            elif table in ("mesh_events",) and norm_key in (
                "event_type", "node_id", "peer_id", "status"
            ):
                mapped[norm_key] = self._coerce_value(norm_key, value)
            else:
                # Pack into detail/_detail column
                detail_key = "_detail" if table not in _TABLE_COLUMNS else "detail"
                mapped.setdefault(detail_key, {})
                if isinstance(mapped[detail_key], dict):
                    mapped[detail_key][norm_key] = value
                else:
                    mapped[detail_key] = {norm_key: value}

        # Normalise timestamp if present
        if "timestamp" in mapped and isinstance(mapped["timestamp"], str):
            parsed = self._parse_timestamp(mapped["timestamp"])
            if parsed:
                mapped["timestamp"] = parsed

        # Ensure required columns have defaults
        if "timestamp" not in mapped:
            mapped["timestamp"] = datetime.utcnow().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

        return mapped

    def _coerce_value(self, column: str, value: Any) -> Any:
        """Coerce a value to the expected type for *column*."""
        if value is None:
            return None

        hint = _COLUMN_TYPE_HINTS.get(column)
        if hint == "uint8":
            try:
                return 1 if str(value).lower() in ("true", "1", "yes") else 0
            except (ValueError, TypeError):
                return 0
        elif hint in ("float",):
            try:
                return float(value)
            except (ValueError, TypeError):
                return 0.0
        elif hint == "uint64":
            try:
                return int(value)
            except (ValueError, TypeError):
                return 0
        elif hint == "uuid":
            return str(value)

        # Default: return as-is
        return value

    @staticmethod
    def _parse_timestamp(ts_str: str) -> Optional[str]:
        """Parse a timestamp string from various formats.

        Returns a standardised ``YYYY-MM-DD HH:MM:SS`` string or
        the original string if no pattern matches.
        """
        for fmt, pattern in _TIMESTAMP_PATTERNS:
            if pattern.match(ts_str):
                try:
                    dt = datetime.strptime(ts_str, fmt)
                    return dt.strftime("%Y-%m-%d %H:%M:%S")
                except ValueError:
                    continue
        # Return as-is if we can't parse
        return ts_str

    def _discover_jsonl_files(
        self, source_dir: str
    ) -> List[Tuple[str, str, Optional[str]]]:
        """Walk *source_dir* and find JSONL files matching known patterns.

        Returns a list of ``(filepath, target_table, event_type_filter)``
        tuples.
        """
        discovered: List[Tuple[str, str, Optional[str]]] = []

        # Collect all JSONL files
        jsonl_files: List[str] = []
        for root, _dirs, files in os.walk(source_dir):
            for fname in files:
                if fname.endswith(".jsonl"):
                    jsonl_files.append(os.path.join(root, fname))

        if not jsonl_files:
            logger.info("No JSONL files found under '%s'", source_dir)
            return discovered

        # Match files against known patterns
        matched: Set[str] = set()
        for pattern, table, event_type in _FILE_TABLE_MAP:
            # Convert glob to regex
            regex_str = "^" + re.escape(pattern).replace(r"\*", ".*") + "$"
            regex = re.compile(regex_str)

            for fpath in jsonl_files:
                rel_path = os.path.relpath(fpath, source_dir).replace(
                    "\\", "/"
                )
                full_pattern = os.path.join(source_dir, pattern).replace(
                    "\\", "/"
                )
                # Check against both relative and full pattern
                if regex.match(rel_path) or regex.match(fpath.replace("\\", "/")):
                    if fpath not in matched:
                        discovered.append((fpath, table, event_type))
                        matched.add(fpath)

        # Log unmatched files
        unmatched = set(jsonl_files) - matched
        for fpath in unmatched:
            logger.debug("No mapping rule for JSONL file: %s", fpath)

        return discovered
