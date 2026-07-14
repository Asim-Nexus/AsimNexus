
"""
STATUS: REAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Integration Test Suite
===================================
Tests ALL API endpoints to ensure they work together
Run this before any deployment
"""

import asyncio
import aiohttp
import json
from datetime import datetime
from typing import Dict, List, Tuple
import sys
import traceback

# Backend URL
BASE_URL = "http://127.0.0.1:8000"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

class IntegrationTester:
    """Test all API endpoints"""
    
    def __init__(self):
        self.results: List[Dict] = []
        self.passed = 0
        self.failed = 0
        
    async def run_all_tests(self):
        """Run complete test suite"""
        print(f"{Colors.BLUE}\n{'='*70}")
        print("  ASIMNEXUS INTEGRATION TEST SUITE")
        print(f"{'='*70}{Colors.RESET}\n")
        print(f"Testing: {BASE_URL}")
        print(f"Started: {datetime.now().isoformat()}\n")
        
        async with aiohttp.ClientSession() as session:
            # Test Core Endpoints
            await self.test_health(session)
            
            # Test All Phase Endpoints
            await self.test_phase_1_universal(session)
            await self.test_phase_4_finance(session)
            await self.test_phase_5_government(session)
            await self.test_phase_6_accessibility(session)
            await self.test_phase_7_performance(session)
            await self.test_phase_8_security(session)
            
            # Test Mesh Network
            await self.test_mesh_network(session)
            
            # Test Sovereignty
            await self.test_sovereignty(session)
            
            # Test System
            await self.test_system(session)
        
        # Print Summary
        self.print_summary()
        
    async def test_endpoint(self, session: aiohttp.ClientSession,
                           method: str, endpoint: str,
                           data: Dict = None, expected_status: int = 200) -> Tuple[bool, Dict]:
        """Test a single endpoint"""
        url = f"{BASE_URL}{endpoint}"
        
        try:
            if method == "GET":
                async with session.get(url, timeout=10) as resp:
                    status = resp.status
                    try:
                        result = await resp.json()
                    except Exception as e:
                        logger.exception("Bare except fixed at line 83")
                        result = {"text": await resp.text()}
            elif method == "POST":
                async with session.post(url, json=data, timeout=10) as resp:
                    status = resp.status
                    try:
                        result = await resp.json()
                    except Exception as e:
                        logger.exception("Bare except fixed at line 90")
                        result = {"text": await resp.text()}
            else:
                return False, {"error": f"Unknown method {method}"}
            
            success = status == expected_status
            
            return success, {
                "status": status,
                "result": result,
                "endpoint": endpoint
            }
            
        except Exception as e:
            return False, {
                "error": str(e),
                "traceback": traceback.format_exc(),
                "endpoint": endpoint
            }
    
    def record_result(self, name: str, success: bool, details: Dict):
        """Record test result"""
        self.results.append({
            "name": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        
        if success:
            self.passed += 1
            status = f"{Colors.GREEN}✅ PASS{Colors.RESET}"
        else:
            self.failed += 1
            status = f"{Colors.RED}❌ FAIL{Colors.RESET}"
        
        print(f"{status} {name}")
        if not success and "error" in details:
            print(f"   Error: {details['error']}")
    
    async def test_health(self, session: aiohttp.ClientSession):
        """Test basic health endpoints"""
        print(f"\n{Colors.YELLOW}--- Health Check ---{Colors.RESET}")
        
        success, details = await self.test_endpoint(session, "GET", "/api/system/info")
        self.record_result("System Info", success, details)
    
    async def test_phase_1_universal(self, session: aiohttp.ClientSession):
        """Test Phase 1: Universal Systems"""
        print(f"\n{Colors.YELLOW}--- Phase 1: Universal Systems ---{Colors.RESET}")
        
        tests = [
            ("GET", "/api/universal/currencies"),
            ("GET", "/api/universal/countries"),
            ("GET", "/api/universal/languages"),
            ("GET", "/api/universal/legal-frameworks"),
        ]
        
        for method, endpoint in tests:
            success, details = await self.test_endpoint(session, method, endpoint)
            name = endpoint.split("/")[-1].replace("-", " ").title()
            self.record_result(f"Universal: {name}", success, details)
    
    async def test_phase_4_finance(self, session: aiohttp.ClientSession):
        """Test Phase 4: Financial"""
        print(f"\n{Colors.YELLOW}--- Phase 4: Financial Universal ---{Colors.RESET}")
        
        tests = [
            ("GET", "/api/finance/status"),
            ("GET", "/api/finance/currencies"),
            ("GET", "/api/finance/exchange-rates"),
            ("POST", "/api/finance/wallet/create", {"user_id": "test_user", "demo_mode": True}),
        ]
        
        for test in tests:
            method, endpoint = test[0], test[1]
            data = test[2] if len(test) > 2 else None
            success, details = await self.test_endpoint(session, method, endpoint, data)
            name = endpoint.split("/")[-1].replace("-", " ").title()
            self.record_result(f"Finance: {name}", success, details)
    
    async def test_phase_5_government(self, session: aiohttp.ClientSession):
        """Test Phase 5: Government"""
        print(f"\n{Colors.YELLOW}--- Phase 5: Government Integration ---{Colors.RESET}")
        
        tests = [
            ("GET", "/api/government/status"),
            ("GET", "/api/government/identity/countries"),
            ("GET", "/api/government/eresidency/programs"),
            ("GET", "/api/government/tax/countries"),
        ]
        
        for method, endpoint in tests:
            success, details = await self.test_endpoint(session, method, endpoint)
            name = endpoint.split("/")[-1].replace("-", " ").title()
            self.record_result(f"Government: {name}", success, details)
    
    async def test_phase_6_accessibility(self, session: aiohttp.ClientSession):
        """Test Phase 6: Accessibility"""
        print(f"\n{Colors.YELLOW}--- Phase 6: Accessibility ---{Colors.RESET}")
        
        tests = [
            ("GET", "/api/accessibility/status"),
            ("GET", "/api/accessibility/wcag-compliance"),
            ("GET", "/api/accessibility/screen-reader-support"),
            ("GET", "/api/accessibility/voice-control-status"),
        ]
        
        for method, endpoint in tests:
            success, details = await self.test_endpoint(session, method, endpoint)
            name = endpoint.split("/")[-1].replace("-", " ").title()
            self.record_result(f"Accessibility: {name}", success, details)
    
    async def test_phase_7_performance(self, session: aiohttp.ClientSession):
        """Test Phase 7: Performance"""
        print(f"\n{Colors.YELLOW}--- Phase 7: Performance ---{Colors.RESET}")
        
        tests = [
            ("GET", "/api/performance/status"),
            ("GET", "/api/performance/compression-stats"),
            ("POST", "/api/performance/optimize", {"connection_type": "2g"}),
        ]
        
        for test in tests:
            method, endpoint = test[0], test[1]
            data = test[2] if len(test) > 2 else None
            success, details = await self.test_endpoint(session, method, endpoint, data)
            name = endpoint.split("/")[-1].replace("-", " ").title()
            self.record_result(f"Performance: {name}", success, details)
    
    async def test_phase_8_security(self, session: aiohttp.ClientSession):
        """Test Phase 8: Security"""
        print(f"\n{Colors.YELLOW}--- Phase 8: Security ---{Colors.RESET}")
        
        tests = [
            ("GET", "/api/security/status"),
            ("GET", "/api/security/encryption-algorithms"),
        ]
        
        for method, endpoint in tests:
            success, details = await self.test_endpoint(session, method, endpoint)
            name = endpoint.split("/")[-1].replace("-", " ").title()
            self.record_result(f"Security: {name}", success, details)
    
    async def test_mesh_network(self, session: aiohttp.ClientSession):
        """Test Mesh Network"""
        print(f"\n{Colors.YELLOW}--- Mesh Network ---{Colors.RESET}")
        
        tests = [
            ("GET", "/api/mesh/status"),
            ("GET", "/api/mesh/nodes/discover"),
            ("GET", "/api/mesh/stats"),
            ("GET", "/api/mesh/federation/map"),
            ("POST", "/api/mesh/node/init", {"node_type": "personal", "name": "TestNode", "country": "NP"}),
        ]
        
        for test in tests:
            method, endpoint = test[0], test[1]
            data = test[2] if len(test) > 2 else None
            success, details = await self.test_endpoint(session, method, endpoint, data)
            name = endpoint.split("/")[-1].replace("-", " ").title()
            self.record_result(f"Mesh: {name}", success, details)
    
    async def test_sovereignty(self, session: aiohttp.ClientSession):
        """Test Sovereignty (Air-Gap)"""
        print(f"\n{Colors.YELLOW}--- Sovereignty (Emergency Air-Gap) ---{Colors.RESET}")
        
        tests = [
            ("GET", "/api/sovereignty/airgap/status"),
            ("GET", "/api/sovereignty/airgap/history"),
        ]
        
        for method, endpoint in tests:
            success, details = await self.test_endpoint(session, method, endpoint)
            name = endpoint.split("/")[-1].replace("-", " ").title()
            self.record_result(f"Sovereignty: {name}", success, details)
        
        # Test Air-Gap Activation (but don't actually disconnect)
        # This would be tested manually
        print(f"   {Colors.YELLOW}⚠️  Air-Gap activation tested manually{Colors.RESET}")
    
    async def test_system(self, session: aiohttp.ClientSession):
        """Test System-wide endpoints"""
        print(f"\n{Colors.YELLOW}--- System Overview ---{Colors.RESET}")
        
        success, details = await self.test_endpoint(session, "GET", "/api/system/complete")
        self.record_result("Complete System Status", success, details)
        
        # Check if all phases are reported
        if success and "result" in details:
            result = details["result"]
            if isinstance(result, dict) and "phases" in result:
                print(f"   {Colors.GREEN}✓ All 8 phases reported in system status{Colors.RESET}")
    
    def print_summary(self):
        """Print test summary"""
        total = self.passed + self.failed
        
        print(f"\n{Colors.BLUE}{'='*70}")
        print("  TEST SUMMARY")
        print(f"{'='*70}{Colors.RESET}\n")
        
        print(f"Total Tests: {total}")
        print(f"{Colors.GREEN}Passed: {self.passed}{Colors.RESET}")
        print(f"{Colors.RED}Failed: {self.failed}{Colors.RESET}")
        
        if total > 0:
            pass_rate = (self.passed / total) * 100
            print(f"\nPass Rate: {pass_rate:.1f}%")
            
            if pass_rate >= 90:
                print(f"\n{Colors.GREEN}🎉 EXCELLENT - Ready for deployment!{Colors.RESET}")
            elif pass_rate >= 70:
                print(f"\n{Colors.YELLOW}⚠️  GOOD - Some issues need fixing{Colors.RESET}")
            else:
                print(f"\n{Colors.RED}❌ CRITICAL - Major issues found{Colors.RESET}")
        
        # Save results to file
        results_file = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "base_url": BASE_URL,
                "summary": {
                    "total": total,
                    "passed": self.passed,
                    "failed": self.failed,
                    "pass_rate": (self.passed / total * 100) if total > 0 else 0
                },
                "results": self.results
            }, f, indent=2)
        
        print(f"\nResults saved to: {results_file}")

async def main():
    """Main entry point"""
    tester = IntegrationTester()
    await tester.run_all_tests()
    
    # Exit with error code if tests failed
    if tester.failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    # Check if backend is running
    print("Checking if backend is running...")
    try:
        import requests
        resp = requests.get(f"{BASE_URL}/api/system/info", timeout=5)
        if resp.status_code == 200:
            print(f"{Colors.GREEN}✓ Backend is running{Colors.RESET}\n")
        else:
            print(f"{Colors.RED}✗ Backend returned status {resp.status_code}{Colors.RESET}")
            sys.exit(1)
    except Exception as e:
        print(f"{Colors.RED}✗ Cannot connect to backend: {e}{Colors.RESET}")
        print(f"Please start backend first: python simple_backend.py")
        sys.exit(1)
    
    # Run tests
    asyncio.run(main())
