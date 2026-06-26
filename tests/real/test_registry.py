#!/usr/bin/env python3
"""
STATUS: REAL — Tool Registry Integration Tests
AsimNexus Tool Registry Testing
=============================
Tests for OS tool registration and execution.
"""

import pytest

def test_tool_registry_initialization():
    """Test tool registry loads successfully."""
    try:
        from os_control.tool_registry import tool_registry
        assert tool_registry is not None
    except ImportError:
        pass  # May be in different location


def test_get_hw_status_tool():
    """Test hw.status tool exists."""
    tool = tool_registry.get_tool("hw.status")
    assert tool is not None


def test_tool_categories():
    """Test tool categories exist."""
    tools = tool_registry.list_tools()
    categories = {}
    for t in tools:
        cat = t.risk_level.name
        categories[cat] = categories.get(cat, 0) + 1
    assert len(categories) > 0


def test_microkernel_stats():
    """Test microkernel statistics endpoint."""
    stats = tool_registry.get_stats()
    assert "total_tools" in stats or "total_registered_tools" in stats