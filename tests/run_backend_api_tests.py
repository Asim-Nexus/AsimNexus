
"""
STATUS: REAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Backend API Tests
===========================
Test all API endpoints
Run: python tests/test_backend_api.py
"""

import requests
import json
import sys
import time

BASE_URL = "http://localhost:8000"

def check_endpoint(method, endpoint, payload=None, description=""):
    """Test single endpoint"""
    try:
        url = f"{BASE_URL}{endpoint}"
        
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=payload, timeout=5)
        else:
            print(f"❌ Unknown method: {method}")
            return False
        
        status = "✅" if response.status_code == 200 else "⚠️"
        print(f"{status} {method} {endpoint} - {response.status_code}")
        
        if response.status_code == 200 and payload:
            try:
                data = response.json()
                print(f"   Response: {json.dumps(data, indent=2)[:200]}...")
            except Exception as e:
                logger.exception("Bare except fixed at line 40")
                print(f"   Response: {response.text[:100]}")
        
        return response.status_code == 200
        
    except requests.exceptions.ConnectionError:
        print(f"❌ {method} {endpoint} - Backend not running")
        return False
    except Exception as e:
        print(f"❌ {method} {endpoint} - {str(e)[:50]}")
        return False

def run_all_tests():
    """Run all API tests"""
    print("\n" + "="*70)
    print("🧪 ASIMNEXUS BACKEND API TESTS")
    print("="*70)
    print(f"Base URL: {BASE_URL}\n")
    
    # Check if backend is running
    try:
        requests.get(f"{BASE_URL}/health", timeout=2)
    except Exception as e:
        logger.exception("Bare except fixed at line 63")
        print("❌ Backend is not running!")
        print("   Start with: python simple_backend.py")
        return
    
    passed = 0
    failed = 0
    
    # Test Health
    print("\n--- Health Check ---")
    if check_endpoint("GET", "/health", description="Health check"):
        passed += 1
    else:
        failed += 1
    
    # Test ΔT Engine
    print("\n--- ΔT Engine ---")
    tests = [
        ("GET", "/api/dharma/status", None, "Dharma status"),
        ("GET", "/api/dharma/influence/status", None, "Influence status"),
        ("GET", "/api/dharma/veto/config", None, "Veto config"),
        ("GET", "/api/dharma/mesh/status", None, "Mesh status"),
    ]
    
    for method, endpoint, payload, desc in tests:
        if check_endpoint(method, endpoint, payload, desc):
            passed += 1
        else:
            failed += 1
    
    # Test Universe
    print("\n--- Personal Universe ---")
    
    # Create universe first
    if check_endpoint("POST", "/api/universe/create", {
        "user_id": "test_api_user",
        "email": "test_api@example.com",
        "display_name": "API Test User"
    }, "Create universe"):
        passed += 1
        
        # Get status
        if check_endpoint("GET", "/api/universe/test_api_user/status", None, "Universe status"):
            passed += 1
        else:
            failed += 1
            
        # Get lifecycle
        if check_endpoint("GET", "/api/universe/test_api_user/lifecycle", None, "Lifecycle"):
            passed += 1
        else:
            failed += 1
    else:
        failed += 3
    
    # Test Universe Stats
    if check_endpoint("GET", "/api/universe/stats", None, "Universe stats"):
        passed += 1
    else:
        failed += 1
    
    # Test Agent
    print("\n--- Agent Mode ---")
    
    if check_endpoint("POST", "/api/agent/mode/on", {
        "user_id": "test_api_user",
        "skills": ["research", "schedule"],
        "max_contract_days": 5
    }, "Activate agent mode"):
        passed += 1
    else:
        failed += 1
    
    if check_endpoint("GET", "/api/agent/status?user_id=test_api_user", None, "Agent status"):
        passed += 1
    else:
        failed += 1
    
    # Test Level-3 Confirmation
    print("\n--- Level-3 Confirmation ---")
    
    init_result = check_endpoint("POST", "/api/confirm/level3/initiate", {
        "action": "test_transfer",
        "params": {"value": 100, "recipient": "user_test"},
        "user_id": "test_api_user",
        "context": {"country_code": "NP"}
    }, "Initiate Level-3")
    
    if init_result:
        passed += 1
    else:
        failed += 1
    
    # Test Sovereignty
    print("\n--- Cultural Sovereignty ---")
    
    tests = [
        ("GET", "/api/sovereignty/countries", None, "List countries"),
        ("GET", "/api/sovereignty/country/NP", None, "Nepal profile"),
        ("GET", "/api/sovereignty/report", None, "Compliance report"),
    ]
    
    for method, endpoint, payload, desc in tests:
        if check_endpoint(method, endpoint, payload, desc):
            passed += 1
        else:
            failed += 1
    
    # Test compliance check
    if check_endpoint("POST", "/api/sovereignty/check", {
        "country_code": "NP",
        "action": "test_action",
        "params": {"value": 100}
    }, "Compliance check"):
        passed += 1
    else:
        failed += 1
    
    # Summary
    print("\n" + "="*70)
    print(f"📊 TEST RESULTS: {passed} passed, {failed} failed")
    total = passed + failed
    if total > 0:
        percentage = (passed / total) * 100
        print(f"📊 Success Rate: {percentage:.1f}%")
        
        if percentage >= 80:
            print("✅ Backend is working well!")
        elif percentage >= 50:
            print("⚠️ Some endpoints need attention")
        else:
            print("❌ Backend needs fixes")
    print("="*70 + "\n")

if __name__ == "__main__":
    run_all_tests()
