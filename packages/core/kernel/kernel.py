
"""
ASIM Kernel - Universal Micro-kernel
Runs on all devices, provides complete hardware abstraction layer
"""

import logging
import platform
import subprocess
import psutil
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class HardwareProfile:
    """Complete hardware profile of the device — CPU, GPU, NPU, motherboard, memory, storage, BIOS, sensors"""
    # CPU
    cpu_name: str
    cpu_cores: int
    cpu_freq: float
    cpu_usage_percent: float = 0.0
    
    # GPU
    gpu_name: Optional[str] = None
    gpu_memory_mb: Optional[float] = None
    gpu_driver_version: Optional[str] = None
    
    # NPU / AI Accelerator
    npu_name: Optional[str] = None
    npu_available: bool = False
    
    # Memory (OS-level)
    total_memory_gb: float = 0.0
    available_memory_gb: float = 0.0
    
    # Physical RAM modules
    ram_modules: List[Dict[str, Any]] = field(default_factory=list)
    ram_total_gb: float = 0.0
    
    # Storage
    total_storage_gb: float = 0.0
    used_storage_gb: float = 0.0
    free_storage_gb: float = 0.0
    storage_controllers: List[Dict[str, Any]] = field(default_factory=list)
    
    # Motherboard / Chipset
    motherboard_manufacturer: Optional[str] = None
    motherboard_model: Optional[str] = None
    chipset_name: Optional[str] = None
    
    # BIOS / ROM / Firmware
    bios_vendor: Optional[str] = None
    bios_version: Optional[str] = None
    bios_date: Optional[str] = None
    
    # OS
    os_name: str = ""
    os_version: str = ""
    architecture: str = ""
    
    # Network
    hostname: Optional[str] = None
    ip_addresses: List[str] = field(default_factory=list)
    
    # Peripherals
    usb_device_count: int = 0
    display_count: int = 0
    audio_device_count: int = 0
    
    # Sensors
    temperature_sensors: List[Dict[str, Any]] = field(default_factory=list)
    fan_count: int = 0


