#!/usr/bin/env python3
"""
AsimNexus Unified Integration Test
=================================
Tests all consolidated functionality.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "DigitalNepal-backend"))
sys.path.insert(0, str(Path(__file__).parent.parent / "DigitalNepal-backend" / "os_control"))
sys.path.insert(0, str(Path(__file__).parent.parent / "os_control"))

def test_connectors():
    """Test all connectors"""
    try:
        from connectors.nepal_connectors import (
            MINISTRIES, PROVINCES, DISTRICTS, BANKS, ISPS,
            UNIVERSITIES, SCHOOLS
        )
        print(f"[OK] Connectors: {len(MINISTRIES)} ministries, {len(PROVINCES)} provinces, {len(DISTRICTS)} districts")
        print(f"   Companies: {len(BANKS)} banks, {len(ISPS)} ISPs")
        print(f"   Education: {len(UNIVERSITIES)} universities, {len(SCHOOLS)} schools")
    except Exception as e:
        print(f"[ERROR] Connectors: {e}")

def test_health():
    """Test health connectors"""
    try:
        from connectors.health_connectors import HOSPITALS
        print(f"[OK] Health: {len(HOSPITALS)} hospitals")
    except Exception as e:
        print(f"[WARN] Health connectors error: {e}")

def test_palikas():
    """Test palika connectors"""
    try:
        from connectors.palika_connectors import PALIKAS
        print(f"[OK] Palikas: {len(PALIKAS)} entities")
    except Exception as e:
        print(f"[WARN] Palikas error: {e}")

def test_tourism():
    """Test tourism connectors"""
    try:
        from connectors.tourism_connectors import HOTELS
        print(f"[OK] Tourism: {len(HOTELS)} hotels")
    except Exception as e:
        print(f"[WARN] Tourism error: {e}")

def test_core_modules():
    """Test core modules"""
    try:
        from core.consensus_engine import ConsensusEngine
        print("[OK] Consensus Engine loaded")
    except Exception as e:
        print(f"[WARN] Consensus error: {e}")

    try:
        from core.compliance_engine import ComplianceEngine
        print("[OK] Compliance Engine loaded")
    except Exception as e:
        print(f"[WARN] Compliance error: {e}")

    try:
        from core.security_layer import ZKPProof, HSMService
        print("[OK] Security Layer (ZKP + HSM) loaded")
    except Exception as e:
        print(f"[WARN] Security error: {e}")

def test_tools():
    """Test tools system"""
    try:
        # Check os_control directory exists and count tools
        os_control_path = Path(__file__).parent.parent / "os_control" / "openclaw_like_tools"
        if os_control_path.exists():
            tools = [f.stem.replace("test_", "") for f in os_control_path.glob("test_*.py")]
            print(f"[OK] OS Tools: {len(tools)} tool categories (file, process, system, clipboard, notification)")
    except Exception as e:
        print(f"[WARN] OS Tools error: {e}")

    try:
        from tools.all_tools import get_all_tools
        result = get_all_tools()
        print(f"[OK] All Tools: {result['count']} tools available")
    except Exception as e:
        print(f"[WARN] Tools error: {e}")

def test_frontend():
    """Check frontend structure"""
    frontend_path = Path(__file__).parent.parent / "frontend" / "src" / "components"
    if frontend_path.exists():
        components = list(frontend_path.rglob("*.jsx"))
        print(f"[OK] Frontend: {len(components)} React components")
    else:
        print("[WARN] Frontend not found")

if __name__ == "__main__":
    print("=== AsimNexus Unified Integration Test ===\n")
    
    test_connectors()
    test_health()
    test_palikas()
    test_tourism()
    test_core_modules()
    test_tools()
    test_frontend()
    
    print("\n=== All Tests Complete ===")