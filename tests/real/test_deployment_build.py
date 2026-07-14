#!/usr/bin/env python3
"""
STATUS: REAL — Deployment Build Tests
AsimNexus Deployment Testing
============================
Tests for Docker build and deployment configuration.
Verifies file content, not just existence.
"""

import os
import pytest

# ── Paths ────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def _path(relative: str) -> str:
    return os.path.join(ROOT, relative)

# ── Dockerfile Backend ───────────────────────────────────────

def test_dockerfile_backend_exists():
    """Test backend Dockerfile exists."""
    path = _path("infrastructure/docker/Dockerfile.backend")
    assert os.path.exists(path), f"{path} missing"

def test_dockerfile_backend_content():
    """Test backend Dockerfile has valid content."""
    path = _path("infrastructure/docker/Dockerfile.backend")
    with open(path) as f:
        content = f.read()
    assert "FROM python:3.11-slim" in content, "Missing Python base image"
    assert "uvicorn" in content, "Missing uvicorn command"
    assert "EXPOSE 8000" in content, "Missing port exposure"
    assert "HEALTHCHECK" in content, "Missing healthcheck"
    assert "asimnexus" in content, "Missing non-root user"
    assert "requirements.txt" in content, "Missing requirements copy"

# ── Dockerfile Frontend ──────────────────────────────────────

def test_dockerfile_frontend_exists():
    """Test frontend Dockerfile exists."""
    path = _path("infrastructure/docker/Dockerfile.frontend")
    assert os.path.exists(path), f"{path} missing"

def test_dockerfile_frontend_content():
    """Test frontend Dockerfile has valid content."""
    path = _path("infrastructure/docker/Dockerfile.frontend")
    with open(path) as f:
        content = f.read()
    assert "FROM node:20-alpine AS builder" in content, "Missing Node builder stage"
    assert "FROM nginx:alpine" in content, "Missing nginx runtime stage"
    assert "nginx.conf" in content, "Missing nginx config copy"
    assert "EXPOSE 80" in content, "Missing port exposure"
    assert "HEALTHCHECK" in content, "Missing healthcheck"
    assert "npm run build" in content, "Missing build step"

# ── Docker Compose ───────────────────────────────────────────

def test_docker_compose_exists():
    """Test docker-compose.prod.yml exists."""
    path = _path("infrastructure/docker/docker-compose.prod.yml")
    assert os.path.exists(path), f"{path} missing"

def test_docker_compose_content():
    """Test docker-compose.prod.yml has valid content."""
    path = _path("infrastructure/docker/docker-compose.prod.yml")
    with open(path) as f:
        content = f.read()
    assert "backend:" in content, "Missing backend service"
    assert "frontend:" in content, "Missing frontend service"
    assert "postgres:" in content, "Missing postgres service"
    assert "redis:" in content, "Missing redis service"
    assert "healthcheck" in content, "Missing healthchecks"
    assert "deploy:" in content, "Missing deploy resource limits"
    assert "volumes:" in content, "Missing volumes"

# ── nginx Config ─────────────────────────────────────────────

def test_nginx_config_exists():
    """Test nginx config exists."""
    path = _path("frontend/nginx.conf")
    assert os.path.exists(path), f"{path} missing"

def test_nginx_config_content():
    """Test nginx config has valid content."""
    path = _path("frontend/nginx.conf")
    with open(path) as f:
        content = f.read()
    assert "listen 80" in content, "Missing listen directive"
    assert "try_files" in content, "Missing SPA fallback"
    assert "proxy_pass" in content, "Missing API proxy"
    assert "X-Frame-Options" in content, "Missing security headers"
    assert "Content-Security-Policy" in content, "Missing CSP header"
    assert "gzip" in content, "Missing gzip compression"
    assert "Cache-Control" in content, "Missing cache control"

# ── K8s Deployment ───────────────────────────────────────────

def test_k8s_deployment_exists():
    """Test K8s deployment manifest exists."""
    path = _path(".kilo/k8s/asimnexus-deployment.yaml")
    assert os.path.exists(path), f"{path} missing"

def test_k8s_deployment_content():
    """Test K8s deployment has valid content."""
    path = _path(".kilo/k8s/asimnexus-deployment.yaml")
    with open(path) as f:
        content = f.read()
    assert "Namespace" in content, "Missing namespace"
    assert "Deployment" in content, "Missing deployment"
    assert "Service" in content, "Missing service"
    assert "Ingress" in content, "Missing ingress"
    assert "livenessProbe" in content, "Missing liveness probe"
    assert "readinessProbe" in content, "Missing readiness probe"

# ── Infrastructure Docker (mirror) ───────────────────────────

def test_infrastructure_docker_backend_exists():
    """Test infrastructure/docker/ backend Dockerfile exists."""
    path = _path("infrastructure/docker/Dockerfile.backend")
    assert os.path.exists(path), f"{path} missing"

def test_infrastructure_docker_frontend_exists():
    """Test infrastructure/docker/ frontend Dockerfile exists."""
    path = _path("infrastructure/docker/Dockerfile.frontend")
    assert os.path.exists(path), f"{path} missing"

def test_infrastructure_docker_compose_exists():
    """Test infrastructure/docker/ docker-compose.prod.yml exists."""
    path = _path("infrastructure/docker/docker-compose.prod.yml")
    assert os.path.exists(path), f"{path} missing"
