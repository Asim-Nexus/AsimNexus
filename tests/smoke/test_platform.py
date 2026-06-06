#!/usr/bin/env python3
"""
STATUS: REAL — Relocated smoke test
ASIMNEXUS Platform Test
=========================
Test PWA, Desktop, Mobile platform endpoints
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

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

def test_platform():
    """Test all platform endpoints"""
    print("=" * 60)
    print("📱 ASIMNEXUS Multi-Platform Test")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Base URL: {BASE_URL}")
    print("-" * 60)
    
    results = {}
    
    # 1. Platform Status
    print("\n🌐 Platform Support:")
    ok, data = _test_endpoint("/api/platform/status", "Platform Status")
    results['platform_status'] = ok
    if ok and data:
        print(f"  Supported: {', '.join(data.get('supported_platforms', []))}")
    
    # 2. Downloads
    print("\n📥 Download Links:")
    ok, data = _test_endpoint("/api/platform/downloads", "Downloads")
    results['downloads'] = ok
    if ok and data:
        for platform, info in data.get('platforms', {}).items():
            print(f"  {platform}: {info.get('name')}")
            print(f"    Features: {', '.join(info.get('features', [])[:3])}...")
    
    # 3. PWA Config
    print("\n📱 PWA Configuration:")
    ok, data = _test_endpoint("/api/pwa/config", "PWA Config")
    results['pwa_config'] = ok
    if ok and data:
        print(f"  Theme: {data.get('theme_color')}")
        print(f"  Shortcuts: {len(data.get('shortcuts', []))}")
    
    # 4. Register Platform (Web)
    print("\n🔧 Register Web Platform:")
    ok, data = _test_endpoint("/api/platform/register", "Register Web",
                            method='POST',
                            data={'platform_hint': 'web', 'session_id': 'test_web_001'})
    results['register_web'] = ok
    if ok and data:
        print(f"  Session: {data.get('session_id', 'N/A')[:20]}...")
        print(f"  Platform: {data.get('platform', {}).get('platform')}")
        print(f"  Capabilities: {len(data.get('platform', {}).get('capabilities', []))}")
    
    # 5. Register Platform (Mobile)
    print("\n🔧 Register Mobile Platform:")
    ok, data = _test_endpoint("/api/platform/register", "Register Mobile",
                            method='POST',
                            data={'platform_hint': 'ios', 'session_id': 'test_mobile_001'})
    results['register_mobile'] = ok
    if ok and data:
        print(f"  Platform: {data.get('platform', {}).get('platform')}")
        print(f"  Biometrics: {'biometrics' in data.get('platform', {}).get('capabilities', [])}")
    
    # 6. Offline Data
    print("\n📴 Offline Support:")
    ok, data = _test_endpoint("/api/offline/data", "Offline Data")
    results['offline_data'] = ok
    if ok and data:
        print(f"  Offline ready: {data.get('offline_ready')}")
        print(f"  Max offline: {data.get('max_offline_duration_hours')} hours")
        print(f"  Cached endpoints: {len(data.get('cached_endpoints', []))}")
    
    # 7. Push Notifications
    print("\n🔔 Push Notifications:")
    ok, data = _test_endpoint("/api/push/subscribe", "Subscribe Push",
                            method='POST',
                            data={'endpoint': 'https://fcm.example.com/token', 
                                  'keys': {'p256dh': 'test', 'auth': 'test'},
                                  'platform': 'web', 'user_id': 'test_user'})
    results['push_subscribe'] = ok
    if ok and data:
        print(f"  Subscription ID: {data.get('subscription_id')}")
        print(f"  Message: {data.get('message')}")
    
    # 8. Summary
    print("\n" + "=" * 60)
    print("📋 Test Summary:")
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    print(f"  Total tests: {total}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {total - passed}")
    
    if passed == total:
        print("\n✅ All platform systems working!")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed")
    
    print("=" * 60)
    return passed == total

if __name__ == "__main__":
    success = test_platform()
    exit(0 if success else 1)
