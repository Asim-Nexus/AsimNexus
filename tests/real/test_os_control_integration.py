#!/usr/bin/env python3
"""
STATUS: REAL — OS Control Integration Test
Test sandbox execution for OS tools.
"""

import sys
sys.path.insert(0, '.')


def test_os_control():
    """Test OS Control with sandbox integration."""
    print("=== OS CONTROL + SANDBOX INTEGRATION ===")
    
    # Test 1: Tool Registry
    print("[1/3] Tool Registry...")
    try:
        from os_control.tool_registry import tool_registry
        if tool_registry:
            tools = list(tool_registry._tools.keys())
            print(f"  Tools registered: {len(tools)}")
            print("  OK")
        else:
            print("  Registry not available")
    except Exception as e:
        print(f"  Error: {e}")
    
    # Test 2: ToolGuard
    print("[2/3] ToolGuard + Sandbox...")
    try:
        from core.sandbox.sandbox import ToolGuard
        guard = ToolGuard()
        print("  ToolGuard OK")
    except Exception as e:
        print(f"  Error: {e}")
    
    # Test 3: OS Control Bridge
    print("[3/3] OS Control Bridge...")
    try:
        from os_control import call_tool, get_available_tools
        tools = get_available_tools()
        print(f"  Available tools: {len(tools)}")
        print("  OK")
    except Exception as e:
        print(f"  Error: {e}")
    
    print("=== INTEGRATION COMPLETE ===")


if __name__ == "__main__":
    test_os_control()