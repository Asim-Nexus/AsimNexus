"""
STATUS: REAL — Core Kernel API Endpoints

AsimNexus Core Kernel API
==========================
System introspection endpoints:
- Hardware Detection
- OS Detection
- System Health
"""

import logging
import platform
import time
from typing import Dict, Any
from fastapi import APIRouter

logger = logging.getLogger("AsimNexus.CoreKernelAPI")

router = APIRouter(prefix="/api/core", tags=["Core System"])


@router.get("/hardware/status")
async def get_hardware_status() -> Dict[str, Any]:
    """Get hardware detection status"""
    try:
        import psutil
        
        cpu = {
            "cores": psutil.cpu_count(logical=False),
            "threads": psutil.cpu_count(logical=True),
            "usage_percent": psutil.cpu_percent(),
            "architecture": platform.machine()
        }
        
        mem = psutil.virtual_memory()
        memory = {
            "total_gb": round(mem.total / (1024**3), 2),
            "available_gb": round(mem.available / (1024**3), 2),
            "used_percent": mem.percent
        }
        
        storage = []
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
                storage.append({
                    "device": part.device,
                    "total_gb": round(usage.total / (1024**3), 2)
                })
            except Exception:
                pass
        
        return {
            "cpu": cpu,
            "memory": memory,
            "storage": storage,
            "initialized": True,
            "timestamp": time.time()
        }
    except Exception as e:
        return {"error": str(e), "initialized": False}


@router.get("/os/status")
async def get_os_status() -> Dict[str, Any]:
    """Get OS detection status"""
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "initialized": True
    }


@router.get("/status")
async def get_core_status() -> Dict[str, Any]:
    """Get overall core system status"""
    return {
        "platform": "AsimNexus Core Kernel",
        "version": "2.0.0",
        "hardware_available": True,
        "os_detected": platform.system(),
        "modules": ["hardware", "os", "network"],
        "timestamp": time.time()
    }