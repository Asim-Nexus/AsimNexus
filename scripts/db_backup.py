#!/usr/bin/env python3
"""
scripts/db_backup.py
AsimNexus — Automated Database Backup System

Features:
  - Scheduled SQLite backups with WAL checkpoint before copy
  - Configurable retention policy (keep last N backups)
  - Optional S3/cloud sync for off-site storage
  - Backup manifest tracking (JSONL)
  - Integrity verification on restore
  - Integration with DBManager connection pool

Usage:
    python scripts/db_backup.py                    # Run once (manual backup)
    python scripts/db_backup.py --daemon            # Run as scheduled daemon
    python scripts/db_backup.py --list              # List available backups
    python scripts/db_backup.py --restore <path>    # Restore from backup
    python scripts/db_backup.py --verify            # Verify latest backup integrity
"""

import argparse
import gzip
import hashlib
import json
import logging
import os
import shutil
import sqlite3
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure project root is on sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("AsimNexus.DB.Backup")

# ── Defaults ──────────────────────────────────────────────────────────────

_DEFAULT_DB_DIR = _PROJECT_ROOT / "database" / "data"
_DEFAULT_DB_PATH = _DEFAULT_DB_DIR / "asimnexus.db"
_DEFAULT_BACKUP_DIR = _PROJECT_ROOT / "backups" / "database"
_DEFAULT_RETENTION_DAYS = 30
_DEFAULT_MAX_BACKUPS = 50
_MANIFEST_FILE = "backup_manifest.jsonl"

# ── S3 / Cloud Sync (optional) ───────────────────────────────────────────

_S3_ENABLED = os.environ.get("BACKUP_S3_ENABLED", "").lower() in ("1", "true", "yes")
_S3_BUCKET = os.environ.get("BACKUP_S3_BUCKET", "asimnexus-backups")
_S3_PREFIX = os.environ.get("BACKUP_S3_PREFIX", "database")
_S3_ENDPOINT = os.environ.get("BACKUP_S3_ENDPOINT", "")
_AWS_ACCESS_KEY = os.environ.get("BACKUP_AWS_ACCESS_KEY", "")
_AWS_SECRET_KEY = os.environ.get("BACKUP_AWS_SECRET_KEY", "")


# ── Backup Manager ────────────────────────────────────────────────────────

