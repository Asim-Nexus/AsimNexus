"""
Real pytest tests for SystemMonitor using mocked psutil
"""

import pytest
import time
from unittest.mock import MagicMock, AsyncMock, patch


# ── Mock Data Helpers ──────────────────────────────────────────────────────

def make_mock_svmem(total=16000000000, used=8000000000, percent=50.0, free=8000000000,
                     available=8000000000, active=4000000000, inactive=2000000000,
                     cached=1000000000, buffers=500000000):
    """Create a mock virtual_memory return value"""
    mem = MagicMock()
    mem.total = total
    mem.used = used
    mem.percent = percent
    mem.free = free
    mem.available = available
    mem.active = active
    mem.inactive = inactive
    mem.cached = cached
    mem.buffers = buffers
    return mem


def make_mock_swap(total=4000000000, used=500000000, free=3500000000, percent=12.5):
    """Create a mock swap_memory return value"""
    swap = MagicMock()
    swap.total = total
    swap.used = used
    swap.free = free
    swap.percent = percent
    return swap


def make_mock_disk_usage(total=500000000000, used=250000000000, free=250000000000, percent=50.0):
    """Create a mock disk_usage return value"""
    du = MagicMock()
    du.total = total
    du.used = used
    du.free = free
    du.percent = percent
    return du


def make_mock_disk_partition(device="C:\\", mountpoint="C:\\", fstype="NTFS", opts="rw"):
    """Create a mock disk partition"""
    part = MagicMock()
    part.device = device
    part.mountpoint = mountpoint
    part.fstype = fstype
    part.opts = opts
    return part


def make_mock_net_io(bytes_sent=1000000, bytes_recv=2000000, packets_sent=5000,
                      packets_recv=8000, errin=0, errout=0, dropin=0, dropout=0):
    """Create a mock net_io_counters return value"""
    io = MagicMock()
    io.bytes_sent = bytes_sent
    io.bytes_recv = bytes_recv
    io.packets_sent = packets_sent
    io.packets_recv = packets_recv
    io.errin = errin
    io.errout = errout
    io.dropin = dropin
    io.dropout = dropout
    return io


def make_mock_battery(percent=85.0, power_plugged=True, secsleft=7200):
    """Create a mock sensors_battery return value"""
    batt = MagicMock()
    batt.percent = percent
    batt.power_plugged = power_plugged
    batt.secsleft = secsleft
    return batt


def make_mock_cpu_freq(current=2400.0, min_=800.0, max_=4800.0):
    """Create a mock cpu_freq return value"""
    freq = MagicMock()
    freq.current = current
    freq.min = min_
    freq.max = max_
    return freq


def make_mock_user(name="testuser", host="localhost", started=1000000.0):
    """Create a mock user return value"""
    user = MagicMock()
    user.name = name
    user.host = host
    user.started = started
    return user


# ── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def monitor():
    """Create a SystemMonitor with mocked psutil"""
    from os_control.openclaw_like_tools.system_monitor import SystemMonitor
    mon = SystemMonitor()
    # Directly inject a mock psutil module
    mock_psutil = MagicMock()
    # Set up commonly used attrs
    mock_psutil.cpu_percent.return_value = 45.0
    mock_psutil.cpu_count.side_effect = lambda logical=True: 8 if logical else 4
    mock_psutil.cpu_freq.return_value = make_mock_cpu_freq()
    mock_psutil.virtual_memory.return_value = make_mock_svmem()
    mock_psutil.swap_memory.return_value = make_mock_swap()
    mock_psutil.disk_partitions.return_value = [make_mock_disk_partition()]
    mock_psutil.disk_usage.return_value = make_mock_disk_usage()
    mock_psutil.disk_io_counters.return_value = make_mock_net_io()  # reuse shape
    mock_psutil.net_io_counters.return_value = make_mock_net_io()
    mock_psutil.sensors_battery.return_value = make_mock_battery()
    mock_psutil.boot_time.return_value = 1000000.0
    mock_psutil.users.return_value = [make_mock_user()]
    mock_psutil.POWER_TIME_UNLIMITED = 2147483647  # from psutil
    mock_psutil.net_connections.return_value = []
    mock_psutil.getloadavg = lambda: (1.0, 0.8, 0.5)
    mon._psutil = mock_psutil
    return mon


