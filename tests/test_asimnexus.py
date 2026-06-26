"""AsimNexus Testing Suite"""
import pytest
import asyncio

class TestAsimNexusTools:
    @pytest.mark.asyncio
    async def test_email_tool(self):
        from tools.api_tools.email_tool import email_tool
        result = await email_tool.send({"to": "test@test.com"})
        assert result["success"] == True
    
    @pytest.mark.asyncio  
    async def test_money_tool(self):
        from tools.api_tools.money_tool import money_tool
        result = await money_tool.get_price({"symbol": "AAPL"})
        assert result["success"] == True

class TestRiskManagement:
    def test_imports(self):
        from risk_management import HallucinationDetector, OverAutomationGuard
        assert HallucinationDetector is not None
        assert OverAutomationGuard is not None
