"""
database/migrations/manager.py
AsimNexus — Schema Migration Manager

A lightweight, Alembic-style migration framework for SQLite.
Supports:
  - Versioned, ordered migrations
  - Automatic pending migration detection
  - Rollback (reverse migrations)
  - Dry-run mode
  - Integration with DBManager

Usage:
    from database.migrations.manager import MigrationManager
    mgr = MigrationManager()
    mgr.run_pending()           # Apply all pending migrations
    mgr.rollback(version=3)     # Rollback to version 3
    mgr.list_migrations()       # Show all migrations with status
"""

import json
import logging
import os
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("AsimNexus.DB.Migration")

_DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "asimnexus.db"


# ── Migration Definition ──────────────────────────────────────────────────

class Migration:
    """A single schema migration with forward and optional reverse."""

    def __init__(
        self,
        version: int,
        description: str,
        up: List[str],
        down: Optional[List[str]] = None,
        dependencies: Optional[List[int]] = None,
    ):
        self.version = version
        self.description = description
        self.up = up          # SQL statements to apply
        self.down = down or []  # SQL statements to revert
        self.dependencies = dependencies or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "description": self.description,
            "up_count": len(self.up),
            "down_count": len(self.down),
            "dependencies": self.dependencies,
        }


# ── Migration Manager ─────────────────────────────────────────────────────

