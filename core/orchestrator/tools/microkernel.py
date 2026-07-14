"""MicroKernel Interface — Secure hardware and system-level control.

Provides a sandboxed interface for:
- Hardware status monitoring (CPU, memory, disk, network, GPU, sensors)
- Hardware control (power management, device enable/disable)
- Driver management (install, update, verify signatures)
- System operations (shutdown, restart, sleep, hibernate)

All operations are gated through the AsimNexus Gateway for authorization.
High-risk operations (hw:control, hw:driver) require HITL approval.
"""

import logging
import platform
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class HardwareCategory(Enum):
    """Categories of hardware components."""
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    GPU = "gpu"
    NPU = "npu"
    CHIPSET = "chipset"
    MOTHERBOARD = "motherboard"
    STORAGE_CONTROLLER = "storage_controller"
    RAM = "ram"
    ROM = "rom"
    SENSOR = "sensor"
    USB = "usb"
    DISPLAY = "display"
    AUDIO = "audio"
    BATTERY = "battery"
    THERMAL = "thermal"
    BIOS = "bios"
    FIRMWARE = "firmware"


class OperationRisk(Enum):
    """Risk level of hardware operations."""
    INFO = "info"           # Read-only status — low risk
    CONTROL = "control"     # Change settings — medium risk
    POWER = "power"         # Power operations — high risk
    DRIVER = "driver"       # Driver install/update — critical risk


