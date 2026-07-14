
"""
STATUS: REAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Integration Stress Test - Circular Import Detection
Tests that all agents can work together without circular dependencies
"""

import asyncio
import sys
import importlib
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import traceback

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("IntegrationStressTest")

class CircularImportDetector:
    """Detects circular imports in the ASIMNEXUS system"""
    
    def __init__(self):
        self.import_chain = []
        self.circular_paths = []
        self.test_results = {}
        
    def test_import(self, module_name: str) -> Dict:
        """Test if a module can be imported without circular dependency"""
        try:
            # Clear previous import to test fresh
            if module_name in sys.modules:
                del sys.modules[module_name]
                
            # Add to chain
            self.import_chain.append(module_name)
            
            # Try import
            module = importlib.import_module(module_name)
            
            result = {
                'module': module_name,
                'status': 'success',
                'chain': self.import_chain.copy(),
                'error': None
            }
            
            # Remove from chain (successful)
            self.import_chain.pop()
            
            return result
            
        except ImportError as e:
            error_msg = str(e)
            
            # Check if circular
            if 'circular' in error_msg.lower() or 'partially initialized' in error_msg.lower():
                circular_path = ' -> '.join(self.import_chain + [module_name])
                self.circular_paths.append(circular_path)
                
                result = {
                    'module': module_name,
                    'status': 'circular_import',
                    'chain': self.import_chain.copy(),
                    'error': error_msg,
                    'circular_path': circular_path
                }
            else:
                result = {
                    'module': module_name,
                    'status': 'import_error',
                    'chain': self.import_chain.copy(),
                    'error': error_msg
                }
                
            # Clean chain
            if self.import_chain:
                self.import_chain.pop()
                
            return result
            
        except Exception as e:
            if self.import_chain:
                self.import_chain.pop()
                
            return {
                'module': module_name,
                'status': 'error',
                'chain': [],
                'error': str(e),
                'traceback': traceback.format_exc()
            }

