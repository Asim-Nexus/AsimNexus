#!/usr/bin/env python3
"""
Tests to validate that Kubernetes YAML files are valid YAML syntax.
"""

from pathlib import Path
import yaml

def test_k8s_manifests_valid_yaml():
    k8s_dir = Path(__file__).resolve().parents[2] / "deploy" / "k8s"
    assert k8s_dir.exists()
    
    yaml_files = list(k8s_dir.glob("*.yaml")) + list(k8s_dir.glob("*.yml"))
    assert len(yaml_files) >= 5  # deployment, service, ingress, configmap, secret, pdb
    
    for f in yaml_files:
        with open(f, "r", encoding="utf-8") as file:
            content = file.read()
            # Parse all documents in the YAML file
            docs = list(yaml.safe_load_all(content))
            assert len(docs) >= 1
            for doc in docs:
                if doc is not None:
                    assert "apiVersion" in doc
                    assert "kind" in doc
                    assert "metadata" in doc
