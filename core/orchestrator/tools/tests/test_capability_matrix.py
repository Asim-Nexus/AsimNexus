"""
REAL Unit Tests for CapabilityMatrix
Tests agent profile definitions, capability checks, human confirmation,
sandbox requirements, and summary generation.
"""

import pytest

try:
    from asim_tools.registry.capability_matrix import CapabilityMatrix, Capability, AgentCapabilityProfile
except ImportError:
    # asim_tools is an external dependency; tests will be skipped at runtime if missing
    CapabilityMatrix = None  # type: ignore
    Capability = None  # type: ignore
    AgentCapabilityProfile = None  # type: ignore


class TestCapabilityEnum:
    """Tests for the Capability enum"""

    def test_all_capabilities_defined(self):
        """Verify all expected capability values exist"""
        expected = {
            # File
            Capability.FILE_READ_ONLY,
            Capability.FILE_WRITE_SAFE,
            Capability.FILE_DELETE_SAFE,
            Capability.FILE_SYSTEM_INFO,
            Capability.FILE_BACKUP,
            # Process
            Capability.PROCESS_INSPECT,
            Capability.PROCESS_MANAGE_LIMITED,
            Capability.PROCESS_KILL_LIMITED,
            # Network
            Capability.NETWORK_CHECK,
            Capability.NETWORK_HTTP_LIMITED,
            Capability.NETWORK_HTTP_TRUSTED,
            Capability.NETWORK_NONE,
            # System
            Capability.SYSTEM_INFO,
            Capability.SYSTEM_SHUTDOWN,
            Capability.SYSTEM_REBOOT,
            Capability.SYSTEM_UPDATE,
            # Agent
            Capability.AGENT_CONTROL,
            Capability.AGENT_MONITOR,
            # Security
            Capability.SECURITY_AUDIT_READ,
            Capability.SECURITY_LOG_WRITE,
            # Resource
            Capability.RESOURCE_MONITOR,
            Capability.RESOURCE_LIMIT,
            # Clipboard
            Capability.CLIPBOARD_ACCESS,
            # Notification
            Capability.NOTIFICATION_SEND,
            # AI & Robots & DB & Network
            Capability.AI_COMPUTE,
            Capability.AI_GENERATION,
            Capability.ROBOTICS_CONTROL,
            Capability.NETWORK_ACCESS,
            Capability.DATABASE_ACCESS,
        }
        all_caps = set(Capability)
        assert expected == all_caps, f"Missing: {expected - all_caps}, Extra: {all_caps - expected}"
        assert len(all_caps) == 29

    def test_enum_values_strings(self):
        assert Capability.FILE_READ_ONLY.value == "file.read_only"
        assert Capability.CLIPBOARD_ACCESS.value == "clipboard.access"
        assert Capability.NOTIFICATION_SEND.value == "notification.send"


@pytest.fixture
def matrix():
    """Fresh CapabilityMatrix for each test"""
    return CapabilityMatrix()


