"""
STATUS: REAL — Tests for Dreaming Engine
Tests: Topic detection, lesson extraction, cycle execution, pruning
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.dreaming.dreaming_engine import (
    DreamingEngine, detect_topics, extract_lesson, generate_briefing, DreamCycle
)


class TestTopicDetection:
    """Test keyword-based topic classifier."""

    def test_detects_coding(self):
        assert "coding" in detect_topics("How do I write a python function?")

    def test_detects_health(self):
        assert "health" in detect_topics("My doctor said to exercise more and eat healthy.")

    def test_detects_finance(self):
        assert "finance" in detect_topics("I need to invest my money and budget better.")

    def test_detects_farming(self):
        assert "farming" in detect_topics("What is the best crop for this season and soil?")

    def test_detects_education(self):
        assert "education" in detect_topics("I want to learn math and study for exams.")

    def test_detects_legal(self):
        assert "legal" in detect_topics("What are my rights in court regarding this contract?")

    def test_general_fallback(self):
        result = detect_topics("Hello world today")
        assert result == ["general"]

    def test_multiple_topics(self):
        result = detect_topics("I need to code a budget app for my farm")
        assert len(result) >= 2


class TestLessonExtraction:
    """Test lesson extraction from messages."""

    def test_extracts_from_assistant_messages(self):
        messages = [
            {"role": "user", "content": "How to code?"},
            {"role": "assistant", "content": "You should use Python and write clean functions with proper error handling.", "id": "msg1"},
        ]
        lesson = extract_lesson(messages)
        assert lesson is not None
        assert lesson.topic == "coding"
        assert "Python" in lesson.summary

    def test_no_lesson_for_short_messages(self):
        messages = [
            {"role": "assistant", "content": "Yes.", "id": "msg1"},
        ]
        lesson = extract_lesson(messages)
        assert lesson is None

    def test_no_lesson_for_empty(self):
        assert extract_lesson([]) is None


class TestBriefingGeneration:
    """Test dream cycle briefing."""

    def test_empty_briefing(self):
        cycle = DreamCycle(cycle_id="abc123", started_at="2024-01-01T00:00:00Z")
        cycle.messages_processed = 0
        briefing = generate_briefing([], cycle)
        assert "No new lessons today" in briefing
        assert "System is rested and ready" in briefing

    def test_briefing_with_lessons(self):
        from core.dreaming.dreaming_engine import Lesson
        cycle = DreamCycle(cycle_id="abc123", started_at="2024-01-01T00:00:00Z")
        cycle.messages_processed = 50
        cycle.lessons_extracted = 3
        cycle.memories_pruned = 2
        lessons = [
            Lesson(topic="coding", summary="Learn Python functions", confidence=0.8),
            Lesson(topic="coding", summary="Use type hints", confidence=0.7),
            Lesson(topic="health", summary="Exercise daily", confidence=0.9),
        ]
        briefing = generate_briefing(lessons, cycle)
        assert "coding(2)" in briefing
        assert "health(1)" in briefing
        assert "50 msgs" in briefing


class TestDreamingEngine:
    """Test DreamingEngine class."""

    def test_initialization(self):
        engine = DreamingEngine(cycle_interval_minutes=30)
        status = engine.status()
        assert status["running"] is False
        assert status["cycle_interval_minutes"] == 30
        assert status["total_cycles"] == 0

    def test_start_stop(self):
        engine = DreamingEngine(cycle_interval_minutes=60)
        engine.stop()
        assert engine.status()["running"] is False

    def test_briefing_before_dream(self):
        engine = DreamingEngine()
        assert "Not yet dreamed" in engine.get_briefing()

    def test_recent_lessons_empty(self):
        engine = DreamingEngine()
        assert engine.get_recent_lessons() == []

    @pytest.mark.asyncio
    async def test_trigger_now_runs_cycle(self):
        """Manual trigger should execute one cycle."""
        engine = DreamingEngine()
        result = await engine.trigger_now()
        assert isinstance(result, str)
        assert engine.status()["total_cycles"] == 1
