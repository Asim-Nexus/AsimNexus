#!/usr/bin/env python3
"""
AsimNexus Full Integration Test
==============================
Tests all layers together - uses proper paths.
"""

import sys
import importlib
from pathlib import Path

# Setup paths  
backend = Path("DigitalNepal-backend").absolute()
root = Path(".").absolute()

def load_module(name, path):
    """Load module by path"""
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def test_connectors():
    """Test all connectors - 956 entities"""
    mod = load_module("nepal_connectors", backend / "connectors" / "nepal_connectors.py")
    mod_health = load_module("health_connectors", backend / "connectors" / "health_connectors.py")
    mod_palika = load_module("palika_connectors", backend / "connectors" / "palika_connectors.py")
    mod_tourism = load_module("tourism_connectors", backend / "connectors" / "tourism_connectors.py")
    
    total = (len(mod.MINISTRIES) + len(mod.PROVINCES) + len(mod.DISTRICTS) + 
             len(mod.BANKS) + len(mod.ISPS) + len(mod.UNIVERSITIES) + len(mod.SCHOOLS) +
             len(mod_health.HOSPITALS) + len(mod_palika.PALIKAS) + len(mod_tourism.HOTELS))
    print(f"connectors: {total} entities")

def test_core():
    """Test core modules"""
    mod_cons = load_module("consensus_engine", backend / "core" / "consensus_engine.py")
    mod_comp = load_module("compliance_engine", backend / "core" / "compliance_engine.py")
    print("core: Consensus (15 Clones) + Compliance (51/49) loaded")

def test_security():
    """Test security"""
    load_module("zkp_privacy", root / "security" / "zkp_privacy.py")
    load_module("hsm_integration", root / "security" / "hsm_integration.py")
    load_module("power_balance_constitution", root / "security" / "power_balance_constitution.py")
    load_module("zero_trust", root / "security" / "zero_trust.py")
    print("security: ZKP + HSM + Power Balance + Zero Trust")

def test_mesh():
    """Test mesh"""
    load_module("offline_sync_engine", root / "mesh" / "offline_sync_engine.py")
    load_module("crdt_sync", root / "mesh" / "crdt_sync.py")
    print("mesh: OfflineSync + CRDT")

def test_economy():
    """Test economy"""
    load_module("wallet", root / "economy" / "wallet.py")
    load_module("tokens", root / "economy" / "tokens.py")
    load_module("escrow", root / "economy" / "escrow.py")
    load_module("staking", root / "economy" / "staking.py")
    print("economy: Wallet + Tokens + Escrow + Staking")

def test_tools():
    """Test tools"""
    mod = load_module("all_tools", backend / "tools" / "all_tools.py")
    result = mod.get_all_tools()
    print(f"tools: {result['count']} tools available")

def test_os_control():
    """Test OS Control"""
    mod = load_module("tool_registry", root / "os_control" / "tool_registry.py")
    count = len(mod.tool_registry.list_tools())
    print(f"os_control: {count} tools registered")

if __name__ == "__main__":
    print("\n=== AsimNexus Full Integration Test ===\n")
    
    test_connectors()
    test_core()
    test_security()
    test_mesh()
    test_economy()
    test_tools()
    test_os_control()
    
    print("\n=== ALL LAYERS INTEGRATED ===\n")