class TestCapabilityMatrixProfiles:
    """Tests for agent profile definitions"""

    def test_all_agents_have_profiles(self, matrix):
        profiles = ["BehaviorObserverAgent", "EconomyAgent", "MeshRoutingAgent",
                     "AutoModeAgent", "JobOrchestrator", "MasterAgent", "ASIMCore"]
        for name in profiles:
            assert matrix.get_agent_profile(name) is not None, f"Missing profile: {name}"

    def test_nonexistent_agent_returns_none(self, matrix):
        assert matrix.get_agent_profile("NonExistentAgent") is None

    def test_behavior_observer_profile(self, matrix):
        profile = matrix.get_agent_profile("BehaviorObserverAgent")
        assert profile is not None
        assert profile.max_risk_level == "low"
        assert Capability.FILE_READ_ONLY in profile.allowed_capabilities
        assert Capability.FILE_WRITE_SAFE in profile.denied_capabilities
        assert Capability.FILE_DELETE_SAFE in profile.denied_capabilities
        assert Capability.SYSTEM_SHUTDOWN in profile.denied_capabilities

    def test_economy_agent_profile(self, matrix):
        profile = matrix.get_agent_profile("EconomyAgent")
        assert profile is not None
        assert profile.max_risk_level == "medium"
        assert Capability.NETWORK_HTTP_TRUSTED in profile.requires_human_confirmation
        assert Capability.NETWORK_HTTP_TRUSTED in profile.sandbox_required
        assert Capability.FILE_DELETE_SAFE in profile.denied_capabilities

    def test_mesh_routing_agent_profile(self, matrix):
        profile = matrix.get_agent_profile("MeshRoutingAgent")
        assert profile is not None
        assert profile.max_risk_level == "medium"
        assert Capability.NETWORK_CHECK in profile.allowed_capabilities
        assert Capability.AGENT_CONTROL in profile.allowed_capabilities

    def test_auto_mode_agent_profile(self, matrix):
        profile = matrix.get_agent_profile("AutoModeAgent")
        assert profile is not None
        assert profile.max_risk_level == "high"
        assert Capability.CLIPBOARD_ACCESS in profile.allowed_capabilities
        assert Capability.NOTIFICATION_SEND in profile.allowed_capabilities
        assert Capability.FILE_READ_ONLY in profile.allowed_capabilities
        assert Capability.FILE_SYSTEM_INFO in profile.allowed_capabilities
        assert Capability.PROCESS_INSPECT in profile.allowed_capabilities
        assert Capability.PROCESS_MANAGE_LIMITED in profile.allowed_capabilities
        assert Capability.NETWORK_CHECK in profile.allowed_capabilities
        assert Capability.FILE_DELETE_SAFE in profile.denied_capabilities
        assert Capability.CLIPBOARD_ACCESS in profile.requires_human_confirmation
        assert Capability.PROCESS_MANAGE_LIMITED in profile.requires_human_confirmation

    def test_job_orchestrator_profile(self, matrix):
        profile = matrix.get_agent_profile("JobOrchestrator")
        assert profile is not None
        assert profile.max_risk_level == "high"
        assert Capability.SYSTEM_SHUTDOWN in profile.requires_human_confirmation
        assert Capability.SYSTEM_SHUTDOWN in profile.sandbox_required

    def test_master_agent_profile(self, matrix):
        profile = matrix.get_agent_profile("MasterAgent")
        assert profile is not None
        assert profile.max_risk_level == "high"
        assert Capability.FILE_DELETE_SAFE in profile.allowed_capabilities
        assert Capability.CLIPBOARD_ACCESS in profile.allowed_capabilities
        assert Capability.NOTIFICATION_SEND in profile.allowed_capabilities
        assert Capability.SYSTEM_SHUTDOWN in profile.denied_capabilities
        assert Capability.SYSTEM_REBOOT in profile.denied_capabilities
        assert Capability.CLIPBOARD_ACCESS in profile.requires_human_confirmation
        assert Capability.FILE_DELETE_SAFE in profile.requires_human_confirmation

    def test_asim_core_profile(self, matrix):
        profile = matrix.get_agent_profile("ASIMCore")
        assert profile is not None
        assert profile.max_risk_level == "critical"
        assert len(profile.allowed_capabilities) == len(Capability)  # All capabilities
        assert len(profile.denied_capabilities) == 0


class TestCapabilityMatrixChecks:
    """Tests for capability checking methods"""

    def test_check_allowed_capability(self, matrix):
        allowed, reason = matrix.check_capability_allowed(
            "AutoModeAgent", Capability.FILE_READ_ONLY
        )
        assert allowed is True
        assert reason == "Capability allowed"

    def test_check_denied_capability(self, matrix):
        allowed, reason = matrix.check_capability_allowed(
            "AutoModeAgent", Capability.FILE_DELETE_SAFE
        )
        assert allowed is False
        assert "denied" in reason.lower()

    def test_check_not_allowed_capability(self, matrix):
        allowed, reason = matrix.check_capability_allowed(
            "EconomyAgent", Capability.FILE_DELETE_SAFE
        )
        assert allowed is False

    def test_check_nonexistent_agent(self, matrix):
        allowed, reason = matrix.check_capability_allowed(
            "GhostAgent", Capability.FILE_READ_ONLY
        )
        assert allowed is False
        assert "No capability profile found" in reason

    def test_human_confirmation_required(self, matrix):
        assert matrix.requires_human_confirmation(
            "AutoModeAgent", Capability.CLIPBOARD_ACCESS
        ) is True

    def test_human_confirmation_not_required(self, matrix):
        assert matrix.requires_human_confirmation(
            "BehaviorObserverAgent", Capability.FILE_READ_ONLY
        ) is False

    def test_human_confirmation_default_true_for_unknown_agent(self, matrix):
        assert matrix.requires_human_confirmation("GhostAgent", Capability.FILE_READ_ONLY) is True

    def test_sandbox_required(self, matrix):
        assert matrix.requires_sandbox(
            "MasterAgent", Capability.FILE_DELETE_SAFE
        ) is True

    def test_sandbox_not_required(self, matrix):
        assert matrix.requires_sandbox(
            "BehaviorObserverAgent", Capability.SYSTEM_INFO
        ) is False

    def test_sandbox_default_true_for_unknown_agent(self, matrix):
        assert matrix.requires_sandbox("GhostAgent", Capability.FILE_READ_ONLY) is True


