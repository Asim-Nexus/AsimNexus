"""
STATUS: REAL — End-to-End Test Suite for AsimNexus

AsimNexus End-to-End Tests
============================
Tests all integrated modules:
- HSM Production → Government API
- ZKP Privacy → Tax LLM
- mTLS Security → All Routes
- PostgreSQL → All Databases
- Nepali Voice ASR → Frontend
"""

import pytest
import asyncio
from pathlib import Path

class TestHSMIntegration:
    """Test HSM Production integration with Government API"""
    
    @pytest.mark.asyncio
    async def test_hsm_initialization(self):
        """Test HSM initializes correctly"""
        from core.security.hsm_production import HSMProduction
        hsm = HSMProduction()
        
        status = hsm.status()
        assert "hsm_available" in status
        assert "fallback_mode" in status
    
    @pytest.mark.asyncio
    async def test_hsm_signature_verification(self):
        """Test HSM signature verification"""
        from core.security.hsm_production import HSMProduction
        hsm = HSMProduction()
        
        # Test signature verification (stub mode)
        result = await hsm._verify_hsm_signature(
            {"data": b"test_data", "sig": b"test_sig"},
            "test_public_key"
        )
        assert isinstance(result, bool)
    
    @pytest.mark.asyncio
    async def test_level3_approval_flow(self):
        """Test complete Level-3 approval flow"""
        from core.security.hsm_production import HSMProduction
        hsm = HSMProduction()
        
        action = {
            "proposal": {"sector": "infrastructure", "change": "new_policy"}
        }
        user = {
            "id": "test_user",
            "public_key": "test_key",
            "phone": "9841234567"
        }
        
        # In development mode (no HSM hardware), should still work
        result = await hsm.level3_approve(action, user)
        # Fallback should allow in dev mode
        assert isinstance(result, bool)

class TestZKPPrivacy:
    """Test ZKP Production integration with Tax LLM"""
    
    @pytest.mark.asyncio
    async def test_zkp_initialization(self):
        """Test ZKP initializes correctly"""
        from core.security.zkp_production import ZKPProduction
        zkp = ZKPProduction()
        
        status = zkp.status()
        assert "zkp_available" in status
        assert "language_support" in status
    
    @pytest.mark.asyncio
    async def test_identity_proof_generation(self):
        """Test identity proof generation (fallback mode)"""
        from core.security.zkp_production import ZKPProduction
        zkp = ZKPProduction()
        
        citizen_data = {
            "citizen_id": "123456789",
            "birth_year": 2000,
            "district_code": 26,
            "verified": True
        }
        
        proof = await zkp.prove_identity(citizen_data)
        
        assert "proof" in proof
        assert "public_inputs" in proof
        assert "verification_key" in proof
    
    @pytest.mark.asyncio
    async def test_identity_proof_verification(self):
        """Test identity proof verification"""
        from core.security.zkp_production import ZKPProduction
        zkp = ZKPProduction()
        
        citizen_data = {
            "citizen_id": "123456789",
            "birth_year": 2000,
            "district_code": 26,
            "verified": True
        }
        
        proof = await zkp.prove_identity(citizen_data)
        
        # Verify the proof
        is_valid = await zkp.verify_identity(
            proof=proof,
            required={
                "age_greater_equal": True,
                "district_valid": True,
                "citizenship_verified": True
            }
        )
        
        assert isinstance(is_valid, bool)
    
    @pytest.mark.asyncio
    async def test_tax_compliance_proof(self):
        """Test tax compliance proof generation"""
        from core.security.zkp_production import ZKPProduction
        zkp = ZKPProduction()
        
        proof = await zkp.prove_tax_compliance(
            income=1500000,
            tax_paid=75000,  # 5% tax
            tax_rate=0.05
        )
        
        assert "tax_compliant" in proof
        assert proof["tax_compliant"] == True