# ── Test SystemMetrics Dataclass ───────────────────────────────────────────

class TestSystemMetrics:
    """Tests for the SystemMetrics dataclass"""

    def test_create_system_metrics(self):
        """Create a SystemMetrics with all fields"""
        from os_control.openclaw_like_tools.system_monitor import SystemMetrics
        sm = SystemMetrics(
            timestamp=1000.0,
            cpu_percent=50.0,
            cpu_count=8,
            cpu_freq=2400.0,
            memory_total=16000000000,
            memory_used=8000000000,
            memory_percent=50.0,
            disk_total=500000000000,
            disk_used=250000000000,
            disk_percent=50.0,
            net_bytes_sent=1000,
            net_bytes_recv=2000,
            boot_time=1000000.0,
            platform="Windows-10",
            hostname="test-pc",
        )
        assert sm.cpu_percent == 50.0
        assert sm.cpu_count == 8
        assert sm.hostname == "test-pc"

    def test_system_metrics_asdict(self):
        """SystemMetrics should be convertible to dict via asdict"""
        from os_control.openclaw_like_tools.system_monitor import SystemMetrics
        from dataclasses import asdict
        sm = SystemMetrics(
            timestamp=1000.0, cpu_percent=50.0, cpu_count=8, cpu_freq=2400.0,
            memory_total=16000000000, memory_used=8000000000, memory_percent=50.0,
            disk_total=500000000000, disk_used=250000000000, disk_percent=50.0,
            net_bytes_sent=1000, net_bytes_recv=2000, boot_time=1000000.0,
            platform="Windows-10", hostname="test-pc",
        )
        d = asdict(sm)
        assert d["cpu_percent"] == 50.0
        assert d["hostname"] == "test-pc"


# ── Test SystemMonitor Init ────────────────────────────────────────────────

class TestSystemMonitorInit:
    """Tests for SystemMonitor initialization"""

    def test_init_creates_instance(self):
        """Init should create SystemMonitor instance"""
        from os_control.openclaw_like_tools.system_monitor import SystemMonitor
        mon = SystemMonitor()
        assert mon._psutil is not None  # psutil should be available
        assert mon._cache_ttl == 1.0


# ── Test CPU Metrics ───────────────────────────────────────────────────────

class TestSystemMonitorCPU:
    """Tests for get_cpu"""

    @pytest.mark.asyncio
    async def test_get_cpu_with_psutil(self, monitor):
        """get_cpu should return CPU metrics when psutil is available"""
        result = await monitor.get_cpu()
        assert result["plugin"] == "system.cpu"
        assert result["percent"] == 45.0
        assert result["count"]["physical"] == 4
        assert result["count"]["logical"] == 8
        assert "frequency_mhz" in result
        assert result["frequency_mhz"]["current"] == 2400.0
        assert result["frequency_mhz"]["min"] == 800.0
        assert result["frequency_mhz"]["max"] == 4800.0
        assert "per_core" in result
        assert "load_avg" in result
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_get_cpu_without_psutil(self):
        """get_cpu should return fallback values when psutil unavailable"""
        from os_control.openclaw_like_tools.system_monitor import SystemMonitor
        mon = SystemMonitor()
        # Disable psutil so _psutil_available() returns False
        mon._psutil_available = lambda: False
        mon._psutil = None
        result = await mon.get_cpu()
        assert result["plugin"] == "system.cpu"
        assert result["percent"] == 0.0
        assert result["count"]["physical"] == 0
        assert result["count"]["logical"] == 0
        assert "note" in result


# ── Test Memory Metrics ────────────────────────────────────────────────────

