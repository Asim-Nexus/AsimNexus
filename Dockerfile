# ASIMNEXUS Production Multi-Stage Docker Build
# ================================================
# Stage 1: Builder — compile dependencies
# Stage 2: Runtime — minimal production image

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
# Use legacy resolver to handle dependency conflicts gracefully
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    grep -v "cudf\|cupy-cuda" requirements.txt > /tmp/requirements-docker.txt && \
    pip install --no-cache-dir --use-deprecated=legacy-resolver -r /tmp/requirements-docker.txt

# ─── Stage 2: Runtime ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

LABEL maintainer="ASIMNEXUS Team"
LABEL description="ASIMNEXUS — Digital Sovereign Entity"
LABEL version="1.1.0"

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

# Copy application code (selective — only production directories)
COPY main.py .
COPY simple_backend.py .
COPY asim_config.py .
COPY backend/ ./backend/
COPY core/ ./core/
COPY core/sectors/ ./core/sectors/
COPY agents/ ./agents/
COPY auth/ ./auth/
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

# Default command — use simple_backend.py (the working backend with all OS Control, Mesh, and Hardware features)
CMD ["python", "simple_backend.py"]
