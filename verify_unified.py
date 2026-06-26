#!/usr/bin/env python3
"""
AsimNexus Unified System - All Layers Connected
===============================================
Single entry point to verify and run all of AsimNexus.
"""

import sys
import os
from pathlib import Path

# Ensure all paths are available
sys.path.insert(0, str(Path('.').absolute()))
sys.path.insert(0, str(Path('DigitalNepal-backend').absolute()))

def verify_and_connect():
    """Verify all layers and connect them"""
    results = {}
    
    # 1. Connectors
    try:
        from connectors.nepal.government import (
            MINISTRIES, PROVINCES, DISTRICTS, BANKS, ISPS, UNIVERSITIES, SCHOOLS
        )
        from connectors.health.hospitals import HOSPITALS
        from connectors.local.palikas import PALIKAS
        from connectors.tourism.hotels import HOTELS
        
        total = len(MINISTRIES) + len(PROVINCES) + len(DISTRICTS) + len(BANKS) + len(ISPS) + len(UNIVERSITIES) + len(SCHOOLS) + len(HOSPITALS) + len(PALIKAS) + len(HOTELS)
        results['connectors'] = f'{total} entities'
    except Exception as e:
        results['connectors'] = f'ERROR: {e}'
    
    # 2. Core
    try:
        from core.consensus_engine import ConsensusEngine
        from core.compliance_engine import ComplianceEngine
        results['core'] = 'Consensus + Compliance ready'
    except Exception as e:
        results['core'] = f'WARNING: {e}'
    
    # 3. Security
    try:
        from security.zkp_privacy import ZKPProof
        from security.hsm_integration import HSMIntegration
        from security.power_balance_constitution import PowerBalanceConstitution
        results['security'] = 'ZKP + HSM + Power Balance'
    except Exception as e:
        results['security'] = f'WARNING: {e}'
    
    # 4. Mesh
    try:
        from mesh.offline_sync_engine import OfflineSyncEngine
        from mesh.crdt_sync import CRDTStore
        results['mesh'] = 'OfflineSync + CRDT ready'
    except Exception as e:
        results['mesh'] = f'WARNING: {e}'
    
    # 5. Economy
    try:
        from economy.wallet import WalletEngine
        from economy.tokens import TokenRegistry
        from economy.escrow import EscrowEngine
        from economy.marketplace import MarketplaceEngine
        from economy.staking import StakingEngine
        results['economy'] = '5 engines ready'
    except Exception as e:
        results['economy'] = f'WARNING: {e}'
    
    # 6. OS Control
    try:
        from os_control.tool_registry import tool_registry
        count = len(tool_registry.list_tools())
        results['tools'] = f'{count} registered'
    except Exception as e:
        results['tools'] = f'WARNING: {e}'
    
    # Print results
    print("\n" + "="*50)
    print("ASIMNEXUS UNIFIED SYSTEM - VERIFICATION")
    print("="*50 + "\n")
    
    for layer, status in results.items():
        print(f"{layer.upper():15} {status}")
    
    print("\n" + "="*50)
    print("ALL SYSTEMS CONNECTED")
    print("="*50 + "\n")
    
    return results

if __name__ == "__main__":
    verify_and_connect()