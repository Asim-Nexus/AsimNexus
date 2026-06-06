#!/usr/bin/env python3
"""
AsimNexus Storage Migration Script.
Migrates from legacy storage (JSONL, in-memory, filesystem) to 4-layer architecture.

Usage:
    python scripts/migrate_storage.py --all          # Full migration
    python scripts/migrate_storage.py --clickhouse   # Phase 1: JSONL → ClickHouse
    python scripts/migrate_storage.py --oltp         # Phase 2: In-memory → OLTP
    python scripts/migrate_storage.py --object-store # Phase 3: Filesystem → Object Store
    python scripts/migrate_storage.py --vector       # Phase 4: Legacy vectors → VectorStore
    python scripts/migrate_storage.py --dry-run      # Preview without executing
    python scripts/migrate_storage.py --status       # Check migration status
    python scripts/migrate_storage.py --enable-dual-write  # Enable dual-write mode
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

try:
    import aiofiles
except ImportError:
    aiofiles = None  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# Ensure the project root is on sys.path so local imports work
# ---------------------------------------------------------------------------

_PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------

logger = logging.getLogger("asimnexus.migrate_storage")


# ===================================================================
# Progress helpers (lightweight, no tqdm dependency required)
# ===================================================================


def _print_progress(phase: str, current: int, total: int, suffix: str = "") -> None:
    """Print a simple progress line to stderr."""
    pct = (current / max(total, 1)) * 100
    bar_len = 40
    filled = int(bar_len * current / max(total, 1))
    bar = "█" * filled + "░" * (bar_len - filled)
    print(
        f"\r  [{bar}] {current}/{total} ({pct:.0f}%)  {suffix}",
        end="",
        file=sys.stderr,
    )
    if current >= total:
        print(file=sys.stderr)


def _print_header(title: str) -> None:
    """Print a section header."""
    width = 72
    print(f"\n{'=' * width}", file=sys.stderr)
    print(f"  {title}".ljust(width), file=sys.stderr)
    print(f"{'=' * width}", file=sys.stderr)


def _print_step(step: str, status: str = "✓", indent: int = 2) -> None:
    """Print a single step result."""
    prefix = " " * indent
    print(f"{prefix}{status} {step}", file=sys.stderr)


# ===================================================================
# Data classes for reporting
# ===================================================================


@dataclass
class PhaseReport:
    """Accumulated result for a single migration phase."""
    phase: str
    status: str = "pending"  # pending | running | completed | failed | skipped
    migrated: int = 0
    failed: int = 0
    errors: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    elapsed_seconds: float = 0.0


# ===================================================================
# Config loader (lightweight — uses the project's config module if
# available, otherwise falls back to raw yaml + env substitution)
# ===================================================================


def _load_config(path: str = "config/storage.yaml") -> Dict[str, Any]:
    """Load storage configuration, with env var substitution.

    Tries ``storage.config.load_storage_config`` first. Falls back to
    raw YAML parsing with manual ``${VAR:-default}`` substitution.
    """
    # Prefer the project's typed config loader
    try:
        from storage.config import load_storage_config as typed_load

        typed_cfg = typed_load(path)
        # Convert to plain dict for maximum compatibility in this script
        return _dataclass_to_dict(typed_cfg)
    except (ImportError, Exception) as exc:
        logger.debug("Typed config loader unavailable (%s), using raw YAML", exc)

    if yaml is None:
        print(
            "ERROR: PyYAML is required. Install with: pip install pyyaml",
            file=sys.stderr,
        )
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as f:
        raw: Dict[str, Any] = yaml.safe_load(f) or {}

    return _walk_and_substitute(raw)


def _dataclass_to_dict(obj: Any) -> Any:
    """Recursively convert a dataclass tree to plain dicts."""
    if hasattr(obj, "__dataclass_fields__"):
        return {
            f.name: _dataclass_to_dict(getattr(obj, f.name))
            for f in obj.__dataclass_fields__.values()
        }
    if isinstance(obj, dict):
        return {k: _dataclass_to_dict(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_dataclass_to_dict(item) for item in obj]
    return obj


_ENV_VAR_PATTERN = None


def _walk_and_substitute(obj: Any) -> Any:
    """Recursively substitute ``${VAR:-default}`` in strings."""
    import re

    pattern = re.compile(r"\$\{(?P<name>[^:}-]+)(?::-(?P<default>[^}]*))?\}")

    def _sub(value: str) -> str:
        def _replacer(m: re.Match) -> str:
            var_name = m.group("name")
            default = m.group("default")
            env_value = os.environ.get(var_name)
            if env_value is not None:
                return env_value
            if default is not None:
                return default
            return m.group(0)

        return pattern.sub(_replacer, value)

    if isinstance(obj, str):
        return _sub(obj) if "${" in obj else obj
    if isinstance(obj, dict):
        return {k: _walk_and_substitute(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_walk_and_substitute(item) for item in obj]
    return obj


# ===================================================================
# Phase 1: ClickHouse — JSONL to ClickHouse
# ===================================================================


async def _phase_clickhouse(
    config: Dict[str, Any],
    dry_run: bool = False,
    dual_write: bool = False,
) -> PhaseReport:
    """Migrate JSONL audit/telemetry files into ClickHouse tables."""
    report = PhaseReport(phase="clickhouse")
    ch_cfg = config.get("clickhouse", {})
    mg_cfg = config.get("migration", {})
    batch_size = int(mg_cfg.get("batch_size", 1000))

    if not ch_cfg.get("enabled", True):
        report.status = "skipped"
        _print_step("ClickHouse layer disabled in config, skipping", "∗")
        return report

    try:
        from storage.clickhouse_engine import AsimNexusEngine
        from storage.adapters.jsonl_migrator import JsonlToClickHouseMigrator

        _print_step(f"ClickHouse DSN: {ch_cfg.get('dsn', 'default')}")

        engine = AsimNexusEngine(dsn=ch_cfg.get("dsn", ""))

        if dry_run:
            _print_step("[DRY-RUN] Phase 1 — scanning JSONL sources...")

            # Discover what would be migrated
            migrator = JsonlToClickHouseMigrator(engine)
            # Replicate discovery logic from jsonl_migrator
            from storage.adapters.jsonl_migrator import (
                JsonlToClickHouseMigrator as _Migrator,
            )

            discovered = migrator._discover_jsonl_files("data")  # type: ignore[union-attr]
            if discovered:
                table_counts: Dict[str, int] = {}
                for fpath, table, _event_filter in discovered:
                    table_counts[table] = table_counts.get(table, 0) + 1
                    _print_step(f"  {fpath} → {table}", "·")
                for tbl, cnt in table_counts.items():
                    _print_step(
                        f"  Total: {cnt} file(s) → table '{tbl}'", "·"
                    )
                report.details["discovered_files"] = [
                    {"path": p, "table": t} for p, t, _ in discovered
                ]
            else:
                _print_step("No JSONL files discovered for migration", "·")

            report.status = "completed"
            return report

        # Connect engine
        await engine.connect()
        _print_step(
            f"Connected: mode={engine.mode}, connected={engine.connected}"
        )

        migrator = JsonlToClickHouseMigrator(engine)

        # Enable dual-write for all matched sources if requested
        if dual_write:
            sources = mg_cfg.get("sources", {})
            for src_key, src_pattern in sources.items():
                import glob as _glob

                for fpath in _glob.glob(src_pattern, recursive=True):
                    table = _infer_table_from_source_key(src_key)
                    migrator.enable_dual_write(fpath, table)
                    _print_step(f"Dual-write enabled: {fpath} → {table}", "·")

        # Run migration
        _print_step("Migrating JSONL files to ClickHouse...")
        start = time.monotonic()

        results = await migrator.migrate_all(source_dir="data")

        elapsed = time.monotonic() - start
        report.elapsed_seconds = elapsed

        # Aggregate results
        for fpath, fresult in results.items():
            report.migrated += fresult.get("migrated", 0)
            report.failed += fresult.get("failed", 0)
            errs = fresult.get("errors", [])
            report.errors.extend(errs[:5])  # keep first 5 per file
            report.details[fpath] = fresult

        await engine.close()

        if report.failed == 0 and report.errors:
            report.status = "completed"
        elif report.migrated > 0:
            report.status = "completed"
        else:
            report.status = "completed"  # nothing to migrate is still OK

    except Exception as exc:
        report.status = "failed"
        report.errors.append(str(exc))
        logger.error("Phase 1 (clickhouse) failed: %s", exc)

    return report


def _infer_table_from_source_key(source_key: str) -> str:
    """Map a migration source key to its target ClickHouse table."""
    mapping = {
        "jsonl_audit": "auth_events",
        "jsonl_telemetry": "ui_telemetry",
        "jsonl_governance": "mesh_events",
        "jsonl_mesh": "mesh_events",
        "jsonl_power_balance": "auth_events",
        "jsonl_personal_os": "auth_events",
    }
    return mapping.get(source_key, "auth_events")


# ===================================================================
# Phase 2: OLTP — In-memory to PostgreSQL
# ===================================================================


async def _phase_oltp(
    config: Dict[str, Any],
    dry_run: bool = False,
) -> PhaseReport:
    """Migrate in-memory data stores into OLTP tables."""
    report = PhaseReport(phase="oltp")
    ol_cfg = config.get("oltp", {})

    if not ol_cfg.get("enabled", True):
        report.status = "skipped"
        _print_step("OLTP layer disabled in config, skipping", "∗")
        return report

    try:
        from storage.oltp_engine import OltpEngine
        from storage.adapters.in_memory_migrator import InMemoryToOltpMigrator

        _print_step(f"OLTP DSN: {ol_cfg.get('dsn', 'default')}")

        engine = OltpEngine(dsn=ol_cfg.get("dsn", ""))

        if dry_run:
            _print_step("[DRY-RUN] Phase 2 — scanning in-memory sources...")
            _print_step(
                "  Will scan: economy (NexusCredits), governance, "
                "identity, node_registry, federation modules",
                "·",
            )
            _print_step(
                "  Pass modules to --oltp via import paths or run "
                "without --dry-run for auto-discovery",
                "·",
            )
            report.status = "completed"
            return report

        await engine.connect()
        _print_step(
            f"Connected: mode={engine.mode}, connected={engine.connected}"
        )

        migrator = InMemoryToOltpMigrator(engine)

        # Attempt to discover and migrate in-memory modules
        modules: Dict[str, Any] = {}

        # Try importing known modules
        _import_known_module(modules, "economy", "economy.nexus_credits", "NexusCredits")
        _import_known_module(
            modules,
            "governance",
            "core.blockchain.governance",
            "BlockchainGovernance",
        )
        _import_known_module(
            modules, "identity", "auth.identity_provider", "IdentityProvider"
        )
        _import_known_module(
            modules, "node_registry", "mesh.node_registry", "NodeRegistry"
        )
        _import_known_module(
            modules, "federation", "core.federation.global_federation", "GlobalFederation"
        )

        if not modules:
            _print_step(
                "No in-memory modules found. "
                "Phase 2 will be limited to what exists.",
                "·",
            )

        start = time.monotonic()

        results = await migrator.migrate_all(modules)

        elapsed = time.monotonic() - start
        report.elapsed_seconds = elapsed
        report.details = results

        # Aggregate
        for mod_name, mod_result in results.items():
            # Count all numeric migration fields
            for key, value in mod_result.items():
                if key.endswith("_migrated") and isinstance(value, (int, float)):
                    report.migrated += int(value)
                elif key == "errors" and isinstance(value, list):
                    report.errors.extend(value[:5])

        await engine.close()
        report.status = "completed"

    except Exception as exc:
        report.status = "failed"
        report.errors.append(str(exc))
        logger.error("Phase 2 (oltp) failed: %s", exc)

    return report


def _import_known_module(
    modules: Dict[str, Any],
    name: str,
    import_path: str,
    class_name: str,
) -> None:
    """Try to import a module and instantiate its main class (if any)."""
    try:
        import importlib

        mod = importlib.import_module(import_path)
        cls = getattr(mod, class_name, None)
        if cls is not None:
            # Try to instantiate if it's a class (not a module)
            if isinstance(cls, type):
                try:
                    instance = cls()
                    modules[name] = instance
                    _print_step(
                        f"  Found {name}: {import_path}.{class_name}()",
                        "·",
                    )
                except Exception:
                    # Some classes need args; just store the class ref
                    modules[name] = cls
                    _print_step(
                        f"  Found {name}: {import_path}.{class_name} (class ref)",
                        "·",
                    )
            else:
                modules[name] = cls
                _print_step(
                    f"  Found {name}: {import_path}.{class_name}",
                    "·",
                )
    except (ImportError, AttributeError) as exc:
        logger.debug("Module %s (%s) not available: %s", name, import_path, exc)


# ===================================================================
# Phase 3: Object Store — Filesystem to S3/MinIO
# ===================================================================


async def _phase_object_store(
    config: Dict[str, Any],
    dry_run: bool = False,
) -> PhaseReport:
    """Migrate local files into object store (S3/MinIO or local fallback)."""
    report = PhaseReport(phase="object_store")
    os_cfg = config.get("object_store", {})

    if not os_cfg.get("enabled", True):
        report.status = "skipped"
        _print_step("Object store layer disabled in config, skipping", "∗")
        return report

    try:
        from storage.object_store import ObjectStore

        store = ObjectStore(
            endpoint=os_cfg.get("endpoint"),
            access_key=os_cfg.get("access_key"),
            secret_key=os_cfg.get("secret_key"),
            region=os_cfg.get("region", "auto"),
            bucket_prefix=os_cfg.get("bucket_prefix", "asimnexus"),
            local_path=os_cfg.get("fallback", {}).get("path", "data/object_store"),
        )

        if dry_run:
            _print_step("[DRY-RUN] Phase 3 — scanning local files for upload...")
            buckets = os_cfg.get("buckets", [])
            _print_step(
                f"  Will upload data to {len(buckets)} bucket(s): {', '.join(buckets)}",
                "·",
            )

            # Scan common local data directories
            local_dirs = [
                "data/audit",
                "data/telemetry",
                "data/mesh",
                "data/exports",
                "data/snapshots",
                "data/backups",
            ]
            total_files = 0
            for d in local_dirs:
                if os.path.isdir(d):
                    files = [
                        os.path.join(dp, f)
                        for dp, _dn, fns in os.walk(d)
                        for f in fns
                        if not f.endswith(".meta.json")
                    ]
                    total_files += len(files)
                    if files:
                        _print_step(f"  {d}: {len(files)} file(s)", "·")

            _print_step(f"  Total files to migrate: {total_files}", "·")
            report.details["files_found"] = total_files
            report.status = "completed"
            return report

        await store.connect()
        _print_step(
            f"Connected: mode={store.mode}, connected={store.connected}"
        )

        buckets = os_cfg.get("buckets", [])
        if not buckets:
            _print_step("No buckets configured, using defaults", "·")
            from storage.object_store import DEFAULT_BUCKETS

            buckets = DEFAULT_BUCKETS

        # Ensure all buckets exist
        for bucket in buckets:
            await store.create_bucket(bucket)

        start = time.monotonic()

        # Migrate local files into the appropriate buckets
        local_mappings = _get_object_store_mappings()
        total_migrated = 0
        total_failed = 0

        for local_dir, bucket in local_mappings:
            if not os.path.isdir(local_dir):
                continue

            for root_str, _dirs, files in os.walk(local_dir):
                for fname in files:
                    if fname.endswith(".meta.json"):
                        continue
                    fpath = os.path.join(root_str, fname)
                    # Compute object key as relative path from local_dir
                    rel_path = os.path.relpath(fpath, local_dir).replace(
                        "\\", "/"
                    )
                    try:
                        async with aiofiles.open(fpath, mode="rb") as f:
                            data = await f.read()
                        ok = await store.upload(bucket, rel_path, data)
                        if ok:
                            total_migrated += 1
                        else:
                            total_failed += 1
                            report.errors.append(
                                f"Upload failed: {fpath} → {bucket}/{rel_path}"
                            )
                    except Exception as exc:
                        total_failed += 1
                        report.errors.append(f"Upload error: {fpath}: {exc}")

        elapsed = time.monotonic() - start
        report.elapsed_seconds = elapsed
        report.migrated = total_migrated
        report.failed = total_failed
        report.details["buckets"] = buckets

        await store.close()
        report.status = "completed"

    except Exception as exc:
        report.status = "failed"
        report.errors.append(str(exc))
        logger.error("Phase 3 (object_store) failed: %s", exc)

    return report


def _get_object_store_mappings() -> List[str, str]:
    """Return (local_dir, bucket) pairs for Phase 3 migration."""
    return [
        ("data/audit", "raw-logs"),
        ("data/telemetry", "raw-logs"),
        ("data/mesh", "raw-logs"),
        ("data/exports", "exports"),
        ("data/snapshots", "snapshots"),
        ("data/backups", "backups"),
    ]


# ===================================================================
# Phase 4: Vector — Legacy vectors to VectorStore
# ===================================================================


async def _phase_vector(
    config: Dict[str, Any],
    dry_run: bool = False,
) -> PhaseReport:
    """Migrate existing vector/embedding data into VectorStore."""
    report = PhaseReport(phase="vector")
    vdb_cfg = config.get("vector_db", {})

    if not vdb_cfg.get("enabled", True):
        report.status = "skipped"
        _print_step("Vector DB layer disabled in config, skipping", "∗")
        return report

    try:
        from storage.vector_store import VectorStore
        from storage.adapters.vector_migrator import VectorDataMigrator

        store = VectorStore(
            chromadb_path=vdb_cfg.get("path", "data/chromadb"),
        )

        if dry_run:
            _print_step("[DRY-RUN] Phase 4 — scanning vector sources...")

            # Check if legacy vectormemory DB exists
            legacy_db = os.getenv(
                "ASIM_VECTOR_DB_PATH", "data/vector_memory.db"
            )
            if os.path.isfile(legacy_db):
                _print_step(
                    f"  Found legacy vectormemory DB: {legacy_db}", "·"
                )

            # Check ChromaDB data
            chroma_path = vdb_cfg.get("path", "data/chromadb")
            if os.path.isdir(chroma_path):
                _print_step(
                    f"  Found existing ChromaDB data: {chroma_path}", "·"
                )

            # Scan JSONL files for vector content
            import glob

            jsonl_files = glob.glob("data/**/*.jsonl", recursive=True)
            if jsonl_files:
                _print_step(
                    f"  Found {len(jsonl_files)} JSONL file(s) with potential vector content",
                    "·",
                )

            report.status = "completed"
            return report

        await store.connect()
        _print_step(
            f"Connected: mode={store._mode}, "
            f"connected={store.connected}"
        )

        migrator = VectorDataMigrator(store)

        start = time.monotonic()

        results = await migrator.migrate_all()

        elapsed = time.monotonic() - start
        report.elapsed_seconds = elapsed
        report.details = results

        # Aggregate
        for src_name, src_result in results.items():
            if isinstance(src_result, dict):
                report.migrated += src_result.get("total", 0)
                errs = src_result.get("errors", [])
                report.errors.extend(errs[:5])
                report.details[src_name] = src_result

        await store.close()
        report.status = "completed"

    except Exception as exc:
        report.status = "failed"
        report.errors.append(str(exc))
        logger.error("Phase 4 (vector) failed: %s", exc)

    return report


# ===================================================================
# Status check
# ===================================================================


async def _check_status(config: Dict[str, Any]) -> PhaseReport:
    """Check which tables/collections already have data vs empty."""
    report = PhaseReport(phase="status")

    _print_header("Storage Status Check")

    try:
        # --- ClickHouse status ---
        ch_cfg = config.get("clickhouse", {})
        if ch_cfg.get("enabled", True):
            _print_step("ClickHouse:")
            try:
                from storage.clickhouse_engine import AsimNexusEngine

                engine = AsimNexusEngine(dsn=ch_cfg.get("dsn", ""))
                await engine.connect()
                _print_step(f"  Mode: {engine.mode}", "·")
                _print_step(f"  Connected: {engine.connected}", "·")

                tables = ch_cfg.get("tables", {})
                for tbl_name in tables:
                    try:
                        result = await engine.query(
                            f"SELECT count(*) as cnt FROM {tbl_name}"
                        )
                        count = result[0]["cnt"] if result else 0
                        status = "has data" if count > 0 else "empty"
                        _print_step(f"  {tbl_name}: {count} rows ({status})", "·")
                        report.details[f"clickhouse.{tbl_name}"] = count
                    except Exception as exc:
                        _print_step(f"  {tbl_name}: error — {exc}", "⚠")

                await engine.close()
            except Exception as exc:
                _print_step(f"  Error connecting: {exc}", "⚠")
        else:
            _print_step("ClickHouse: disabled", "∗")

        # --- OLTP status ---
        ol_cfg = config.get("oltp", {})
        if ol_cfg.get("enabled", True):
            _print_step("OLTP:")
            try:
                from storage.oltp_engine import OltpEngine

                engine = OltpEngine(dsn=ol_cfg.get("dsn", ""))
                await engine.connect()
                _print_step(f"  Mode: {engine.mode}", "·")

                tables = ol_cfg.get("tables", [])
                for tbl in tables:
                    try:
                        result = await engine.query(
                            f"SELECT count(*) as cnt FROM {tbl}"
                        )
                        count = result[0]["cnt"] if result else 0
                        status = "has data" if count > 0 else "empty"
                        _print_step(f"  {tbl}: {count} rows ({status})", "·")
                        report.details[f"oltp.{tbl}"] = count
                    except Exception as exc:
                        _print_step(f"  {tbl}: error — {exc}", "⚠")

                await engine.close()
            except Exception as exc:
                _print_step(f"  Error connecting: {exc}", "⚠")
        else:
            _print_step("OLTP: disabled", "∗")

        # --- Object store status ---
        os_cfg = config.get("object_store", {})
        if os_cfg.get("enabled", True):
            _print_step("Object Store:")
            try:
                from storage.object_store import ObjectStore

                store = ObjectStore(
                    endpoint=os_cfg.get("endpoint"),
                    access_key=os_cfg.get("access_key"),
                    secret_key=os_cfg.get("secret_key"),
                    region=os_cfg.get("region", "auto"),
                    bucket_prefix=os_cfg.get(
                        "bucket_prefix", "asimnexus"
                    ),
                    local_path=os_cfg.get("fallback", {}).get(
                        "path", "data/object_store"
                    ),
                )
                await store.connect()
                _print_step(f"  Mode: {store.mode}", "·")

                buckets = os_cfg.get("buckets", [])
                for bucket in buckets:
                    try:
                        objects = await store.list(bucket)
                        status = (
                            f"has {len(objects)} object(s)"
                            if objects
                            else "empty"
                        )
                        _print_step(f"  {bucket}: {status}", "·")
                        report.details[f"object_store.{bucket}"] = len(objects)
                    except Exception as exc:
                        _print_step(f"  {bucket}: error — {exc}", "⚠")

                await store.close()
            except Exception as exc:
                _print_step(f"  Error connecting: {exc}", "⚠")
        else:
            _print_step("Object Store: disabled", "∗")

        # --- Vector DB status ---
        vdb_cfg = config.get("vector_db", {})
        if vdb_cfg.get("enabled", True):
            _print_step("Vector DB:")
            try:
                from storage.vector_store import VectorStore

                store = VectorStore(
                    chromadb_path=vdb_cfg.get("path", "data/chromadb"),
                )
                await store.connect()
                _print_step(f"  Mode: {store._mode}", "·")

                collections = vdb_cfg.get("collections", {})
                for col_name in collections:
                    try:
                        count = await store.count(collection=col_name)
                        status = (
                            "has data" if count > 0 else "empty"
                        )
                        _print_step(f"  {col_name}: {count} item(s) ({status})", "·")
                        report.details[f"vector_db.{col_name}"] = count
                    except Exception as exc:
                        _print_step(f"  {col_name}: error — {exc}", "⚠")

                await store.close()
            except Exception as exc:
                _print_step(f"  Error connecting: {exc}", "⚠")
        else:
            _print_step("Vector DB: disabled", "∗")

        report.status = "completed"

    except Exception as exc:
        report.status = "failed"
        report.errors.append(str(exc))
        logger.error("Status check failed: %s", exc)

    return report


# ===================================================================
# Enable dual-write
# ===================================================================


def _enable_dual_write(config_path: str = "config/storage.yaml") -> PhaseReport:
    """Set ``migration.dual_write=true`` in the config file."""
    report = PhaseReport(phase="enable_dual_write")

    try:
        if yaml is None:
            raise ImportError("PyYAML is required")

        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        # Ensure migration section exists
        if "migration" not in data:
            data["migration"] = {}
        data["migration"]["dual_write"] = True

        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

        _print_step(
            f"Set migration.dual_write=true in {config_path}", "✓"
        )
        report.status = "completed"

    except Exception as exc:
        report.status = "failed"
        report.errors.append(str(exc))
        logger.error("Failed to enable dual-write: %s", exc)

    return report


# ===================================================================
# Summary printer
# ===================================================================


def _print_summary(reports: List[PhaseReport]) -> None:
    """Print a human-readable summary of all completed phases."""
    _print_header("Migration Summary")

    summary: Dict[str, Dict[str, Any]] = {}

    for r in reports:
        summary[r.phase] = {
            "status": r.status,
            "migrated": r.migrated,
            "failed": r.failed,
            "elapsed_seconds": round(r.elapsed_seconds, 2),
            "errors": r.errors[:3],  # show max 3 errors per phase
        }

        icon = {"completed": "✓", "failed": "✗", "skipped": "∗", "pending": "·"}.get(
            r.status, "?"
        )
        elapsed_str = f" [{r.elapsed_seconds:.1f}s]" if r.elapsed_seconds else ""
        print(
            f"  {icon} {r.phase}: "
            f"migrated={r.migrated}, "
            f"failed={r.failed}"
            f"{elapsed_str}",
            file=sys.stderr,
        )

        if r.errors:
            for err in r.errors[:3]:
                print(f"       ⚠ {err}", file=sys.stderr)

    # JSON summary on stdout for programmatic consumption
    print(json.dumps(summary, indent=2))


# ===================================================================
# CLI
# ===================================================================


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="AsimNexus Storage Migration Script — "
        "migrate from legacy storage to 4-layer architecture.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python scripts/migrate_storage.py --all           "
            "Full migration\n"
            "  python scripts/migrate_storage.py --clickhouse   "
            "Phase 1 only\n"
            "  python scripts/migrate_storage.py --status       "
            "Check current status\n"
            "  python scripts/migrate_storage.py --dry-run      "
            "Preview without executing\n"
            "  python scripts/migrate_storage.py "
            "--enable-dual-write  Enable dual-write mode\n"
        ),
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all 4 migration phases in dependency order",
    )
    parser.add_argument(
        "--clickhouse",
        action="store_true",
        help="Phase 1: Migrate JSONL → ClickHouse",
    )
    parser.add_argument(
        "--oltp",
        action="store_true",
        help="Phase 2: Migrate in-memory → OLTP (PostgreSQL)",
    )
    parser.add_argument(
        "--object-store",
        action="store_true",
        dest="object_store",
        help="Phase 3: Migrate filesystem → Object Store (S3/MinIO)",
    )
    parser.add_argument(
        "--vector",
        action="store_true",
        help="Phase 4: Migrate legacy vectors → VectorStore",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        dest="dry_run",
        help="Scan sources and report what would be migrated, but don't execute",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Check which tables/collections already have data vs empty",
    )
    parser.add_argument(
        "--enable-dual-write",
        action="store_true",
        dest="enable_dual_write",
        help="Set migration.dual_write=true in config for zero-downtime migration",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/storage.yaml",
        help="Path to storage configuration YAML (default: config/storage.yaml)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Set logging level (default: INFO)",
    )

    return parser


async def _main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Handle --enable-dual-write (synchronous file edit, no async needed)
    if args.enable_dual_write:
        report = _enable_dual_write(config_path=args.config)
        _print_summary([report])
        sys.exit(0 if report.status == "completed" else 1)

    # Load config
    try:
        config = _load_config(args.config)
    except FileNotFoundError:
        print(
            f"ERROR: Configuration file not found: {args.config}",
            file=sys.stderr,
        )
        sys.exit(1)
    except Exception as exc:
        print(
            f"ERROR: Failed to load configuration: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)

    # Handle --status
    if args.status:
        report = await _check_status(config)
        _print_summary([report])
        sys.exit(0 if report.status == "completed" else 1)

    # Determine which phases to run
    phases_to_run: List[str] = []
    if args.all:
        phases_to_run = ["clickhouse", "oltp", "object_store", "vector"]
    else:
        if args.clickhouse:
            phases_to_run.append("clickhouse")
        if args.oltp:
            phases_to_run.append("oltp")
        if args.object_store:
            phases_to_run.append("object_store")
        if args.vector:
            phases_to_run.append("vector")

    if not phases_to_run:
        parser.print_help()
        print(
            "\nNo migration phases specified. Use --all or one of: "
            "--clickhouse, --oltp, --object-store, --vector",
            file=sys.stderr,
        )
        sys.exit(1)

    # Run phases
    reports: List[PhaseReport] = []
    phase_map = {
        "clickhouse": ("Phase 1: JSONL → ClickHouse", _phase_clickhouse),
        "oltp": ("Phase 2: In-memory → OLTP", _phase_oltp),
        "object_store": ("Phase 3: Filesystem → Object Store", _phase_object_store),
        "vector": ("Phase 4: Legacy vectors → VectorStore", _phase_vector),
    }

    overall_exit_code = 0

    for phase_key in phases_to_run:
        title, phase_fn = phase_map[phase_key]
        _print_header(title)

        report = await phase_fn(config, dry_run=args.dry_run)
        reports.append(report)

        if report.status == "failed":
            overall_exit_code = 1

        _print_step(
            f"Status: {report.status}, "
            f"migrated={report.migrated}, "
            f"failed={report.failed}",
            "✓" if report.status == "completed" else "✗",
        )

    # Print summary
    _print_summary(reports)
    sys.exit(overall_exit_code)


# ===================================================================
# Entry point
# ===================================================================


def main() -> None:
    """Synchronous entry point for ``python -m scripts.migrate_storage``."""
    try:
        asyncio.run(_main())
    except KeyboardInterrupt:
        print("\nInterrupted by user.", file=sys.stderr)
        sys.exit(130)


if __name__ == "__main__":
    main()
