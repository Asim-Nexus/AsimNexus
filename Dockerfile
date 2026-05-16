# ASIMNEXUS - Digital Sovereign Entity
# Master Terminal - Unified System Orchestration
# Supports all components: OCR, Cloud, Government APIs, Neural Gateway

ARG BASE_IMAGE=python:3.11-slim
FROM ${BASE_IMAGE}

LABEL maintainer="ASIMNEXUS Team"
LABEL version="1.0.0-master-terminal"
LABEL description="ASIMNEXUS - Digital Sovereign Entity with Master Terminal"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ASIM_ENV=production
ENV ASIM_VERSION=1.0.0
ENV LOG_LEVEL=INFO

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    libffi-dev \
    libssl-dev \
    libpq-dev \
    libopencv-dev \
    pkg-config \
    curl \
    wget \
    git \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip setuptools==78.1.1 wheel

# Copy requirements first (for better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/data /app/memory /app/logs /app/config /app/models /app/tests

# Create non-root user for security
RUN useradd -m -u 1000 asimnexus && \
    chown -R asimnexus:asimnexus /app
USER asimnexus

# Expose ports
# 8000 - ASIMNEXUS API endpoint
# 8080 - Alternative API endpoint
# 3000 - Web UI (if available)
EXPOSE 8000 8080 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Set permissions
RUN chmod +x /app/asim-nexus-root/main.py

# Default command - Run ASIMNEXUS Master Terminal
CMD ["python", "asim-nexus-root/main.py"]
