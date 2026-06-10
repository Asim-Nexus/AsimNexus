#!/usr/bin/env bash
# =============================================================================
# ASIMNEXUS Database Restore Script
# =============================================================================
# Restores a PostgreSQL or SQLite backup from a local file or S3-compatible
# object storage.
#
# Usage:
#   # Restore PostgreSQL from a local file
#   ./scripts/restore.sh pg /path/to/asimnexus-pg-20250101-030000.dump.gz
#
#   # Restore SQLite from a local file
#   ./scripts/restore.sh sqlite /path/to/asimnexus-sqlite-20250101-030000.db.gz
#
#   # Restore PostgreSQL from S3 (latest backup)
#   ./scripts/restore.sh pg latest
#
#   # List available backups
#   ./scripts/restore.sh list
#
# ⚠️  WARNING: Restoring will OVERWRITE the current database. Make sure you
#    have a recent backup before proceeding.
# =============================================================================

set -euo pipefail

# ── Config ─────────────────────────────────────────────────────────────────
DB_TYPE="${1:-}"         # pg | sqlite | list
BACKUP_SOURCE="${2:-}"   # file path or "latest"

DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-asimnexus}"
DB_USER="${DB_USER:-postgres}"
DB_PASSWORD="${DB_PASSWORD:-postgres}"
SQLITE_DB_PATH="${SQLITE_DB_PATH:-data/asim_core.db}"

LOCAL_BACKUP_DIR_PG="./backups/postgres"
LOCAL_BACKUP_DIR_SQLITE="./backups/sqlite"

S3_ENDPOINT="${S3_ENDPOINT:-}"
S3_BUCKET="${S3_BUCKET:-asimnexus-backups}"
S3_ACCESS_KEY="${S3_ACCESS_KEY:-}"
S3_SECRET_KEY="${S3_SECRET_KEY:-}"