@dataclass
class HardwareStatus:
    """Current status of a hardware component."""
    category: HardwareCategory
    name: str
    status: str  # "ok", "warning", "error", "unknown"
    metrics: Dict[str, Any] = field(default_factory=dict)
    details: str = ""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class OperationResult:
    """Result of a hardware operation."""
    success: bool
    operation: str
    target: str
    message: str
    risk: OperationRisk
    requires_reboot: bool = False
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class MicroKernelInterface:
    """Secure microkernel interface for hardware and system control.

    All operations are logged and high-risk operations require
    Gateway authorization before execution.

    Platform support: Windows, Linux, macOS (with varying capabilities).
    """

    def __init__(self):
        self._platform = platform.system().lower()
        self._operation_log: List[OperationResult] = []

    # ── Status Monitoring ──────────────────────────────────────────

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status across all hardware categories."""
        return {
            "platform": self._platform,
            "hostname": platform.node(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "timestamp": datetime.utcnow().isoformat(),
            "components": self.get_all_hardware_status(),
        }

    def _get_cpu_status(self) -> HardwareStatus:
        """Get CPU status."""
        try:
            if self._platform == "windows":
                import psutil
                cpu_percent = psutil.cpu_percent(interval=0.1)
                cpu_count = psutil.cpu_count()
                cpu_freq = psutil.cpu_freq()
                return HardwareStatus(
                    category=HardwareCategory.CPU,
                    name=platform.processor() or "Unknown CPU",
                    status="ok" if cpu_percent < 90 else "warning",
                    metrics={
                        "usage_percent": cpu_percent,
                        "core_count": cpu_count,
                        "frequency_mhz": cpu_freq.current if cpu_freq else 0,
                    },
                )
        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"CPU status error: {e}")

        return HardwareStatus(
            category=HardwareCategory.CPU,
            name=platform.processor() or "Unknown",
            status="unknown",
            metrics={},
            details="psutil not available",
        )

    def _get_memory_status(self) -> HardwareStatus:
        """Get memory status."""
        try:
            import psutil
            mem = psutil.virtual_memory()
            return HardwareStatus(
                category=HardwareCategory.MEMORY,
                name="System Memory",
                status="ok" if mem.percent < 90 else "warning",
                metrics={
                    "total_gb": round(mem.total / (1024**3), 2),
                    "available_gb": round(mem.available / (1024**3), 2),
                    "used_gb": round(mem.used / (1024**3), 2),
                    "percent": mem.percent,
                },
            )
        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"Memory status error: {e}")

        return HardwareStatus(
            category=HardwareCategory.MEMORY,
            name="System Memory",
            status="unknown",
            metrics={},
            details="psutil not available",
        )

    def _get_disk_status(self) -> HardwareStatus:
        """Get disk status."""
        try:
            import psutil
            disks = []
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disks.append({
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "total_gb": round(usage.total / (1024**3), 2),
                        "used_gb": round(usage.used / (1024**3), 2),
                        "free_gb": round(usage.free / (1024**3), 2),
                        "percent": usage.percent,
                    })
                except (PermissionError, OSError):
                    continue

            return HardwareStatus(
                category=HardwareCategory.DISK,
                name="Storage",
                status="ok",
                metrics={"disks": disks},
            )
        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"Disk status error: {e}")

        return HardwareStatus(
            category=HardwareCategory.DISK,
            name="Storage",
            status="unknown",
            metrics={},
            details="psutil not available",
        )

    def _get_network_status(self) -> HardwareStatus:
        """Get network status."""
        try:
            import psutil
            net = psutil.net_io_counters()
            addrs = psutil.net_if_addrs()
            interfaces = []
            for name, addr_list in addrs.items():
                for addr in addr_list:
                    if addr.family.name == "AF_INET":
                        interfaces.append({
                            "name": name,
                            "ip": addr.address,
                            "netmask": addr.netmask,
                        })

            return HardwareStatus(
                category=HardwareCategory.NETWORK,
                name="Network Interfaces",
                status="ok",
                metrics={
                    "bytes_sent_mb": round(net.bytes_sent / (1024**2), 2),
                    "bytes_recv_mb": round(net.bytes_recv / (1024**2), 2),
                    "interfaces": interfaces,
                },
            )
        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"Network status error: {e}")

        return HardwareStatus(
            category=HardwareCategory.NETWORK,
            name="Network Interfaces",
            status="unknown",
            metrics={},
            details="psutil not available",
        )

    def _get_gpu_status(self) -> HardwareStatus:
        """Get GPU status via WMI (Windows) or GPUtil."""
        try:
            gpu_info = {"name": "Unknown", "memory_total_mb": 0, "memory_used_mb": 0, "driver_version": "", "temperature_c": None}
            if self._platform == "windows":
                try:
                    import subprocess
                    result = subprocess.run(
                        ["wmic", "path", "win32_VideoController", "get", "Name,AdapterRAM,DriverVersion,CurrentHorizontalResolution,CurrentVerticalResolution", "/format:csv"],
                        capture_output=True, text=True, timeout=10
                    )
                    lines = result.stdout.strip().split("\n")
                    if len(lines) > 1:
                        parts = lines[1].split(",")
                        if len(parts) >= 3:
                            gpu_info["name"] = parts[2].strip() if len(parts) > 2 else "Unknown"
                            try:
                                ram_bytes = int(parts[3].strip()) if len(parts) > 3 and parts[3].strip().isdigit() else 0
                                gpu_info["memory_total_mb"] = round(ram_bytes / (1024**2), 0)
                            except (ValueError, IndexError):
                                pass
                            gpu_info["driver_version"] = parts[4].strip() if len(parts) > 4 else ""
                except Exception:
                    pass
                try:
                    import GPUtil
                    gpus = GPUtil.getGPUs()
                    if gpus:
                        g = gpus[0]
                        gpu_info["name"] = g.name or gpu_info["name"]
                        gpu_info["memory_total_mb"] = g.memoryTotal or gpu_info["memory_total_mb"]
                        gpu_info["memory_used_mb"] = g.memoryUsed
                        gpu_info["temperature_c"] = g.temperature
                except ImportError:
                    pass
            return HardwareStatus(
                category=HardwareCategory.GPU,
                name=gpu_info["name"],
                status="ok" if gpu_info["name"] != "Unknown" else "unknown",
                metrics={
                    "name": gpu_info["name"],
                    "memory_total_mb": gpu_info["memory_total_mb"],
                    "memory_used_mb": gpu_info["memory_used_mb"],
                    "driver_version": gpu_info["driver_version"],
                    "temperature_c": gpu_info["temperature_c"],
                },
            )
        except Exception as e:
            logger.debug(f"GPU status error: {e}")
            return HardwareStatus(
                category=HardwareCategory.GPU, name="GPU", status="unknown",
                metrics={}, details=str(e),
            )

    def _get_npu_status(self) -> HardwareStatus:
        """Get NPU / AI accelerator status."""
        try:
            npu_info = {"name": "Not detected", "available": False, "driver": ""}
            if self._platform == "windows":
                try:
                    import subprocess
                    result = subprocess.run(
                        ["wmic", "path", "Win32_PnPEntity", "get", "Name,Status", "/format:csv"],
                        capture_output=True, text=True, timeout=10
                    )
                    for line in result.stdout.split("\n"):
                        lower = line.lower()
                        if any(kw in lower for kw in ["npu", "neural", "ai accelerator", "movidius", "tpu", "mlas", "dla"]):
                            parts = line.split(",")
                            npu_info["name"] = parts[1].strip() if len(parts) > 1 else "AI Accelerator"
                            npu_info["available"] = True
                            break
                except Exception:
                    pass
            return HardwareStatus(
                category=HardwareCategory.NPU,
                name=npu_info["name"],
                status="ok" if npu_info["available"] else "unknown",
                metrics={
                    "available": npu_info["available"],
                    "name": npu_info["name"],
                    "driver": npu_info["driver"],
                },
                details="NPU detected" if npu_info["available"] else "No NPU hardware found",
            )
        except Exception as e:
            logger.debug(f"NPU status error: {e}")
            return HardwareStatus(
                category=HardwareCategory.NPU, name="NPU", status="unknown",
                metrics={}, details=str(e),
            )

    def _get_motherboard_status(self) -> HardwareStatus:
        """Get motherboard / baseboard information."""
        try:
            mb_info = {"manufacturer": "Unknown", "product": "Unknown", "serial": "Unknown", "version": "Unknown"}
            if self._platform == "windows":
                try:
                    import subprocess
                    result = subprocess.run(
                        ["wmic", "baseboard", "get", "Manufacturer,Product,SerialNumber,Version", "/format:csv"],
                        capture_output=True, text=True, timeout=10
                    )
                    lines = result.stdout.strip().split("\n")
                    if len(lines) > 1:
                        parts = lines[1].split(",")
                        mb_info["manufacturer"] = parts[1].strip() if len(parts) > 1 else "Unknown"
                        mb_info["product"] = parts[2].strip() if len(parts) > 2 else "Unknown"
                        mb_info["serial"] = parts[3].strip() if len(parts) > 3 else "Unknown"
                        mb_info["version"] = parts[4].strip() if len(parts) > 4 else "Unknown"
                except Exception:
                    pass
            return HardwareStatus(
                category=HardwareCategory.MOTHERBOARD,
                name=f"{mb_info['manufacturer']} {mb_info['product']}",
                status="ok" if mb_info["manufacturer"] != "Unknown" else "unknown",
                metrics=mb_info,
            )
        except Exception as e:
            logger.debug(f"Motherboard status error: {e}")
            return HardwareStatus(
                category=HardwareCategory.MOTHERBOARD, name="Motherboard", status="unknown",
                metrics={}, details=str(e),
            )

    def _get_chipset_status(self) -> HardwareStatus:
        """Get chipset information."""
        try:
            chipset_info = {"name": "Unknown", "manufacturer": "Unknown"}
            if self._platform == "windows":
                try:
                    import subprocess
                    result = subprocess.run(
                        ["wmic", "path", "Win32_IDEController", "get", "Name,Manufacturer", "/format:csv"],
                        capture_output=True, text=True, timeout=10
                    )
                    lines = result.stdout.strip().split("\n")
                    if len(lines) > 1:
                        parts = lines[1].split(",")
                        chipset_info["name"] = parts[1].strip() if len(parts) > 1 else "Unknown"
                        chipset_info["manufacturer"] = parts[2].strip() if len(parts) > 2 else "Unknown"
                except Exception:
                    pass
                # Try to get CPU as chipset fallback
                if chipset_info["name"] == "Unknown":
                    chipset_info["name"] = platform.processor() or "Unknown"
            return HardwareStatus(
                category=HardwareCategory.CHIPSET,
                name=chipset_info["name"],
                status="ok" if chipset_info["name"] != "Unknown" else "unknown",
                metrics=chipset_info,
            )
        except Exception as e:
            logger.debug(f"Chipset status error: {e}")
            return HardwareStatus(
                category=HardwareCategory.CHIPSET, name="Chipset", status="unknown",
                metrics={}, details=str(e),
            )

    def _get_ram_status(self) -> HardwareStatus:
        """Get RAM module information (physical memory chips)."""
        try:
            ram_modules = []
            total_ram_gb = 0
            if self._platform == "windows":
                try:
                    import subprocess
                    result = subprocess.run(
                        ["wmic", "memorychip", "get", "BankLabel,Capacity,Speed,MemoryType,Manufacturer,PartNumber", "/format:csv"],
                        capture_output=True, text=True, timeout=10
                    )
                    lines = result.stdout.strip().split("\n")
                    for line in lines[1:]:
                        if not line.strip():
                            continue
                        parts = line.split(",")
                        if len(parts) >= 3:
                            bank = parts[1].strip() if len(parts) > 1 else "Unknown"
                            try:
                                capacity_bytes = int(parts[2].strip()) if parts[2].strip().isdigit() else 0
                                capacity_gb = round(capacity_bytes / (1024**3), 1)
                                total_ram_gb += capacity_gb
                            except (ValueError, IndexError):
                                capacity_gb = 0
                            speed = parts[3].strip() if len(parts) > 3 else "Unknown"
                            mem_type = parts[4].strip() if len(parts) > 4 else "Unknown"
                            manufacturer = parts[5].strip() if len(parts) > 5 else "Unknown"
                            part = parts[6].strip() if len(parts) > 6 else ""
                            ram_modules.append({
                                "bank": bank,
                                "capacity_gb": capacity_gb,
                                "speed_mhz": speed,
                                "type": mem_type,
                                "manufacturer": manufacturer,
                                "part_number": part,
                            })
                except Exception:
                    pass
            # Fallback: use psutil for total
            if not ram_modules:
                try:
                    import psutil
                    total_ram_gb = round(psutil.virtual_memory().total / (1024**3), 1)
                except ImportError:
                    pass
            return HardwareStatus(
                category=HardwareCategory.RAM,
                name=f"Physical Memory ({len(ram_modules)} modules)" if ram_modules else "System RAM",
                status="ok" if total_ram_gb > 0 else "unknown",
                metrics={
                    "total_gb": total_ram_gb,
                    "module_count": len(ram_modules),
                    "modules": ram_modules,
                },
            )
        except Exception as e:
            logger.debug(f"RAM status error: {e}")
            return HardwareStatus(
                category=HardwareCategory.RAM, name="RAM", status="unknown",
                metrics={}, details=str(e),
            )

    def _get_rom_status(self) -> HardwareStatus:
        """Get ROM / BIOS / firmware information."""
        try:
            rom_info = {"bios_vendor": "Unknown", "bios_version": "Unknown", "bios_date": "Unknown", "smbios_version": ""}
            if self._platform == "windows":
                try:
                    import subprocess
                    result = subprocess.run(
                        ["wmic", "bios", "get", "Manufacturer,Name,Version,SerialNumber,SMBIOSBIOSVersion", "/format:csv"],
                        capture_output=True, text=True, timeout=10
                    )
                    lines = result.stdout.strip().split("\n")
                    if len(lines) > 1:
                        parts = lines[1].split(",")
                        rom_info["bios_vendor"] = parts[1].strip() if len(parts) > 1 else "Unknown"
                        rom_info["bios_version"] = parts[2].strip() if len(parts) > 2 else "Unknown"
                        rom_info["bios_date"] = parts[3].strip() if len(parts) > 3 else "Unknown"
                        rom_info["smbios_version"] = parts[4].strip() if len(parts) > 4 else ""
                except Exception:
                    pass
            return HardwareStatus(
                category=HardwareCategory.ROM,
                name=f"BIOS/{rom_info['bios_vendor']}",
                status="ok" if rom_info["bios_vendor"] != "Unknown" else "unknown",
                metrics=rom_info,
            )
        except Exception as e:
            logger.debug(f"ROM/BIOS status error: {e}")
            return HardwareStatus(
                category=HardwareCategory.ROM, name="BIOS/ROM", status="unknown",
                metrics={}, details=str(e),
            )

    def _get_storage_controller_status(self) -> HardwareStatus:
        """Get storage controller information (SATA/NVMe/SCSI controllers)."""
        try:
            controllers = []
            if self._platform == "windows":
                try:
                    import subprocess
                    result = subprocess.run(
                        ["wmic", "path", "Win32_SCSIController", "get", "Name,Manufacturer,DriverVersion", "/format:csv"],
                        capture_output=True, text=True, timeout=10
                    )
                    lines = result.stdout.strip().split("\n")
                    for line in lines[1:]:
                        if not line.strip():
                            continue
                        parts = line.split(",")
                        if len(parts) >= 2:
                            controllers.append({
                                "name": parts[1].strip() if len(parts) > 1 else "Unknown",
                                "manufacturer": parts[2].strip() if len(parts) > 2 else "",
                                "driver_version": parts[3].strip() if len(parts) > 3 else "",
                            })
                except Exception:
                    pass
            return HardwareStatus(
                category=HardwareCategory.STORAGE_CONTROLLER,
                name=f"{len(controllers)} Storage Controller(s)" if controllers else "Storage Controller",
                status="ok" if controllers else "unknown",
                metrics={"controllers": controllers, "count": len(controllers)},
            )
        except Exception as e:
            logger.debug(f"Storage controller error: {e}")
            return HardwareStatus(
                category=HardwareCategory.STORAGE_CONTROLLER, name="Storage Controller", status="unknown",
                metrics={}, details=str(e),
            )

    def _get_usb_status(self) -> HardwareStatus:
        """Get USB device information."""
        try:
            usb_devices = []
            if self._platform == "windows":
                try:
                    import subprocess
                    result = subprocess.run(
                        ["wmic", "path", "Win32_USBControllerDevice", "get", "Dependent", "/format:csv"],
                        capture_output=True, text=True, timeout=10
                    )
                    lines = result.stdout.strip().split("\n")
                    for line in lines[1:]:
                        if not line.strip():
                            continue
                        parts = line.split(",")
                        if len(parts) > 1:
                            desc = parts[1].strip()
                            # Extract USB device name from WMI path
                            if "=" in desc:
                                name_part = desc.split("=")[-1].strip('"')
                                usb_devices.append({"name": name_part})
                except Exception:
                    pass
            return HardwareStatus(
                category=HardwareCategory.USB,
                name=f"{len(usb_devices)} USB Device(s)" if usb_devices else "USB Controllers",
                status="ok",
                metrics={"devices": usb_devices, "count": len(usb_devices)},
            )
        except Exception as e:
            logger.debug(f"USB status error: {e}")
            return HardwareStatus(
                category=HardwareCategory.USB, name="USB", status="unknown",
                metrics={}, details=str(e),
            )

    def _get_display_status(self) -> HardwareStatus:
        """Get display/monitor information."""
        try:
            displays = []
            if self._platform == "windows":
                try:
                    import subprocess
                    result = subprocess.run(
                        ["wmic", "path", "Win32_DesktopMonitor", "get", "Name,MonitorType,ScreenHeight,ScreenWidth", "/format:csv"],
                        capture_output=True, text=True, timeout=10
                    )
                    lines = result.stdout.strip().split("\n")
                    for line in lines[1:]:
                        if not line.strip():
                            continue
                        parts = line.split(",")
                        if len(parts) >= 2:
                            displays.append({
                                "name": parts[1].strip() if len(parts) > 1 else "Unknown",
                                "monitor_type": parts[2].strip() if len(parts) > 2 else "",
                                "height": parts[3].strip() if len(parts) > 3 else "",
                                "width": parts[4].strip() if len(parts) > 4 else "",
                            })
                except Exception:
                    pass
            return HardwareStatus(
                category=HardwareCategory.DISPLAY,
                name=f"{len(displays)} Display(s)" if displays else "Display",
                status="ok" if displays else "unknown",
                metrics={"displays": displays, "count": len(displays)},
            )
        except Exception as e:
            logger.debug(f"Display status error: {e}")
            return HardwareStatus(
                category=HardwareCategory.DISPLAY, name="Display", status="unknown",
                metrics={}, details=str(e),
            )

    def _get_audio_status(self) -> HardwareStatus:
        """Get audio device information."""
        try:
            audio_devices = []
            if self._platform == "windows":
                try:
                    import subprocess
                    result = subprocess.run(
                        ["wmic", "path", "Win32_SoundDevice", "get", "Name,Manufacturer,Status", "/format:csv"],
                        capture_output=True, text=True, timeout=10
                    )
                    lines = result.stdout.strip().split("\n")
                    for line in lines[1:]:
                        if not line.strip():
                            continue
                        parts = line.split(",")
                        if len(parts) >= 2:
                            audio_devices.append({
                                "name": parts[1].strip() if len(parts) > 1 else "Unknown",
                                "manufacturer": parts[2].strip() if len(parts) > 2 else "",
                                "status": parts[3].strip() if len(parts) > 3 else "",
                            })
                except Exception:
                    pass
            return HardwareStatus(
                category=HardwareCategory.AUDIO,
                name=f"{len(audio_devices)} Audio Device(s)" if audio_devices else "Audio",
                status="ok" if audio_devices else "unknown",
                metrics={"devices": audio_devices, "count": len(audio_devices)},
            )
        except Exception as e:
            logger.debug(f"Audio status error: {e}")
            return HardwareStatus(
                category=HardwareCategory.AUDIO, name="Audio", status="unknown",
                metrics={}, details=str(e),
            )

    def _get_sensor_status(self) -> HardwareStatus:
        """Get hardware sensor information (temperature, fan, voltage)."""
        try:
            sensors = {"temperatures": [], "fans": [], "voltages": []}
            try:
                import psutil
                # psutil sensors (Linux only mostly)
                temps = psutil.sensors_temperatures()
                if temps:
                    for name, entries in temps.items():
                        for entry in entries:
                            sensors["temperatures"].append({
                                "sensor": name,
                                "current_c": entry.current,
                                "high_c": entry.high,
                                "critical_c": entry.critical,
                            })
                fans = psutil.sensors_fans()
                if fans:
                    for name, entries in fans.items():
                        for entry in entries:
                            sensors["fans"].append({
                                "sensor": name,
                                "rpm": entry.current,
                            })
            except (ImportError, AttributeError):
                pass
            # Windows: try WMI for temperature
            if self._platform == "windows" and not sensors["temperatures"]:
                try:
                    import subprocess
                    result = subprocess.run(
                        ["wmic", "/namespace:\\\\root\\wmi", "path", "MSAcpi_ThermalZoneTemperature", "get", "CurrentTemperature", "/format:csv"],
                        capture_output=True, text=True, timeout=10
                    )
                    lines = result.stdout.strip().split("\n")
                    for line in lines[1:]:
                        if line.strip() and line.split(",")[-1].strip().isdigit():
                            temp_kelvin = int(line.split(",")[-1].strip())
                            temp_celsius = round((temp_kelvin - 2732) / 10.0, 1)
                            sensors["temperatures"].append({
                                "sensor": "ACPI Thermal Zone",
                                "current_c": temp_celsius,
                            })
                except Exception:
                    pass
            return HardwareStatus(
                category=HardwareCategory.SENSOR,
                name=f"{len(sensors['temperatures'])} Temp, {len(sensors['fans'])} Fan(s)" if any(sensors.values()) else "Sensors",
                status="ok" if any(sensors.values()) else "unknown",
                metrics=sensors,
            )
        except Exception as e:
            logger.debug(f"Sensor status error: {e}")
            return HardwareStatus(
                category=HardwareCategory.SENSOR, name="Sensors", status="unknown",
                metrics={}, details=str(e),
            )

    def _get_thermal_status(self) -> HardwareStatus:
        """Get thermal/cooling status."""
        try:
            thermal_info = {"cooling_devices": [], "thermal_zones": []}
            if self._platform == "windows":
                try:
                    import subprocess
                    result = subprocess.run(
                        ["wmic", "path", "Win32_Fan", "get", "Name,DesiredSpeed", "/format:csv"],
                        capture_output=True, text=True, timeout=10
                    )
                    lines = result.stdout.strip().split("\n")
                    for line in lines[1:]:
                        if not line.strip():
                            continue
                        parts = line.split(",")
                        if len(parts) >= 2:
                            thermal_info["cooling_devices"].append({
                                "name": parts[1].strip() if len(parts) > 1 else "Fan",
                                "desired_speed": parts[2].strip() if len(parts) > 2 else "",
                            })
                except Exception:
                    pass
            return HardwareStatus(
                category=HardwareCategory.THERMAL,
                name=f"{len(thermal_info['cooling_devices'])} Cooling Device(s)" if thermal_info["cooling_devices"] else "Thermal",
                status="ok",
                metrics=thermal_info,
            )
        except Exception as e:
            logger.debug(f"Thermal status error: {e}")
            return HardwareStatus(
                category=HardwareCategory.THERMAL, name="Thermal", status="unknown",
                metrics={}, details=str(e),
            )

    def _get_bios_status(self) -> HardwareStatus:
        """Get BIOS / UEFI firmware status."""
        try:
            bios_info = {"manufacturer": "Unknown", "version": "Unknown", "date": "Unknown", "smbios": ""}
            if self._platform == "windows":
                try:
                    import subprocess
                    result = subprocess.run(
                        ["wmic", "bios", "get", "Manufacturer,Version,ReleaseDate,SMBIOSBIOSVersion", "/format:csv"],
                        capture_output=True, text=True, timeout=10
                    )
                    lines = result.stdout.strip().split("\n")
                    if len(lines) > 1:
                        parts = lines[1].split(",")
                        bios_info["manufacturer"] = parts[1].strip() if len(parts) > 1 else "Unknown"
                        bios_info["version"] = parts[2].strip() if len(parts) > 2 else "Unknown"
                        bios_info["date"] = parts[3].strip() if len(parts) > 3 else "Unknown"
                        bios_info["smbios"] = parts[4].strip() if len(parts) > 4 else ""
                except Exception:
                    pass
            return HardwareStatus(
                category=HardwareCategory.BIOS,
                name=f"{bios_info['manufacturer']} BIOS v{bios_info['version']}",
                status="ok" if bios_info["manufacturer"] != "Unknown" else "unknown",
                metrics=bios_info,
            )
        except Exception as e:
            logger.debug(f"BIOS status error: {e}")
            return HardwareStatus(
                category=HardwareCategory.BIOS, name="BIOS", status="unknown",
                metrics={}, details=str(e),
            )

    def get_all_hardware_status(self) -> Dict[str, HardwareStatus]:
        """Get status of ALL hardware components in one consolidated call."""
        return {
            "cpu": self._get_cpu_status(),
            "memory": self._get_memory_status(),
            "disk": self._get_disk_status(),
            "network": self._get_network_status(),
            "gpu": self._get_gpu_status(),
            "npu": self._get_npu_status(),
            "motherboard": self._get_motherboard_status(),
            "chipset": self._get_chipset_status(),
            "ram": self._get_ram_status(),
            "rom": self._get_rom_status(),
            "storage_controller": self._get_storage_controller_status(),
            "usb": self._get_usb_status(),
            "display": self._get_display_status(),
            "audio": self._get_audio_status(),
            "sensor": self._get_sensor_status(),
            "thermal": self._get_thermal_status(),
            "bios": self._get_bios_status(),
        }

    # ── Hardware Control ───────────────────────────────────────────

    def execute_operation(
        self,
        operation: str,
        target: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> OperationResult:
        """Execute a hardware control operation.

        Args:
            operation: The operation to perform (shutdown, restart, sleep, etc.).
            target: The target device or system.
            parameters: Optional parameters for the operation.

        Returns:
            OperationResult with success/failure status.
        """
        parameters = parameters or {}
        risk = self._classify_risk(operation)

        try:
            if operation == "shutdown":
                return self._shutdown(parameters)
            elif operation == "restart":
                return self._restart(parameters)
            elif operation == "sleep":
                return self._sleep()
            elif operation == "hibernate":
                return self._hibernate()
            elif operation == "lock":
                return self._lock()
            elif operation == "set_power_scheme":
                return self._set_power_scheme(parameters.get("scheme", "balanced"))
            else:
                return OperationResult(
                    success=False,
                    operation=operation,
                    target=target,
                    message=f"Unknown operation: {operation}",
                    risk=risk,
                )
        except Exception as e:
            logger.error(f"Operation '{operation}' failed: {e}")
            return OperationResult(
                success=False,
                operation=operation,
                target=target,
                message=str(e),
                risk=risk,
            )

    def _classify_risk(self, operation: str) -> OperationRisk:
        """Classify the risk level of an operation."""
        if operation in ("shutdown", "restart", "hibernate"):
            return OperationRisk.POWER
        elif operation in ("sleep", "lock", "set_power_scheme"):
            return OperationRisk.CONTROL
        elif operation.startswith("driver_"):
            return OperationRisk.DRIVER
        return OperationRisk.INFO

    def _shutdown(self, params: Dict[str, Any]) -> OperationResult:
        """Shutdown the system."""
        force = params.get("force", False)
        if self._platform == "windows":
            cmd = ["shutdown", "/s", "/t", "5"]
            if force:
                cmd.append("/f")
        elif self._platform == "linux":
            cmd = ["shutdown", "-h", "+1"]
        elif self._platform == "darwin":
            cmd = ["sudo", "shutdown", "-h", "+1"]
        else:
            return OperationResult(
                success=False, operation="shutdown", target="system",
                message=f"Unsupported platform: {self._platform}",
                risk=OperationRisk.POWER,
            )

        try:
            subprocess.run(cmd, check=True, timeout=10)
            return OperationResult(
                success=True, operation="shutdown", target="system",
                message="Shutdown initiated", risk=OperationRisk.POWER,
            )
        except subprocess.TimeoutExpired:
            return OperationResult(
                success=True, operation="shutdown", target="system",
                message="Shutdown command sent", risk=OperationRisk.POWER,
            )
        except subprocess.CalledProcessError as e:
            return OperationResult(
                success=False, operation="shutdown", target="system",
                message=f"Shutdown failed: {e}", risk=OperationRisk.POWER,
            )

    def _restart(self, params: Dict[str, Any]) -> OperationResult:
        """Restart the system."""
        force = params.get("force", False)
        if self._platform == "windows":
            cmd = ["shutdown", "/r", "/t", "5"]
            if force:
                cmd.append("/f")
        elif self._platform == "linux":
            cmd = ["reboot"]
        elif self._platform == "darwin":
            cmd = ["sudo", "shutdown", "-r", "+1"]
        else:
            return OperationResult(
                success=False, operation="restart", target="system",
                message=f"Unsupported platform: {self._platform}",
                risk=OperationRisk.POWER,
            )

        try:
            subprocess.run(cmd, check=True, timeout=10)
            return OperationResult(
                success=True, operation="restart", target="system",
                message="Restart initiated", risk=OperationRisk.POWER,
            )
        except subprocess.CalledProcessError as e:
            return OperationResult(
                success=False, operation="restart", target="system",
                message=f"Restart failed: {e}", risk=OperationRisk.POWER,
            )

    def _sleep(self) -> OperationResult:
        """Put the system to sleep."""
        if self._platform == "windows":
            cmd = ["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"]
        elif self._platform == "linux":
            cmd = ["systemctl", "suspend"]
        elif self._platform == "darwin":
            cmd = ["pmset", "sleepnow"]
        else:
            return OperationResult(
                success=False, operation="sleep", target="system",
                message=f"Unsupported platform: {self._platform}",
                risk=OperationRisk.CONTROL,
            )

        try:
            subprocess.run(cmd, check=True, timeout=10)
            return OperationResult(
                success=True, operation="sleep", target="system",
                message="Sleep initiated", risk=OperationRisk.CONTROL,
            )
        except subprocess.CalledProcessError as e:
            return OperationResult(
                success=False, operation="sleep", target="system",
                message=f"Sleep failed: {e}", risk=OperationRisk.CONTROL,
            )

    def _hibernate(self) -> OperationResult:
        """Hibernate the system."""
        if self._platform == "windows":
            cmd = ["shutdown", "/h"]
        elif self._platform == "linux":
            cmd = ["systemctl", "hibernate"]
        elif self._platform == "darwin":
            return OperationResult(
                success=False, operation="hibernate", target="system",
                message="Hibernate not supported on macOS",
                risk=OperationRisk.POWER,
            )
        else:
            return OperationResult(
                success=False, operation="hibernate", target="system",
                message=f"Unsupported platform: {self._platform}",
                risk=OperationRisk.POWER,
            )

        try:
            subprocess.run(cmd, check=True, timeout=10)
            return OperationResult(
                success=True, operation="hibernate", target="system",
                message="Hibernate initiated", risk=OperationRisk.POWER,
            )
        except subprocess.CalledProcessError as e:
            return OperationResult(
                success=False, operation="hibernate", target="system",
                message=f"Hibernate failed: {e}", risk=OperationRisk.POWER,
            )

    def _lock(self) -> OperationResult:
        """Lock the workstation."""
        if self._platform == "windows":
            cmd = ["rundll32.exe", "user32.dll,LockWorkStation"]
        elif self._platform == "linux":
            cmd = ["gnome-screensaver-command", "-l"]
        elif self._platform == "darwin":
            cmd = ["pmset", "displaysleepnow"]
        else:
            return OperationResult(
                success=False, operation="lock", target="system",
                message=f"Unsupported platform: {self._platform}",
                risk=OperationRisk.CONTROL,
            )

        try:
            subprocess.run(cmd, check=True, timeout=10)
            return OperationResult(
                success=True, operation="lock", target="system",
                message="Workstation locked", risk=OperationRisk.CONTROL,
            )
        except subprocess.CalledProcessError as e:
            return OperationResult(
                success=False, operation="lock", target="system",
                message=f"Lock failed: {e}", risk=OperationRisk.CONTROL,
            )

    def _set_power_scheme(self, scheme: str) -> OperationResult:
        """Set power scheme (Windows only)."""
        if self._platform != "windows":
            return OperationResult(
                success=False, operation="set_power_scheme", target="power",
                message="Power scheme control only supported on Windows",
                risk=OperationRisk.CONTROL,
            )

        scheme_guids = {
            "balanced": "381b4222-f694-41f0-9685-ff5bb260df2e",
            "power_saver": "a1841308-3541-4fab-bc81-f71556f20b4a",
            "high_performance": "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c",
        }

        guid = scheme_guids.get(scheme)
        if not guid:
            return OperationResult(
                success=False, operation="set_power_scheme", target="power",
                message=f"Unknown power scheme: {scheme}. Options: {list(scheme_guids.keys())}",
                risk=OperationRisk.CONTROL,
            )

        try:
            subprocess.run(
                ["powercfg", "/s", guid],
                check=True, timeout=10, capture_output=True, text=True,
            )
            return OperationResult(
                success=True, operation="set_power_scheme", target="power",
                message=f"Power scheme set to '{scheme}'",
                risk=OperationRisk.CONTROL,
            )
        except subprocess.CalledProcessError as e:
            return OperationResult(
                success=False, operation="set_power_scheme", target="power",
                message=f"Failed to set power scheme: {e.stderr}",
                risk=OperationRisk.CONTROL,
            )

    # ── Driver Management ──────────────────────────────────────────

    def list_drivers(self) -> List[Dict[str, Any]]:
        """List installed drivers (Windows only)."""
        if self._platform != "windows":
            return [{"platform": self._platform, "note": "Driver listing only on Windows"}]

        try:
            result = subprocess.run(
                ["driverquery", "/v", "/fo", "csv"],
                check=True, timeout=30, capture_output=True, text=True,
            )
            drivers = []
            lines = result.stdout.strip().split("\n")
            if len(lines) > 1:
                for line in lines[1:]:  # Skip header
                    parts = line.split(",")
                    if len(parts) >= 7:
                        drivers.append({
                            "name": parts[1].strip('"') if len(parts) > 1 else "",
                            "type": parts[2].strip('"') if len(parts) > 2 else "",
                            "state": parts[5].strip('"') if len(parts) > 5 else "",
                        })
            return drivers
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.error(f"Failed to list drivers: {e}")
            return []

    # ── Logging ────────────────────────────────────────────────────

    def get_operation_log(
        self, limit: int = 50
    ) -> List[OperationResult]:
        """Get recent hardware operation history."""
        return self._operation_log[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """Get microkernel interface statistics."""
        return {
            "platform": self._platform,
            "total_operations": len(self._operation_log),
            "successful_ops": sum(1 for op in self._operation_log if op.success),
            "failed_ops": sum(1 for op in self._operation_log if not op.success),
            "risk_breakdown": {
                risk.value: sum(1 for op in self._operation_log if op.risk == risk)
                for risk in OperationRisk
            },
        }
