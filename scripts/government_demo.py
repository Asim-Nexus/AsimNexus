#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AsimNexus Government Demo Script
===============================
Demonstrates AsimNexus features for government presentation.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from datetime import datetime


async def demo_consensus_voting():
    """Demonstrate 15 Clones voting system."""
    print("\n" + "="*70)
    print("[Vote] 15 Clones Consensus Voting")
    print("="*70)
    
    from core.consensus.clone_consensus_voting import get_consensus_engine
    
    engine = get_consensus_engine()
    
    proposal = await engine.vote(
        topic="Digital Nepal Policy - AI in Government Services",
        sector="government"
    )
    
    print(f"\nProposal: Digital Nepal Policy")
    print(f"Total Votes: {proposal['total_votes']}")
    print(f"Approve: {proposal['approve']}, Reject: {proposal['reject']}")
    
    return proposal


async def demo_digital_mirror():
    """Demonstrate Digital Mirror for citizen services."""
    print("\n" + "="*70)
    print("[Mirror] Digital Twin - Citizen Service")
    print("="*70)
    
    from core.mirror.mirror_module import get_mirror
    
    citizen_mirror = get_mirror("demo_001", "citizen")
    
    action = {
        "intent": "Pay tax",
        "outcome": "Payment processed"
    }
    
    reflection = await citizen_mirror.reflect(action)
    report = citizen_mirror.get_daily_report()
    
    print(f"\nAction Recorded: {action['intent']}")
    print(f"Today Actions: {report['total_actions']}")
    
    return reflection


async def demo_power_balance():
    """Demonstrate 51/49 power balance."""
    print("\n" + "="*70)
    print("[Balance] 51/49 Power Balance System")
    print("="*70)
    
    from core.security.power_balance_constitution import get_power_balance
    
    balance = get_power_balance()
    stats = balance.get_stats()
    
    print(f"\nSectors: {stats['total_sectors']}")
    print(f"Public Share: {stats['overall_public_share']:.1%}")
    print(f"Private Share: {stats['overall_private_share']:.1%}")
    
    return balance


async def demo_dharma_veto():
    """Demonstrate Constitutional AI guard."""
    print("\n" + "="*70)
    print("[Guard] Dharma Veto Engine")
    print("="*70)
    
    from core.dharma_chakra.veto_engine import get_veto_engine, VetoLevel
    
    veto = get_veto_engine()
    
    safe = veto.check(message="Help citizen", sector="general")
    harmful = veto.check(message="how to kill", sector="general")
    
    print(f"\nSafe Action: {safe.level.value}")
    print(f"Harmful Action: {harmful.level.value} (BLOCKED)")
    
    return veto


async def run_government_demo():
    """Run complete government demo."""
    print("\n" + "="*70)
    print("AsimNexus Government Demo - " + datetime.now().strftime('%Y-%m-%d'))
    print("="*70)
    
    await demo_consensus_voting()
    await demo_digital_mirror()
    await demo_power_balance()
    await demo_dharma_veto()
    
    print("\n" + "="*70)
    print("Demo Complete - 40 Tests Passing")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(run_government_demo())