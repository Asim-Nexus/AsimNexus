# ASIMNEXUS Production Multi-Stage Docker Build
# ================================================
# Stage 1: Builder — compile dependencies
# Stage 2: Runtime — minimal production image
#
# Build: docker build -f infra/docker/Dockerfile -t asimnexus:latest .
# Or from root: docker build -f infra/docker/Dockerfile -t asimnexus:latest .

# ─── Stage 1: Builder ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    libssl-dev \
    libffi-dev \
    libpq-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for Docker layer caching
COPY requirements.txt .
# Filter out GPU-only packages (cudf requires conda, cupy needs CUDA runtime)
# and install the rest — GPU packages can be added manually if CUDA is available
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    grep -v "cudf\|cupy-cuda" requirements.txt > /tmp/requirements-docker.txt && \
    pip install --no-cache-dir --use-deprecated=legacy-resolver -r /tmp/requirements-docker.txt

# ─── Stage 2: Runtime ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

LABEL maintainer="ASIMNEXUS Team"
LABEL description="ASIMNEXUS — Digital Sovereign Entity"
LABEL version="2.0.0"

WORKDIR /app

# Install only runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python site-packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code — organized by new structure
COPY main.py .
COPY simple_backend.py .
COPY asim_config.py .

# Apps (runnable applications)
COPY apps/backend/ ./apps/backend/

# Packages (shared libraries)
COPY packages/core/ ./packages/core/
COPY packages/mesh/ ./packages/mesh/
COPY packages/security/ ./packages/security/
COPY packages/agents/ ./packages/agents/
COPY packages/connectors/ ./packages/connectors/
COPY packages/economy/ ./packages/economy/
COPY packages/governance/ ./packages/governance/
COPY packages/storage/ ./packages/storage/
COPY packages/data-lake/ ./packages/data-lake/
COPY packages/kernel/ ./packages/kernel/
COPY packages/os-control/ ./packages/os-control/
COPY packages/monitoring/ ./packages/monitoring/
COPY packages/cloud/ ./packages/cloud/

# Legacy paths for backward compatibility (will be symlinked by migration scripts)
COPY core/ ./core/
COPY agents/ ./agents/
COPY auth/ ./auth/
COPY backend/ ./backend/
COPY bridge/ ./bridge/
COPY connectors/ ./connectors/
COPY economy/ ./economy/
COPY governance/ ./governance/
COPY integrations/ ./integrations/
COPY mesh/ ./mesh/
COPY monitoring/ ./monitoring/
COPY os_control/ ./os_control/
COPY runtime/ ./runtime/
COPY security/ ./security/
COPY storage/ ./storage/
COPY tools/ ./tools/

# Create data directories
RUN mkdir -p /app/data /app/logs /app/config /app/models

# Create non-root user for security
RUN useradd -m -u 1000 asimnexus && \
    chown -R asimnexus:asimnexus /app
USER asimnexus

# Expose ports
EXPOSE 8000 8080 8766

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["python", "simple_backend.py"]
