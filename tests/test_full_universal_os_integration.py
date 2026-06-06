
"""
STATUS: REAL — Auto-labeled by batch_label.py
"""

"""
Test Full Universal OS Integration
===================================

Test all components together:
- Original 9 improvements
- 5 World OS components
- 3 Universal OS components
"""

import asyncio
from datetime import date
from core.new_architecture_integration import NewASIMNEXUS, ASIMConfig
from core.digital_twin_system import Gender


async def test_full_integration():
    """Test full integration of all components"""
    print("=" * 60)
    print("Testing ASIMNEXUS Universal World OS - Full Integration")
    print("=" * 60)
    
    # Initialize with all components enabled
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
        enable_life_automation=True
    )
    
    asim = NewASIMNEXUS(config)
    
    try:
        # Initialize
        print("\n🔧 Initializing ASIMNEXUS Universal World OS...")
        await asim.initialize()
        
        # Verify all components
        print("\n✅ Verifying all components...")
        
        # Original components
        assert asim.state_manager is not None, "State manager not initialized"
        print("  ✓ State Manager")
        
        assert asim.cache_manager is not None, "Cache manager not initialized"
        print("  ✓ Cache Manager")
        
        assert asim.hybrid_router is not None, "Hybrid router not initialized"
        print("  ✓ Hybrid Router")
        
        assert asim.smart_llm_router is not None, "Smart LLM router not initialized"
        print("  ✓ Smart LLM Router")
        
        assert asim.tool_engine is not None, "Tool engine not initialized"
        print("  ✓ Tool Engine")
        
        assert asim.hybrid_rag is not None, "Hybrid RAG not initialized"
        print("  ✓ Hybrid RAG")
        
        assert asim.agent_system is not None, "Agent system not initialized"
        print("  ✓ Agent System")
        
        assert asim.execution_pipeline is not None, "Execution pipeline not initialized"
        print("  ✓ Execution Pipeline")
        
        # World OS components
        assert asim.microkernel is not None, "Microkernel not initialized"
        print("  ✓ Microkernel")
        
        assert asim.p2p_network is not None, "P2P network not initialized"
        print("  ✓ P2P Network")
        
        assert asim.uplink_connector is not None, "Uplink connector not initialized"
        print("  ✓ Uplink Connector")
        
        assert asim.daylight_connector is not None, "Daylight connector not initialized"
        print("  ✓ Daylight Connector")
        
        assert asim.dimo_connector is not None, "DIMO connector not initialized"
        print("  ✓ DIMO Connector")
        
        assert asim.rbe_algorithm is not None, "RBE algorithm not initialized"
        print("  ✓ RBE Algorithm")
        
        assert asim.mythos_scanner is not None, "Mythos scanner not initialized"
        print("  ✓ Mythos Scanner")
        
        # Universal OS components
        assert asim.api_gateway is not None, "API gateway not initialized"
        print("  ✓ API Gateway")
        
        assert asim.digital_twin_system is not None, "Digital twin system not initialized"
        print("  ✓ Digital Twin System")
        
        assert asim.life_automation is not None, "Life automation not initialized"
        print("  ✓ Life Automation")
        
        # Test digital twin creation
        print("\n👥 Testing digital twin creation...")
        twin_result = asim.create_digital_twin(
            legal_name="Test User",
            date_of_birth=date(1990, 1, 1),
            nationality="US",
            gender=Gender.MALE
        )
        
        assert "twin_id" in twin_result, "Digital twin creation failed"
        print(f"  ✓ Created twin: {twin_result['twin_id']}")
        
        # Test getting twin
        twin_data = asim.get_digital_twin(twin_result['twin_id'])
        assert "life_stage" in twin_data, "Failed to get twin data"
        print(f"  ✓ Twin life stage: {twin_data['life_stage']}")
        
        # Get stats
        print("\n📊 Getting system statistics...")
        stats = await asim.get_stats()
        
        print("\n  World OS Stats:")
        if stats.get('world_os'):
            print(f"    Microkernel: {stats['world_os'].get('microkernel', {})}")
            print(f"    P2P Network: {stats['world_os'].get('p2p_network', {})}")
            print(f"    RBE: {stats['world_os'].get('rbe', {})}")
            print(f"    Mythos: {stats['world_os'].get('mythos', {})}")
        
        print("\n  Universal OS Stats:")
        if stats.get('universal_os'):
            print(f"    API Gateway: {stats['universal_os'].get('api_gateway', {})}")
            print(f"    Digital Twins: {stats['universal_os'].get('digital_twins', {})}")
            print(f"    Life Automation: {stats['universal_os'].get('life_automation', {})}")
        
        print("\n" + "=" * 60)
        print("✅ Full Universal World OS Integration Test Passed!")
        print("=" * 60)
        
        print("\n📊 Summary:")
        print(f"  - Original Components: 9")
        print(f"  - World OS Components: 5")
        print(f"  - Universal OS Components: 3")
        print(f"  - Total Components: 17")
        print(f"  - Digital Twins: {stats['universal_os']['digital_twins']['total_twins']}")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise
    
    finally:
        # Shutdown
        print("\n🛑 Shutting down...")
        await asim.shutdown()
        print("✅ Shutdown complete")


if __name__ == "__main__":
    asyncio.run(test_full_integration())