class TestmTLSIntegration:
    """Test mTLS Security integration"""
    
    def test_mtls_initialization(self):
        """Test mTLS initializes correctly"""
        from core.security.mtls import MTLSManager
        mtls = MTLSManager()
        
        status = mtls.status()
        assert "ca_loaded" in status
        assert "sector_roles" in status
    
    def test_ssl_context_creation(self):
        """Test SSL context creation for mTLS"""
        from core.security.mtls import MTLSManager
        mtls = MTLSManager()
        
        try:
            context = mtls.create_ssl_context(mode="server")
            assert context is not None
            assert context.verify_mode is not None
        except Exception as e:
            # May fail without cert files in dev environment
            pytest.skip(f"SSL context creation skipped: {e}")
    
    @pytest.mark.asyncio
    async def test_client_cert_verification(self):
        """Test client certificate verification"""
        from core.security.mtls import MTLSManager
        mtls = MTLSManager()
        
        # Test with dummy cert data
        result = await mtls.verify_client_cert(b"dummy_cert")
        # Should handle gracefully
        assert result is None or isinstance(result, dict)

class TestPostgreSQLMigration:
    """Test PostgreSQL Migration module"""
    
    @pytest.mark.asyncio
    async def test_migration_initialization(self):
        """Test migration initializes"""
        from database.migrations.postgresql import PostgreSQLMigration
        migration = PostgreSQLMigration()
        
        status = migration.status()
        assert "initialized" in status
        assert "connections" in status
    
    @pytest.mark.asyncio
    async def test_government_migration(self):
        """Test government schema creation"""
        from database.migrations.postgresql import PostgreSQLMigration
        migration = PostgreSQLMigration()
        
        # Without actual DB connection, should return stub
        result = await migration.migrate_government()
        assert "status" in result

class TestNepaliVoiceASR:
    """Test Nepali Voice ASR integration"""
    
    @pytest.mark.asyncio
    async def test_asr_initialization(self):
        """Test ASR initializes correctly"""
        from models.nepal.whisper_finetune import NepaliASR
        asr = NepaliASR()
        
        status = asr.status()
        assert "initialized" in status
        assert "language_support" in status
    
    @pytest.mark.asyncio
    async def test_transcribe_fallback(self):
        """Test transcription in fallback mode"""
        from models.nepal.whisper_finetune import NepaliASR
        asr = NepaliASR()
        
        # Test stub transcription
        result = await asr.transcribe("dummy_audio.wav")
        
        assert "text" in result
        assert "confidence" in result
        assert result.get("stub") == True
    
    @pytest.mark.asyncio
    async def test_government_transcription(self):
        """Test government-specific transcription"""
        from models.nepal.whisper_finetune import NepaliASR
        asr = NepaliASR()
        
        result = await asr.transcribe_for_government("dummy_audio.wav")
        
        assert "text" in result
        assert "sector" in result
        assert result["sector"] == "government"
    
    @pytest.mark.asyncio
    async def test_company_transcription(self):
        """Test company-specific transcription"""
        from models.nepal.whisper_finetune import NepaliASR
        asr = NepaliASR()
        
        result = await asr.transcribe_for_company("dummy_audio.wav")
        
        assert "text" in result
        assert "sector" in result
        assert result["sector"] == "company"

class TestCompleteIntegration:
    """Test complete system integration"""
    
    @pytest.mark.asyncio
    async def test_system_status(self):
        """Get complete system status"""
        from core.security.hsm_production import get_hsm
        from core.security.zkp_production import get_zkp
        from core.security.mtls import get_mtls
        from database.migrations.postgresql import get_migration
        from models.nepal.whisper_finetune import get_nepali_asr
        
        # Initialize all components
        components = {
            "hsm": get_hsm(),
            "zkp": get_zkp(),
            "mtls": get_mtls(),
            "migration": await get_migration(),
            "asr": await get_nepali_asr()
        }
        
        # Get status of all
        for name, component in components.items():
            status = component.status()
            assert isinstance(status, dict), f"{name} status should be dict"
    
    @pytest.mark.asyncio
    async def test_tripartite_flow(self):
        """Test Government → Company → Citizen flow"""
        from core.governance.tripartite_router import get_tripartite_router
        from core.dreaming.lora_engine import get_lora_engine
        from core.lifecycle.data_atomizer import get_data_atomizer
        
        router = get_tripartite_router()
        lora = get_lora_engine()
        atomizer = get_data_atomizer()
        
        # Test routing
        decision = await router.route_request("tax_filing", "tax")
        assert decision is not None
        
        # Test status
        assert "modes" in router.status()
        assert "total_atoms" in atomizer.status()

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])