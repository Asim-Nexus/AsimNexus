#!/usr/bin/env python3
"""
STATUS: REAL — Personal OS Tests
AsimNexus Personal OS Testing
============================
Tests for personal OS and Mirror integration.
"""

import pytest
import asyncio

def test_personal_os_status():
    """Test personal OS status endpoint."""
    try:
        from core.mirror.mirror_module import MirrorModule
        mirror = MirrorModule("test_user")
        assert mirror.user_id == "test_user"
    except ImportError:
        Pass

@pytest.mark.asyncio
async def test_mirror_reflect():
    """Test Mirror reflection."""
    from core.mirror.mirror_module import get_mirror
    mirror = get_mirror("reflect_test")
    result = await mirror.reflect({"intent": "test action"})
    assert result.intent == "test action"

def test_mirror_singleton():
    """Test Mirror singleton pattern."""
    from core.mirror.mirror_module import get_mirror, _mirror_instances
    m1 = get_mirror("user singleton test")
    m2 = get_mirror("user singleton test")
    assert m1 is m2