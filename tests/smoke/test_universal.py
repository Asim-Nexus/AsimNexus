#!/usr/bin/env python3
"""
STATUS: REAL — Relocated smoke test
ASIMNEXUS Universal Systems Test
=================================
Test all worldwide universal systems
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

def _test_endpoint(url, name):
    """Test a single endpoint"""
    try:
        response = requests.get(f"{BASE_URL}{url}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {name}: OK")
            return True, data
        else:
            print(f"❌ {name}: HTTP {response.status_code}")
            return False, None
    except Exception as e:
        print(f"❌ {name}: {str(e)}")
        return False, None

def test_universal_systems():
    """Test all universal system endpoints"""
    print("=" * 60)
    print("🌍 ASIMNEXUS Universal Systems Test")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Base URL: {BASE_URL}")
    print("-" * 60)
    
    results = {}
    
    # 1. Universal Status
    print("\n📊 Universal System Status:")
    ok, data = _test_endpoint("/api/universal/status", "Universal Status")
    results['universal_status'] = ok
    if ok and data:
        print(f"  Currencies: {data.get('universal_systems', {}).get('currency', {}).get('total_currencies', 0)}")
        print(f"  Countries: {data.get('universal_systems', {}).get('legal', {}).get('total_countries', 0)}")
        print(f"  Timezones: {data.get('universal_systems', {}).get('timezone', {}).get('total_timezones', 0)}")
        print(f"  Languages: {data.get('universal_systems', {}).get('i18n', {}).get('tier1_languages', 0)}")
    
    # 2. Currencies
    print("\n💰 Currency System:")
    ok, data = _test_endpoint("/api/universal/currencies", "All Currencies")
    results['currencies'] = ok
    if ok and data:
        print(f"  Total currencies: {data.get('total', 0)}")
        
    # Country-specific currencies
    ok, data = _test_endpoint("/api/universal/currencies/US", "US Currencies")
    if ok and data:
        print(f"  US currencies: {data.get('count', 0)}")
    
    ok, data = _test_endpoint("/api/universal/currencies/NP", "Nepal Currencies")
    if ok and data:
        print(f"  Nepal currencies: {data.get('count', 0)}")
    
    # 3. Countries
    print("\n🏛️ Legal Framework:")
    ok, data = _test_endpoint("/api/universal/countries", "All Countries")
    results['countries'] = ok
    if ok and data:
        print(f"  Total countries: {data.get('total', 0)}")
        print(f"  Dharma compatible: {data.get('stats', {}).get('dharma_compatible', 0)}")
        print(f"  Crypto friendly: {data.get('stats', {}).get('crypto_friendly', 0)}")
    
    # Country details
    ok, data = _test_endpoint("/api/universal/countries/NP", "Nepal Details")
    if ok and data:
        print(f"  Nepal - Dharma: {data.get('dharma_compatible')}")
        print(f"  Nepal - Crypto: {data.get('crypto_regulation')}")
    
    ok, data = _test_endpoint("/api/universal/countries/US", "US Details")
    if ok and data:
        print(f"  US - Dharma: {data.get('dharma_compatible')}")
    
    # 4. Languages
    print("\n🗣️ Language System:")
    ok, data = _test_endpoint("/api/universal/languages", "All Languages")
    results['languages'] = ok
    if ok and data:
        print(f"  Total languages: {data.get('total', 0)}")
        print(f"  Est. speakers: {data.get('stats', {}).get('estimated_speakers_billions', 0)} billion")
    
    # Language details
    ok, data = _test_endpoint("/api/universal/languages/ne", "Nepali Details")
    if ok and data:
        print(f"  Nepali - Speakers: {data.get('speakers_millions', 0)}M")
        print(f"  Nepali - Translation: {data.get('sample_translations', {}).get('welcome', '')}")
    
    # 5. Timezones
    print("\n🕐 Timezone System:")
    ok, data = _test_endpoint("/api/universal/timezones", "All Timezones")
    results['timezones'] = ok
    if ok and data:
        print(f"  Total timezones: {data.get('stats', {}).get('total_timezones', 0)}")
        print(f"  Countries covered: {data.get('stats', {}).get('countries_covered', 0)}")
    
    # Country timezones
    ok, data = _test_endpoint("/api/universal/timezones/NP", "Nepal Timezones")
    if ok and data:
        print(f"  Nepal timezones: {len(data.get('timezones', []))}")
    
    # 6. Summary
    print("\n" + "=" * 60)
    print("📋 Test Summary:")
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    print(f"  Total tests: {total}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {total - passed}")
    
    if passed == total:
        print("\n✅ All universal systems working correctly!")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed")
    
    print("=" * 60)
    assert passed == total, f"{total - passed} test(s) failed"

if __name__ == "__main__":
    success = test_universal_systems()
    exit(0 if success else 1)
