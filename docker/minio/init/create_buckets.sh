#!/bin/bash
# =============================================================================
# ASIMNEXUS MinIO — Bucket Initialisation Script
# =============================================================================
# Creates all required MinIO buckets for the 4-layer storage system.
# Designed to run as a Kubernetes init container or standalone.
#
# Usage:
#   MINIO_ENDPOINT=http://minio:9000 \
#   MINIO_ROOT_USER=minioadmin \
#   MINIO_ROOT_PASSWORD=minioadmin \
#   ./create_buckets.sh
# =============================================================================

set -euo pipefail

# ─── Configuration ───────────────────────────────────────────────────────────
ENDPOINT="${MINIO_ENDPOINT:-http://localhost:9000}"
ACCESS_KEY="${MINIO_ROOT_USER:-minioadmin}"
SECRET_KEY="${MINIO_ROOT_PASSWORD:-minioadmin}"
ALIAS="${MC_ALIAS:-asimnexus}"

# ─── Buckets to create ───────────────────────────────────────────────────────
BUCKETS=(
    "models"       # AI/ML model storage
    "data"         # Application data
    "backups"      # Database and system backups
    "logs"         # Centralised log storage
    "memory"       # Persistent memory snapshots
    "config"       # Configuration files
    "federation"   # Cross-instance federation artifacts
    "artifacts"    # Build artifacts and releases
)

# ─── Functions ───────────────────────────────────────────────────────────────

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"
}

create_bucket() {
    local bucket="$1"
    log "Creating bucket: ${bucket}"
    if mc mb "${ALIAS}/${bucket}" --ignore-existing 2>/dev/null; then
        log "  ✓ Bucket '${bucket}' ready"
    else
        log "  ⚠ Bucket '${bucket}' may already exist or error occurred"
    fi
}

# ─── Main ────────────────────────────────────────────────────────────────────

log "=== MinIO Bucket Initialisation ==="
log "Endpoint: ${ENDPOINT}"
log "Alias:    ${ALIAS}"
log "Buckets:  ${BUCKETS[*]}"
log ""

# Configure mc alias
log "Configuring MinIO client alias..."
mc alias set "${ALIAS}" "${ENDPOINT}" "${ACCESS_KEY}" "${SECRET_KEY}"
log ""

# Create each bucket
log "Creating ${#BUCKETS[@]} buckets..."
for bucket in "${BUCKETS[@]}"; do
    create_bucket "${bucket}"
done

log ""
log "=== MinIO initialisation complete ==="
log "All ${#BUCKETS[@]} buckets are ready."

# Verify
log ""
log "Verifying buckets..."
mc ls "${ALIAS}/" | awk '{print "  " $NF}'