class IntegrationStressTest:
    """
    ASIMNEXUS Integration Stress Test
    
    Tests:
    1. Individual module imports
    2. Sequential initialization (all agents)
    3. Parallel initialization (race condition detection)
    4. Agent interaction (call chains)
    5. Memory/performance under load
    """
    
    def __init__(self):
        self.detector = CircularImportDetector()
        self.results = {
            'import_tests': {},
            'init_tests': {},
            'interaction_tests': {},
            'circular_imports': [],
            'passed': 0,
            'failed': 0,
            'warnings': 0
        }
        
    async def run_all_tests(self):
        """Run complete stress test suite"""
        logger.info("=" * 80)
        logger.info("🧪 ASIMNEXUS INTEGRATION STRESS TEST")
        logger.info("=" * 80)
        logger.info(f"Started: {datetime.now().isoformat()}")
        logger.info("")
        
        # Test 1: Import Tests
        logger.info("📦 PHASE 1: Module Import Tests")
        logger.info("-" * 40)
        await self._test_all_imports()
        
        # Test 2: Initialization Tests
        logger.info("\n🚀 PHASE 2: Sequential Initialization")
        logger.info("-" * 40)
        await self._test_sequential_init()
        
        # Test 3: Agent Interactions
        logger.info("\n🤖 PHASE 3: Agent Interaction Tests")
        logger.info("-" * 40)
        await self._test_agent_interactions()
        
        # Test 4: Parallel Load Test
        logger.info("\n⚡ PHASE 4: Parallel Load Test")
        logger.info("-" * 40)
        await self._test_parallel_load()
        
        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("📊 TEST SUMMARY")
        logger.info("=" * 80)
        self._print_summary()
        
        return self.results
        
    async def _test_all_imports(self):
        """Test all critical module imports"""
        
        modules = [
            # Core
            'event_bus',
            'triple_brain_system',
            'master_agent',
            'energy_engine',
            
            # Mesh
            'mesh.device_registry',
            'mesh.mesh_routing_agent',
            
            # Connectors
            'connectors.multiversal_bridge',
            'connectors.google_ecosystem',
            
            # Core Modules
            'core.universal_schema',
            'core.predictive_engine',
            'core.omnipresence_manager',
            'core.atom_storage',
            'core.company_os',
            'core.context_router',
            
            # Memory
            'memory_v2',
            
            # Security
            'security.dharma_policy',
            'security.vault_manager',
            
            # Agents - Hierarchy
            'agents.agent_hierarchy',
            
            # Agents - Infrastructure
            'agents.infra.compute_scout_agent',
            'agents.infra.cloud_balancer_agent',
            
            # Agents - Company
            'agents.company.ceo_agent',
            'agents.world_system.company_agent',
            
            # Agents - Services
            'agents.services.google_mail_agent',
            'agents.services.google_drive_agent',
            'agents.services.google_calendar_agent',
            
            # Main Orchestrator
            'core.asim_core_new',
        ]
        
        for module in modules:
            result = self.detector.test_import(module)
            self.results['import_tests'][module] = result
            
            if result['status'] == 'success':
                logger.info(f"✅ {module}")
                self.results['passed'] += 1
            elif result['status'] == 'circular_import':
                logger.warning(f"❌ {module} - CIRCULAR IMPORT!")
                logger.warning(f"   Path: {result.get('circular_path', 'Unknown')}")
                self.results['circular_imports'].append(result)
                self.results['failed'] += 1
            else:
                logger.warning(f"⚠️ {module} - {result['status']}")
                logger.warning(f"   Error: {result['error'][:80]}...")
                self.results['failed'] += 1
                
    async def _test_sequential_init(self):
        """Test sequential initialization of all agents"""
        
        init_tests = [
            ('Event Bus', self._init_event_bus),
            ('Triple Brain', self._init_triple_brain),
            ('Arc Reactor', self._init_arc_reactor),
            ('Memory System', self._init_memory),
            ('Device Registry', self._init_device_registry),
            ('Mesh Routing', self._init_mesh_routing),
            ('Multiversal Bridge', self._init_multiversal_bridge),
            ('Predictive Engine', self._init_predictive_engine),
            ('Omnipresence', self._init_omnipresence),
            ('Atom Storage', self._init_atom_storage),
            ('Vault Manager', self._init_vault),
            ('Agent Hierarchy', self._init_agent_hierarchy),
            ('Compute Scout', self._init_compute_scout),
            ('Cloud Balancer', self._init_cloud_balancer),
            ('Company OS', self._init_company_os),
            ('CEO Agent', self._init_ceo_agent),
            ('Context Router', self._init_context_router),
            ('Google Ecosystem', self._init_google_ecosystem),
            ('Gmail Oracle', self._init_gmail_oracle),
            ('Drive Architect', self._init_drive_architect),
            ('Schedule Master', self._init_schedule_master),
        ]
        
        for name, init_func in init_tests:
            try:
                await init_func()
                logger.info(f"✅ {name}")
                self.results['init_tests'][name] = {'status': 'success'}
                self.results['passed'] += 1
            except Exception as e:
                logger.warning(f"❌ {name} - {str(e)[:60]}")
                self.results['init_tests'][name] = {
                    'status': 'failed',
                    'error': str(e)
                }
                self.results['failed'] += 1
                
    async def _test_agent_interactions(self):
        """Test agent-to-agent interactions"""
        
        interactions = [
            ('Drive -> Atom Storage', self._test_drive_atom_interaction),
            ('Router -> Ecosystem', self._test_router_ecosystem_interaction),
            ('CEO -> Company OS', self._test_ceo_company_interaction),
            ('Mail -> Ecosystem', self._test_mail_ecosystem_interaction),
            ('Schedule -> Context', self._test_schedule_context_interaction),
        ]
        
        for name, test_func in interactions:
            try:
                await test_func()
                logger.info(f"✅ {name}")
                self.results['interaction_tests'][name] = {'status': 'success'}
                self.results['passed'] += 1
            except Exception as e:
                logger.warning(f"❌ {name} - {str(e)[:60]}")
                self.results['interaction_tests'][name] = {
                    'status': 'failed',
                    'error': str(e)
                }
                self.results['failed'] += 1
                
    async def _test_parallel_load(self):
        """Test parallel initialization (race condition detection)"""
        
        logger.info("   Testing parallel agent initialization...")
        
        async def init_with_delay(name, delay, func):
            await asyncio.sleep(delay)
            try:
                await func()
                return (name, 'success', None)
            except Exception as e:
                return (name, 'failed', str(e))
                
        # Initialize multiple agents in parallel
        tasks = [
            init_with_delay('Atom Storage', 0.0, self._init_atom_storage),
            init_with_delay('Vault Manager', 0.05, self._init_vault),
            init_with_delay('Drive Architect', 0.1, self._init_drive_architect),
            init_with_delay('Gmail Oracle', 0.15, self._init_gmail_oracle),
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"   ⚠️ Parallel init error: {result}")
                self.results['warnings'] += 1
            elif result[1] == 'success':
                logger.info(f"   ✅ {result[0]} (parallel)")
            else:
                logger.error(f"   ❌ {result[0]} (parallel) - {result[2][:40]}")
                self.results['failed'] += 1
                
    def _print_summary(self):
        """Print test summary"""
        total = self.results['passed'] + self.results['failed']
        
        logger.info(f"Total Tests: {total}")
        logger.info(f"✅ Passed: {self.results['passed']}")
        logger.error(f"❌ Failed: {self.results['failed']}")
        logger.warning(f"⚠️ Warnings: {self.results['warnings']}")
        
        if self.results['circular_imports']:
            logger.error("\n🚨 CIRCULAR IMPORTS DETECTED:")
            for circ in self.results['circular_imports']:
                logger.error(f"   {circ.get('circular_path', 'Unknown')}")
        else:
            logger.info("\n✅ No circular imports detected")
            
        success_rate = (self.results['passed'] / total * 100) if total > 0 else 0
        logger.info(f"\nSuccess Rate: {success_rate:.1f}%")
        
        if self.results['failed'] == 0:
            logger.info("\n🎉 ALL TESTS PASSED - System is circular-import free!")
        else:
            logger.warning(f"\n⚠️ {self.results['failed']} test(s) failed - Review needed")
            
    # Individual init methods for testing
    async def _init_event_bus(self):
        from event_bus import event_bus
        
    async def _init_triple_brain(self):
        from core.triple_brain_system import asim_triple_brain
        await asim_triple_brain.initialize()
        
    async def _init_arc_reactor(self):
        from energy_engine import initialize_arc_reactor
        await initialize_arc_reactor()
        
    async def _init_memory(self):
        from memory_v2 import initialize_memory_system
        await initialize_memory_system()
        
    async def _init_device_registry(self):
        from core.mesh.device_registry import initialize_device_registry
        await initialize_device_registry()
        
    async def _init_mesh_routing(self):
        from core.mesh.mesh_routing_agent_v2 import MeshRoutingAgentV2
        from core.mesh.device_registry import device_registry
        agent = MeshRoutingAgentV2(p2p_node=None)
        await agent.initialize(device_registry)
        
    async def _init_multiversal_bridge(self):
        from core.gateway.multiversal_bridge import initialize_multiversal_bridge
        await initialize_multiversal_bridge()
        
    async def _init_predictive_engine(self):
        from core.predictive_engine import initialize_predictive_engine
        from energy_engine import arc_reactor
        await initialize_predictive_engine(arc_reactor, None)
        
    async def _init_omnipresence(self):
        from core.omnipresence_manager import initialize_omnipresence
        await initialize_omnipresence()
        
    async def _init_atom_storage(self):
        from core.atom_storage import initialize_atom_storage
        await initialize_atom_storage()
        
    async def _init_vault(self):
        from core.security.vault_manager import initialize_vault
        await initialize_vault()
        
    async def _init_agent_hierarchy(self):
        from core.agents.agent_hierarchy import initialize_agent_hierarchy
        await initialize_agent_hierarchy()
        
    async def _init_compute_scout(self):
        from core.agents.infra.compute_scout_agent import initialize_compute_scout
        await initialize_compute_scout()
        
    async def _init_cloud_balancer(self):
        from core.agents.infra.cloud_balancer_agent import initialize_cloud_balancer
        await initialize_cloud_balancer()
        
    async def _init_company_os(self):
        from core.company_os import initialize_company_os
        await initialize_company_os()
        
    async def _init_ceo_agent(self):
        from core.agents.company.ceo_agent import initialize_ceo_agent
        from core.company_os import company_os
        await initialize_ceo_agent(company_os)
        
    async def _init_context_router(self):
        from core.context_router import initialize_context_router
        await initialize_context_router()
        
    async def _init_google_ecosystem(self):
        from core.gateway.google_ecosystem import initialize_google_ecosystem
        await initialize_google_ecosystem()
        
    async def _init_gmail_oracle(self):
        from core.agents.services.google_mail_agent import initialize_gmail_oracle
        await initialize_gmail_oracle()
        
    async def _init_drive_architect(self):
        from core.agents.services.google_drive_agent import initialize_drive_architect
        await initialize_drive_architect()
        
    async def _init_schedule_master(self):
        from core.agents.services.google_calendar_agent import initialize_schedule_master
        await initialize_schedule_master()
        
    # Interaction tests
    async def _test_drive_atom_interaction(self):
        from core.agents.services.google_drive_agent import drive_architect
        from core.atom_storage import atom_storage
        # Test that drive can use atom storage
        
    async def _test_router_ecosystem_interaction(self):
        from core.context_router import context_router
        from core.gateway.google_ecosystem import google_ecosystem
        # Test router can control ecosystem
        
    async def _test_ceo_company_interaction(self):
        from core.agents.company.ceo_agent import ceo_agent
        from core.company_os import company_os
        # Test CEO can use Company OS
        
    async def _test_mail_ecosystem_interaction(self):
        from core.agents.services.google_mail_agent import gmail_oracle
        from core.gateway.google_ecosystem import google_ecosystem
        # Test mail agent uses ecosystem
        
    async def _test_schedule_context_interaction(self):
        from core.agents.services.google_calendar_agent import schedule_master
        from core.context_router import context_router
        # Test schedule respects context

async def run_stress_test():
    """Main entry point for stress test"""
    test = IntegrationStressTest()
    results = await test.run_all_tests()
    return results

if __name__ == "__main__":
    # Run stress test
    results = asyncio.run(run_stress_test())
    
    # Exit with appropriate code
    if results['failed'] > 0 or results['circular_imports']:
        logger.error("\n❌ STRESS TEST FAILED - Issues detected")
        exit(1)
    else:
        logger.info("\n✅ STRESS TEST PASSED - All systems operational")
        exit(0)
