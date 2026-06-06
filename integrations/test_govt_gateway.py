
"""
STATUS: REAL — Auto-labeled by batch_label.py
"""

"""
Test Government Gateway
=======================
Test government API integration
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from govt_gateway import get_govt_gateway, GovtService

def test_govt_gateway():
    """Test Government Gateway functionality"""
    
    print("🧪 Testing Government Gateway")
    print("=" * 60)
    
    gateway = get_govt_gateway()
    
    # Test 1: Get status
    print("\n📊 Government Gateway Status:")
    status = gateway.get_status()
    print(f"   API Key Configured: {status['api_key_configured']}")
    print(f"   Base URL: {status['base_url']}")
    print(f"   Total Requests: {status['total_requests']}")
    print(f"   Available Services: {status['available_services']}")
    
    # Test 2: Get available services
    print("\n📋 Available Government Services:")
    services = gateway.get_available_services()
    for service in services:
        print(f"   - {service['service']}: {service['description']}")
        print(f"     Endpoints: {', '.join(service['endpoints'])}")
    
    # Test 3: Nagarik App verification (mock)
    print("\n📱 Testing Nagarik App Verification (Mock):")
    result = gateway.make_request(
        service=GovtService.NAGARIK_APP,
        endpoint="/verify/citizenship",
        parameters={"citizenship_number": "12345678"},
        use_mock=True
    )
    print(f"   Success: {result['success']}")
    print(f"   Mode: {result['mode']}")
    if result['success']:
        print(f"   Status: {result['data']['status']}")
        print(f"   Citizen Data: {result['data'].get('citizenship_data', {})}")
    
    # Test 4: Citizenship verification (mock)
    print("\n📄 Testing Citizenship Verification (Mock):")
    result = gateway.make_request(
        service=GovtService.CITIZENSHIP_VERIFICATION,
        endpoint="/verify/citizenship",
        parameters={"citizenship_number": "12345678"},
        use_mock=True
    )
    print(f"   Success: {result['success']}")
    print(f"   Valid: {result['data'].get('valid')}")
    print(f"   Verification ID: {result['data'].get('verification_id')}")
    
    # Test 5: License verification (mock)
    print("\n🚗 Testing License Verification (Mock):")
    result = gateway.make_request(
        service=GovtService.LICENSE_VERIFICATION,
        endpoint="/verify/license",
        parameters={"license_number": "NEP123456"},
        use_mock=True
    )
    print(f"   Success: {result['success']}")
    print(f"   Valid: {result['data'].get('valid')}")
    if result['data'].get('valid'):
        print(f"   License Data: {result['data'].get('license_data', {})}")
    
    # Test 6: Public services (mock)
    print("\n🏛️ Testing Public Services (Mock):")
    result = gateway.make_request(
        service=GovtService.PUBLIC_SERVICES,
        endpoint="/services/list",
        parameters={"service_type": "all"},
        use_mock=True
    )
    print(f"   Success: {result['success']}")
    print(f"   Total Services: {result['data'].get('total_services')}")
    
    # Test 7: List requests
    print("\n📜 Request History:")
    requests = gateway.list_requests(limit=5)
    print(f"   Total: {len(requests)}")
    for req in requests:
        print(f"   - {req['request_id']}: {req['service']} ({req['status']})")
    
    print("\n" + "=" * 60)
    print("🎯 Test Complete")
    print("=" * 60)
    print("\n💡 Government Gateway ready for API integration!")
    print("\n📝 To use with real government APIs:")
    print("   1. Set GOVT_API_KEY environment variable")
    print("   2. Set GOVT_API_BASE_URL to official government API endpoint")
    print("   3. Use: gateway.make_request(service, endpoint, params, use_mock=False)")
    print("\n⚠️  Note: Real government API integration requires official credentials")

if __name__ == "__main__":
    test_govt_gateway()
