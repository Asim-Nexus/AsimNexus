#!/usr/bin/env python3
"""
STATUS: REAL — Relocated smoke test
ASIMNEXUS Infrastructure Test
===============================
Test CDN and Mesh network endpoints

NOTE: Requires a running server at BASE_URL.
Set ASIM_SERVER_RUNNING=1 to skip server check.
"""

import requests
import json
import os
import sys
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

def _server_available() -> bool:
    """Check if the server is running."""
    if os.environ.get("ASIM_SERVER_RUNNING", "").lower() in ("1", "true", "yes"):
        return True
    try:
        resp = requests.get(f"{BASE_URL}/health/live", timeout=2)
        return resp.status_code == 200
    except Exception:
        return False

def _test_endpoint(url, name, method='GET', data=None):
    """Test a single endpoint"""
    try:
        if method == 'GET':
            response = requests.get(f"{BASE_URL}{url}", timeout=5)
        else:
            response = requests.post(f"{BASE_URL}{url}", json=data, timeout=5)
        
        if response.status_code == 200:
            data_resp = response.json()
            print(f"✅ {name}: OK")
            return True, data_resp
        else:
            print(f"❌ {name}: HTTP {response.status_code}")
            return False, None
    except Exception as e:
        print(f"❌ {name}: {str(e)}")
        return False, None

def test_infrastructure():
    """Test all infrastructure endpoints"""
    print("=" * 60)
    print("🌐 ASIMNEXUS Infrastructure Test")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Base URL: {BASE_URL}")
    print("-" * 60)
    
    results = {}
    
    # 1. Infrastructure Status
    print("\n🌍 Global Infrastructure Status:")
    ok, data = _test_endpoint("/api/infrastructure/status", "Infrastructure Status")
    results['infrastructure_status'] = ok
    if ok and data:
        cdn = data.get('infrastructure', {}).get('cdn', {})
        mesh = data.get('infrastructure', {}).get('mesh', {})
        print(f"  CDN Locations: {cdn.get('total_locations', 0)}")
        print(f"  Countries Covered: {cdn.get('countries_covered', 0)}")
        print(f"  Mesh Nodes: {mesh.get('total_nodes', 0)}")
        print(f"  Dharma Avg: {mesh.get('avg_dharma_score', 0)}")
    
    # 2. CDN Locations
    print("\n🌐 CDN Edge Locations:")
    ok, data = _test_endpoint("/api/infrastructure/cdn/locations", "CDN Locations")
    results['cdn_locations'] = ok
    if ok and data:
        print(f"  Total locations: {data.get('stats', {}).get('total_locations', 0)}")
        print(f"  Tier 1: {data.get('stats', {}).get('tier1', 0)}")
        regions = list(data.get('stats', {}).get('by_region', {}).keys())[:5]
        print(f"  Regions: {regions}")
    
    # CDN Routing
    ok, data = _test_endpoint("/api/infrastructure/cdn/routing/NP", "CDN Routing Nepal")
    if ok and data:
        print(f"  Primary: {data.get('primary', {}).get('name', 'N/A')}")
    
    # CDN Nearest
    ok, data = _test_endpoint("/api/infrastructure/cdn/nearest?lat=27.7172&lon=85.3240", "CDN Nearest Kathmandu")
    if ok and data:
        nearest_name = data.get('nearest', {}).get('name', 'N/A')
        print(f"  Nearest: {nearest_name}")
    
    # 3. Mesh Network
    print("\n📡 Federated Mesh Network:")
    ok, data = _test_endpoint("/api/infrastructure/mesh/status", "Mesh Status")
    results['mesh_status'] = ok
    if ok and data:
        mesh_stats = data.get('mesh', {})
        print(f"  Total nodes: {mesh_stats.get('total_nodes', 0)}")
        print(f"  Online: {mesh_stats.get('online_nodes', 0)}")
        print(f"  Dharma avg: {mesh_stats.get('avg_dharma_score', 0)}")
    
    # Mesh Nodes
    ok, data = _test_endpoint("/api/infrastructure/mesh/nodes", "Mesh Nodes")
    if ok and data:
        print(f"  Nodes returned: {data.get('total', 0)}")
        if data.get('total', 0) > 0:
            first = data['nodes'][0]
            print(f"  Sample: {first.get('name')} ({first.get('country')})")
    
    # Sovereign Nodes
    ok, data = _test_endpoint("/api/infrastructure/mesh/sovereign-nodes", "Sovereign Nodes")
    if ok and data:
        sovereign = data.get('sovereign_nodes', [])
        print(f"  Sovereign nodes: {len(sovereign)}")
        for node in sovereign[:3]:
            print(f"    {node.get('country')}: {node.get('name')} (Dharma: {node.get('dharma_score')})")
    
    # 4. Join Mesh
    print("\n🔗 Join Mesh Network:")
    ok, data = _test_endpoint("/api/infrastructure/mesh/join", "Join Mesh",
                            method='POST',
                            data={'user_id': 'test_user', 'country': 'NP', 
                                  'latitude': 27.7172, 'longitude': 85.3240})
    results['mesh_join'] = ok
    if ok and data:
        print(f"  Node ID: {data.get('node_id', 'N/A')[:20]}...")
        print(f"  Connections: {len(data.get('connections', []))}")
        print(f"  Dharma Score: {data.get('dharma_score', 0)}")
    
    # 5. Summary
    print("\n" + "=" * 60)
    print("📋 Test Summary:")
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    print(f"  Total tests: {total}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {total - passed}")
    
    if passed == total:
        print("\n✅ All infrastructure systems working!")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed")
    
    print("=" * 60)
    assert passed == total, f"{total - passed} test(s) failed"

if __name__ == "__main__":
    if not _server_available():
        print(f"⚠️  Server at {BASE_URL} not available. Set ASIM_SERVER_RUNNING=1 to force.")
        sys.exit(0)  # Skip gracefully
    success = test_infrastructure()
    exit(0 if success else 1)