class MigrationManager:
    """Manages schema migrations for the AsimNexus SQLite database."""

    def __init__(self, db_path: str = str(_DEFAULT_DB_PATH)):
        self.db_path = Path(db_path)
        self._migrations: Dict[int, Migration] = {}
        self._load_migrations()

    # ── Public API ───────────────────────────────────────────────────────

    def run_pending(self, dry_run: bool = False) -> List[Dict[str, Any]]:
        """Detect and apply all pending migrations in order.

        Args:
            dry_run: If True, only report what would be applied.

        Returns:
            List of result dicts with keys: version, description, success, error
        """
        applied = self._get_applied_versions()
        results = []

        for version in sorted(self._migrations.keys()):
            if version in applied:
                continue
            migration = self._migrations[version]

            # Check dependencies
            missing_deps = [
                d for d in migration.dependencies if d not in applied
            ]
            if missing_deps:
                results.append({
                    "version": version,
                    "description": migration.description,
                    "success": False,
                    "error": f"Missing dependencies: {missing_deps}",
                })
                continue

            if dry_run:
                logger.info("[DRY RUN] Would apply v%d: %s", version, migration.description)
                results.append({
                    "version": version,
                    "description": migration.description,
                    "success": True,
                    "dry_run": True,
                })
                continue

            # Apply migration
            try:
                self._apply_migration(migration)
                logger.info("Applied v%d: %s", version, migration.description)
                results.append({
                    "version": version,
                    "description": migration.description,
                    "success": True,
                })
            except Exception as exc:
                logger.error("Failed v%d: %s — %s", version, migration.description, exc)
                results.append({
                    "version": version,
                    "description": migration.description,
                    "success": False,
                    "error": str(exc),
                })
                break  # Stop on first failure

        return results

    def rollback(self, target_version: int = 0,
                 dry_run: bool = False) -> List[Dict[str, Any]]:
        """Rollback migrations to a target version.

        Args:
            target_version: Rollback to this version (exclusive).
                            Use 0 to rollback all.
            dry_run: If True, only report what would be rolled back.

        Returns:
            List of result dicts.
        """
        applied = sorted(self._get_applied_versions(), reverse=True)
        results = []

        for version in applied:
            if version <= target_version:
                break
            migration = self._migrations.get(version)
            if not migration:
                results.append({
                    "version": version,
                    "success": False,
                    "error": f"Migration definition not found for v{version}",
                })
                continue

            if not migration.down:
                results.append({
                    "version": version,
                    "description": migration.description,
                    "success": False,
                    "error": "No reverse migration defined",
                })
                continue

            if dry_run:
                logger.info("[DRY RUN] Would rollback v%d: %s", version, migration.description)
                results.append({
                    "version": version,
                    "description": migration.description,
                    "success": True,
                    "dry_run": True,
                })
                continue

            try:
                self._rollback_migration(migration)
                logger.info("Rolled back v%d: %s", version, migration.description)
                results.append({
                    "version": version,
                    "description": migration.description,
                    "success": True,
                })
            except Exception as exc:
                logger.error("Rollback failed v%d: %s", version, exc)
                results.append({
                    "version": version,
                    "description": migration.description,
                    "success": False,
                    "error": str(exc),
                })
                break

        return results

    def list_migrations(self) -> List[Dict[str, Any]]:
        """List all registered migrations with their applied status."""
        applied = self._get_applied_versions()
        results = []
        for version in sorted(self._migrations.keys()):
            mig = self._migrations[version]
            results.append({
                "version": version,
                "description": mig.description,
                "applied": version in applied,
                "has_rollback": len(mig.down) > 0,
                "dependencies": mig.dependencies,
            })
        return results

    def get_current_version(self) -> int:
        """Return the highest applied migration version."""
        applied = self._get_applied_versions()
        return max(applied) if applied else 0

    def get_pending_versions(self) -> List[int]:
        """Return list of pending migration versions."""
        applied = self._get_applied_versions()
        return sorted([
            v for v in self._migrations.keys() if v not in applied
        ])

    def create_migration_file(self, version: int, description: str,
                              up_statements: List[str],
                              down_statements: Optional[List[str]] = None) -> str:
        """Generate a migration file on disk for manual editing.

        Returns the filepath of the created migration file.
        """
        migrations_dir = Path(__file__).parent / "versions"
        migrations_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{version:04d}_{description.lower().replace(' ', '_')}.json"
        filepath = migrations_dir / filename

        content = {
            "version": version,
            "description": description,
            "up": up_statements,
            "down": down_statements or [],
            "created_at": datetime.utcnow().isoformat() + "Z",
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(content, f, indent=2)

        logger.info("Migration file created: %s", filepath)
        return str(filepath)

    # ── Internals ────────────────────────────────────────────────────────

    def _get_applied_versions(self) -> set:
        """Query the schema_version table for applied versions."""
        if not self.db_path.exists():
            return set()
        try:
            conn = sqlite3.connect(str(self.db_path))
            row = conn.execute(
                "SELECT GROUP_CONCAT(version) FROM schema_version"
            ).fetchone()
            conn.close()
            if row and row[0]:
                return set(int(v) for v in row[0].split(","))
            return set()
        except (sqlite3.OperationalError, ValueError):
            return set()

    def _apply_migration(self, migration: Migration) -> None:
        """Apply a single migration within a transaction."""
        conn = sqlite3.connect(str(self.db_path))
        try:
            conn.execute("BEGIN")
            for stmt in migration.up:
                conn.execute(stmt)
            conn.execute(
                "INSERT INTO schema_version (version, description) VALUES (?, ?)",
                (migration.version, migration.description),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _rollback_migration(self, migration: Migration) -> None:
        """Rollback a single migration within a transaction."""
        conn = sqlite3.connect(str(self.db_path))
        try:
            conn.execute("BEGIN")
            for stmt in migration.down:
                conn.execute(stmt)
            conn.execute(
                "DELETE FROM schema_version WHERE version = ?",
                (migration.version,),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _load_migrations(self) -> None:
        """Load all registered migrations into the internal registry.

        Migrations are loaded from:
          1. The hardcoded _REGISTERED_MIGRATIONS list below
          2. JSON files in database/migrations/versions/ directory
        """
        # Load hardcoded migrations
        for mig in _REGISTERED_MIGRATIONS:
            self._migrations[mig.version] = mig

        # Load version files from disk
        versions_dir = Path(__file__).parent / "versions"
        if versions_dir.exists():
            for fpath in sorted(versions_dir.glob("*.json")):
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    mig = Migration(
                        version=data["version"],
                        description=data["description"],
                        up=data.get("up", []),
                        down=data.get("down", []),
                        dependencies=data.get("dependencies", []),
                    )
                    # File-based migrations override hardcoded ones
                    self._migrations[mig.version] = mig
                except (json.JSONDecodeError, KeyError) as exc:
                    logger.warning("Skipping invalid migration file %s: %s", fpath.name, exc)


# ── Registered Migrations ─────────────────────────────────────────────────
# These are the canonical migrations for the AsimNexus database.
# They are loaded into the MigrationManager on construction.

_REGISTERED_MIGRATIONS: List[Migration] = [
    Migration(
        version=1,
        description="Initial schema — conversations, api_keys, schema_version",
        up=[
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
        down=[
            "DROP TABLE IF EXISTS api_keys",
            "DROP TABLE IF EXISTS conversations",
        ],
    ),
    Migration(
        version=2,
        description="Add self_awareness_knowledge table",
        up=[
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
        down=[
            "DROP TABLE IF EXISTS self_awareness_knowledge",
        ],
    ),
    Migration(
        version=3,
        description="Add build_actions table for SelfBuilder persistence",
        up=[
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
        down=[
            "DROP TABLE IF EXISTS build_actions",
        ],
    ),
    Migration(
        version=4,
        description="Add mirror_reflections table for MirrorModule persistence",
        up=[
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
        down=[
            "DROP TABLE IF EXISTS mirror_reflections",
        ],
    ),
    Migration(
        version=5,
        description="Add evolution_suggestions table for EvolutionEngine persistence",
        up=[
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
        down=[
            "DROP TABLE IF EXISTS evolution_suggestions",
        ],
    ),
    Migration(
        version=6,
        description="Add dream_cycles table for DreamingEngine persistence",
        up=[
            """CREATE TABLE IF NOT EXISTS dream_cycles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cycle_id TEXT UNIQUE NOT NULL,
                lessons_count INTEGER DEFAULT 0,
                pruned_count INTEGER DEFAULT 0,
                bug_stats TEXT,
                started_at TEXT NOT NULL DEFAULT (datetime('now')),
                completed_at TEXT
            )""",
            "CREATE INDEX IF NOT EXISTS idx_dream_cycles_started ON dream_cycles(started_at)",
        ],
        down=[
            "DROP TABLE IF EXISTS dream_cycles",
        ],
    ),
    Migration(
        version=7,
        description="Add mesh_nodes table for MeshCoordinator persistence",
        up=[
            """CREATE TABLE IF NOT EXISTS mesh_nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                node_id TEXT UNIQUE NOT NULL,
                node_type TEXT,
                address TEXT,
                country TEXT,
                tier TEXT DEFAULT 'full',
                state TEXT DEFAULT 'disconnected',
                last_seen TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )""",
            "CREATE INDEX IF NOT EXISTS idx_mesh_nodes_type ON mesh_nodes(node_type)",
            "CREATE INDEX IF NOT EXISTS idx_mesh_nodes_state ON mesh_nodes(state)",
        ],
        down=[
            "DROP TABLE IF EXISTS mesh_nodes",
        ],
    ),
    Migration(
        version=8,
        description="Add security_events table for audit logging",
        up=[
            """CREATE TABLE IF NOT EXISTS security_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT UNIQUE NOT NULL,
                event_type TEXT NOT NULL,
                user_id TEXT,
                ip_address TEXT,
                details TEXT,
                severity TEXT DEFAULT 'info',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )""",
            "CREATE INDEX IF NOT EXISTS idx_security_events_type ON security_events(event_type)",
            "CREATE INDEX IF NOT EXISTS idx_security_events_created ON security_events(created_at)",
        ],
        down=[
            "DROP TABLE IF EXISTS security_events",
        ],
    ),
]


# ── Convenience ───────────────────────────────────────────────────────────

def get_migration_manager(db_path: Optional[str] = None) -> MigrationManager:
    """Get a MigrationManager instance."""
    return MigrationManager(db_path=db_path or str(_DEFAULT_DB_PATH))


def run_pending_migrations(db_path: Optional[str] = None,
                           dry_run: bool = False) -> List[Dict[str, Any]]:
    """Convenience: create manager and run pending migrations."""
    mgr = get_migration_manager(db_path)
    return mgr.run_pending(dry_run=dry_run)


# ── CLI ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="AsimNexus Migration Manager")
    parser.add_argument("--db-path", default=str(_DEFAULT_DB_PATH))
    parser.add_argument("--dry-run", action="store_true", help="Dry run only")

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("list", help="List all migrations")
    subparsers.add_parser("pending", help="Show pending migrations")
    subparsers.add_parser("run", help="Run pending migrations")

    rollback_parser = subparsers.add_parser("rollback", help="Rollback migrations")
    rollback_parser.add_argument("--to", type=int, default=0, help="Target version")

    create_parser = subparsers.add_parser("create", help="Create a migration file")
    create_parser.add_argument("--version", type=int, required=True)
    create_parser.add_argument("--description", type=str, required=True)
    create_parser.add_argument("--up", type=str, nargs="+", required=True,
                               help="SQL statements for forward migration")
    create_parser.add_argument("--down", type=str, nargs="*",
                               help="SQL statements for rollback")

    args = parser.parse_args()
    mgr = get_migration_manager(args.db_path)

    if args.command == "list":
        for m in mgr.list_migrations():
            status = "APPLIED" if m["applied"] else "PENDING"
            rb = " [rollback]" if m["has_rollback"] else ""
            print(f"  v{m['version']:3d}  {status:8s}  {m['description']}{rb}")

    elif args.command == "pending":
        pending = mgr.get_pending_versions()
        if pending:
            print("Pending migrations:", pending)
        else:
            print("No pending migrations.")

    elif args.command == "run":
        results = mgr.run_pending(dry_run=args.dry_run)
        for r in results:
            status = "OK" if r["success"] else "FAIL"
            dr = " [DRY RUN]" if r.get("dry_run") else ""
            err = f" — {r.get('error', '')}" if r.get("error") else ""
            print(f"  v{r['version']:3d}  {status:4s}{dr}  {r['description']}{err}")

    elif args.command == "rollback":
        results = mgr.rollback(target_version=args.to, dry_run=args.dry_run)
        for r in results:
            status = "OK" if r["success"] else "FAIL"
            dr = " [DRY RUN]" if r.get("dry_run") else ""
            err = f" — {r.get('error', '')}" if r.get("error") else ""
            print(f"  v{r['version']:3d}  {status:4s}{dr}  {r.get('description', '?')}{err}")

    elif args.command == "create":
        fpath = mgr.create_migration_file(
            version=args.version,
            description=args.description,
            up_statements=args.up,
            down_statements=args.down,
        )
        print(f"Migration file created: {fpath}")

    else:
        parser.print_help()
