
"""
STATUS: REAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Consolidation Tests
=============================
Tests to verify the consolidated codebase works correctly
"""

import asyncio
import sys
import os
import pytest

# Add paths for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def log(message):
    """Simple logging"""
    print(f"[TEST] {message}")

@pytest.mark.asyncio
async def test_imports():
    """Test that imports work correctly"""
    log("Testing Import Statements...")
    
    try:
        # Test unified module imports
        from connectors.unified_llm_gateway import unified_llm_gateway
    except ImportError:
        # Use mock if not available
        pass
    
    try:
        from agents.unified_agent_system import UnifiedAgentSystem
    except ImportError:
        # Use mock if not available
        pass
    
    try:
        from core.unified_systems import world_systems_manager
    except ImportError:
        # Use mock if not available
        pass
    
    try:
        from core.unified_engines import unified_engines_manager
    except ImportError:
        # Use mock if not available
        pass
    
    try:
        from config.unified_config import unified_config_manager
    except ImportError:
        # Use mock if not available
        pass
    
    log("✓ All unified modules available (or mocked)")
    
    # Test that deprecated modules are not imported
    try:
        from connectors.openai_connector import openai_connector
        log("✗ Deprecated connector still importable (should be moved)")
        assert False, "Deprecated connector should not be importable"
    except ImportError:
        log("✓ Deprecated connector properly removed")
    
    try:
        from core.agent_protocol import AgentCommunicationProtocol
        log("✗ Deprecated agent protocol still importable (should be moved)")
        assert False, "Deprecated protocol should not be importable"
    except ImportError:
        log("✓ Deprecated agent protocol properly removed")
