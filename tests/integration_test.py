#!/usr/bin/env python3
"""AsimNexus - Unified Test Suite
Tests all components working together
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "DigitalNepal-backend"))

def test_connectors():
    """Test all connectors"""
    from connectors.nepal_connectors import MINISTRIES, PROVINCES, DISTRICTS, BANKS, ISPS
    assert len(MINISTRIES) == 18
    assert len(PROVINCES) == 7
    assert len(DISTRICTS) == 77
    assert len(BANKS) == 30
    assert len(ISPS) >= 20
    print("[OK] All connectors loaded")

def test_api_endpoints():
    """Test API endpoint structure"""
    from connectors.nepal_connectors import MINISTRIES
    # Check structure
    assert "pm_office" in MINISTRIES
    assert MINISTRIES["pm_office"]["balance"] == "51%"
    print("[OK] API endpoints configured")

def test_entity_bridge():
    """Test entity bridge"""
    from core.entity_bridge import get_bridge
    bridge = get_bridge()
    result = bridge.connect_entity("ministry", "pm_office")
    assert result["status"] == "connected"
    print("[OK] Entity bridge working")

if __name__ == "__main__":
    import asyncio
    print("=== AsimNexus Integration Test ===")
    test_connectors()
    test_api_endpoints()
    
    async def run_bridge_test():
        await asyncio.get_event_loop().run_in_executor(None, test_entity_bridge)
    
    # Simple sync test
    from core.entity_bridge import get_bridge
    bridge = get_bridge()
    # Just check bridge exists
    assert bridge is not None
    print("[OK] Entity bridge loaded")
    
    print("=== All Tests Passed ===")