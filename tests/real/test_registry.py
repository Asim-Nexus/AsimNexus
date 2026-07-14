#!/usr/bin/env python3
"""
STATUS: REAL — Tool Registry Integration Tests
AsimNexus Tool Registry Testing
=============================
Tests for OS tool registration and execution.

Covers:
- Basic registry initialization
- Full tool catalog via ``list_tools()`` (dict API)
- Full tool catalog via ``list_registrations()`` (rich metadata API)
- Single tool lookup via ``get_tool()``
- Registry statistics via ``get_stats()``
- Tool execution via ``execute_tool()``
- Tool metadata completeness (risk_level, capabilities, allowed_args)
"""

import pytest

try:
    from core.orchestrator.tool_registry import tool_registry
except ImportError:
    tool_registry = None

# ── Expected tool categories and counts ────────────────────────────────

EXPECTED_CATEGORIES = {
    "file": 7,        # file.list, file.read, file.write, file.copy, file.move, file.delete, file.info
    "process": 3,     # process.list, process.start, process.close
    "system": 7,      # system.cpu, system.memory, system.disk, system.network, system.battery, system.info, system.all
    "clipboard": 2,   # clipboard.read, clipboard.write
    "notification": 1, # notification.send
    "hw": 24,         # hw.status, hw.cpu, hw.memory, hw.disk, hw.network, hw.gpu, hw.npu, hw.motherboard,
                      # hw.chipset, hw.ram, hw.rom, hw.storage_controller, hw.usb, hw.display, hw.audio,
                      # hw.sensor, hw.thermal, hw.bios, hw.battery, hw.all, hw.power.* (4), hw.drivers.list, hw.stats
}

EXPECTED_MIN_TOOLS = 40  # At least 40 tools from asim_tools + 3 fallback

# ── Basic Initialization ───────────────────────────────────────────────

def test_tool_registry_initialization():
    """Test tool registry loads successfully."""
    if tool_registry is None:
        pytest.skip("tool_registry not available")
    assert tool_registry is not None

# ── Dict-based API (list_tools) ────────────────────────────────────────

def test_list_tools_returns_dict():
    """``list_tools()`` returns a dict with tool_id → metadata."""
    if tool_registry is None:
        pytest.skip("tool_registry not available")
    tools = tool_registry.list_tools()
    assert isinstance(tools, dict)
    assert len(tools) >= EXPECTED_MIN_TOOLS, (
        f"Expected at least {EXPECTED_MIN_TOOLS} tools, got {len(tools)}"
    )

def test_list_tools_contains_hw_status():
    """``hw.status`` tool exists in the catalog."""
    if tool_registry is None:
        pytest.skip("tool_registry not available")
    tools = tool_registry.list_tools()
    assert "hw.status" in tools, (
        f"hw.status not found in registered tools: {list(tools.keys())}"
    )

def test_list_tools_contains_file_read():
    """``file.read`` tool exists in the catalog."""
    if tool_registry is None:
        pytest.skip("tool_registry not available")
    tools = tool_registry.list_tools()
    assert "file.read" in tools, (
        f"file.read not found in registered tools: {list(tools.keys())}"
    )

def test_list_tools_contains_system_all():
    """``system.all`` tool exists in the catalog."""
    if tool_registry is None:
        pytest.skip("tool_registry not available")
    tools = tool_registry.list_tools()
    assert "system.all" in tools

def test_list_tools_metadata_completeness():
    """Each tool entry in ``list_tools()`` has required metadata fields."""
    if tool_registry is None:
        pytest.skip("tool_registry not available")
    tools = tool_registry.list_tools()
    for tid, meta in tools.items():
        assert "desc" in meta, f"{tid} missing 'desc'"
        assert "risk" in meta, f"{tid} missing 'risk'"
        assert "category" in meta, f"{tid} missing 'category'"
        # Rich metadata from asim_tools registry — allowed_args may be
        # a dict (from asim_tools) or absent (from fallback tools)
        if "allowed_args" in meta and meta["allowed_args"] is not None:
            assert isinstance(meta["allowed_args"], (dict, list)), (
                f"{tid} allowed_args not a dict or list: {type(meta['allowed_args'])}"
            )
        if "required_capabilities" in meta:
            assert isinstance(meta["required_capabilities"], list), (
                f"{tid} required_capabilities not a list"
            )

def test_list_tools_categories():
    """Tools are organized into expected categories."""
    if tool_registry is None:
        pytest.skip("tool_registry not available")
    tools = tool_registry.list_tools()
    categories = set()
    for tid in tools:
        cat = tid.split(".")[0] if "." in tid else "system"
        categories.add(cat)
    for expected_cat in EXPECTED_CATEGORIES:
        assert expected_cat in categories, (
            f"Expected category '{expected_cat}' not found. "
            f"Found categories: {sorted(categories)}"
        )

# ── Rich-metadata API (list_registrations) ─────────────────────────────

def test_list_registrations_returns_list():
    """``list_registrations()`` returns a list of ``ToolRegistration`` objects."""
    if tool_registry is None:
        pytest.skip("tool_registry not available")
    registrations = tool_registry.list_registrations()
    assert isinstance(registrations, list)
    assert len(registrations) >= EXPECTED_MIN_TOOLS, (
        f"Expected at least {EXPECTED_MIN_TOOLS} registrations, got {len(registrations)}"
    )

