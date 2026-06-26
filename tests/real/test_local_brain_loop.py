#!/usr/bin/env python3
"""
STATUS: REAL — Local Brain Loop Tests
AsimNexus Dreaming Engine Testing
=================================
Tests for overnight learning and brain evolution.
"""

import asyncio
import pytest


def test_dreaming_engine_initialization():
    """Test Dreaming Engine initializes."""
    from core.mirror.dreaming_engine import DreamingEngine
    engine = DreamingEngine()
    assert engine.user_id == "default"


def test_dream_types():
    """Test dream types enum."""
    from core.mirror.dreaming_engine import DreamType
    assert DreamType.PREDICTION.value == "prediction"
    assert DreamType.PATTERN.value == "pattern"


def test_dream_dataclass():
    """Test Dream dataclass."""
    from core.mirror.dreaming_engine import Dream, DreamType
    dream = Dream(
        dream_type=DreamType.PREDICTION,
        content="Test prediction",
        confidence=0.8
    )
    assert dream.content == "Test prediction"
    assert dream.confidence == 0.8


@pytest.mark.asyncio
async def test_nightly_evolution():
    """Test nightly evolution process."""
    from core.mirror.dreaming_engine import DreamingEngine
    engine = DreamingEngine()
    reflections = [{"intent": "test", "outcome": "success", "timestamp": 1.0}]
    dreams = await engine.nightly_evolution(reflections)
    assert isinstance(dreams, list)