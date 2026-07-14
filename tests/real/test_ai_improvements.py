"""
Phase 5.4: AI Improvements Tests
"""
import pytest
from fastapi.testclient import TestClient

def test_nepali_fine_tuner_exists():
    """Nepali fine tuner module exists."""
    from core.ai_improvements import NepaliFineTuner
    assert NepaliFineTuner is not None

def test_nepali_fine_tune():
    """Fine-tune on Nepali works."""
    from core.ai_improvements import NepaliFineTuner
    tuner = NepaliFineTuner()
    result = tuner.fine_tune("gpt-4")
    assert result["status"] == "success"

def test_multimodal_processor_exists():
    """Multi-modal processor exists."""
    from core.ai_improvements import MultiModalProcessor
    assert MultiModalProcessor is not None

def test_multimodal_process():
    """Multi-modal process works."""
    from core.ai_improvements import MultiModalProcessor
    mm = MultiModalProcessor()
    result = mm.process("text", "नमस्ते")
    assert result["status"] == "processed"

def test_ai_status_endpoint():
    """AI status endpoint works."""
    from app import app
    client = TestClient(app)
    response = client.get("/api/ai/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data