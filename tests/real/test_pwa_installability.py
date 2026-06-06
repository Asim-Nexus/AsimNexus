#!/usr/bin/env python3
"""
Tests for PWA manifest validation and installability criteria.
"""

import json
from pathlib import Path

def test_pwa_manifest_structure():
    manifest_path = Path(__file__).resolve().parents[2] / "deploy" / "pwa" / "manifest.json"
    assert manifest_path.exists()
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
        
    # Check standard fields required for PWA installability
    assert "name" in manifest
    assert "short_name" in manifest
    assert "start_url" in manifest
    assert "display" in manifest
    assert manifest["display"] in ["standalone", "minimal-ui", "fullscreen"]
    assert "icons" in manifest
    assert len(manifest["icons"]) >= 1
    
    # Check that icons have required keys
    for icon in manifest["icons"]:
        assert "src" in icon
        assert "sizes" in icon
        assert "type" in icon