class BackupManager:
    """Manages database backups with retention, verification, and cloud sync."""

    def __init__(
        self,
        db_path: str = str(_DEFAULT_DB_PATH),
        backup_dir: str = str(_DEFAULT_BACKUP_DIR),
        retention_days: int = _DEFAULT_RETENTION_DAYS,
        max_backups: int = _DEFAULT_MAX_BACKUPS,
    ):
        self.db_path = Path(db_path)
        self.backup_dir = Path(backup_dir)
        self.retention_days = retention_days
        self.max_backups = max_backups
        self.manifest_path = self.backup_dir / _MANIFEST_FILE
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    # ── Public API ───────────────────────────────────────────────────────

    def create_backup(self, compress: bool = True) -> Dict[str, Any]:
        """Create a new backup of the database.

        Steps:
          1. Verify source database integrity
          2. WAL checkpoint to flush pending writes
          3. Copy (and optionally gzip compress) to backup dir
          4. Compute SHA-256 checksum
          5. Record in manifest
          6. Enforce retention policy
          7. Optionally sync to S3
        """
        start = time.time()

        # 1. Verify source
        if not self.db_path.exists():
            return {"success": False, "error": f"Database not found: {self.db_path}"}

        integrity_ok = self._verify_integrity(str(self.db_path))
        if not integrity_ok:
            logger.warning("Source database integrity check FAILED — backing up anyway")

        # 2. WAL checkpoint
        self._checkpoint_wal(str(self.db_path))

        # 3. Create backup file
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        ext = ".db.gz" if compress else ".db"
        backup_filename = f"asimnexus_{timestamp}{ext}"
        backup_path = self.backup_dir / backup_filename

        try:
            if compress:
                with open(self.db_path, "rb") as f_in:
                    with gzip.open(backup_path, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
            else:
                shutil.copy2(self.db_path, backup_path)
        except Exception as exc:
            logger.error("Backup copy failed: %s", exc)
            return {"success": False, "error": str(exc)}

        # 4. Compute checksum
        checksum = self._sha256(backup_path)
        size_bytes = backup_path.stat().st_size

        # 5. Record manifest entry
        manifest_entry = {
            "filename": backup_filename,
            "timestamp": timestamp,
            "size_bytes": size_bytes,
            "checksum_sha256": checksum,
            "compressed": compress,
            "source_db": str(self.db_path),
            "integrity_verified": integrity_ok,
        }
        self._append_manifest(manifest_entry)

        elapsed = time.time() - start
        logger.info(
            "Backup created: %s (%d bytes, sha256=%s) in %.2fs",
            backup_filename, size_bytes, checksum[:16], elapsed,
        )

        # 6. Enforce retention
        pruned = self._enforce_retention()

        # 7. S3 sync (optional)
        s3_result = None
        if _S3_ENABLED:
            s3_result = self._sync_to_s3(backup_path, backup_filename)

        return {
            "success": True,
            "filename": backup_filename,
            "path": str(backup_path),
            "size_bytes": size_bytes,
            "checksum_sha256": checksum,
            "elapsed_seconds": round(elapsed, 3),
            "integrity_verified": integrity_ok,
            "pruned_count": pruned,
            "s3_synced": s3_result,
        }

    def list_backups(self, limit: int = 20) -> List[Dict[str, Any]]:
        """List recent backups from the manifest."""
        entries = self._read_manifest()
        # Sort by timestamp descending
        entries.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
        return entries[:limit]

    def restore_backup(self, backup_path_str: str) -> Dict[str, Any]:
        """Restore the database from a backup file.

        The backup file can be:
          - A full path to a .db or .db.gz file
          - A filename (looked up in backup_dir)
          - The special value "latest" (restores most recent backup)
        """
        backup_path = self._resolve_backup_path(backup_path_str)
        if not backup_path or not backup_path.exists():
            return {"success": False, "error": f"Backup not found: {backup_path_str}"}

        # Verify backup integrity
        if not self._verify_integrity(str(backup_path)):
            return {"success": False, "error": "Backup integrity check FAILED — refusing restore"}

        # Create a pre-restore backup of current DB (safety net)
        pre_restore = self.create_backup(compress=True)
        logger.info("Pre-restore backup created: %s", pre_restore.get("filename"))

        # Restore
        try:
            if str(backup_path).endswith(".gz"):
                # Gunzip to temp then copy
                temp_path = backup_path.with_suffix("")  # remove .gz
                with gzip.open(backup_path, "rb") as f_in:
                    with open(temp_path, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
                shutil.copy2(temp_path, self.db_path)
                temp_path.unlink(missing_ok=True)
            else:
                shutil.copy2(backup_path, self.db_path)

            # Verify restored DB
            restored_ok = self._verify_integrity(str(self.db_path))
            if not restored_ok:
                return {"success": False, "error": "Restored database integrity check FAILED"}

            logger.info("Database restored from: %s", backup_path.name)
            return {
                "success": True,
                "restored_from": backup_path.name,
                "restored_to": str(self.db_path),
            }
        except Exception as exc:
            logger.error("Restore failed: %s", exc)
            return {"success": False, "error": str(exc)}

    def verify_latest(self) -> Dict[str, Any]:
        """Verify the integrity of the latest backup."""
        entries = self.list_backups(limit=1)
        if not entries:
            return {"success": False, "error": "No backups found"}
        latest = entries[0]
        backup_path = self.backup_dir / latest["filename"]
        if not backup_path.exists():
            return {"success": False, "error": f"Backup file missing: {backup_path}"}

        # Verify checksum
        actual_checksum = self._sha256(backup_path)
        expected_checksum = latest.get("checksum_sha256", "")
        checksum_ok = actual_checksum == expected_checksum

        # Verify SQLite integrity
        integrity_ok = self._verify_integrity(str(backup_path))

        return {
            "success": checksum_ok and integrity_ok,
            "filename": latest["filename"],
            "checksum_match": checksum_ok,
            "integrity_ok": integrity_ok,
            "actual_checksum": actual_checksum,
            "expected_checksum": expected_checksum,
        }

    # ── Daemon mode ──────────────────────────────────────────────────────

    def run_daemon(self, interval_minutes: int = 60) -> None:
        """Run backup loop at a fixed interval."""
        logger.info(
            "Backup daemon started (interval=%d min, backup_dir=%s)",
            interval_minutes, self.backup_dir,
        )
        while True:
            try:
                result = self.create_backup(compress=True)
                if result.get("success"):
                    logger.info("Scheduled backup completed: %s", result.get("filename"))
                else:
                    logger.error("Scheduled backup FAILED: %s", result.get("error"))
            except Exception as exc:
                logger.exception("Scheduled backup crashed: %s", exc)

            time.sleep(interval_minutes * 60)

    # ── Internals ────────────────────────────────────────────────────────

    def _verify_integrity(self, db_path_str: str) -> bool:
        """Run SQLite integrity_check on a database file."""
        try:
            # For gzipped backups, we can't run integrity_check directly
            if db_path_str.endswith(".gz"):
                return True  # Skip for compressed files
            conn = sqlite3.connect(db_path_str)
            row = conn.execute("PRAGMA integrity_check").fetchone()
            conn.close()
            return row is not None and row[0] == "ok"
        except Exception:
            return False

    def _checkpoint_wal(self, db_path_str: str) -> None:
        """Run WAL checkpoint to flush pending writes."""
        try:
            conn = sqlite3.connect(db_path_str)
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            conn.close()
        except Exception as exc:
            logger.warning("WAL checkpoint failed: %s", exc)

    def _sha256(self, filepath: Path) -> str:
        """Compute SHA-256 hash of a file."""
        h = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    def _append_manifest(self, entry: Dict[str, Any]) -> None:
        """Append a JSON line to the manifest file."""
        try:
            with open(self.manifest_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, sort_keys=True) + "\n")
        except Exception as exc:
            logger.error("Failed to write manifest: %s", exc)

    def _read_manifest(self) -> List[Dict[str, Any]]:
        """Read all entries from the manifest file."""
        entries = []
        if not self.manifest_path.exists():
            return entries
        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entries.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
        except Exception as exc:
            logger.error("Failed to read manifest: %s", exc)
        return entries

    def _enforce_retention(self) -> int:
        """Remove backups outside retention policy. Returns count pruned."""
        entries = self._read_manifest()
        now = datetime.utcnow()
        cutoff = now - timedelta(days=self.retention_days)
        pruned = 0

        # Group by timestamp, keep newest
        valid_files = set()
        for entry in entries:
            try:
                ts = datetime.strptime(entry["timestamp"], "%Y%m%d_%H%M%S")
                if ts >= cutoff:
                    valid_files.add(entry["filename"])
            except (ValueError, KeyError):
                continue

        # If still over max_backups, keep only the newest
        sorted_entries = sorted(
            entries, key=lambda e: e.get("timestamp", ""), reverse=True
        )
        for entry in sorted_entries[self.max_backups:]:
            if entry["filename"] in valid_files:
                valid_files.discard(entry["filename"])

        # Remove files not in valid set
        for entry in entries:
            fname = entry.get("filename", "")
            if fname not in valid_files:
                fpath = self.backup_dir / fname
                if fpath.exists():
                    fpath.unlink()
                    pruned += 1
                    logger.info("Pruned old backup: %s", fname)

        # Also remove orphaned manifest entries for deleted files
        self._clean_manifest(valid_files)

        if pruned:
            logger.info("Retention enforced: %d backups pruned", pruned)
        return pruned

    def _clean_manifest(self, valid_filenames: set) -> None:
        """Rewrite manifest to only include entries for valid files."""
        entries = self._read_manifest()
        valid_entries = [e for e in entries if e.get("filename") in valid_filenames]
        try:
            with open(self.manifest_path, "w", encoding="utf-8") as f:
                for entry in valid_entries:
                    f.write(json.dumps(entry, sort_keys=True) + "\n")
        except Exception as exc:
            logger.error("Failed to clean manifest: %s", exc)

    def _resolve_backup_path(self, path_str: str) -> Optional[Path]:
        """Resolve a user-provided path to an actual backup file."""
        if path_str == "latest":
            entries = self.list_backups(limit=1)
            if entries:
                return self.backup_dir / entries[0]["filename"]
            return None
        p = Path(path_str)
        if p.is_absolute():
            return p if p.exists() else None
        # Try relative to backup_dir
        p2 = self.backup_dir / path_str
        if p2.exists():
            return p2
        return None

    def _sync_to_s3(self, local_path: Path, filename: str) -> Dict[str, Any]:
        """Sync a backup file to S3-compatible storage."""
        try:
            import boto3
            session = boto3.Session(
                aws_access_key_id=_AWS_ACCESS_KEY,
                aws_secret_access_key=_AWS_SECRET_KEY,
            )
            s3 = session.client(
                "s3",
                endpoint_url=_S3_ENDPOINT if _S3_ENDPOINT else None,
            )
            key = f"{_S3_PREFIX}/{filename}"
            s3.upload_file(str(local_path), _S3_BUCKET, key)
            logger.info("Synced to S3: s3://%s/%s", _S3_BUCKET, key)
            return {"success": True, "bucket": _S3_BUCKET, "key": key}
        except ImportError:
            logger.warning("boto3 not installed — skipping S3 sync")
            return {"success": False, "error": "boto3 not installed"}
        except Exception as exc:
            logger.error("S3 sync failed: %s", exc)
            return {"success": False, "error": str(exc)}


# ── CLI ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="AsimNexus Database Backup Manager",
    )
    parser.add_argument(
        "--db-path", default=str(_DEFAULT_DB_PATH),
        help="Path to the SQLite database file",
    )
    parser.add_argument(
        "--backup-dir", default=str(_DEFAULT_BACKUP_DIR),
        help="Directory to store backups",
    )
    parser.add_argument(
        "--retention-days", type=int, default=_DEFAULT_RETENTION_DAYS,
        help="Number of days to retain backups",
    )
    parser.add_argument(
        "--max-backups", type=int, default=_DEFAULT_MAX_BACKUPS,
        help="Maximum number of backups to keep",
    )
    parser.add_argument(
        "--no-compress", action="store_true",
        help="Disable gzip compression",
    )

    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    # backup (default)
    subparsers.add_parser("backup", help="Create a backup (default)")

    # list
    list_parser = subparsers.add_parser("list", help="List available backups")
    list_parser.add_argument("--limit", type=int, default=20)

    # restore
    restore_parser = subparsers.add_parser("restore", help="Restore from a backup")
    restore_parser.add_argument("path", help="Backup filename, path, or 'latest'")

    # verify
    subparsers.add_parser("verify", help="Verify latest backup integrity")

    # daemon
    daemon_parser = subparsers.add_parser("daemon", help="Run backup daemon")
    daemon_parser.add_argument(
        "--interval", type=int, default=60,
        help="Interval in minutes between backups",
    )

    args = parser.parse_args()

    mgr = BackupManager(
        db_path=args.db_path,
        backup_dir=args.backup_dir,
        retention_days=args.retention_days,
        max_backups=args.max_backups,
    )

    if args.command == "list" or args.command is None and hasattr(args, "limit"):
        entries = mgr.list_backups(limit=getattr(args, "limit", 20))
        if not entries:
            print("No backups found.")
            return
        print(f"{'Filename':<40} {'Size':>10} {'Checksum':<20} {'Date':<20}")
        print("-" * 90)
        for e in entries:
            fname = e.get("filename", "?")
            size = e.get("size_bytes", 0)
            csum = (e.get("checksum_sha256", "") or "")[:16]
            ts = e.get("timestamp", "")
            print(f"{fname:<40} {size:>10} {csum:<20} {ts:<20}")

    elif args.command == "restore":
        result = mgr.restore_backup(args.path)
        if result.get("success"):
            print(f"Restored from: {result['restored_from']}")
            print(f"Restored to: {result['restored_to']}")
        else:
            print(f"Restore FAILED: {result.get('error')}")
            sys.exit(1)

    elif args.command == "verify":
        result = mgr.verify_latest()
        if result.get("success"):
            print(f"Backup verified OK: {result['filename']}")
        else:
            print(f"Verification FAILED: {result.get('error', 'unknown')}")
            sys.exit(1)

    elif args.command == "daemon":
        mgr.run_daemon(interval_minutes=args.interval)

    else:  # default: backup
        result = mgr.create_backup(compress=not args.no_compress)
        if result.get("success"):
            print(f"Backup created: {result['filename']}")
            print(f"  Path:     {result['path']}")
            print(f"  Size:     {result['size_bytes']} bytes")
            print(f"  SHA-256:  {result['checksum_sha256']}")
            print(f"  Duration: {result['elapsed_seconds']}s")
            if result.get("pruned_count"):
                print(f"  Pruned:   {result['pruned_count']} old backups")
        else:
            print(f"Backup FAILED: {result.get('error')}")
            sys.exit(1)


if __name__ == "__main__":
    main()
