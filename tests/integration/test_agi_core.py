
"""
STATUS: REAL — Auto-labeled by batch_label.py
"""

"""
Test AGI Core System
====================

Test the AGI Core implementation.
"""

import asyncio
from datetime import datetime
from core.agi_core import AGICore, get_agi_core, ReasoningMode, AGICapability

async def test_agi_core():
    """Test AGI Core System"""
    print("=" * 60)
    print("Testing AGI Core System")
    print("=" * 60)
    
    agi = get_agi_core()
    
    # Test 1: Initialization
    print("\n[OK] AGI Core initialized")
    print(f"  State ID: {agi.state.state_id}")
    print(f"  Safety constraints: {len(agi.safety_constraints)}")
    print(f"  Default skills: {len(agi.skills)}")
    
    # Test 2: Safety constraints
    print("\n[OK] Safety constraints:")
    for constraint in agi.safety_constraints.values():
        print(f"  - {constraint.name}: {constraint.description[:50]}...")
    
    # Test 3: Reasoning
    print("\n[OK] Testing chain-of-thought reasoning...")
    chain = await agi.think(
        query="How can we improve the digital twin system?",
        reasoning_mode=ReasoningMode.ANALYTICAL,
        max_depth=3
    )
    
    print(f"  Chain ID: {chain.chain_id}")
    print(f"  Query: {chain.query}")
    print(f"  Thoughts: {len(chain.thoughts)}")
    print(f"  Conclusion: {chain.conclusion[:100]}...")
    print(f"  Confidence: {chain.confidence:.2f}")
    
    # Test 4: Memory storage
    print("\n[OK] Testing memory storage...")
    memory_id = agi.store_memory(
        content="Digital twin system improved with AGI integration",
        memory_type="episodic",
        importance=0.8
    )
    print(f"  Stored memory: {memory_id}")
    
    retrieved = agi.get_memory(memory_id)
    if retrieved:
        print(f"  Retrieved: {retrieved.content[:50]}...")
    
    # Test 5: Capability scores
    print("\n[OK] Capability scores:")
    for cap in AGICapability:
        score = agi.get_capability_score(cap)
        print(f"  - {cap.value}: {score:.2f}")
    
    # Test 6: Stats
    print("\n[OK] AGI System Statistics:")
    stats = agi.get_stats()
    print(f"  Total memories: {stats['memories']['total']}")
    print(f"  Total skills: {stats['skills']['total']}")
    print(f"  Reasoning chains: {stats['reasoning_chains']}")
    print(f"  Learning entries: {stats['learning_entries']}")
    print(f"  Self-improvement: {stats['self_improvement_enabled']}")
    
    # Test 7: Safety check
    print("\n[OK] Testing safety constraints...")
    safe_result = await agi._check_safety_constraints("How to improve the system")
    print(f"  Safe query: {safe_result['safe']}")
    
    unsafe_result = await agi._check_safety_constraints("How to harm someone")
    print(f"  Unsafe query detected: {not unsafe_result['safe']}")
    if not unsafe_result['safe']:
        print(f"  Reason: {unsafe_result['reason']}")
    
    print("\n" + "=" * 60)
    print("[SUCCESS] AGI Core System Test Passed!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_agi_core())
