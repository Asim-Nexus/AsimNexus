"""
STATUS: REAL — Integration tests for tripartite system (Gov/Company/User)

AsimNexus Tripartite Integration Tests
======================================
Tests integration between:
- Government API (51%)
- Company API (49%)
- Citizen API (Local-First)
"""

import pytest
import asyncio
from pathlib import Path

# Test fixtures
@pytest.fixture
def gov_api():
    """Government API fixture"""
    try:
        from core.nepal.tax_llm import get_tax_llm
        return get_tax_llm()
    except ImportError:
        return None

@pytest.fixture
def company_api():
    """Company API fixture"""
    try:
        from core.economy.job_marketplace import marketplace
        return marketplace
    except ImportError:
        return None

@pytest.fixture
def citizen_api():
    """Citizen API fixture"""
    try:
        from core.identity.digital_twin import get_digital_twin
        return get_digital_twin("test_user")
    except ImportError:
        return None

# Government tests
def test_gov_tax_calculation(gov_api):
    """Test tax calculation for Nepal"""
    if gov_api is None:
        pytest.skip("Tax LLM not available")
    
    result = gov_api.calculate_income_tax(1500000, {"medical": 100000})
    
    assert result.taxable_income > 0
    assert result.tax_amount > 0
    assert result.effective_rate > 0

def test_gov_tax_vat():
    """Test VAT calculation"""
    try:
        from core.nepal.tax_llm import get_tax_llm
        tax = get_tax_llm()
        vat = tax.calculate_vat(1000, "standard")
        assert vat == 130  # 13% of 1000
    except ImportError:
        pytest.skip("Tax LLM not available")

# Company tests
def test_company_payment():
    """Test company payment processing"""
    try:
        from core.nepal.banking_integrations import process_payment
        result = process_payment("esewa", 1000, "NPR")
        assert result.get("success") == True
    except ImportError:
        pytest.skip("Banking integration not available")

# Citizen tests
def test_citizen_twin_creation():
    """Test digital twin creation"""
    try:
        from core.identity.digital_twin import DigitalTwin
        twin = DigitalTwin("test_citizen")
        status = twin.status()
        assert "user_id" in status
    except ImportError:
        pytest.skip("Digital Twin not available")

# Cross-module tests
def test_cross_module_routing():
    """Test tripartite router"""
    try:
        from core.governance.tripartite_router import get_tripartite_router, OperationMode
        router = get_tripartite_router()
        
        decision = asyncio.run(router.route_request("tax_calculation", "tax"))
        assert decision.mode in OperationMode
    except ImportError:
        pytest.skip("Tripartite router not available")

def test_lora_engine_integration():
    """Test LoRA engine"""
    try:
        from core.dreaming.lora_engine import get_lora_engine, LoRAConfig
        engine = get_lora_engine()
        
        # Create test adapter
        config = LoRAConfig()
        path = asyncio.run(engine.create_adapter_from_dreams(
            "test",
            [{"topic": "tax", "summary": "test lesson"}],
            config
        ))
        assert path.endswith(".bin")
    except ImportError:
        pytest.skip("LoRA engine not available")

def test_sms_gateway():
    """Test SMS gateway"""
    try:
        from mesh.sms_gateway import get_sms_gateway
        gateway = get_sms_gateway()
        
        status = gateway.status()
        assert "operators" in status
        assert "NTC" in status["operators"]
    except ImportError:
        pytest.skip("SMS gateway not available")

def test_control_panel():
    """Test user control panel"""
    try:
        from core.control_panel import get_control_panel
        panel = get_control_panel()
        
        # Test mode setting
        result = panel.set_active_mode("test_user", "public")
        assert result["mode"] == "public"
        
        # Test world getting
        world = panel.get_user_world("test_user")
        assert "active_mode" in world
    except ImportError:
        pytest.skip("Control panel not available")

def test_data_atomizer():
    """Test data atomizer"""
    try:
        from core.lifecycle.data_atomizer import get_data_atomizer
        atomizer = get_data_atomizer()
        
        # Create test atoms
        atoms = asyncio.run(atomizer.atomize_user_data(
            "test_user",
            {"work": {"job": "developer", "salary": 100000}}
        ))
        assert len(atoms) > 0
    except ImportError:
        pytest.skip("Data atomizer not available")

# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])