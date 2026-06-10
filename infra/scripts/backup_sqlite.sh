#!/usr/bin/env bash
# =============================================================================
# ASIMNEXUS SQLite Backup Script
# =============================================================================
# Creates a safe, consistent snapshot of the SQLite database using the backup
# API, then compresses and optionally uploads to S3.
#
# SQLite backups are safe to take while the application is running (VACUUM INTO
# or .backup commands use read locks that allow concurrent reads).
#
# Usage:
#   ./scripts/backup_sqlite.sh                          # default path
#   ./scripts/backup_sqlite.sh /custom/path/asimnexus.db
#
# Environment:
#   SQLITE_DB_PATH=data/asim_core.db
#   BACKUP_RETENTION_DAYS=14
#   S3_ENDPOINT=                           # (optional)
#   S3_BUCKET=asimnexus-backups
#   S3_ACCESS_KEY=
#   S3_SECRET_KEY=
# =============================================================================

set -euo pipefail

# ── Config ─────────────────────────────────────────────────────────────────
SQLITE_DB_PATH="${SQLITE_DB_PATH:-data/asim_core.db}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-14}"

S3_ENDPOINT="${S3_ENDPOINT:-}"
S3_BUCKET="${S3_BUCKET:-asimnexus-backups}"
S3_ACCESS_KEY="${S3_ACCESS_KEY:-}"
S3_SECRET_KEY="${S3_SECRET_KEY:-}"

BACKUP_DIR="./backups/sqlite"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
FILENAME="asimnexus-sqlite-${TIMESTAMP}.db.gz"
FILEPATH="${BACKUP_DIR}/${FILENAME}"

mkdir -p "${BACKUP_DIR}"

# ── Helper ─────────────────────────────────────────────────────────────────
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

# ── Pre-flight checks ─────────────────────────────────────────────────────
if [ ! -f "${SQLITE_DB_PATH}" ]; then
    log "ERROR: SQLite database not found at: ${SQLITE_DB_PATH}"
    log "Set SQLITE_DB_PATH env var if the database is at a different location."
    exit 1
fi

if ! command -v sqlite3 &>/dev/null; then
    log "ERROR: sqlite3 not found. Install it: apt install sqlite3"
    exit 1
fi

# ── Backup using sqlite3 backup API ────────────────────────────────────────
log "Starting SQLite backup: ${SQLITE_DB_PATH} → ${FILEPATH}"

TMPFILE=$(mktemp)
sqlite3 "${SQLITE_DB_PATH}" ".backup ${TMPFILE}" 2>&1
if [ $? -ne 0 ]; then
    log "ERROR: SQLite backup command failed"
    rm -f "${TMPFILE}"
    exit 1
fi

# Compress
gzip -c "${TMPFILE}" > "${FILEPATH}"
rm -f "${TMPFILE}"

# ── Verify ─────────────────────────────────────────────────────────────────
if [ ! -s "${FILEPATH}" ]; then
    log "ERROR: Backup file is empty: ${FILEPATH}"
    rm -f "${FILEPATH}"
    exit 1
fi

# Quick integrity check: verify it's a valid gzip
if ! gzip -t "${FILEPATH}" 2>/dev/null; then
    log "ERROR: Backup file is corrupted (gzip integrity check failed)"
    rm -f "${FILEPATH}"
    exit 1
fi

BACKUP_SIZE=$(du -h "${FILEPATH}" | cut -f1)
log "Backup verified OK: ${FILENAME} (${BACKUP_SIZE})"

# ── Retention ──────────────────────────────────────────────────────────────
find "${BACKUP_DIR}" -name "asimnexus-sqlite-*.db.gz" -type f -mtime +${BACKUP_RETENTION_DAYS} -delete
log "Cleaned up backups older than ${BACKUP_RETENTION_DAYS} days"

# ── Optional S3 upload ─────────────────────────────────────────────────────
if [ -n "${S3_ENDPOINT}" ] && [ -n "${S3_ACCESS_KEY}" ] && [ -n "${S3_SECRET_KEY}" ]; then
    log "Uploading to S3: ${S3_ENDPOINT}/${S3_BUCKET}..."

    if command -v mc &>/dev/null; then
        mc alias set asimbackup "${S3_ENDPOINT}" "${S3_ACCESS_KEY}" "${S3_SECRET_KEY}" 2>/dev/null
        mc cp "${FILEPATH}" "asimbackup/${S3_BUCKET}/sqlite/${FILENAME}"
        log "S3 upload complete (mc)"
    else
        log "WARNING: mc CLI not found. Skipping S3 upload."
    fi
fi

log "SQLite backup completed: ${FILENAME} (${BACKUP_SIZE})"
exit 0
