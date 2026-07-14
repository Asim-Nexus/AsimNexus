#!/usr/bin/env python3
"""
STATUS: REAL — Local Brain Loop Tests
AsimNexus Dreaming Engine Testing
=================================
Tests for overnight learning and brain evolution.
"""

import asyncio
import pytest
from unittest.mock import patch

def test_dreaming_engine_initialization():
    """Test Dreaming Engine initializes."""
    from core.mirror.dreaming_engine import DreamingEngine
    engine = DreamingEngine()
    assert engine.user_id == "default"

def test_dream_types():
    """Test dream types enum."""
    from core.mirror.dreaming_engine import DreamType
    assert DreamType.INTEGRATION.value == "integration"
    assert DreamType.PATTERN_RECOGNITION.value == "pattern_recognition"
    assert DreamType.EVOLUTION.value == "evolution"

def test_dream_dataclass():
    """Test Dream dataclass."""
    from core.mirror.dreaming_engine import Dream, DreamType
    dream = Dream(
        dream_type=DreamType.INTEGRATION,
        content="Test integration",
    )
    assert dream.content == "Test integration"
    assert dream.dream_type == DreamType.INTEGRATION

@pytest.mark.asyncio
@pytest.mark.timeout(15)
async def test_nightly_evolution():
    """Test nightly evolution with DreamingEngine."""
    from core.mirror.dreaming_engine import DreamingEngine

    engine = DreamingEngine()
    reflections = [
        {"intent": f"test_{i}", "outcome": "success", "timestamp": float(i)}
        for i in range(12)
    ]
    dreams = await engine.nightly_evolution(reflections)
    assert isinstance(dreams, list)
    assert len(dreams) >= 1
    assert dreams[0].content is not None
    assert "Integrated" in dreams[0].content
