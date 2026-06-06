
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Capability Matrix
Define complete capabilities and agent profiles
"""

from enum import Enum
from typing import Dict, List, Set, Any
from dataclasses import dataclass

class Capability(Enum):
    """Complete capability definitions"""
    
    # File capabilities
    FILE_READ_ONLY = "file.read_only"
    FILE_WRITE_SAFE = "file.write_safe"
    FILE_DELETE_SAFE = "file.delete_safe"
    FILE_SYSTEM_INFO = "file.system_info"
    FILE_BACKUP = "file.backup"
    
    # Process capabilities
    PROCESS_INSPECT = "process.inspect"
    PROCESS_MANAGE_LIMITED = "process.manage_limited"
    PROCESS_KILL_LIMITED = "process.kill_limited"
    
    # Network capabilities
    NETWORK_CHECK = "network.check"
    NETWORK_HTTP_LIMITED = "network.http_limited"
    NETWORK_HTTP_TRUSTED = "network.http_trusted"
    NETWORK_NONE = "network.none"
    
    # System capabilities
    SYSTEM_INFO = "system.info"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_REBOOT = "system.reboot"
    SYSTEM_UPDATE = "system.update"
    
    # Agent capabilities
    AGENT_CONTROL = "agent.control"
    AGENT_MONITOR = "agent.monitor"
    
    # Security capabilities
    SECURITY_AUDIT_READ = "security.audit_read"
    SECURITY_LOG_WRITE = "security.log_write"
    
    # Resource capabilities
    RESOURCE_MONITOR = "resource.monitor"
    RESOURCE_LIMIT = "resource.limit"
    
    # Clipboard capabilities
    CLIPBOARD_ACCESS = "clipboard.access"
    
    # Notification capabilities
    NOTIFICATION_SEND = "notification.send"

@dataclass
class AgentCapabilityProfile:
    """Agent capability profile"""
    agent_name: str
    allowed_capabilities: Set[Capability]
    denied_capabilities: Set[Capability]
    requires_human_confirmation: Set[Capability]
    max_risk_level: str  # low, medium, high, critical
    sandbox_required: Set[Capability]

class CapabilityMatrix:
    """Complete capability matrix for ASIMNEXUS"""
    
    def __init__(self):
        self.agent_profiles = self._define_agent_profiles()
        self.capability_descriptions = self._define_capability_descriptions()
        self.risk_levels = self._define_risk_levels()
    
    def _define_agent_profiles(self) -> Dict[str, AgentCapabilityProfile]:
        """Define capability profiles for all agents"""
        
        profiles = {}
        
        # BehaviorObserverAgent
        profiles["BehaviorObserverAgent"] = AgentCapabilityProfile(
            agent_name="BehaviorObserverAgent",
            allowed_capabilities={
                Capability.FILE_READ_ONLY,
                Capability.FILE_SYSTEM_INFO,
                Capability.PROCESS_INSPECT,
                Capability.SYSTEM_INFO,
                Capability.RESOURCE_MONITOR,
                Capability.AGENT_MONITOR
            },
            denied_capabilities={
                Capability.FILE_WRITE_SAFE,
                Capability.FILE_DELETE_SAFE,
                Capability.PROCESS_MANAGE_LIMITED,
                Capability.PROCESS_KILL_LIMITED,
                Capability.SYSTEM_SHUTDOWN,
                Capability.SYSTEM_REBOOT,
                Capability.AGENT_CONTROL
            },
            requires_human_confirmation=set(),
            max_risk_level="low",
            sandbox_required=set()
        )
        
        # EconomyAgent
        profiles["EconomyAgent"] = AgentCapabilityProfile(
            agent_name="EconomyAgent",
            allowed_capabilities={
                Capability.FILE_READ_ONLY,
                Capability.FILE_WRITE_SAFE,
                Capability.FILE_BACKUP,
                Capability.NETWORK_HTTP_LIMITED,
                Capability.NETWORK_HTTP_TRUSTED,
                Capability.SYSTEM_INFO,
                Capability.RESOURCE_MONITOR
            },
            denied_capabilities={
                Capability.FILE_DELETE_SAFE,
                Capability.PROCESS_MANAGE_LIMITED,
                Capability.PROCESS_KILL_LIMITED,
                Capability.SYSTEM_SHUTDOWN,
                Capability.SYSTEM_REBOOT,
                Capability.NETWORK_CHECK
            },
            requires_human_confirmation={
                Capability.NETWORK_HTTP_TRUSTED
            },
            max_risk_level="medium",
            sandbox_required={
                Capability.NETWORK_HTTP_TRUSTED
            }
        )
        
        # MeshRoutingAgent
        profiles["MeshRoutingAgent"] = AgentCapabilityProfile(
            agent_name="MeshRoutingAgent",
            allowed_capabilities={
                Capability.NETWORK_CHECK,
                Capability.NETWORK_HTTP_LIMITED,
                Capability.SYSTEM_INFO,
                Capability.RESOURCE_MONITOR,
                Capability.AGENT_CONTROL,
                Capability.AGENT_MONITOR
            },
            denied_capabilities={
                Capability.FILE_WRITE_SAFE,
                Capability.FILE_DELETE_SAFE,
                Capability.PROCESS_MANAGE_LIMITED,
                Capability.SYSTEM_SHUTDOWN,
                Capability.SYSTEM_REBOOT
            },
            requires_human_confirmation=set(),
            max_risk_level="medium",
            sandbox_required=set()
        )
        
        # AutoModeAgent
        profiles["AutoModeAgent"] = AgentCapabilityProfile(
            agent_name="AutoModeAgent",
            allowed_capabilities={
                Capability.SYSTEM_INFO,
                Capability.RESOURCE_MONITOR,
                Capability.AGENT_CONTROL,
                Capability.AGENT_MONITOR,
                Capability.SECURITY_AUDIT_READ,
                Capability.SECURITY_LOG_WRITE,
                Capability.FILE_WRITE_SAFE,
                Capability.FILE_BACKUP,
                Capability.CLIPBOARD_ACCESS,
                Capability.NOTIFICATION_SEND,
                Capability.FILE_READ_ONLY,
                Capability.FILE_SYSTEM_INFO,
                Capability.PROCESS_INSPECT,
                Capability.PROCESS_MANAGE_LIMITED,
                Capability.NETWORK_CHECK,
            },
            denied_capabilities={
                Capability.FILE_DELETE_SAFE,
                Capability.PROCESS_KILL_LIMITED,
                Capability.SYSTEM_SHUTDOWN,
                Capability.SYSTEM_REBOOT,
                Capability.NETWORK_HTTP_TRUSTED
            },
            requires_human_confirmation={
                Capability.SYSTEM_SHUTDOWN,
                Capability.SYSTEM_REBOOT,
                Capability.SYSTEM_UPDATE,
                Capability.CLIPBOARD_ACCESS,
                Capability.PROCESS_MANAGE_LIMITED,
            },
            max_risk_level="high",
            sandbox_required={
                Capability.SYSTEM_UPDATE,
                Capability.FILE_DELETE_SAFE,
            }
        )
        
        # JobOrchestrator
        profiles["JobOrchestrator"] = AgentCapabilityProfile(
            agent_name="JobOrchestrator",
            allowed_capabilities={
                Capability.AGENT_CONTROL,
                Capability.AGENT_MONITOR,
                Capability.SYSTEM_INFO,
                Capability.RESOURCE_MONITOR,
                Capability.FILE_WRITE_SAFE,
                Capability.FILE_BACKUP,
                Capability.PROCESS_MANAGE_LIMITED,
                Capability.NETWORK_CHECK
            },
            denied_capabilities={
                Capability.FILE_DELETE_SAFE,
                Capability.PROCESS_KILL_LIMITED,
                Capability.SYSTEM_SHUTDOWN,
                Capability.SYSTEM_REBOOT
            },
            requires_human_confirmation={
                Capability.SYSTEM_SHUTDOWN,
                Capability.SYSTEM_REBOOT,
                Capability.PROCESS_KILL_LIMITED
            },
            max_risk_level="high",
            sandbox_required={
                Capability.PROCESS_KILL_LIMITED,
                Capability.SYSTEM_SHUTDOWN,
                Capability.SYSTEM_REBOOT
            }
        )
        
        # MasterAgent
        profiles["MasterAgent"] = AgentCapabilityProfile(
            agent_name="MasterAgent",
            allowed_capabilities={
                # All capabilities except critical system operations
                Capability.FILE_READ_ONLY,
                Capability.FILE_WRITE_SAFE,
                Capability.FILE_DELETE_SAFE,
                Capability.FILE_SYSTEM_INFO,
                Capability.FILE_BACKUP,
                Capability.PROCESS_INSPECT,
                Capability.PROCESS_MANAGE_LIMITED,
                Capability.NETWORK_CHECK,
                Capability.NETWORK_HTTP_LIMITED,
                Capability.NETWORK_HTTP_TRUSTED,
                Capability.SYSTEM_INFO,
                Capability.AGENT_CONTROL,
                Capability.AGENT_MONITOR,
                Capability.SECURITY_AUDIT_READ,
                Capability.SECURITY_LOG_WRITE,
                Capability.RESOURCE_MONITOR,
                Capability.RESOURCE_LIMIT,
                Capability.CLIPBOARD_ACCESS,
                Capability.NOTIFICATION_SEND,
            },
            denied_capabilities={
                # Critical system operations always denied
                Capability.SYSTEM_SHUTDOWN,
                Capability.SYSTEM_REBOOT,
                Capability.SYSTEM_UPDATE
            },
            requires_human_confirmation={
                Capability.FILE_DELETE_SAFE,
                Capability.PROCESS_MANAGE_LIMITED,
                Capability.NETWORK_HTTP_TRUSTED,
                Capability.RESOURCE_LIMIT,
                Capability.CLIPBOARD_ACCESS,
            },
            max_risk_level="high",
            sandbox_required={
                Capability.FILE_DELETE_SAFE,
                Capability.PROCESS_MANAGE_LIMITED,
                Capability.NETWORK_HTTP_TRUSTED
            }
        )
        
        # ASIMCore (System)
        profiles["ASIMCore"] = AgentCapabilityProfile(
            agent_name="ASIMCore",
            allowed_capabilities=set(Capability),  # All capabilities
            denied_capabilities=set(),
            requires_human_confirmation={
                Capability.SYSTEM_SHUTDOWN,
                Capability.SYSTEM_REBOOT,
                Capability.SYSTEM_UPDATE,
                Capability.FILE_DELETE_SAFE
            },
            max_risk_level="critical",
            sandbox_required={
                Capability.SYSTEM_SHUTDOWN,
                Capability.SYSTEM_REBOOT,
                Capability.SYSTEM_UPDATE,
                Capability.FILE_DELETE_SAFE
            }
        )
        
        return profiles
    
    def _define_capability_descriptions(self) -> Dict[Capability, str]:
        """Define descriptions for all capabilities"""
        return {
            Capability.FILE_READ_ONLY: "Read files and directories (no modification)",
            Capability.FILE_WRITE_SAFE: "Write files with backup and validation",
            Capability.FILE_DELETE_SAFE: "Delete files with recycle bin/backup",
            Capability.FILE_SYSTEM_INFO: "Get file system information and statistics",
            Capability.FILE_BACKUP: "Create backups of files and directories",
            
            Capability.PROCESS_INSPECT: "View running processes and their information",
            Capability.PROCESS_MANAGE_LIMITED: "Manage non-critical processes",
            Capability.PROCESS_KILL_LIMITED: "Kill non-system processes",
            
            Capability.NETWORK_CHECK: "Check network connectivity and status",
            Capability.NETWORK_HTTP_LIMITED: "Make HTTP requests to trusted domains only",
            Capability.NETWORK_HTTP_TRUSTED: "Make HTTP requests to any domain",
            Capability.NETWORK_NONE: "No network access",
            
            Capability.SYSTEM_INFO: "Read system information and metrics",
            Capability.SYSTEM_SHUTDOWN: "Shutdown the system",
            Capability.SYSTEM_REBOOT: "Reboot the system",
            Capability.SYSTEM_UPDATE: "Update system software",
            
            Capability.AGENT_CONTROL: "Control and manage other agents",
            Capability.AGENT_MONITOR: "Monitor agent status and activities",
            
            Capability.SECURITY_AUDIT_READ: "Read security audit logs",
            Capability.SECURITY_LOG_WRITE: "Write to security logs",
            
            Capability.RESOURCE_MONITOR: "Monitor system resources (CPU, memory, disk)",
            Capability.RESOURCE_LIMIT: "Set limits on system resources",
            Capability.CLIPBOARD_ACCESS: "Read and write clipboard contents with consent",
            Capability.NOTIFICATION_SEND: "Send system notifications to the user"
        }
    
    def _define_risk_levels(self) -> Dict[str, Dict[str, Any]]:
        """Define risk levels and their implications"""
        return {
            "low": {
                "description": "Safe operations with minimal system impact",
                "requires_confirmation": False,
                "requires_sandbox": False,
                "audit_level": "basic"
            },
            "medium": {
                "description": "Operations with moderate risk or system impact",
                "requires_confirmation": False,
                "requires_sandbox": False,
                "audit_level": "detailed"
            },
            "high": {
                "description": "Operations with significant risk or system impact",
                "requires_confirmation": True,
                "requires_sandbox": True,
                "audit_level": "comprehensive"
            },
            "critical": {
                "description": "Operations that can severely impact system",
                "requires_confirmation": True,
                "requires_sandbox": True,
                "audit_level": "complete"
            }
        }
    
    def get_agent_profile(self, agent_name: str) -> AgentCapabilityProfile:
        """Get capability profile for an agent"""
        return self.agent_profiles.get(agent_name)
    
    def check_capability_allowed(self, agent_name: str, capability: Capability) -> tuple[bool, str]:
        """Check if agent is allowed to use a capability"""
        profile = self.get_agent_profile(agent_name)
        
        if not profile:
            return False, f"No capability profile found for agent: {agent_name}"
        
        # Check if capability is explicitly denied
        if capability in profile.denied_capabilities:
            return False, f"Capability {capability.value} is denied for {agent_name}"
        
        # Check if capability is allowed
        if capability not in profile.allowed_capabilities:
            return False, f"Capability {capability.value} not allowed for {agent_name}"
        
        return True, "Capability allowed"
    
    def requires_human_confirmation(self, agent_name: str, capability: Capability) -> bool:
        """Check if capability requires human confirmation"""
        profile = self.get_agent_profile(agent_name)
        if not profile:
            return True  # Default to requiring confirmation
        
        return capability in profile.requires_human_confirmation
    
    def requires_sandbox(self, agent_name: str, capability: Capability) -> bool:
        """Check if capability requires sandbox execution"""
        profile = self.get_agent_profile(agent_name)
        if not profile:
            return True  # Default to requiring sandbox
        
        return capability in profile.sandbox_required
    
    def get_agent_risk_level(self, agent_name: str) -> str:
        """Get maximum risk level for agent"""
        profile = self.get_agent_profile(agent_name)
        return profile.max_risk_level if profile else "critical"
    
    def get_capabilities_for_risk_level(self, risk_level: str) -> List[Capability]:
        """Get all capabilities allowed for a risk level"""
        risk_config = self.risk_levels.get(risk_level, {})
        
        # This is simplified - in practice, would be more sophisticated
        if risk_level == "low":
            return [
                Capability.FILE_READ_ONLY,
                Capability.FILE_SYSTEM_INFO,
                Capability.PROCESS_INSPECT,
                Capability.NETWORK_CHECK,
                Capability.SYSTEM_INFO,
                Capability.AGENT_MONITOR,
                Capability.RESOURCE_MONITOR
            ]
        elif risk_level == "medium":
            low_caps = self.get_capabilities_for_risk_level("low")
            return low_caps + [
                Capability.FILE_WRITE_SAFE,
                Capability.FILE_BACKUP,
                Capability.PROCESS_MANAGE_LIMITED,
                Capability.NETWORK_HTTP_LIMITED,
                Capability.AGENT_CONTROL
            ]
        elif risk_level == "high":
            medium_caps = self.get_capabilities_for_risk_level("medium")
            return medium_caps + [
                Capability.FILE_DELETE_SAFE,
                Capability.PROCESS_KILL_LIMITED,
                Capability.NETWORK_HTTP_TRUSTED,
                Capability.SECURITY_AUDIT_READ,
                Capability.SECURITY_LOG_WRITE,
                Capability.RESOURCE_LIMIT
            ]
        else:  # critical
            return list(Capability)
    
    def validate_agent_capabilities(self, agent_name: str, requested_capabilities: List[Capability]) -> tuple[bool, List[str]]:
        """Validate if agent can request all capabilities"""
        issues = []
        
        profile = self.get_agent_profile(agent_name)
        if not profile:
            return False, ["No capability profile found"]
        
        for cap in requested_capabilities:
            allowed, reason = self.check_capability_allowed(agent_name, cap)
            if not allowed:
                issues.append(reason)
        
        return len(issues) == 0, issues
    
    def get_capability_summary(self) -> Dict[str, Any]:
        """Get summary of capability matrix"""
        return {
            "total_capabilities": len(Capability),
            "total_agents": len(self.agent_profiles),
            "risk_levels": list(self.risk_levels.keys()),
            "agent_profiles": {
                name: {
                    "allowed_capabilities": len(profile.allowed_capabilities),
                    "denied_capabilities": len(profile.denied_capabilities),
                    "requires_confirmation": len(profile.requires_human_confirmation),
                    "requires_sandbox": len(profile.sandbox_required),
                    "max_risk_level": profile.max_risk_level
                }
                for name, profile in self.agent_profiles.items()
            }
        }

# Global capability matrix instance
capability_matrix = CapabilityMatrix()
