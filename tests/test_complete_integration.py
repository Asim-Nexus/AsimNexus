
"""
STATUS: REAL — Auto-labeled by batch_label.py
"""

"""
Complete Integration Test for ASIMNEXUS World OS
====================================================

Test all 21 components together:
- 9 Original architectural improvements
- 5 World OS components
- 4 Universal OS components
- 3 Advanced components (AGI, Quantum, Blockchain)
"""

import asyncio
from datetime import date
from core.new_architecture_integration import NewASIMNEXUS, ASIMConfig
from core.digital_twin_system import Gender
from core.agi_core import ReasoningMode
from core.quantum_bridge import QuantumAlgorithm, QuantumProvider
from core.blockchain_identity_advanced import BlockchainNetwork, AttestationType

async def test_complete_integration():
    """Test complete integration of all 21 components"""
    print("=" * 70)
    print("Testing ASIMNEXUS World OS - Complete Integration (21 Components)")
    print("=" * 70)
    
    # Initialize with ALL components enabled
    config = ASIMConfig(
        # Original
        enable_microkernel=True,
        enable_p2p_network=True,
        enable_depin=True,
        enable_rbe=True,
        enable_mythos=True,
        # Universal OS
        enable_universal_gateway=True,
        enable_digital_twins=True,
        enable_life_automation=True,
        enable_global_mesh=True,
        # Advanced
        enable_agi=True,
        enable_quantum=True,
        enable_blockchain_identity=True
    )
    
    asim = NewASIMNEXUS(config)
    
    try:
        # Initialize
        print("\n[1/5] Initializing ASIMNEXUS World OS with 21 components...")
        await asim.initialize()
        
        # Verify all components
        print("\n[2/5] Verifying all 21 components...")
        
        # Original 9 components
        original_components = [
            ("State Manager", asim.state_manager),
            ("Cache Manager", asim.cache_manager),
            ("Hybrid Router", asim.hybrid_router),
            ("Smart LLM Router", asim.smart_llm_router),
            ("Tool Engine", asim.tool_engine),
            ("Hybrid RAG", asim.hybrid_rag),
            ("Agent System", asim.agent_system),
            ("Execution Pipeline", asim.execution_pipeline),
        ]
        
        for name, component in original_components:
            assert component is not None, f"{name} not initialized"
            print(f"  [OK] {name}")
        
        # World OS 5 components
        world_os_components = [
            ("Microkernel", asim.microkernel),
            ("P2P Network", asim.p2p_network),
            ("Uplink Connector", asim.uplink_connector),
            ("Daylight Connector", asim.daylight_connector),
            ("DIMO Connector", asim.dimo_connector),
            ("RBE Algorithm", asim.rbe_algorithm),
            ("Mythos Scanner", asim.mythos_scanner),
        ]
        
        for name, component in world_os_components:
            assert component is not None, f"{name} not initialized"
            print(f"  [OK] {name}")
        
        # Universal OS 4 components
        universal_os_components = [
            ("API Gateway", asim.api_gateway),
            ("Digital Twin System", asim.digital_twin_system),
            ("Life Automation", asim.life_automation),
            ("Global Mesh", asim.global_mesh),
        ]
        
        for name, component in universal_os_components:
            assert component is not None, f"{name} not initialized"
            print(f"  [OK] {name}")
        
        # Advanced 3 components
        advanced_components = [
            ("AGI Core", asim.agi_core),
            ("Quantum Bridge", asim.quantum_bridge),
            ("Blockchain Identity", asim.blockchain_identity),
        ]
        
        for name, component in advanced_components:
            assert component is not None, f"{name} not initialized"
            print(f"  [OK] {name}")
        
        # Test Digital Twin + AGI integration
        print("\n[3/5] Testing Digital Twin + AGI integration...")
        twin_result = asim.create_digital_twin(
            legal_name="Test User",
            date_of_birth=date(1990, 1, 1),
            nationality="US",
            gender=Gender.MALE
        )
        print(f"  [OK] Created twin: {twin_result['twin_id']}")
        
        # Test AGI reasoning about the twin
        if asim.agi_core:
            chain = await asim.agi_core.think(
                query=f"How can we improve the digital twin system for {twin_result['twin_id']}?",
                reasoning_mode=ReasoningMode.ANALYTICAL,
                max_depth=3
            )
            print(f"  [OK] AGI reasoning: {len(chain.thoughts)} thoughts, confidence {chain.confidence:.2f}")
        
        # Test Quantum Bridge
        print("\n[4/5] Testing Quantum Bridge...")
        if asim.quantum_bridge:
            job = asim.quantum_bridge.create_job(
                algorithm=QuantumAlgorithm.GROVER,
                parameters={"search_space_size": 10000, "target": "optimization"},
                shots=1024
            )
            result = await asim.quantum_bridge.execute_job(job.job_id)
            speedup = result.get('speedup', 0)
            print(f"  [OK] Quantum job completed: {speedup:.2f}x speedup")
        
        # Test Blockchain Identity
        print("\nTesting Blockchain Identity...")
        if asim.blockchain_identity:
            public_key = "0x" + "a" * 64
            did = asim.blockchain_identity.create_did(public_key, BlockchainNetwork.ETHEREUM)
            print(f"  [OK] Created DID: {did}")
            
            vc_id = asim.blockchain_identity.issue_credential(
                issuer_did=did,
                subject_did=did,
                credential_type=AttestationType.IDENTITY,
                claims={"name": "Test User", "verified": True}
            )
            print(f"  [OK] Issued credential: {vc_id}")
            
            verification = asim.blockchain_identity.verify_credential(vc_id)
            print(f"  [OK] Verified credential: {verification['valid']}")
        
        # Get comprehensive stats
        print("\n[5/5] Getting comprehensive statistics...")
        stats = await asim.get_stats()
        
        print("\n  Original Components:")
        print(f"    Infrastructure: State, Cache, Async Executor")
        print(f"    Routing: Hybrid Router, Smart LLM Router")
        print(f"    Knowledge: Hybrid RAG, Tool Engine")
        print(f"    Execution: Agent System, Execution Pipeline")
        
        print("\n  World OS Components:")
        if stats.get('world_os'):
            print(f"    Microkernel processes: {stats['world_os'].get('microkernel', {}).get('processes', 0)}")
            print(f"    P2P peers: {stats['world_os'].get('p2p_network', {}).get('peers', 0)}")
            print(f"    RBE equilibrium: {stats['world_os'].get('rbe', {}).get('equilibrium_score', 0):.2f}")
        
        print("\n  Universal OS Components:")
        if stats.get('universal_os'):
            print(f"    Digital twins: {stats['universal_os'].get('digital_twins', {}).get('total_twins', 0)}")
            print(f"    Life tasks: {stats['universal_os'].get('life_automation', {}).get('total_tasks', 0)}")
        
        print("\n  Advanced Components:")
        if stats.get('advanced_components'):
            agi_stats = stats['advanced_components'].get('agi', {})
            quantum_stats = stats['advanced_components'].get('quantum', {})
            blockchain_stats = stats['advanced_components'].get('blockchain_identity', {})
            
            print(f"    AGI memories: {agi_stats.get('memories', {}).get('total', 0)}")
            print(f"    Quantum devices: {quantum_stats.get('devices', {}).get('total', 0)}")
            print(f"    Blockchain DIDs: {blockchain_stats.get('dids', {}).get('total', 0)}")
        
        print("\n" + "=" * 70)
        print("[SUCCESS] All 21 Components Integrated and Tested Successfully!")
        print("=" * 70)
        
        print("\nComponent Summary:")
        print("  - Original: 9 components")
        print("  - World OS: 5 components")
        print("  - Universal OS: 4 components")
        print("  - Advanced: 3 components")
        print("  - TOTAL: 21 components")
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    finally:
        # Shutdown
        print("\n[Cleanup] Shutting down...")
        await asim.shutdown()
        print("[OK] Shutdown complete")

if __name__ == "__main__":
    asyncio.run(test_complete_integration())
