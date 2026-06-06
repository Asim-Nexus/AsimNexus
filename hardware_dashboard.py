
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

import psutil
import time
import json

def monitor_hardware():
    """Monitor RTX 2060 and system"""
    while True:
        stats = {
            "timestamp": time.time(),
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "gpu_load": "N/A (Needs nvidia-ml-py)",
            "temperature": "N/A (Needs monitoring)"
        }
        print(f"🖥️ CPU: {stats["cpu_percent"]:.1f}% | RAM: {stats["memory_percent"]:.1f}%")
        time.sleep(1)

if __name__ == "__main__":
    monitor_hardware()
