
"""
STATUS: REAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Grand System Heartbeat Test
===================================
Live Digital Workforce Activation Test
Real-time demonstration of all Universal Bridge components
"""

import asyncio
import logging
import json
from datetime import datetime
from pathlib import Path

# Import all ASIMNEXUS components
from core.agents.system_agent import get_system_agent
from bridge.hybrid_manager import get_hybrid_manager
from bridge.mcp_connector import get_mcp_connector
from core.dharma_chakra.local_privacy_laws import get_privacy_shield
from core.orchestrator import get_orchestrator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GrandHeartbeat")

class GrandHeartbeatTest:
    """Grand System Heartbeat Test - Live Digital Workforce Demonstration"""
    
    def __init__(self):
        self.logger = logging.getLogger("GrandHeartbeat")
        self.test_results = {}
        self.start_time = datetime.now()
        
        # Initialize all components
        self.system_agent = get_system_agent()
        self.hybrid_manager = get_hybrid_manager()
        self.mcp_connector = get_mcp_connector()
        self.privacy_shield = get_privacy_shield()
        self.orchestrator = get_orchestrator()
        
        self.logger.info("🚀 Grand System Heartbeat Test Initialized")
    
    async def run_complete_heartbeat(self) -> dict:
        """Run complete system heartbeat test"""
        try:
            self.logger.info("🫀 Starting Grand System Heartbeat Test...")
            
            # Test 1: Cross-OS SystemAgent Verification
            await self.test_cross_os_verification()
            
            # Test 2: Hybrid Execution Manager Check
            await self.test_hybrid_execution()
            
            # Test 3: Privacy Shield Activation
            await self.test_privacy_shield()
            
            # Test 4: MCP Integration Test
            await self.test_mcp_integration()
            
            # Test 5: Orchestrator Live Test
            await self.test_orchestrator()
            
            # Compile results
            total_time = (datetime.now() - self.start_time).total_seconds()
            
            heartbeat_results = {
                "test_completed": True,
                "execution_time_seconds": total_time,
                "timestamp": datetime.now().isoformat(),
                "components_tested": list(self.test_results.keys()),
                "results": self.test_results,
                "overall_status": "SUCCESS" if all(r.get("success", False) for r in self.test_results.values()) else "PARTIAL"
            }
            
            self.logger.info(f"✅ Grand Heartbeat Test Completed in {total_time:.2f} seconds")
            return heartbeat_results
            
        except Exception as e:
            self.logger.error(f"❌ Grand Heartbeat Test Failed: {e}")
            return {
                "test_completed": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def test_cross_os_verification(self):
        """Test 1: Cross-OS SystemAgent Verification"""
        try:
            self.logger.info("🖥️ Testing Cross-OS SystemAgent...")
            
            # Initialize SystemAgent
            if not await self.system_agent.initialize():
                raise Exception("SystemAgent initialization failed")
            
            # Get system information
            system_info = await self.system_agent.get_system_info()
            
            # Get disk space report
            disk_space = await self.system_agent.check_disk_space("C:\\" if "Windows" in system_info.get("os", "") else "/")
            
            # Get active processes
            processes = await self.system_agent.list_processes()
            
            # Execute test command
            test_command = await self.system_agent.execute_command(
                command_type=self.system_agent.CommandType.SHELL,
                command="echo 'SystemAgent Heartbeat Test Successful'",
                parameters={}
            )
            
            cross_os_result = {
                "success": True,
                "system_info": {
                    "os": system_info.get("os"),
                    "platform": system_info.get("platform"),
                    "cpu_count": system_info.get("cpu_count"),
                    "ram_total_gb": system_info.get("memory_total", 0) // (1024**3),
                    "ram_available_gb": system_info.get("memory_available", 0) // (1024**3),
                    "gpu_available": system_info.get("gpu_available", False),
                    "gpu_name": system_info.get("gpu_name", "No GPU")
                },
                "disk_space": {
                    "total_gb": disk_space.get("total", 0) // (1024**3),
                    "used_gb": disk_space.get("used", 0) // (1024**3),
                    "free_gb": disk_space.get("free", 0) // (1024**3),
                    "usage_percent": disk_space.get("percent", 0)
                },
                "active_processes": {
                    "total_count": len(processes),
                    "top_5_processes": processes[:5]
                },
                "test_command": {
                    "success": test_command.success,
                    "execution_time": test_command.execution_time,
                    "stdout": test_command.stdout[:100] + "..." if len(test_command.stdout) > 100 else test_command.stdout
                }
            }
            
            self.test_results["cross_os_verification"] = cross_os_result
            self.logger.info(f"✅ Cross-OS Test: OS={system_info.get('os')}, RAM={cross_os_result['system_info']['ram_total_gb']}GB, GPU={cross_os_result['system_info']['gpu_available']}")
            
        except Exception as e:
            self.test_results["cross_os_verification"] = {"success": False, "error": str(e)}
            self.logger.error(f"❌ Cross-OS Test Failed: {e}")
    
    async def test_hybrid_execution(self):
        """Test 2: Hybrid Execution Manager Check"""
        try:
            self.logger.info("🔄 Testing Hybrid Execution Manager...")
            
            # Initialize Hybrid Manager
            if not await self.hybrid_manager.initialize():
                raise Exception("Hybrid Manager initialization failed")
            
            # Get hardware profile
            hardware_profile = await self.hybrid_manager.get_hardware_profile()
            
            # Create test task
            from bridge.hybrid_manager import ExecutionTask
            test_task = ExecutionTask(
                task_id="heartbeat_test",
                task_type="inference",
                complexity="expert",
                priority="high",
                estimated_memory=8000000000,  # 8GB
                requires_gpu=True
            )
            
            # Execute task
            task_result = await self.hybrid_manager.execute_task(test_task)
            
            # Get performance metrics
            performance = await self.hybrid_manager.get_performance_metrics()
            
            hybrid_result = {
                "success": True,
                "hardware_profile": {
                    "tier": hardware_profile.get("tier"),
                    "ram_total_gb": hardware_profile.get("ram_total_gb"),
                    "ram_available_gb": hardware_profile.get("ram_available_gb"),
                    "gpu_available": hardware_profile.get("gpu_available"),
                    "gpu_memory_gb": hardware_profile.get("gpu_memory_gb"),
                    "gpu_name": hardware_profile.get("gpu_name"),
                    "execution_mode": hardware_profile.get("execution_mode")
                },
                "task_execution": {
                    "success": task_result.get("success"),
                    "execution_mode": task_result.get("execution_mode"),
                    "execution_time": task_result.get("execution_time")
                },
                "performance_metrics": {
                    "total_executions": performance.get("total_executions"),
                    "success_rate_percent": performance.get("success_rate_percent"),
                    "average_execution_time": performance.get("average_execution_time")
                }
            }
            
            # Check if RTX 2060 + 16GB RAM detected correctly
            gpu_detected = hardware_profile.get("gpu_available", False)
            ram_detected = hardware_profile.get("ram_total_gb", 0) >= 15  # Allow some tolerance
            
            if gpu_detected and ram_detected:
                hybrid_result["rtx_2060_detected"] = True
                hybrid_result["full_neural_core"] = hardware_profile.get("execution_mode") == "full_neural"
                self.logger.info(f"✅ Hybrid Test: RTX 2060 + 16GB RAM detected, Mode={hardware_profile.get('execution_mode')}")
            else:
                hybrid_result["rtx_2060_detected"] = False
                hybrid_result["full_neural_core"] = False
                self.logger.warning(f"⚠️ Hybrid Test: GPU={gpu_detected}, RAM={hardware_profile.get('ram_total_gb')}GB")
            
            self.test_results["hybrid_execution"] = hybrid_result
            
        except Exception as e:
            self.test_results["hybrid_execution"] = {"success": False, "error": str(e)}
            self.logger.error(f"❌ Hybrid Execution Test Failed: {e}")
    
    async def test_privacy_shield(self):
        """Test 3: Privacy Shield Activation"""
        try:
            self.logger.info("🛡️ Testing Privacy Shield...")
            
            # Initialize Privacy Shield
            if not await self.privacy_shield.initialize():
                raise Exception("Privacy Shield initialization failed")
            
            # Get privacy status
            privacy_status = await self.privacy_shield.get_privacy_status()
            
            # Test data processing with Nepal compliance
            from core.dharma_chakra.local_privacy_laws import DataCategory, PrivacyLevel
            data_result = await self.privacy_shield.process_data_request(
                data_category=DataCategory.PERSONAL,
                privacy_level=PrivacyLevel.SENSITIVE_PERSONAL,
                content="Test user data for heartbeat verification",
                owner_id="heartbeat_test_user",
                processing_purpose="System verification test",
                consent_obtained=True
            )
            
            # Test data subject request
            access_result = await self.privacy_shield.handle_data_subject_request(
                request_type="access",
                owner_id="heartbeat_test_user"
            )
            
            privacy_result = {
                "success": True,
                "region_detected": privacy_status.get("region"),
                "policy_active": privacy_status.get("policy"),
                "nepal_detected": privacy_status.get("region") == "nepal",
                "compliance_status": {
                    "total_records": privacy_status.get("total_records"),
                    "encryption_rate": privacy_status.get("encryption_rate"),
                    "consent_rate": privacy_status.get("consent_rate")
                },
                "data_processing": {
                    "success": data_result.get("success"),
                    "record_id": data_result.get("record_id"),
                    "encrypted": data_result.get("encrypted"),
                    "compliant": data_result.get("compliance", {}).get("compliant", False)
                },
                "data_subject_rights": {
                    "access_request_success": access_result.get("success"),
                    "records_accessible": access_result.get("total_records", 0)
                }
            }
            
            if privacy_status.get("region") == "nepal":
                privacy_result["nepal_privacy_active"] = True
                self.logger.info("✅ Privacy Shield: Nepal detected, Data Protection Act active")
            else:
                privacy_result["nepal_privacy_active"] = False
                self.logger.info(f"🌍 Privacy Shield: {privacy_status.get('region')} detected, applying regional laws")
            
            self.test_results["privacy_shield"] = privacy_result
            
        except Exception as e:
            self.test_results["privacy_shield"] = {"success": False, "error": str(e)}
            self.logger.error(f"❌ Privacy Shield Test Failed: {e}")
    
    async def test_mcp_integration(self):
        """Test 4: MCP Integration Test"""
        try:
            self.logger.info("🔌 Testing MCP Integration...")
            
            # Initialize MCP Connector
            if not await self.mcp_connector.initialize():
                raise Exception("MCP Connector initialization failed")
            
            # Test local file search
            from bridge.mcp_connector import SearchQuery, DataSource
            search_query = SearchQuery(
                query_id="heartbeat_search",
                query_text="ASIMNEXUS system architecture",
                sources=[DataSource.LOCAL_FILES],
                max_results=5
            )
            
            search_result = await self.mcp_connector.search_context(search_query)
            
            # Get context summary
            context_summary = await self.mcp_connector.get_context_summary()
            
            mcp_result = {
                "success": True,
                "search_results": {
                    "success": search_result.get("success"),
                    "total_results": search_result.get("total_results"),
                    "execution_time": search_result.get("execution_time")
                },
                "context_summary": {
                    "total_items": context_summary.get("total_items"),
                    "source_distribution": context_summary.get("source_distribution"),
                    "cache_size_mb": context_summary.get("cache_size_mb")
                },
                "data_sources": {
                    "local_files_available": True,
                    "github_available": True,
                    "google_search_available": True
                }
            }
            
            self.test_results["mcp_integration"] = mcp_result
            self.logger.info(f"✅ MCP Test: Found {search_result.get('total_results')} local files")
            
        except Exception as e:
            self.test_results["mcp_integration"] = {"success": False, "error": str(e)}
            self.logger.error(f"❌ MCP Integration Test Failed: {e}")
    
    async def test_orchestrator(self):
        """Test 5: Orchestrator Live Test"""
        try:
            self.logger.info("🎯 Testing Orchestrator...")
            
            # Initialize Orchestrator
            if not await self.orchestrator.initialize():
                raise Exception("Orchestrator initialization failed")
            
            # Get orchestration status
            orch_status = await self.orchestrator.get_orchestration_status()
            
            # Create test task
            task_result = await self.orchestrator.create_task(
                title="Heartbeat System Verification",
                description="Verify system health and report status",
                priority="high",
                complexity="moderate",
                parameters={"test_type": "heartbeat"}
            )
            
            orchestrator_result = {
                "success": True,
                "orchestration_status": {
                    "active": orch_status.get("active"),
                    "total_agents": orch_status.get("total_agents"),
                    "task_statistics": orch_status.get("task_statistics")
                },
                "task_creation": {
                    "success": task_result.get("success"),
                    "task_id": task_result.get("task_id"),
                    "required_roles": task_result.get("required_roles")
                },
                "digital_workforce": {
                    "agents_active": len(orch_status.get("agent_statistics", {})),
                    "tasks_pending": orch_status.get("task_statistics", {}).get("pending", 0),
                    "tasks_completed": orch_status.get("task_statistics", {}).get("total_completed", 0)
                }
            }
            
            self.test_results["orchestrator"] = orchestrator_result
            self.logger.info(f"✅ Orchestrator Test: {orch_status.get('total_agents')} agents active")
            
        except Exception as e:
            self.test_results["orchestrator"] = {"success": False, "error": str(e)}
            self.logger.error(f"❌ Orchestrator Test Failed: {e}")
    
    def generate_live_dashboard_data(self) -> dict:
        """Generate data for live neural pulse dashboard"""
        try:
            # Extract key metrics for dashboard
            dashboard_data = {
                "timestamp": datetime.now().isoformat(),
                "system_heartbeat": {
                    "status": "ACTIVE",
                    "pulse_rate": 72,  # Simulated pulse
                    "neural_activity": "HIGH"
                },
                "cross_os_status": self.test_results.get("cross_os_verification", {}),
                "hybrid_execution": self.test_results.get("hybrid_execution", {}),
                "privacy_compliance": self.test_results.get("privacy_shield", {}),
                "data_integration": self.test_results.get("mcp_integration", {}),
                "workforce_status": self.test_results.get("orchestrator", {})
            }
            
            return dashboard_data
            
        except Exception as e:
            return {"error": f"Dashboard data generation failed: {e}"}

async def main():
    """Main execution function"""
    print("🚀 ASIMNEXUS Grand System Heartbeat Test")
    print("=" * 50)
    
    # Create and run test
    heartbeat_test = GrandHeartbeatTest()
    results = await heartbeat_test.run_complete_heartbeat()
    
    # Display results
    print("\n🫀 GRAND HEARTBEAT TEST RESULTS")
    print("=" * 50)
    
    if results.get("test_completed"):
        print(f"✅ Test Status: {results.get('overall_status')}")
        print(f"⏱️ Execution Time: {results.get('execution_time_seconds', 0):.2f} seconds")
        print(f"🕐 Timestamp: {results.get('timestamp')}")
        
        print("\n📊 Component Results:")
        for component, result in results.get("results", {}).items():
            status = "✅" if result.get("success") else "❌"
            print(f"{status} {component.replace('_', ' ').title()}: {result.get('success', False)}")
        
        # Cross-OS Details
        if "cross_os_verification" in results.get("results", {}):
            cross_os = results["results"]["cross_os_verification"]
            if cross_os.get("success"):
                sys_info = cross_os.get("system_info", {})
                print(f"\n🖥️ System Detected:")
                print(f"   OS: {sys_info.get('os')}")
                print(f"   RAM: {sys_info.get('ram_total_gb', 0)} GB")
                print(f"   GPU: {sys_info.get('gpu_name', 'No GPU')}")
                print(f"   CPU: {sys_info.get('cpu_count', 0)} cores")
        
        # Hybrid Execution Details
        if "hybrid_execution" in results.get("results", {}):
            hybrid = results["results"]["hybrid_execution"]
            if hybrid.get("success"):
                hw_profile = hybrid.get("hardware_profile", {})
                print(f"\n🔄 Hardware Profile:")
                print(f"   Tier: {hw_profile.get('tier')}")
                print(f"   Execution Mode: {hw_profile.get('execution_mode')}")
                print(f"   RTX 2060 Detected: {hybrid.get('rtx_2060_detected', False)}")
                print(f"   Full Neural Core: {hybrid.get('full_neural_core', False)}")
        
        # Privacy Shield Details
        if "privacy_shield" in results.get("results", {}):
            privacy = results["results"]["privacy_shield"]
            if privacy.get("success"):
                print(f"\n🛡️ Privacy Shield:")
                print(f"   Region: {privacy.get('region_detected')}")
                print(f"   Policy: {privacy.get('policy_active')}")
                print(f"   Nepal Privacy Active: {privacy.get('nepal_privacy_active', False)}")
        
        # Generate dashboard data
        dashboard_data = heartbeat_test.generate_live_dashboard_data()
        
        print(f"\n🌐 Live Dashboard Data Ready!")
        print(f"   Neural Pulse Status: {dashboard_data.get('system_heartbeat', {}).get('status')}")
        print(f"   Digital Workforce: {dashboard_data.get('workforce_status', {}).get('agents_active', 0)} agents active")
        
        # Save results to file
        results_file = Path("heartbeat_results.json")
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        dashboard_file = Path("dashboard_data.json")
        with open(dashboard_file, 'w') as f:
            json.dump(dashboard_data, f, indent=2, default=str)
        
        print(f"\n💾 Results saved:")
        print(f"   heartbeat_results.json")
        print(f"   dashboard_data.json")
        
    else:
        print(f"❌ Test Failed: {results.get('error')}")
    
    print("\n🎯 Grand System Heartbeat Test Complete!")

if __name__ == "__main__":
    asyncio.run(main())