# ── Colors ─────────────────────────────────────────────────────────────────
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# ── Helper ─────────────────────────────────────────────────────────────────
log()    { echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $*"; }
warn()   { echo -e "${YELLOW}[WARN]${NC} $*"; }
error()  { echo -e "${RED}[ERROR]${NC} $*" >&2; }

confirm() {
    echo -e "${RED}⚠️  DATA LOSS WARNING${NC}"
    echo "This will OVERWRITE the current database."
    echo "Target: ${DB_TYPE} at ${DB_HOST}:${DB_PORT}/${DB_NAME}"
    read -rp "Are you sure? Type 'yes' to continue: " CONFIRM
    if [ "${CONFIRM}" != "yes" ]; then
        echo "Restore cancelled."
        exit 1
    fi
}

# ── List available backups ─────────────────────────────────────────────────
list_backups() {
    echo "=== Local PostgreSQL Backups ==="
    if [ -d "${LOCAL_BACKUP_DIR_PG}" ]; then
        ls -lhS "${LOCAL_BACKUP_DIR_PG}" 2>/dev/null || echo "(none)"
    else
        echo "(no backups directory)"
    fi

    echo ""
    echo "=== Local SQLite Backups ==="
    if [ -d "${LOCAL_BACKUP_DIR_SQLITE}" ]; then
        ls -lhS "${LOCAL_BACKUP_DIR_SQLITE}" 2>/dev/null || echo "(none)"
    else
        echo "(no backups directory)"
    fi

    if [ -n "${S3_ENDPOINT}" ] && command -v mc &>/dev/null; then
        echo ""
        echo "=== S3 Backups ==="
        mc ls "asimbackup/${S3_BUCKET}/" 2>/dev/null || echo "(none or no S3 alias configured)"
    fi
    exit 0
}

# ── Find latest backup ────────────────────────────────────────────────────
find_latest() {
    local dir="$1" pattern="$2"
    local latest
    latest=$(find "${dir}" -name "${pattern}" -type f -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2-)
    echo "${latest}"
}

# ── Restore PostgreSQL ─────────────────────────────────────────────────────
restore_pg() {
    local source_file="$1"

    # Resolve "latest"
    if [ "${source_file}" = "latest" ]; then
        source_file=$(find_latest "${LOCAL_BACKUP_DIR_PG}" "asimnexus-pg-*.dump.gz")
        if [ -z "${source_file}" ]; then
            error "No local PostgreSQL backups found."
            exit 1
        fi
        log "Using latest backup: ${source_file}"
    fi

    # Download from S3 if needed
    if [[ "${source_file}" == s3://* ]]; then
        if ! command -v mc &>/dev/null; then
            error "mc CLI required for S3 downloads. Install from https://dl.min.io/client/mc/release/"
            exit 1
        fi
        local tmpfile
        tmpfile=$(mktemp)
        log "Downloading from S3: ${source_file}"
        mc cp "${source_file}" "${tmpfile}"
        source_file="${tmpfile}"
    fi

    # Validate file
    if [ ! -f "${source_file}" ]; then
        error "Backup file not found: ${source_file}"
        exit 1
    fi

    confirm

    log "Restoring PostgreSQL database: ${DB_HOST}:${DB_PORT}/${DB_NAME}"

    # Drop and recreate the target database
    export PGPASSWORD="${DB_PASSWORD}"
    psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres \
        -c "DROP DATABASE IF EXISTS ${DB_NAME};" \
        -c "CREATE DATABASE ${DB_NAME};"

    # Restore from custom format dump
    pg_restore \
        -h "${DB_HOST}" \
        -p "${DB_PORT}" \
        -U "${DB_USER}" \
        -d "${DB_NAME}" \
        --no-owner \
        --no-acl \
        --clean \
        --if-exists \
        --verbose \
        "${source_file}"

    unset PGPASSWORD

    # Clean up temp file
    if [[ "${source_file}" == /tmp/tmp* ]]; then
        rm -f "${source_file}"
    fi

    log "PostgreSQL restore completed successfully."
}

# ── Restore SQLite ─────────────────────────────────────────────────────────
restore_sqlite() {
    local source_file="$1"

    # Resolve "latest"
    if [ "${source_file}" = "latest" ]; then
        source_file=$(find_latest "${LOCAL_BACKUP_DIR_SQLITE}" "asimnexus-sqlite-*.db.gz")
        if [ -z "${source_file}" ]; then
            error "No local SQLite backups found."
            exit 1
        fi
        log "Using latest backup: ${source_file}"
    fi

    # Validate file
    if [ ! -f "${source_file}" ]; then
        error "Backup file not found: ${source_file}"
        exit 1
    fi

    confirm

    log "Restoring SQLite database: ${SQLITE_DB_PATH}"

    # Ensure target directory exists
    mkdir -p "$(dirname "${SQLITE_DB_PATH}")"

    # Decompress and restore
    if [[ "${source_file}" == *.gz ]]; then
        gzip -dc "${source_file}" > "${SQLITE_DB_PATH}"
    else
        cp "${source_file}" "${SQLITE_DB_PATH}"
    fi

    # Verify
    if sqlite3 "${SQLITE_DB_PATH}" "PRAGMA integrity_check;" 2>&1 | grep -qi "error"; then
        error "SQLite integrity check FAILED after restore!"
        exit 1
    fi

    log "SQLite restore completed successfully. Integrity check passed."
}

# ── Main ───────────────────────────────────────────────────────────────────
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║         ASIMNEXUS Database Restore Utility                  ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

case "${DB_TYPE}" in
    pg)
        restore_pg "${BACKUP_SOURCE}"
        ;;
    sqlite)
        restore_sqlite "${BACKUP_SOURCE}"
        ;;
    list)
        list_backups
        ;;
    "")
        echo "Usage: $0 {pg|sqlite|list} [backup-file|latest]"
        echo ""
        echo "Examples:"
        echo "  $0 list                          # List available backups"
        echo "  $0 pg latest                     # Restore latest PostgreSQL backup"
        echo "  $0 pg /path/to/backup.dump.gz    # Restore specific PostgreSQL backup"
        echo "  $0 sqlite latest                 # Restore latest SQLite backup"
        echo "  $0 sqlite /path/to/backup.db.gz  # Restore specific SQLite backup"
        exit 1
        ;;
    *)
        error "Unknown database type: ${DB_TYPE}. Use 'pg', 'sqlite', or 'list'."
        exit 1
        ;;
esac
