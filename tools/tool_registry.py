"""AsimNexus Tools Registry Integration"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from typing import Dict, Any
from .api_tools import email_tool, notification_tool, money_tool, internet_tool, database_tool
from .ai_tools import dall_e_tool, perplexity_tool, quantum_tool, security_tool
from .device_tools import iot_tool, isaac_tool, home_assistant_tool
from .file_tools import file_read_tool, file_edit_tool, file_delete_tool

# Import OS Control Tools
try:
    from importlib import import_module
    os_module = import_module("os_control.tool_registry")
    tool_registry = getattr(os_module, "tool_registry", None)
    OS_TOOLS_AVAILABLE = tool_registry is not None
except ImportError:
    tool_registry = None
    OS_TOOLS_AVAILABLE = False

NEW_TOOLS = {
    "tool.email.send": email_tool,
    "tool.email.read": email_tool,
    "tool.notification.send": notification_tool,
    "tool.money.price": money_tool,
    "tool.money.convert": money_tool,
    "tool.internet.fetch": internet_tool,
    "tool.internet.search": internet_tool,
    "tool.database.query": database_tool,
    "tool.database.execute": database_tool,
    "tool.ai.dall_e": dall_e_tool,
    "tool.ai.perplexity": perplexity_tool,
    "tool.ai.quantum": quantum_tool,
    "tool.ai.security": security_tool,
    "tool.robot.iot": iot_tool,
    "tool.robot.isaac": isaac_tool,
    "tool.robot.homeassistant": home_assistant_tool,
    "tool.file.read": file_read_tool,
    "tool.file.write": file_edit_tool,
    "tool.file.delete": file_delete_tool,
}

def register_new_tools():
    """Register new AsimNexus tools in OS Control registry."""
    if tool_registry and OS_TOOLS_AVAILABLE:
        from os_control.tool_registry import ToolRegistration, RiskLevel, Capability
        
        registrations = [
            (ToolRegistration(tool_id="tool.email.send", description="Send email", risk_level=RiskLevel.MEDIUM,
                required_capabilities={Capability.NETWORK_ACCESS}, handler=email_tool.send)),
            (ToolRegistration(tool_id="tool.email.read", description="Read emails", risk_level=RiskLevel.MEDIUM,
                required_capabilities={Capability.NETWORK_ACCESS}, handler=email_tool.read)),
            (ToolRegistration(tool_id="tool.notification.send", description="Send notification", risk_level=RiskLevel.LOW,
                required_capabilities={Capability.NOTIFICATION_SEND}, handler=notification_tool.send)),
            (ToolRegistration(tool_id="tool.money.price", description="Get stock price", risk_level=RiskLevel.LOW,
                required_capabilities={Capability.NETWORK_ACCESS}, handler=money_tool.get_price)),
            (ToolRegistration(tool_id="tool.money.convert", description="Currency convert", risk_level=RiskLevel.LOW,
                required_capabilities={Capability.NETWORK_ACCESS}, handler=money_tool.convert_currency)),
            (ToolRegistration(tool_id="tool.internet.fetch", description="Fetch web content", risk_level=RiskLevel.LOW,
                required_capabilities={Capability.NETWORK_ACCESS}, handler=internet_tool.fetch)),
            (ToolRegistration(tool_id="tool.internet.search", description="Web search", risk_level=RiskLevel.LOW,
                required_capabilities={Capability.NETWORK_ACCESS}, handler=internet_tool.search)),
            (ToolRegistration(tool_id="tool.database.query", description="DB query", risk_level=RiskLevel.MEDIUM,
                required_capabilities={Capability.DATABASE_ACCESS}, handler=database_tool.query)),
            (ToolRegistration(tool_id="tool.database.execute", description="DB execute", risk_level=RiskLevel.HIGH,
                required_capabilities={Capability.DATABASE_ACCESS}, handler=database_tool.execute)),
            (ToolRegistration(tool_id="tool.ai.dall_e", description="Generate images", risk_level=RiskLevel.MEDIUM,
                required_capabilities={Capability.AI_GENERATION}, handler=dall_e_tool.generate)),
            (ToolRegistration(tool_id="tool.ai.perplexity", description="Perplexity search", risk_level=RiskLevel.LOW,
                required_capabilities={Capability.NETWORK_ACCESS}, handler=perplexity_tool.search)),
            (ToolRegistration(tool_id="tool.ai.quantum", description="Quantum computing", risk_level=RiskLevel.MEDIUM,
                required_capabilities={Capability.AI_COMPUTE}, handler=quantum_tool.run_circuit)),
            (ToolRegistration(tool_id="tool.ai.security", description="Security scan", risk_level=RiskLevel.MEDIUM,
                required_capabilities={Capability.SYSTEM_INFO}, handler=security_tool.scan)),
            (ToolRegistration(tool_id="tool.robot.iot", description="IoT control", risk_level=RiskLevel.MEDIUM,
                required_capabilities={Capability.NETWORK_ACCESS}, handler=iot_tool.control_device)),
            (ToolRegistration(tool_id="tool.robot.isaac", description="NVIDIA Isaac control", risk_level=RiskLevel.MEDIUM,
                required_capabilities={Capability.ROBOTICS_CONTROL}, handler=isaac_tool.run_simulation)),
            (ToolRegistration(tool_id="tool.robot.homeassistant", description="Home Assistant control", risk_level=RiskLevel.MEDIUM,
                required_capabilities={Capability.NETWORK_ACCESS}, handler=home_assistant_tool.control_entity)),
            (ToolRegistration(tool_id="tool.file.read", description="Read file", risk_level=RiskLevel.LOW,
                required_capabilities={Capability.FILE_READ_ONLY}, handler=file_read_tool.read)),
            (ToolRegistration(tool_id="tool.file.write", description="Write file", risk_level=RiskLevel.MEDIUM,
                required_capabilities={Capability.FILE_WRITE_SAFE}, handler=file_edit_tool.write)),
            (ToolRegistration(tool_id="tool.file.delete", description="Delete file", risk_level=RiskLevel.HIGH,
                required_capabilities={Capability.FILE_DELETE_SAFE}, handler=file_delete_tool.delete)),
        ]
        
        for reg in registrations:
            tool_registry.register_tool(reg)
        return True
    return False

__all__ = ["NEW_TOOLS", "register_new_tools", "OS_TOOLS_AVAILABLE", "tool_registry"]