class TestSystemMonitorMemory:
    """Tests for get_memory"""

    @pytest.mark.asyncio
    async def test_get_memory_with_psutil(self, monitor):
        """get_memory should return memory metrics"""
        result = await monitor.get_memory()
        assert result["plugin"] == "system.memory"
        assert result["virtual"]["total"] == 16000000000
        assert result["virtual"]["used"] == 8000000000
        assert result["virtual"]["percent"] == 50.0
        assert result["virtual"]["total_gb"] > 0
        assert result["swap"]["total"] == 4000000000
        assert result["swap"]["used"] == 500000000
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_get_memory_without_psutil(self):
        """get_memory should return fallback without psutil"""
        from os_control.openclaw_like_tools.system_monitor import SystemMonitor
        mon = SystemMonitor()
        # Disable psutil so _psutil_available() returns False
        mon._psutil_available = lambda: False
        mon._psutil = None
        result = await mon.get_memory()
        assert result["plugin"] == "system.memory"
        assert result["virtual"]["total"] == 0
        assert result["virtual"]["percent"] == 0.0
        assert "note" in result


# ── Test Disk Metrics ──────────────────────────────────────────────────────

class TestSystemMonitorDisk:
    """Tests for get_disk"""

    @pytest.mark.asyncio
    async def test_get_disk_with_psutil(self, monitor):
        """get_disk should return disk metrics"""
        result = await monitor.get_disk()
        assert result["plugin"] == "system.disk"
        assert len(result["partitions"]) == 1
        assert result["partitions"][0]["device"] == "C:\\"
        assert result["partitions"][0]["fstype"] == "NTFS"
        assert "io" in result
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_get_disk_without_psutil(self):
        """get_disk should return fallback without psutil"""
        from os_control.openclaw_like_tools.system_monitor import SystemMonitor
        mon = SystemMonitor()
        # Disable psutil so _psutil_available() returns False
        mon._psutil_available = lambda: False
        mon._psutil = None
        result = await mon.get_disk()
        assert result["plugin"] == "system.disk"
        assert result["partitions"] == []
        assert "note" in result

    @pytest.mark.asyncio
    async def test_get_disk_handles_permission_error(self, monitor):
        """get_disk should handle PermissionError on disk_usage"""
        monitor._psutil.disk_usage.side_effect = PermissionError("Access denied")
        result = await monitor.get_disk()
        assert result["partitions"][0].get("note") == "access denied"


# ── Test Network Metrics ───────────────────────────────────────────────────

class TestSystemMonitorNetwork:
    """Tests for get_network"""

    @pytest.mark.asyncio
    async def test_get_network_with_psutil(self, monitor):
        """get_network should return network metrics"""
        result = await monitor.get_network()
        assert result["plugin"] == "system.network"
        assert result["io"]["bytes_sent"] == 1000000
        assert result["io"]["bytes_recv"] == 2000000
        assert result["io"]["bytes_sent_mb"] > 0
        assert result["io"]["bytes_recv_mb"] > 0
        assert "interfaces" in result
        assert "connections" in result
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_get_network_without_psutil(self):
        """get_network should return fallback without psutil"""
        from os_control.openclaw_like_tools.system_monitor import SystemMonitor
        mon = SystemMonitor()
        # Disable psutil so _psutil_available() returns False
        mon._psutil_available = lambda: False
        mon._psutil = None
        result = await mon.get_network()
        assert result["plugin"] == "system.network"
        assert "note" in result


# ── Test Battery Metrics ───────────────────────────────────────────────────

class TestSystemMonitorBattery:
    """Tests for get_battery"""

    @pytest.mark.asyncio
    async def test_get_battery_with_psutil(self, monitor):
        """get_battery should return battery metrics"""
        result = await monitor.get_battery()
        assert result["plugin"] == "system.battery"
        assert result["percent"] == 85.0
        assert result["power_plugged"] is True
        assert result["seconds_left"] == 7200
        assert result["minutes_left"] == 120.0
        assert result["hours_left"] == 2.0
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_get_battery_no_battery(self, monitor):
        """get_battery should handle no battery detected"""
        monitor._psutil.sensors_battery.return_value = None
        result = await monitor.get_battery()
        assert "note" in result
        assert "no battery" in result["note"].lower()

    @pytest.mark.asyncio
    async def test_get_battery_unlimited_secsleft(self, monitor):
        """get_battery should handle POWER_TIME_UNLIMITED"""
        monitor._psutil.sensors_battery.return_value = make_mock_battery(
            secsleft=monitor._psutil.POWER_TIME_UNLIMITED
        )
        result = await monitor.get_battery()
        assert "seconds_left" not in result  # Should not include when unlimited

    @pytest.mark.asyncio
    async def test_get_battery_without_psutil(self):
        """get_battery should return fallback without psutil"""
        from os_control.openclaw_like_tools.system_monitor import SystemMonitor
        mon = SystemMonitor()
        # Disable psutil so _psutil_available() returns False
        mon._psutil_available = lambda: False
        mon._psutil = None
        result = await mon.get_battery()
        assert result["plugin"] == "system.battery"
        assert "note" in result


