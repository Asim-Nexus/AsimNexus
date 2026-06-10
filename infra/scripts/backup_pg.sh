#!/usr/bin/env bash
# =============================================================================
# ASIMNEXUS PostgreSQL Backup Script
# =============================================================================
# Creates a compressed, timestamped pg_dump archive and uploads it to S3-compatible
# object storage (MinIO / AWS S3) for off-site disaster recovery.
#
# Usage:
#   ./scripts/backup_pg.sh                   # uses defaults/env vars
#   ./scripts/backup_pg.sh /custom/path      # custom backup directory
#
# Environment variables (with defaults):
#   DB_HOST=localhost
#   DB_PORT=5432
#   DB_NAME=asimnexus
#   DB_USER=postgres
#   DB_PASSWORD=postgres
#   BACKUP_RETENTION_DAYS=14
#   S3_ENDPOINT=                                   # (optional) S3 upload
#   S3_BUCKET=asimnexus-backups
#   S3_ACCESS_KEY=
#   S3_SECRET_KEY=
# =============================================================================

set -euo pipefail

# ── Config ─────────────────────────────────────────────────────────────────
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-asimnexus}"
DB_USER="${DB_USER:-postgres}"
DB_PASSWORD="${DB_PASSWORD:-postgres}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-14}"

S3_ENDPOINT="${S3_ENDPOINT:-}"
S3_BUCKET="${S3_BUCKET:-asimnexus-backups}"
S3_ACCESS_KEY="${S3_ACCESS_KEY:-}"
S3_SECRET_KEY="${S3_SECRET_KEY:-}"

BACKUP_DIR="${1:-./backups/postgres}"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
FILENAME="asimnexus-pg-${TIMESTAMP}.dump.gz"
FILEPATH="${BACKUP_DIR}/${FILENAME}"
ERROR_LOG="${BACKUP_DIR}/backup_errors.log"

mkdir -p "${BACKUP_DIR}"

# ── Helper ─────────────────────────────────────────────────────────────────
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

cleanup() {
    # Remove incomplete backup on exit
    if [ -f "${FILEPATH}" ] && [ ! -s "${FILEPATH}" ]; then
        rm -f "${FILEPATH}"
        log "Removed incomplete backup: ${FILEPATH}"
    fi
}
trap cleanup EXIT

# ── Dependencies check ─────────────────────────────────────────────────────
if ! command -v pg_dump &>/dev/null; then
    log "ERROR: pg_dump not found. Install postgresql-client (apt: postgresql-client, brew: libpq)."
    exit 1
fi

# ── Perform backup ─────────────────────────────────────────────────────────
log "Starting PostgreSQL backup: ${DB_HOST}:${DB_PORT}/${DB_NAME} → ${FILEPATH}"

export PGPASSWORD="${DB_PASSWORD}"
pg_dump \
    -h "${DB_HOST}" \
    -p "${DB_PORT}" \
    -U "${DB_USER}" \
    -d "${DB_NAME}" \
    --no-owner \
    --no-acl \
    --format=custom \
    --compress=9 \
    --file="${FILEPATH}" 2>>"${ERROR_LOG}"

unset PGPASSWORD

# ── Verify backup integrity ────────────────────────────────────────────────
if ! pg_restore --list "${FILEPATH}" > /dev/null 2>&1; then
    log "ERROR: Backup verification FAILED for ${FILENAME}"
    rm -f "${FILEPATH}"
    exit 1
fi

BACKUP_SIZE=$(du -h "${FILEPATH}" | cut -f1)
log "Backup verified OK: ${FILENAME} (${BACKUP_SIZE})"

# ── Retention: remove local backups older than N days ──────────────────────
find "${BACKUP_DIR}" -name "asimnexus-pg-*.dump.gz" -type f -mtime +${BACKUP_RETENTION_DAYS} -delete
log "Cleaned up backups older than ${BACKUP_RETENTION_DAYS} days from ${BACKUP_DIR}"

# ── Optional S3 upload ─────────────────────────────────────────────────────
if [ -n "${S3_ENDPOINT}" ] && [ -n "${S3_ACCESS_KEY}" ] && [ -n "${S3_SECRET_KEY}" ]; then
    log "Uploading backup to S3: ${S3_ENDPOINT}/${S3_BUCKET}..."

    if command -v mc &>/dev/null; then
        # Using MinIO Client
        mc alias set asimbackup "${S3_ENDPOINT}" "${S3_ACCESS_KEY}" "${S3_SECRET_KEY}" 2>/dev/null
        mc cp "${FILEPATH}" "asimbackup/${S3_BUCKET}/postgres/${FILENAME}"
        log "S3 upload complete (mc)"
    elif command -v aws &>/dev/null; then
        # Using AWS CLI
        export AWS_ACCESS_KEY_ID="${S3_ACCESS_KEY}"
        export AWS_SECRET_ACCESS_KEY="${S3_SECRET_KEY}"
        aws s3 cp "${FILEPATH}" "s3://${S3_BUCKET}/postgres/${FILENAME}" \
            --endpoint-url "${S3_ENDPOINT}"
        log "S3 upload complete (aws cli)"
    else
        # Using curl (AWS S3 presigned or compatible)
        log "WARNING: Neither mc nor aws CLI found. Skipping S3 upload."
        log "Install mc from https://dl.min.io/client/mc/release/ or awscli from pip."
    fi

    # Purge remote backups older than 30 days
    log "Remote retention: 30 days (manual policy on S3 bucket lifecycle)"
fi

log "Backup completed successfully: ${FILENAME} (${BACKUP_SIZE})"
exit 0
