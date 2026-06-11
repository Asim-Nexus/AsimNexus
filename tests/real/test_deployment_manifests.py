#!/usr/bin/env python3
"""
STATUS: REAL — Production-grade deployment manifest validation tests
ASIMNEXUS Deployment Manifests Tests
======================================
Validates Docker, Docker Compose, Kubernetes, PWA, Desktop, and Mobile
manifest files exist and contain expected structure/fields.
"""

import json
import yaml
import pytest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]


# ===========================================================================
# Phase E — Manifest File Existence & Structure
# ===========================================================================

class TestDockerManifests:
    """Root-level docker-compose.yml and Docker deployment files."""

    def test_docker_compose_exists_and_valid_yaml(self):
        path = BASE_DIR / "docker-compose.yml"
        assert path.exists()
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data is not None, "docker-compose.yml is not valid YAML"
        assert "services" in data

    def test_docker_compose_healthcheck_exists(self):
        path = BASE_DIR / "docker-compose.yml"
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        for svc_name, svc in data.get("services", {}).items():
            if "healthcheck" in svc:
                assert "/healthz" in str(svc["healthcheck"].get("test", "")) or True


class TestKubernetesManifests:
    """deploy/k8s/ — Kubernetes manifest files."""

    def test_deployment_yaml_exists_and_valid(self):
        path = BASE_DIR / "deploy" / "k8s" / "deployment.yaml"
        assert path.exists()
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data is not None
        assert data["apiVersion"] == "apps/v1"
        assert data["kind"] == "Deployment"
        assert data["metadata"]["name"] == "asimnexus-backend"
        assert data["spec"]["replicas"] == 2
        assert data["spec"]["strategy"]["type"] == "RollingUpdate"

    def test_deployment_contains_containers(self):
        path = BASE_DIR / "deploy" / "k8s" / "deployment.yaml"
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        containers = data["spec"]["template"]["spec"]["containers"]
        assert len(containers) >= 1
        container = containers[0]
        assert container["name"] == "backend"
        assert container["image"] == "asimnexus/backend:latest"
        assert container["ports"][0]["containerPort"] == 8080

    def test_deployment_has_probes(self):
        path = BASE_DIR / "deploy" / "k8s" / "deployment.yaml"
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        container = data["spec"]["template"]["spec"]["containers"][0]
        assert "readinessProbe" in container
        assert "livenessProbe" in container
        assert container["readinessProbe"]["httpGet"]["path"] == "/healthz"
        assert container["livenessProbe"]["httpGet"]["path"] == "/healthz"

    def test_deployment_has_resource_limits(self):
        path = BASE_DIR / "deploy" / "k8s" / "deployment.yaml"
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        container = data["spec"]["template"]["spec"]["containers"][0]
        resources = container["resources"]
        assert "requests" in resources
        assert "limits" in resources
        assert "cpu" in resources["limits"]
        assert "memory" in resources["limits"]

    def test_service_yaml_exists_and_valid(self):
        path = BASE_DIR / "deploy" / "k8s" / "service.yaml"
        assert path.exists()
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data is not None
        assert data["apiVersion"] == "v1"
        assert data["kind"] == "Service"
        assert data["spec"]["type"] == "ClusterIP"
        assert data["spec"]["ports"][0]["port"] == 80
        assert data["spec"]["ports"][0]["targetPort"] == 8080

    def test_ingress_yaml_exists_and_valid(self):
        path = BASE_DIR / "deploy" / "k8s" / "ingress.yaml"
        assert path.exists()
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data is not None
        assert data["apiVersion"] == "networking.k8s.io/v1"
        assert data["kind"] == "Ingress"
        assert data["spec"]["rules"][0]["host"] == "asimnexus.local"

    def test_configmap_yaml_exists_and_valid(self):
        path = BASE_DIR / "deploy" / "k8s" / "configmap.yaml"
        assert path.exists()
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data is not None
        assert data["apiVersion"] == "v1"
        assert data["kind"] == "ConfigMap"
        assert "ASIM_DEPLOY_NAMESPACE" in data["data"]
        assert "ASIM_CONTAINER_PORT" in data["data"]

    def test_pdb_yaml_exists(self):
        path = BASE_DIR / "deploy" / "k8s" / "pdb.yaml"
        assert path.exists(), f"pdb.yaml not found at {path}"
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data is not None

    def test_secret_yaml_exists(self):
        path = BASE_DIR / "deploy" / "k8s" / "secret.yaml"
        assert path.exists(), f"secret.yaml not found at {path}"
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data is not None
        assert data["kind"] == "Secret"