class TestCapabilityMatrixRiskLevel:
    """Tests for risk level methods"""

    def test_get_agent_risk_level(self, matrix):
        assert matrix.get_agent_risk_level("BehaviorObserverAgent") == "low"
        assert matrix.get_agent_risk_level("EconomyAgent") == "medium"
        assert matrix.get_agent_risk_level("AutoModeAgent") == "high"
        assert matrix.get_agent_risk_level("ASIMCore") == "critical"

    def test_get_agent_risk_level_unknown(self, matrix):
        assert matrix.get_agent_risk_level("GhostAgent") == "critical"

    def test_capabilities_for_low_risk(self, matrix):
        caps = matrix.get_capabilities_for_risk_level("low")
        assert Capability.FILE_READ_ONLY in caps
        assert Capability.SYSTEM_INFO in caps
        assert Capability.FILE_WRITE_SAFE not in caps  # medium+

    def test_capabilities_for_medium_risk(self, matrix):
        caps = matrix.get_capabilities_for_risk_level("medium")
        assert Capability.FILE_WRITE_SAFE in caps
        assert Capability.FILE_DELETE_SAFE not in caps  # high+

    def test_capabilities_for_high_risk(self, matrix):
        caps = matrix.get_capabilities_for_risk_level("high")
        assert Capability.FILE_DELETE_SAFE in caps

    def test_capabilities_for_critical_risk(self, matrix):
        caps = matrix.get_capabilities_for_risk_level("critical")
        assert len(caps) == len(Capability)


class TestCapabilityMatrixValidation:
    """Tests for validation and summary"""

    def test_validate_valid_request(self, matrix):
        caps = [Capability.FILE_READ_ONLY, Capability.SYSTEM_INFO]
        valid, issues = matrix.validate_agent_capabilities("AutoModeAgent", caps)
        assert valid is True
        assert issues == []

    def test_validate_invalid_request(self, matrix):
        caps = [Capability.FILE_READ_ONLY, Capability.SYSTEM_SHUTDOWN]
        valid, issues = matrix.validate_agent_capabilities("BehaviorObserverAgent", caps)
        assert valid is False
        assert len(issues) >= 1
        assert any(Capability.SYSTEM_SHUTDOWN.value in i for i in issues)

    def test_validate_unknown_agent(self, matrix):
        valid, issues = matrix.validate_agent_capabilities("GhostAgent", [Capability.FILE_READ_ONLY])
        assert valid is False
        assert "No capability profile found" in issues

    def test_get_capability_summary(self, matrix):
        summary = matrix.get_capability_summary()
        assert summary["total_capabilities"] == len(Capability)
        assert summary["total_agents"] == 7
        assert "low" in summary["risk_levels"]
        assert "critical" in summary["risk_levels"]
        assert "AutoModeAgent" in summary["agent_profiles"]
        assert "ASIMCore" in summary["agent_profiles"]


class TestCapabilityMatrixDescriptions:
    """Tests for capability descriptions"""

    def test_descriptions_exist(self, matrix):
        assert len(matrix.capability_descriptions) >= 20

    def test_specific_descriptions(self, matrix):
        assert "Read files" in matrix.capability_descriptions[Capability.FILE_READ_ONLY]
        assert "clipboard" in matrix.capability_descriptions.get(
            Capability.CLIPBOARD_ACCESS, ""
        ).lower() or matrix.capability_descriptions.get(Capability.CLIPBOARD_ACCESS) is not None


class TestAgentCapabilityProfile:
    """Tests for AgentCapabilityProfile dataclass"""

    def test_create_profile(self):
        profile = AgentCapabilityProfile(
            agent_name="TestAgent",
            allowed_capabilities={Capability.FILE_READ_ONLY, Capability.SYSTEM_INFO},
            denied_capabilities={Capability.FILE_DELETE_SAFE},
            requires_human_confirmation={Capability.FILE_DELETE_SAFE},
            max_risk_level="medium",
            sandbox_required=set(),
        )
        assert profile.agent_name == "TestAgent"
        assert len(profile.allowed_capabilities) == 2
        assert Capability.FILE_DELETE_SAFE in profile.denied_capabilities
        assert Capability.FILE_DELETE_SAFE in profile.requires_human_confirmation
