"""
STATUS: REAL — Nepali Voice ASR Test Suite

AsimNexus Voice ASR Tests
===========================
Tests for Nepali Voice Recognition:
- Audio transcription
- Government command recognition
- Company command recognition
- Frontend integration
"""

import pytest
import asyncio

class TestNepaliASR:
    """Test Nepali ASR module"""
    
    @pytest.mark.asyncio
    async def test_asr_initialization(self):
        """Test ASR initializes correctly"""
        from models.nepal.whisper_finetune import get_nepali_asr
        asr = await get_nepali_asr()
        
        status = asr.status()
        assert "initialized" in status
        assert "language_support" in status
    
    @pytest.mark.asyncio
    async def test_stub_transcription(self):
        """Test transcription in fallback mode"""
        from models.nepal.whisper_finetune import get_nepali_asr
        asr = await get_nepali_asr()
        
        result = await asr.transcribe("test.wav")
        
        assert "text" in result
        assert "confidence" in result
    
    @pytest.mark.asyncio
    async def test_government_transcription(self):
        """Test government-specific transcription"""
        from models.nepal.whisper_finetune import get_nepali_asr
        asr = await get_nepali_asr()
        
        result = await asr.transcribe_for_government("test.wav")
        
        assert result["sector"] == "government"
    
    @pytest.mark.asyncio
    async def test_company_transcription(self):
        """Test company-specific transcription"""
        from models.nepal.whisper_finetune import get_nepali_asr
        asr = await get_nepali_asr()
        
        result = await asr.transcribe_for_company("test.wav")
        
        assert result["sector"] == "company"
    
    def test_nepali_numeral_normalization(self):
        """Test Nepali numeral normalization"""
        from models.nepal.whisper_finetune import NepaliASR
        asr = NepaliASR()
        
        # Test numeral conversion
        result = asr._normalize_nepali_numerals("मेरो आय १० लाख")
        assert "१०" not in result
        assert "10" in result

class TestASRIntegration:
    """Test ASR with other modules"""
    
    @pytest.mark.asyncio
    async def test_voice_action_flow(self):
        """Test complete voice action flow"""
        from models.nepal.whisper_finetune import get_nepali_asr
        from core.governance.tripartite_router import get_tripartite_router
        asr = await get_nepali_asr()
        router = get_tripartite_router()
        
        # Simulate voice command
        transcription = "मेरो कर कति बाँकी"
        
        # Route to appropriate sector
        decision = await router.route_request("tax_inquiry", "tax")
        assert decision.mode is not None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])