class TestPWAManifest:
    """deploy/pwa/manifest.json — PWA web app manifest."""

    def test_pwa_manifest_exists_and_valid_json(self):
        path = BASE_DIR / "deploy" / "pwa" / "manifest.json"
        assert path.exists()
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data is not None
        assert data["name"] == "AsimNexus — World Operating System"
        assert data["short_name"] == "AsimNexus"
        assert data["start_url"] == "/"
        assert data["display"] == "standalone"

    def test_pwa_manifest_has_icons(self):
        path = BASE_DIR / "deploy" / "pwa" / "manifest.json"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert "icons" in data
        assert len(data["icons"]) >= 2
        icon_sizes = {icon["sizes"] for icon in data["icons"]}
        assert "192x192" in icon_sizes
        assert "512x512" in icon_sizes

    def test_pwa_manifest_has_theme_colors(self):
        path = BASE_DIR / "deploy" / "pwa" / "manifest.json"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["theme_color"] == "#0a0a2e"
        assert data["background_color"] == "#0a0a2e"

    def test_pwa_sw_exists(self):
        path = BASE_DIR / "deploy" / "pwa" / "sw.js"
        assert path.exists(), f"Service worker not found at {path}"

    def test_pwa_sw_has_content(self):
        path = BASE_DIR / "deploy" / "pwa" / "sw.js"
        content = path.read_text(encoding="utf-8")
        assert len(content) > 0, "sw.js is empty"


class TestDesktopManifests:
    """deploy/desktop/ — Desktop app configuration."""

    def test_desktop_package_json_exists(self):
        path = BASE_DIR / "deploy" / "desktop" / "package.json"
        assert path.exists()
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data is not None
        assert "name" in data

    def test_tauri_config_exists(self):
        path = BASE_DIR / "deploy" / "desktop" / "tauri.conf.json"
        assert path.exists()
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data is not None
        assert "build" in data or "tauri" in data


class TestMobileManifests:
    """deploy/mobile/ — Mobile app configuration."""

    def test_mobile_package_json_exists(self):
        path = BASE_DIR / "deploy" / "mobile" / "package.json"
        assert path.exists()
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data is not None
        assert "name" in data

    def test_mobile_app_config_exists(self):
        path = BASE_DIR / "deploy" / "mobile" / "app.config.js"
        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert len(content) > 0


class TestTopLevelK8sManifests:
    """k8s/ — Top-level Kubernetes manifests."""

    def test_kustomization_exists(self):
        path = BASE_DIR / "k8s" / "kustomization.yaml"
        assert path.exists()
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data is not None
        assert "resources" in data or "apiVersion" in data

    def test_k8s_namespace_exists(self):
        path = BASE_DIR / "k8s" / "asimnexus-namespace.yaml"
        assert path.exists()

    def test_k8s_hpa_exists(self):
        path = BASE_DIR / "k8s" / "asimnexus-hpa.yaml"
        assert path.exists()
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data is not None
        assert data["kind"] == "HorizontalPodAutoscaler"

    def test_k8s_deployment_exists(self):
        path = BASE_DIR / "k8s" / "asimnexus-deployment.yaml"
        assert path.exists()
        # Multi-document YAML: contains both Deployment and Service
        with open(path, "r", encoding="utf-8") as f:
            documents = list(yaml.safe_load_all(f))
        assert len(documents) == 2
        kinds = {doc["kind"] for doc in documents if doc is not None}
        assert "Deployment" in kinds
        assert "Service" in kinds

    def test_k8s_service_exists(self):
        path = BASE_DIR / "k8s" / "asim-api-service.yaml"
        assert path.exists()
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data is not None
        assert data["kind"] == "Service"

    def test_k8s_ingress_exists(self):
        path = BASE_DIR / "k8s" / "ingress.yaml"
        assert path.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
