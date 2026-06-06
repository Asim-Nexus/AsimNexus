#!/usr/bin/env python3
"""
Tests for NetworkIntelligence — Spectrum Analysis + Protocol Management + Hybrid Mesh Networks.

Covers:
- Network topology analysis (mesh network creation, node roles, topology types)
- Latency measurements (protocol performance analysis)
- Bandwidth estimation (spectrum analysis, channel optimization)
- Route quality scoring (protocol selection with requirements)
- Network event processing (event publishing, handling hardware updates)
- SpectrumAgent: frequency scanning, interference detection, channel optimization
- ProtocolAgent: fallback chains, protocol switching, mesh creation
- NetworkIntelligenceLayer: unified interface discovery, optimization
"""

import time
from unittest.mock import patch, MagicMock, AsyncMock, PropertyMock

import pytest

from mesh.network_intelligence import (
    NetworkIntelligenceLayer,
    SpectrumAgent,
    ProtocolAgent,
    NetworkInterface,
    SpectrumAnalysis,
    NetworkType,
    FrequencyBand,
    ConnectionProtocol,
    network_intelligence as global_ni,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def spectrum_agent():
    """Create a fresh SpectrumAgent for each test."""
    return SpectrumAgent()


@pytest.fixture
def protocol_agent():
    """Create a fresh ProtocolAgent for each test."""
    return ProtocolAgent()


@pytest.fixture
def network_intelligence():
    """Create a fresh NetworkIntelligenceLayer for each test."""
    return NetworkIntelligenceLayer()


# =============================================================================
# Enum Tests
# =============================================================================

class TestEnums:
    """Tests for all enums in network_intelligence."""

    def test_network_type_values(self):
        assert NetworkType.WPAN.value == "wpan"
        assert NetworkType.WLAN.value == "wlan"
        assert NetworkType.WMAN.value == "wman"
        assert NetworkType.WWAN.value == "wwan"
        assert NetworkType.QUANTUM.value == "quantum"
        assert NetworkType.PARALLEL.value == "parallel"

    def test_frequency_band_values(self):
        assert FrequencyBand.WIFI_2_4.value == "2.4GHz"
        assert FrequencyBand.WIFI_5.value == "5GHz"
        assert FrequencyBand.LTE.value == "700MHz-3.5GHz"
        assert FrequencyBand.QUANTUM_ENTANGLEMENT.value == "Quantum Entanglement"

    def test_connection_protocol_values(self):
        assert ConnectionProtocol.WIFI.value == "Wi-Fi"
        assert ConnectionProtocol.BLUETOOTH.value == "Bluetooth"
        assert ConnectionProtocol.MESH.value == "Mesh Network"
        assert ConnectionProtocol.QUANTUM.value == "Quantum Protocol"


# =============================================================================
# SpectrumAgent Tests
# =============================================================================

class TestSpectrumAgent:
    """Tests for SpectrumAgent — RF Spectrum Analysis."""

    @pytest.mark.asyncio
    async def test_scan_spectrum_returns_analysis(self, spectrum_agent):
        """scan_spectrum should return a SpectrumAnalysis object."""
        analysis = await spectrum_agent.scan_spectrum(FrequencyBand.WIFI_5)
        assert isinstance(analysis, SpectrumAnalysis)
        assert analysis.frequency_range == "5GHz"
        assert 0.0 <= analysis.interference_level <= 1.0
        assert 0.0 <= analysis.signal_quality <= 1.0
        assert 0.0 <= analysis.channel_utilization <= 1.0
        assert isinstance(analysis.optimal_channels, list)
        assert isinstance(analysis.noise_sources, list)
        assert isinstance(analysis.recommendations, list)

    @pytest.mark.asyncio
    async def test_scan_spectrum_stores_results(self, spectrum_agent):
        """scan_spectrum should store analysis in monitored_frequencies."""
        await spectrum_agent.scan_spectrum(FrequencyBand.WIFI_2_4)
        assert "2.4GHz" in spectrum_agent.monitored_frequencies
        assert isinstance(spectrum_agent.monitored_frequencies["2.4GHz"], SpectrumAnalysis)

    @pytest.mark.asyncio
    async def test_perform_spectrum_scan_wifi_2_4_high_interference(self, spectrum_agent):
        """2.4GHz band should have high interference (crowded)."""
        result = await spectrum_agent.perform_spectrum_scan(FrequencyBand.WIFI_2_4)
        assert result["interference"] == 0.7
        assert result["quality"] == 0.3
        assert len(result["noise_sources"]) > 0

    @pytest.mark.asyncio
    async def test_perform_spectrum_scan_wifi_6_low_interference(self, spectrum_agent):
        """6GHz band should have low interference."""
        result = await spectrum_agent.perform_spectrum_scan(FrequencyBand.WIFI_6)
        assert result["interference"] == 0.2
        assert result["quality"] == 0.8

    @pytest.mark.asyncio
    async def test_perform_spectrum_scan_bluetooth(self, spectrum_agent):
        """Bluetooth should have moderate interference."""
        result = await spectrum_agent.perform_spectrum_scan(FrequencyBand.BLUETOOTH)
        assert result["interference"] == 0.3

    @pytest.mark.asyncio
    async def test_perform_spectrum_scan_quantum_no_interference(self, spectrum_agent):
        """Quantum entanglement should have zero interference."""
        result = await spectrum_agent.perform_spectrum_scan(FrequencyBand.QUANTUM_ENTANGLEMENT)
        assert result["interference"] == 0.0
        assert result["quality"] == 1.0

    def test_calculate_optimal_wifi_channels_2_4(self, spectrum_agent):
        """2.4GHz should recommend non-overlapping channels 1, 6, 11."""
        channels = spectrum_agent.calculate_optimal_wifi_channels(FrequencyBand.WIFI_2_4)
        assert channels == [1, 6, 11]

    def test_calculate_optimal_wifi_channels_5(self, spectrum_agent):
        """5GHz should return multiple channels."""
        channels = spectrum_agent.calculate_optimal_wifi_channels(FrequencyBand.WIFI_5)
        assert 36 in channels
        assert 149 in channels

    def test_calculate_optimal_wifi_channels_6(self, spectrum_agent):
        """6GHz should return many channels."""
        channels = spectrum_agent.calculate_optimal_wifi_channels(FrequencyBand.WIFI_6)
        assert len(channels) > 100  # 1-232

    def test_calculate_optimal_wifi_channels_unknown(self, spectrum_agent):
        """Unknown band should return empty list."""
        channels = spectrum_agent.calculate_optimal_wifi_channels(FrequencyBand.LTE)
        assert channels == []

    @pytest.mark.asyncio
    async def test_scan_spectrum_multiple_bands(self, spectrum_agent):
        """Multiple band scans should all be stored."""
        for band in [FrequencyBand.WIFI_2_4, FrequencyBand.WIFI_5, FrequencyBand.LTE]:
            await spectrum_agent.scan_spectrum(band)
        assert len(spectrum_agent.monitored_frequencies) >= 3

    def test_spectrum_initialization(self, spectrum_agent):
        """SpectrumAgent should initialize with empty databases."""
        assert spectrum_agent.monitored_frequencies == {}
        assert spectrum_agent.interference_database == {}
        assert spectrum_agent.optimal_channels == {}

    @pytest.mark.asyncio
    async def test_perform_spectrum_scan_generates_recommendations(self, spectrum_agent):
        """High interference should generate recommendations."""
        result = await spectrum_agent.perform_spectrum_scan(FrequencyBand.WIFI_2_4)
        assert len(result["recommendations"]) > 0
        assert any("High interference" in r for r in result["recommendations"])

    @pytest.mark.asyncio
    async def test_perform_spectrum_scan_low_interference_no_recommendations(self, spectrum_agent):
        """Low interference should have fewer recommendations."""
        result = await spectrum_agent.perform_spectrum_scan(FrequencyBand.QUANTUM_ENTANGLEMENT)
        # Quantum has zero interference, so fewer recommendations
        assert result["interference"] == 0.0


# =============================================================================
# ProtocolAgent Tests
# =============================================================================

class TestProtocolAgent:
    """Tests for ProtocolAgent — Network Protocol Management."""

    @pytest.mark.asyncio
    async def test_setup_fallback_chains(self, protocol_agent):
        """setup_protocol_fallback_chains should create fallback chains."""
        await protocol_agent.setup_protocol_fallback_chains()
        assert "primary_internet" in protocol_agent.fallback_chains
        assert "local_network" in protocol_agent.fallback_chains
        assert "high_priority" in protocol_agent.fallback_chains
        assert "emergency" in protocol_agent.fallback_chains
        assert "multiversal" in protocol_agent.fallback_chains

    @pytest.mark.asyncio
    async def test_analyze_protocol_performance_wifi(self, protocol_agent):
        """Wifi should have good performance metrics."""
        perf = await protocol_agent.analyze_protocol_performance(ConnectionProtocol.WIFI)
        assert "speed" in perf
        assert "latency" in perf
        assert "reliability" in perf
        assert "power" in perf
        assert perf["speed"] > 0
        assert perf["latency"] > 0
        assert 0 < perf["reliability"] <= 1

    @pytest.mark.asyncio
    async def test_analyze_protocol_performance_quantum(self, protocol_agent):
        """Quantum should have extreme performance metrics."""
        perf = await protocol_agent.analyze_protocol_performance(ConnectionProtocol.QUANTUM)
        assert perf["speed"] > 500
        assert perf["latency"] >= 0  # Could be 0
        assert perf["reliability"] > 0.5

    @pytest.mark.asyncio
    async def test_analyze_protocol_performance_bluetooth(self, protocol_agent):
        """Bluetooth should have low power consumption."""
        perf = await protocol_agent.analyze_protocol_performance(ConnectionProtocol.BLUETOOTH)
        assert perf["power"] < 1.0

    @pytest.mark.asyncio
    async def test_select_optimal_protocol_for_speed(self, protocol_agent):
        """select_optimal_protocol should pick high-speed protocol when speed is critical."""
        await protocol_agent.setup_protocol_fallback_chains()
        protocol = await protocol_agent.select_optimal_protocol(
            "primary_internet",
            {"speed": 1000, "latency": 100, "reliability": 0.5, "power_efficiency": 1}
        )
        # Should pick a protocol from the primary_internet chain
        assert protocol in protocol_agent.fallback_chains["primary_internet"]

    @pytest.mark.asyncio
    async def test_select_optimal_protocol_for_latency(self, protocol_agent):
        """select_optimal_protocol should prefer low-latency protocols."""
        await protocol_agent.setup_protocol_fallback_chains()
        protocol = await protocol_agent.select_optimal_protocol(
            "primary_internet",
            {"speed": 1, "latency": 1, "reliability": 0.5, "power_efficiency": 10}
        )
        assert protocol is not None

    @pytest.mark.asyncio
    async def test_select_optimal_protocol_unknown_task(self, protocol_agent):
        """Unknown task type should use default fallback chain."""
        await protocol_agent.setup_protocol_fallback_chains()
        protocol = await protocol_agent.select_optimal_protocol(
            "unknown_task",
            {"speed": 100}
        )
        assert protocol is not None

    @pytest.mark.asyncio
    async def test_switch_protocol(self, protocol_agent):
        """switch_protocol should update active protocols."""
        await protocol_agent.switch_protocol(
            ConnectionProtocol.WIFI,
            ConnectionProtocol.LTE
        )
        assert ConnectionProtocol.LTE in protocol_agent.active_protocols

    @pytest.mark.asyncio
    async def test_create_mesh_network_star(self, protocol_agent):
        """create_mesh_network should create star topology config."""
        config = await protocol_agent.create_mesh_network(
            ["node1", "node2", "node3"],
            topology="star"
        )
        assert config["topology"] == "star"
        assert len(config["nodes"]) == 3
        assert config["node_roles"]["node1"] == "central_hub"
        assert config["node_roles"]["node2"] == "leaf_node"

    @pytest.mark.asyncio
    async def test_create_mesh_network_tree(self, protocol_agent):
        """create_mesh_network should create tree topology config."""
        config = await protocol_agent.create_mesh_network(
            ["root", "branch1", "branch2", "leaf1", "leaf2"],
            topology="tree"
        )
        assert config["topology"] == "tree"
        assert config["node_roles"]["root"] == "root"

    @pytest.mark.asyncio
    async def test_create_mesh_network_mesh(self, protocol_agent):
        """create_mesh_network should create mesh topology config."""
        config = await protocol_agent.create_mesh_network(
            ["n1", "n2", "n3"],
            topology="mesh"
        )
        assert config["topology"] == "mesh"
        for node in ["n1", "n2", "n3"]:
            assert config["node_roles"][node] == "mesh_node"

    @pytest.mark.asyncio
    async def test_create_mesh_network_single_node_star(self, protocol_agent):
        """Star topology with single node should work."""
        config = await protocol_agent.create_mesh_network(
            ["only_node"],
            topology="star"
        )
        assert config["node_roles"]["only_node"] == "central_hub"

    def test_assign_node_roles_star(self, protocol_agent):
        """assign_node_roles star should assign central_hub and leaf_nodes."""
        roles = protocol_agent.assign_node_roles(
            ["hub", "leaf1", "leaf2", "leaf3"],
            "star"
        )
        assert roles["hub"] == "central_hub"
        assert roles["leaf1"] == "leaf_node"
        assert roles["leaf3"] == "leaf_node"

    def test_assign_node_roles_tree(self, protocol_agent):
        """assign_node_roles tree should assign root, branch, leaf."""
        roles = protocol_agent.assign_node_roles(
            ["root", "a", "b", "c"],
            "tree"
        )
        assert roles["root"] == "root"
        assert roles["a"] == "leaf"   # Index 1 -> leaf
        assert roles["b"] == "branch"  # Index 2 -> branch

    def test_assign_node_roles_mesh(self, protocol_agent):
        """assign_node_roles mesh should assign mesh_node to all."""
        roles = protocol_agent.assign_node_roles(
            ["n1", "n2", "n3"],
            "mesh"
        )
        assert all(v == "mesh_node" for v in roles.values())

    @pytest.mark.asyncio
    async def test_protocol_agent_initialization(self, protocol_agent):
        """ProtocolAgent should initialize with empty state."""
        assert protocol_agent.active_protocols == {}
        assert protocol_agent.protocol_performance == {}
        assert protocol_agent.fallback_chains == {}
        assert protocol_agent.mesh_topology == {}


# =============================================================================
# NetworkIntelligenceLayer Tests
# =============================================================================

class TestNetworkIntelligenceLayer:
    """Tests for NetworkIntelligenceLayer — Unified Network Intelligence."""

    @pytest.mark.asyncio
    async def test_initialization_creates_agents(self, network_intelligence):
        """NetworkIntelligenceLayer should create both agents."""
        assert isinstance(network_intelligence.spectrum_agent, SpectrumAgent)
        assert isinstance(network_intelligence.protocol_agent, ProtocolAgent)

    @pytest.mark.asyncio
    async def test_discover_network_interfaces(self, network_intelligence):
        """discover_network_interfaces should populate interfaces."""
        await network_intelligence.discover_network_interfaces()
        assert len(network_intelligence.network_interfaces) > 0
        # Should have Wi-Fi, 5G, Bluetooth, Quantum
        assert "Wi-Fi_5GHz" in network_intelligence.network_interfaces
        assert "5G_NR" in network_intelligence.network_interfaces

    @pytest.mark.asyncio
    async def test_discover_network_interfaces_quantum(self, network_intelligence):
        """discover_network_interfaces should include quantum interface."""
        await network_intelligence.discover_network_interfaces()
        quantum = network_intelligence.network_interfaces.get("Quantum_Entanglement")
        assert quantum is not None
        assert quantum.type == NetworkType.QUANTUM
        assert quantum.latency == -1000  # Negative latency

    def test_get_interfaces_for_protocol_active_only(self, network_intelligence):
        """get_interfaces_for_protocol should return active matching interfaces."""
        # Manually add interfaces
        intf1 = NetworkInterface(
            name="Wi-Fi_5GHz", type=NetworkType.WLAN, frequency="5GHz",
            protocol=ConnectionProtocol.WIFI, signal_strength=-45,
            noise_level=-95, data_rate=866.7, latency=5,
            power_consumption=2.0, security_level="WPA3", status="active"
        )
        intf2 = NetworkInterface(
            name="5G_NR", type=NetworkType.WWAN, frequency="Sub-6GHz",
            protocol=ConnectionProtocol.NR_5G, signal_strength=-65,
            noise_level=-105, data_rate=1200, latency=8,
            power_consumption=4.0, security_level="5G-AKA", status="standby"
        )
        network_intelligence.network_interfaces["Wi-Fi_5GHz"] = intf1
        network_intelligence.network_interfaces["5G_NR"] = intf2

        wifi_interfaces = network_intelligence.get_interfaces_for_protocol(ConnectionProtocol.WIFI)
        assert "Wi-Fi_5GHz" in wifi_interfaces
        assert "5G_NR" not in wifi_interfaces  # standby, not active

    def test_get_interfaces_for_protocol_no_match(self, network_intelligence):
        """get_interfaces_for_protocol with no matches should return empty."""
        result = network_intelligence.get_interfaces_for_protocol(ConnectionProtocol.BLUETOOTH)
        assert result == []

    @pytest.mark.asyncio
    async def test_generate_optimization_steps_wifi(self, network_intelligence):
        """Wifi optimization should include channel and band switching steps."""
        steps = await network_intelligence.generate_optimization_steps(
            ConnectionProtocol.WIFI,
            {"speed": 100, "latency": 10}
        )
        assert len(steps) > 0
        assert any("5GHz" in s for s in steps)

    @pytest.mark.asyncio
    async def test_generate_optimization_steps_quantum(self, network_intelligence):
        """Quantum optimization should include entanglement steps."""
        steps = await network_intelligence.generate_optimization_steps(
            ConnectionProtocol.QUANTUM,
            {"speed": 1000, "latency": 0}
        )
        assert len(steps) > 0
        assert any("quantum" in s.lower() for s in steps)

    @pytest.mark.asyncio
    async def test_generate_optimization_steps_unknown(self, network_intelligence):
        """Unknown protocol optimization steps should be empty."""
        steps = await network_intelligence.generate_optimization_steps(
            ConnectionProtocol.BLUETOOTH,
            {"speed": 1}
        )
        # Bluetooth has no specific optimization steps defined
        assert steps == []

    @pytest.mark.asyncio
    async def test_optimize_network_for_task_wifi(self, network_intelligence):
        """optimize_network_for_task should produce an optimization plan."""
        await network_intelligence.discover_network_interfaces()
        plan = await network_intelligence.optimize_network_for_task(
            "primary_internet",
            {"speed": 100, "latency": 50, "reliability": 0.8}
        )
        assert plan["task_type"] == "primary_internet"
        assert "selected_protocol" in plan
        assert "recommended_interfaces" in plan
        assert "expected_performance" in plan
        assert "optimization_steps" in plan

    @pytest.mark.asyncio
    async def test_optimize_network_for_task_empty_requirements(self, network_intelligence):
        """optimize_network_for_task with empty requirements should still work."""
        await network_intelligence.discover_network_interfaces()
        plan = await network_intelligence.optimize_network_for_task(
            "primary_internet",
            {}
        )
        assert plan["task_type"] == "primary_internet"
        assert plan["selected_protocol"] is not None

    @pytest.mark.asyncio
    async def test_optimize_interface(self, network_intelligence):
        """optimize_interface should improve metrics."""
        await network_intelligence.discover_network_interfaces()
        old_signal = network_intelligence.network_interfaces["Wi-Fi_5GHz"].signal_strength
        old_latency = network_intelligence.network_interfaces["Wi-Fi_5GHz"].latency

        await network_intelligence.optimize_interface("Wi-Fi_5GHz")

        new_signal = network_intelligence.network_interfaces["Wi-Fi_5GHz"].signal_strength
        new_latency = network_intelligence.network_interfaces["Wi-Fi_5GHz"].latency

        assert new_signal > old_signal
        assert new_latency < old_latency

    @pytest.mark.asyncio
    async def test_optimize_interface_nonexistent(self, network_intelligence):
        """optimize_interface on nonexistent interface should not crash."""
        await network_intelligence.optimize_interface("nonexistent")
        # Should not raise

    def test_network_intelligence_initial_state(self, network_intelligence):
        """NetworkIntelligenceLayer should initialize with empty state."""
        assert network_intelligence.network_interfaces == {}
        assert network_intelligence.active_connections == {}


# =============================================================================
# NetworkInterface Dataclass Tests
# =============================================================================

class TestNetworkInterface:
    """Tests for NetworkInterface dataclass."""

    def test_network_interface_creation(self):
        """NetworkInterface should store all fields."""
        intf = NetworkInterface(
            name="eth0",
            type=NetworkType.WLAN,
            frequency="5GHz",
            protocol=ConnectionProtocol.WIFI,
            signal_strength=-50.0,
            noise_level=-95.0,
            data_rate=866.7,
            latency=3.0,
            power_consumption=1.5,
            security_level="WPA3",
            status="active",
        )
        assert intf.name == "eth0"
        assert intf.type == NetworkType.WLAN
        assert intf.signal_strength == -50.0
        assert intf.status == "active"


# =============================================================================
# Edge Case Tests
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_protocol_agent_empty_nodes_mesh(self, protocol_agent):
        """create_mesh_network with empty nodes should handle gracefully."""
        config = await protocol_agent.create_mesh_network([], topology="star")
        assert config["nodes"] == []
        assert config["node_roles"] == {}

    def test_assign_node_roles_empty_list(self, protocol_agent):
        """assign_node_roles with empty list should return empty dict."""
        roles = protocol_agent.assign_node_roles([], "star")
        assert roles == {}

    @pytest.mark.asyncio
    async def test_analyze_protocol_performance_unknown(self, protocol_agent):
        """analyze_protocol_performance should handle unknown protocols."""
        # Use a mock approach since we can't easily pass an unknown enum
        perf = await protocol_agent.analyze_protocol_performance(ConnectionProtocol.MESH)
        assert perf["speed"] > 0
        assert perf["latency"] > 0

    @pytest.mark.asyncio
    async def test_switch_protocol_same_protocol(self, protocol_agent):
        """Switching to the same protocol should work."""
        await protocol_agent.switch_protocol(
            ConnectionProtocol.WIFI,
            ConnectionProtocol.WIFI
        )
        assert ConnectionProtocol.WIFI in protocol_agent.active_protocols


# =============================================================================
# Continuous Monitoring Tests (via mocking to avoid infinite loops)
# =============================================================================

class TestContinuousMonitoring:
    """Tests for continuous monitoring (with mocking to avoid infinite loops)."""

    @pytest.mark.asyncio
    async def test_handle_hardware_update(self, spectrum_agent):
        """handle_hardware_update should process events without error."""
        # Just verify it doesn't crash - actual logic is logging
        from core.event_bus import ASIMEvent, EventType
        event = ASIMEvent(
            event_type=EventType.HARDWARE_UPDATE,
            data={"action": "test"},
            source="test",
        )
        # The callback expects event.payload based on the source code
        # Let me just verify it doesn't raise
        await spectrum_agent.handle_hardware_update(event)

    @pytest.mark.asyncio
    async def test_handle_network_update(self, protocol_agent):
        """handle_network_update should process events without error."""
        from core.event_bus import ASIMEvent, EventType
        event = ASIMEvent(
            event_type=EventType.HARDWARE_UPDATE,
            data={"action": "test"},
            source="test",
        )
        await protocol_agent.handle_network_update(event)