def test_list_registrations_has_rich_metadata():
    """Each ``ToolRegistration`` has tool_id, description, risk_level, capabilities."""
    if tool_registry is None:
        pytest.skip("tool_registry not available")
    registrations = tool_registry.list_registrations()
    for reg in registrations:
        assert hasattr(reg, "tool_id"), f"Registration missing tool_id: {reg}"
        assert hasattr(reg, "description"), f"{reg.tool_id} missing description"
        assert hasattr(reg, "risk_level"), f"{reg.tool_id} missing risk_level"
        assert hasattr(reg, "required_capabilities"), f"{reg.tool_id} missing required_capabilities"
        assert hasattr(reg, "requires_confirmation"), f"{reg.tool_id} missing requires_confirmation"
        assert hasattr(reg, "sandbox_required"), f"{reg.tool_id} missing sandbox_required"
        assert hasattr(reg, "allowed_args"), f"{reg.tool_id} missing allowed_args"

def test_list_registrations_risk_levels():
    """Risk levels are valid enum values: LOW, MEDIUM, HIGH, CRITICAL."""
    if tool_registry is None:
        pytest.skip("tool_registry not available")
    valid_risks = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
    registrations = tool_registry.list_registrations()
    for reg in registrations:
        risk = reg.risk_level.value if hasattr(reg.risk_level, "value") else str(reg.risk_level)
        assert risk.upper() in valid_risks, (
            f"{reg.tool_id} has invalid risk level: {risk}"
        )

# ── Single Tool Lookup ─────────────────────────────────────────────────

def test_get_tool_returns_registration():
    """``get_tool()`` returns a ``ToolRegistration`` for a known tool."""
    if tool_registry is None:
        pytest.skip("tool_registry not available")
    reg = tool_registry.get_tool("hw.status")
    assert reg is not None
    assert hasattr(reg, "tool_id")
    assert reg.tool_id == "hw.status"

def test_get_tool_returns_none_for_unknown():
    """``get_tool()`` returns ``None`` for an unknown tool."""
    if tool_registry is None:
        pytest.skip("tool_registry not available")
    reg = tool_registry.get_tool("nonexistent.tool.xyz")
    assert reg is None

def test_get_tool_file_read_has_allowed_args():
    """``file.read`` tool has ``allowed_args`` with path and encoding."""
    if tool_registry is None:
        pytest.skip("tool_registry not available")
    reg = tool_registry.get_tool("file.read")
    if reg is not None:
        assert hasattr(reg, "allowed_args")
        if reg.allowed_args:
            assert "path" in reg.allowed_args or "file_path" in reg.allowed_args, (
                f"file.read allowed_args missing path: {reg.allowed_args}"
            )

# ── Statistics ─────────────────────────────────────────────────────────

def test_get_stats_returns_dict():
    """``get_stats()`` returns a dict with total_tools, tool_names, categories."""
    if tool_registry is None:
        pytest.skip("tool_registry not available")
    stats = tool_registry.get_stats()
    assert isinstance(stats, dict)
    assert "total_tools" in stats
    assert "tool_names" in stats
    assert "categories" in stats
    assert stats["total_tools"] >= EXPECTED_MIN_TOOLS

def test_get_stats_categories():
    """``get_stats()`` categories include file, process, system, clipboard, notification, hw."""
    if tool_registry is None:
        pytest.skip("tool_registry not available")
    stats = tool_registry.get_stats()
    categories = stats.get("categories", [])
    for expected_cat in EXPECTED_CATEGORIES:
        assert expected_cat in categories, (
            f"Expected category '{expected_cat}' in stats, got {categories}"
        )

# ── Tool Execution ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_execute_tool_returns_dict():
    """``execute_tool()`` returns a dict with success, verdict, output, error."""
    if tool_registry is None:
        pytest.skip("tool_registry not available")
    result = await tool_registry.execute_tool(
        tool_id="hw.status",
        parameters={},
        agent_name="AutoModeAgent",
    )
    assert isinstance(result, dict)
    assert "success" in result
    assert "verdict" in result
    assert "output" in result
    assert "error" in result
    assert "call_id" in result
    assert "execution_ms" in result

@pytest.mark.asyncio
async def test_execute_tool_unknown_tool():
    """``execute_tool()`` returns error for unknown tool."""
    if tool_registry is None:
        pytest.skip("tool_registry not available")
    result = await tool_registry.execute_tool(
        tool_id="nonexistent.tool",
        parameters={},
    )
    assert result["success"] is False
    assert result["verdict"] in ("error", "denied")

# ── Fallback Tools ─────────────────────────────────────────────────────

def test_fallback_tools_present():
    """Fallback tools (web_search, rag_query) are always present."""
    if tool_registry is None:
        pytest.skip("tool_registry not available")
    tools = tool_registry.list_tools()
    assert "web_search" in tools
    assert "rag_query" in tools
    assert tools["web_search"]["category"] == "web"
    assert tools["rag_query"]["category"] == "knowledge"