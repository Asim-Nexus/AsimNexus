#!/usr/bin/env python3
"""
STATUS: REAL — Deployment Build Tests
AsimNexus Deployment Testing
============================
Tests for Docker build and deployment configuration.
"""

import os
import pytest


def test_dockerfile_backend_exists():
    """Test backend Dockerfile exists."""
    path = "infra/docker/Dockerfile.backend"
    assert os.path.exists(path), f"{path} missing"


def test_dockerfile_frontend_exists():
    """Test frontend Dockerfile exists."""
    path = "infra/docker/Dockerfile.frontend"
    assert os.path.exists(path), f"{path} missing"


def test_docker_compose_exists():
    """Test docker-compose.prod.yml exists."""
    path = "infra/docker/docker-compose.prod.yml"
    assert os.path.exists(path), f"{path} missing"


def test_k8s_deployment_exists():
    """Test K8s deployment manifest exists."""
    path = ".kilo/k8s/asimnexus-deployment.yaml"
    assert os.path.exists(path), f"{path} missing"


def test_nginx_config_exists():
    """Test nginx config exists."""
    path = "frontend/nginx.conf"
    assert os.path.exists(path), f"{path} missing"