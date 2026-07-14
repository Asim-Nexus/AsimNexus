"""
ASIMNEXUS System Monitor Tools
Real-time system metrics: CPU, memory, disk, network, battery
"""

import asyncio
import json
import logging
import os
import platform
import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger("AsimNexus.SystemMonitor")


@dataclass
class SystemMetrics:
    """Snapshot of system metrics at a point in time"""
    timestamp: float
    cpu_percent: float
    cpu_count: int
    cpu_freq: Optional[float]
    memory_total: int
    memory_used: int
    memory_percent: float
    disk_total: int
    disk_used: int
    disk_percent: float
    net_bytes_sent: int
    net_bytes_recv: int
    boot_time: float
    platform: str
    hostname: str


class SystemMonitor:
    """Real system monitoring using psutil"""

    def __init__(self):
        self._psutil = None
        self._last_cpu_times = None
        self._last_net_io = None
        self._last_snapshot_time = 0.0
        self._cached_metrics: Optional[SystemMetrics] = None
        self._cache_ttl = 1.0  # seconds
        self._load_psutil()

    def _load_psutil(self) -> bool:
        """Lazy-load psutil"""
        if self._psutil is not None:
            return True
        try:
            import psutil
            self._psutil = psutil
            logger.info("✅ SystemMonitor: psutil loaded")
            return True
        except ImportError:
            logger.warning("⚠️ SystemMonitor: psutil not available — using fallback metrics")
            return False

    def _psutil_available(self) -> bool:
        return self._load_psutil()

    async def get_cpu(self) -> Dict[str, Any]:
        """Get CPU metrics: percent, count, frequency"""
        result = {
            "plugin": "system.cpu",
            "timestamp": time.time(),
        }
        if self._psutil_available():
            # CPU percent over 0.1s interval
            result["percent"] = self._psutil.cpu_percent(interval=0.1)
            result["count"] = {
                "physical": self._psutil.cpu_count(logical=False),
                "logical": self._psutil.cpu_count(logical=True),
            }
            try:
                freq = self._psutil.cpu_freq()
                if freq:
                    result["frequency_mhz"] = {
                        "current": round(freq.current, 1),
                        "min": round(freq.min, 1) if freq.min else None,
                        "max": round(freq.max, 1) if freq.max else None,
                    }
            except Exception:
                pass
            # Per-core usage
            try:
                result["per_core"] = self._psutil.cpu_percent(interval=0.05, percpu=True)
            except Exception:
                pass
            result["load_avg"] = getattr(self._psutil, "getloadavg", lambda: None)()
        else:
            result["percent"] = 0.0
            result["count"] = {"physical": 0, "logical": 0}
            result["note"] = "psutil not available — install with: pip install psutil"
        return result

    async def get_memory(self) -> Dict[str, Any]:
        """Get memory metrics: virtual and swap"""
        result = {
            "plugin": "system.memory",
            "timestamp": time.time(),
        }
        if self._psutil_available():
            mem = self._psutil.virtual_memory()
            result["virtual"] = {
                "total": mem.total,
                "available": mem.available,
                "used": mem.used,
                "percent": mem.percent,
                "free": mem.free,
                "active": getattr(mem, "active", None),
                "inactive": getattr(mem, "inactive", None),
                "cached": getattr(mem, "cached", None),
                "buffers": getattr(mem, "buffers", None),
            }
            # Human-readable
            result["virtual"]["total_gb"] = round(mem.total / (1024**3), 2)
            result["virtual"]["used_gb"] = round(mem.used / (1024**3), 2)
            result["virtual"]["available_gb"] = round(mem.available / (1024**3), 2)

            try:
                swap = self._psutil.swap_memory()
                result["swap"] = {
                    "total": swap.total,
                    "used": swap.used,
                    "free": swap.free,
                    "percent": swap.percent,
                    "total_gb": round(swap.total / (1024**3), 2),
                    "used_gb": round(swap.used / (1024**3), 2),
                }
            except Exception:
                pass
        else:
            result["virtual"] = {"total": 0, "used": 0, "percent": 0.0}
            result["note"] = "psutil not available"
        return result

    async def get_disk(self) -> Dict[str, Any]:
        """Get disk metrics: usage, partitions, IO"""
        result = {
            "plugin": "system.disk",
            "timestamp": time.time(),
        }
        if self._psutil_available():
            # All partitions
            partitions = []
            for part in self._psutil.disk_partitions():
                try:
                    usage = self._psutil.disk_usage(part.mountpoint)
                    partitions.append({
                        "device": part.device,
                        "mountpoint": part.mountpoint,
                        "fstype": part.fstype,
                        "total": usage.total,
                        "used": usage.used,
                        "free": usage.free,
                        "percent": usage.percent,
                        "total_gb": round(usage.total / (1024**3), 2),
                        "used_gb": round(usage.used / (1024**3), 2),
                        "free_gb": round(usage.free / (1024**3), 2),
                    })
                except (PermissionError, OSError):
                    partitions.append({
                        "device": part.device,
                        "mountpoint": part.mountpoint,
                        "fstype": part.fstype,
                        "note": "access denied",
                    })
            result["partitions"] = partitions

            try:
                io = self._psutil.disk_io_counters()
                if io:
                    result["io"] = {
                        "read_count": io.read_count,
                        "write_count": io.write_count,
                        "read_bytes": io.read_bytes,
                        "write_bytes": io.write_bytes,
                        "read_time_ms": io.read_time,
                        "write_time_ms": io.write_time,
                    }
            except Exception:
                pass
        else:
            result["partitions"] = []
            result["note"] = "psutil not available"
        return result

    async def get_network(self) -> Dict[str, Any]:
        """Get network metrics: interfaces, IO counters, connections"""
        result = {
            "plugin": "system.network",
            "timestamp": time.time(),
        }
        if self._psutil_available():
            try:
                io = self._psutil.net_io_counters()
                result["io"] = {
                    "bytes_sent": io.bytes_sent,
                    "bytes_recv": io.bytes_recv,
                    "packets_sent": io.packets_sent,
                    "packets_recv": io.packets_recv,
                    "errin": io.errin,
                    "errout": io.errout,
                    "dropin": io.dropin,
                    "dropout": io.dropout,
                }
                # Human-readable
                result["io"]["bytes_sent_mb"] = round(io.bytes_sent / (1024**2), 2)
                result["io"]["bytes_recv_mb"] = round(io.bytes_recv / (1024**2), 2)
            except Exception:
                pass

            # Per-interface stats
            try:
                interfaces = {}
                for iface, stats in self._psutil.net_io_counters(pernic=True).items():
                    interfaces[iface] = {
                        "bytes_sent": stats.bytes_sent,
                        "bytes_recv": stats.bytes_recv,
                        "packets_sent": stats.packets_sent,
                        "packets_recv": stats.packets_recv,
                        "speed_mbps": None,
                    }
                result["interfaces"] = interfaces
            except Exception:
                pass

            # Active connections count (filtered, no sensitive data)
            try:
                connections = self._psutil.net_connections()
                # Count by status
                status_counts = {}
                for conn in connections:
                    s = conn.status
                    status_counts[s] = status_counts.get(s, 0) + 1
                result["connections"] = {
                    "total": len(connections),
                    "by_status": status_counts,
                }
            except (PermissionError, Exception):
                result["connections"] = {"total": -1, "note": "insufficient permissions"}
        else:
            result["note"] = "psutil not available"
        return result

    async def get_battery(self) -> Dict[str, Any]:
        """Get battery status"""
        result = {
            "plugin": "system.battery",
            "timestamp": time.time(),
        }
        if self._psutil_available():
            try:
                batt = self._psutil.sensors_battery()
                if batt:
                    result["percent"] = batt.percent
                    result["power_plugged"] = batt.power_plugged
                    if batt.secsleft > 0 and batt.secsleft != self._psutil.POWER_TIME_UNLIMITED:
                        result["seconds_left"] = batt.secsleft
                        result["minutes_left"] = round(batt.secsleft / 60, 1)
                        result["hours_left"] = round(batt.secsleft / 3600, 2)
                else:
                    result["note"] = "no battery detected"
            except Exception:
                result["note"] = "battery info unavailable"
        else:
            result["note"] = "psutil not available"
        return result

    async def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information (read-only, safe)"""
        result = {
            "plugin": "system.info",
            "timestamp": time.time(),
        }
        result["platform"] = platform.platform()
        result["system"] = platform.system()
        result["release"] = platform.release()
        result["version"] = platform.version()
        result["machine"] = platform.machine()
        result["processor"] = platform.processor()
        result["hostname"] = platform.node()
        result["python_version"] = platform.python_version()

        if self._psutil_available():
            result["boot_time"] = self._psutil.boot_time()
            result["uptime_seconds"] = time.time() - self._psutil.boot_time()
            result["uptime_days"] = round(result["uptime_seconds"] / 86400, 2)
            result["users"] = []
            try:
                for user in self._psutil.users():
                    result["users"].append({
                        "name": user.name,
                        "host": user.host,
                        "started": user.started,
                    })
            except Exception:
                pass

        # Environment info (safe subset)
        result["environment"] = {
            "home": os.environ.get("HOME") or os.environ.get("USERPROFILE", ""),
            "temp": os.environ.get("TMP") or os.environ.get("TEMP", ""),
            "shell": os.environ.get("SHELL") or os.environ.get("ComSpec", ""),
        }

        return result

    async def get_all_metrics(self) -> SystemMetrics:
        """Get a consolidated snapshot of all system metrics"""
        if self._psutil_available():
            psutil = self._psutil
            cpu = psutil.cpu_percent(interval=0.2)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            net = psutil.net_io_counters()
            boot = psutil.boot_time()
            try:
                freq = psutil.cpu_freq()
                cpu_freq = freq.current if freq else None
            except Exception:
                cpu_freq = None

            return SystemMetrics(
                timestamp=time.time(),
                cpu_percent=cpu,
                cpu_count=psutil.cpu_count(),
                cpu_freq=cpu_freq,
                memory_total=mem.total,
                memory_used=mem.used,
                memory_percent=mem.percent,
                disk_total=disk.total,
                disk_used=disk.used,
                disk_percent=disk.percent,
                net_bytes_sent=net.bytes_sent,
                net_bytes_recv=net.bytes_recv,
                boot_time=boot,
                platform=platform.system(),
                hostname=platform.node(),
            )
        else:
            return SystemMetrics(
                timestamp=time.time(),
                cpu_percent=0.0,
                cpu_count=0,
                cpu_freq=None,
                memory_total=0,
                memory_used=0,
                memory_percent=0.0,
                disk_total=0,
                disk_used=0,
                disk_percent=0.0,
                net_bytes_sent=0,
                net_bytes_recv=0,
                boot_time=0.0,
                platform=platform.system(),
                hostname=platform.node(),
            )


# Global singleton
_system_monitor = None


def get_system_monitor() -> SystemMonitor:
    """Get or create the global SystemMonitor singleton"""
    global _system_monitor
    if _system_monitor is None:
        _system_monitor = SystemMonitor()
    return _system_monitor