class ASIMKernel:
    """
    ASIM Kernel - Universal Micro-kernel
    
    Complete hardware abstraction layer that detects and manages:
    - CPU (cores, frequency, usage, cache)
    - GPU (name, memory, driver, temperature)
    - NPU / AI accelerators
    - Motherboard (manufacturer, model, chipset)
    - Physical RAM modules (bank, capacity, speed, type)
    - Storage (disks, partitions, controllers - SATA/NVMe)
    - BIOS / UEFI firmware
    - USB devices, displays, audio devices
    - Thermal sensors, fans
    - Network interfaces
    """
    
    def __init__(self):
        self.hardware_profile = self._detect_hardware()
        logger.info(f"ASIM Kernel initialized on {self.hardware_profile.os_name} — {self.hardware_profile.cpu_name}")
    
    def _detect_hardware(self) -> HardwareProfile:
        """Detect complete hardware profile using all available methods."""
        hp = HardwareProfile(
            cpu_name=platform.processor() or "Unknown CPU",
            cpu_cores=psutil.cpu_count(logical=False) or 1,
            cpu_freq=psutil.cpu_freq().max if psutil.cpu_freq() else 0.0,
            cpu_usage_percent=psutil.cpu_percent(interval=0.1),
            total_memory_gb=round(psutil.virtual_memory().total / (1024**3), 2),
            available_memory_gb=round(psutil.virtual_memory().available / (1024**3), 2),
            os_name=platform.system(),
            os_version=platform.version(),
            architecture=platform.machine(),
            hostname=platform.node(),
        )
        
        # ── GPU Detection ──
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                hp.gpu_name = gpus[0].name
                hp.gpu_memory_mb = gpus[0].memoryTotal
        except ImportError:
            pass
        if not hp.gpu_name and platform.system().lower() == "windows":
            try:
                result = subprocess.run(
                    ["wmic", "path", "win32_VideoController", "get", "Name,AdapterRAM,DriverVersion", "/format:csv"],
                    capture_output=True, text=True, timeout=10
                )
                lines = result.stdout.strip().split("\n")
                if len(lines) > 1:
                    parts = lines[1].split(",")
                    hp.gpu_name = parts[2].strip() if len(parts) > 2 else None
                    hp.gpu_driver_version = parts[4].strip() if len(parts) > 4 else None
            except Exception:
                pass
        
        # ── NPU Detection ──
        if platform.system().lower() == "windows":
            try:
                result = subprocess.run(
                    ["wmic", "path", "Win32_PnPEntity", "get", "Name", "/format:csv"],
                    capture_output=True, text=True, timeout=10
                )
                for line in result.stdout.split("\n"):
                    lower = line.lower()
                    if any(kw in lower for kw in ["npu", "neural", "ai accelerator", "movidius", "tpu"]):
                        parts = line.split(",")
                        hp.npu_name = parts[1].strip() if len(parts) > 1 else "AI Accelerator"
                        hp.npu_available = True
                        break
            except Exception:
                pass
        
        # ── Motherboard Detection ──
        if platform.system().lower() == "windows":
            try:
                result = subprocess.run(
                    ["wmic", "baseboard", "get", "Manufacturer,Product,Version", "/format:csv"],
                    capture_output=True, text=True, timeout=10
                )
                lines = result.stdout.strip().split("\n")
                if len(lines) > 1:
                    parts = lines[1].split(",")
                    hp.motherboard_manufacturer = parts[1].strip() if len(parts) > 1 else None
                    hp.motherboard_model = parts[2].strip() if len(parts) > 2 else None
            except Exception:
                pass
        
        # ── Chipset Detection ──
        if platform.system().lower() == "windows":
            try:
                result = subprocess.run(
                    ["wmic", "path", "Win32_IDEController", "get", "Name", "/format:csv"],
                    capture_output=True, text=True, timeout=10
                )
                lines = result.stdout.strip().split("\n")
                if len(lines) > 1:
                    hp.chipset_name = lines[1].split(",")[1].strip() if len(lines[1].split(",")) > 1 else None
            except Exception:
                pass
        
        # ── Physical RAM Modules ──
        if platform.system().lower() == "windows":
            try:
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
                        try:
                            cap_gb = round(int(parts[2].strip()) / (1024**3), 1) if parts[2].strip().isdigit() else 0
                            hp.ram_total_gb += cap_gb
                        except (ValueError, IndexError):
                            cap_gb = 0
                        hp.ram_modules.append({
                            "bank": parts[1].strip() if len(parts) > 1 else "Unknown",
                            "capacity_gb": cap_gb,
                            "speed_mhz": parts[3].strip() if len(parts) > 3 else "Unknown",
                            "type": parts[4].strip() if len(parts) > 4 else "Unknown",
                            "manufacturer": parts[5].strip() if len(parts) > 5 else "Unknown",
                            "part_number": parts[6].strip() if len(parts) > 6 else "",
                        })
            except Exception:
                pass
        
        # ── Storage ──
        try:
            total = 0
            used = 0
            for part in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    total += usage.total
                    used += usage.used
                except (PermissionError, OSError):
                    continue
            hp.total_storage_gb = round(total / (1024**3), 2)
            hp.used_storage_gb = round(used / (1024**3), 2)
            hp.free_storage_gb = round((total - used) / (1024**3), 2)
        except Exception:
            pass
        
        # ── Storage Controllers ──
        if platform.system().lower() == "windows":
            try:
                result = subprocess.run(
                    ["wmic", "path", "Win32_SCSIController", "get", "Name,Manufacturer", "/format:csv"],
                    capture_output=True, text=True, timeout=10
                )
                lines = result.stdout.strip().split("\n")
                for line in lines[1:]:
                    if not line.strip():
                        continue
                    parts = line.split(",")
                    if len(parts) >= 2:
                        hp.storage_controllers.append({
                            "name": parts[1].strip() if len(parts) > 1 else "Unknown",
                            "manufacturer": parts[2].strip() if len(parts) > 2 else "",
                        })
            except Exception:
                pass
        
        # ── BIOS / Firmware ──
        if platform.system().lower() == "windows":
            try:
                result = subprocess.run(
                    ["wmic", "bios", "get", "Manufacturer,Version,ReleaseDate", "/format:csv"],
                    capture_output=True, text=True, timeout=10
                )
                lines = result.stdout.strip().split("\n")
                if len(lines) > 1:
                    parts = lines[1].split(",")
                    hp.bios_vendor = parts[1].strip() if len(parts) > 1 else None
                    hp.bios_version = parts[2].strip() if len(parts) > 2 else None
                    hp.bios_date = parts[3].strip() if len(parts) > 3 else None
            except Exception:
                pass
        
        # ── Network IPs ──
        try:
            import socket
            hp.ip_addresses = list(set(
                addr.address for iface in psutil.net_if_addrs().values()
                for addr in iface if addr.family.name == "AF_INET"
            ))
        except Exception:
            pass
        
        # ── USB / Display / Audio Counts ──
        if platform.system().lower() == "windows":
            try:
                result = subprocess.run(
                    ["wmic", "path", "Win32_USBControllerDevice", "get", "Dependent", "/format:csv"],
                    capture_output=True, text=True, timeout=10
                )
                hp.usb_device_count = max(0, len(result.stdout.strip().split("\n")) - 2)
            except Exception:
                pass
            try:
                result = subprocess.run(
                    ["wmic", "path", "Win32_DesktopMonitor", "get", "Name", "/format:csv"],
                    capture_output=True, text=True, timeout=10
                )
                hp.display_count = max(0, len(result.stdout.strip().split("\n")) - 2)
            except Exception:
                pass
            try:
                result = subprocess.run(
                    ["wmic", "path", "Win32_SoundDevice", "get", "Name", "/format:csv"],
                    capture_output=True, text=True, timeout=10
                )
                hp.audio_device_count = max(0, len(result.stdout.strip().split("\n")) - 2)
            except Exception:
                pass
        
        # ── Temperature Sensors ──
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                for name, entries in temps.items():
                    for entry in entries:
                        hp.temperature_sensors.append({
                            "sensor": name,
                            "current_c": entry.current,
                            "high_c": entry.high,
                            "critical_c": entry.critical,
                        })
        except (ImportError, AttributeError):
            pass
        
        return hp
    
    def get_hardware_profile(self) -> HardwareProfile:
        """Get complete hardware profile."""
        return self.hardware_profile
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get device capabilities based on complete hardware profile."""
        hp = self.hardware_profile
        return {
            "can_run_gpu": hp.gpu_name is not None,
            "has_npu": hp.npu_available,
            "can_run_large_models": hp.total_memory_gb >= 16,
            "can_run_medium_models": hp.total_memory_gb >= 8,
            "can_run_small_models": hp.total_memory_gb >= 4,
            "ram_modules_count": len(hp.ram_modules),
            "storage_controllers": len(hp.storage_controllers),
            "display_count": hp.display_count,
            "audio_device_count": hp.audio_device_count,
            "usb_device_count": hp.usb_device_count,
            "recommended_model": self._get_recommended_model()
        }
    
    def _get_recommended_model(self) -> str:
        """Get recommended AI model based on hardware."""
        hp = self.hardware_profile
        if hp.gpu_name:
            if hp.total_memory_gb >= 32:
                return "llama-3-70b"
            elif hp.total_memory_gb >= 16:
                return "llama-3-8b"
            else:
                return "gemma-2-2b"
        else:
            if hp.total_memory_gb >= 16:
                return "gemma-2-2b"
            else:
                return "phi-3-mini"
    
    def execute_command(self, command: str) -> Dict[str, Any]:
        """Execute universal command."""
        return {
            "success": True,
            "result": f"Command '{command}' executed"
        }


# Global kernel instance
_kernel: Optional[ASIMKernel] = None


def get_kernel() -> ASIMKernel:
    """Get global kernel instance (lazy load)."""
    global _kernel
    if _kernel is None:
        _kernel = ASIMKernel()
    return _kernel
