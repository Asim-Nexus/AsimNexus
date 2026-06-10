# ─── AsimNexus Backend ───────────────────────────────────────────────────────
# Multi-stage build for production deployment
# Base image: python:3.11-slim (approved by user)
# ─────────────────────────────────────────────────────────────────────────────

FROM python:3.11-slim AS base

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for layer caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . /app

# Create data directory for SQLite and telemetry
RUN mkdir -p /app/data /app/deploy/release

# Environment
ENV PYTHONUNBUFFERED=1
ENV ASIM_DEPLOY_NAMESPACE=asimnexus
ENV ASIM_RELEASE_CHANNEL=stable
ENV ASIM_ROOT=/app

# Expose the backend port
EXPOSE 8080

# Healthcheck — uses the /healthz endpoint added in Milestone 6
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/healthz || exit 1

# Run the backend
CMD ["python", "-m", "uvicorn", "simple_backend:create_app", "--factory", "--host", "0.0.0.0", "--port", "8080"]