# ── Test System Info ───────────────────────────────────────────────────────

class TestSystemMonitorSystemInfo:
    """Tests for get_system_info"""

    @pytest.mark.asyncio
    async def test_get_system_info(self, monitor):
        """get_system_info should return platform and system info"""
        result = await monitor.get_system_info()
        assert result["plugin"] == "system.info"
        assert "platform" in result
        assert "system" in result
        assert "release" in result
        assert "version" in result
        assert "machine" in result
        assert "processor" in result
        assert "hostname" in result
        assert "python_version" in result
        assert "boot_time" in result
        assert "uptime_seconds" in result
        assert "uptime_days" in result
        assert "users" in result
        assert len(result["users"]) == 1
        assert result["users"][0]["name"] == "testuser"
        assert "environment" in result
        assert "timestamp" in result


# ── Test All Metrics ───────────────────────────────────────────────────────

class TestSystemMonitorAllMetrics:
    """Tests for get_all_metrics"""

    @pytest.mark.asyncio
    async def test_get_all_metrics_with_psutil(self, monitor):
        """get_all_metrics should return a SystemMetrics with all data"""
        result = await monitor.get_all_metrics()
        from os_control.openclaw_like_tools.system_monitor import SystemMetrics
        assert isinstance(result, SystemMetrics)
        assert result.cpu_percent == 45.0
        assert result.cpu_count == 8
        assert result.cpu_freq == 2400.0
        assert result.memory_total == 16000000000
        assert result.memory_percent == 50.0
        assert result.disk_total == 500000000000
        assert result.disk_percent == 50.0
        assert result.net_bytes_sent == 1000000
        assert result.net_bytes_recv == 2000000
        assert result.boot_time == 1000000.0
        assert result.platform is not None
        assert result.hostname is not None
        assert result.timestamp > 0

    @pytest.mark.asyncio
    async def test_get_all_metrics_without_psutil(self):
        """get_all_metrics should return default SystemMetrics without psutil"""
        from os_control.openclaw_like_tools.system_monitor import SystemMonitor
        mon = SystemMonitor()
        # Disable psutil so _psutil_available() returns False
        mon._psutil_available = lambda: False
        mon._psutil = None
        result = await mon.get_all_metrics()
        assert result.cpu_percent == 0.0
        assert result.cpu_count == 0
        assert result.cpu_freq is None
        assert result.memory_total == 0
        assert result.memory_percent == 0.0
        assert result.disk_total == 0
        assert result.disk_percent == 0.0
        assert result.net_bytes_sent == 0
        assert result.net_bytes_recv == 0
        assert result.boot_time == 0.0

    @pytest.mark.asyncio
    async def test_get_all_metrics_handles_cpu_freq_exception(self, monitor):
        """get_all_metrics should handle cpu_freq exception gracefully"""
        monitor._psutil.cpu_freq.side_effect = Exception("No freq data")
        result = await monitor.get_all_metrics()
        assert result.cpu_freq is None


# ── Test Global Singleton ──────────────────────────────────────────────────

class TestGetSystemMonitor:
    """Tests for the get_system_monitor singleton"""

    def test_get_system_monitor_returns_instance(self):
        """get_system_monitor should return a SystemMonitor"""
        from os_control.openclaw_like_tools.system_monitor import get_system_monitor
        mon = get_system_monitor()
        from os_control.openclaw_like_tools.system_monitor import SystemMonitor
        assert isinstance(mon, SystemMonitor)
