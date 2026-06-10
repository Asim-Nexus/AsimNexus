#!/usr/bin/env python3
"""
STATUS: REAL — System scan script

Full System Scan for ASIMNEXUS
"""

import subprocess
import platform
import psutil
import json
from datetime import datetime
from pathlib import Path

def run_command(cmd):
    """Run a command and return output"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True, timeout=30)
        return result.stdout
    except:
        return "Error running command"

def get_system_info():
    """Get comprehensive system information"""
    report = []
    report.append("=" * 60)
    report.append("FULL SYSTEM SCAN REPORT")
    report.append("=" * 60)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    # System Overview
    report.append("## SYSTEM OVERVIEW")
    report.append(f"Platform: {platform.platform()}")
    report.append(f"Processor: {platform.processor()}")
    report.append(f"Machine: {platform.machine()}")
    report.append(f"Node: {platform.node()}")
    report.append(f"Python Version: {platform.python_version()}")
    report.append("")
    
    # CPU Info
    report.append("## CPU INFORMATION")
    report.append(f"Physical Cores: {psutil.cpu_count(logical=False)}")
    report.append(f"Logical Cores: {psutil.cpu_count(logical=True)}")
    report.append(f"Current CPU Usage: {psutil.cpu_percent()}%")
    report.append(f"CPU Frequency: {psutil.cpu_freq().current if psutil.cpu_freq() else 'N/A'} MHz")
    report.append("")
    
    # Memory Info
    report.append("## MEMORY INFORMATION")
    mem = psutil.virtual_memory()
    report.append(f"Total RAM: {mem.total / (1024**3):.2f} GB")
    report.append(f"Available RAM: {mem.available / (1024**3):.2f} GB")
    report.append(f"Used RAM: {mem.used / (1024**3):.2f} GB ({mem.percent}%)")
    report.append(f"Free RAM: {mem.free / (1024**3):.2f} GB")
    report.append("")
    
    # Disk Info
    report.append("## DISK INFORMATION")
    for partition in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            report.append(f"Drive {partition.device} ({partition.fstype})")
            report.append(f"  Mount: {partition.mountpoint}")
            report.append(f"  Total: {usage.total / (1024**3):.2f} GB")
            report.append(f"  Used: {usage.used / (1024**3):.2f} GB ({usage.percent}%)")
            report.append(f"  Free: {usage.free / (1024**3):.2f} GB")
        except:
            pass
    report.append("")
    
    # GPU Info (NVIDIA)
    report.append("## GPU INFORMATION")
    nvidia_smi = run_command("nvidia-smi --query-gpu=name,memory.total,driver_version,temperature.gpu,utilization.gpu --format=csv,noheader")
    if nvidia_smi and "NVIDIA" in nvidia_smi:
        for line in nvidia_smi.strip().split('\n'):
            if line.strip():
                parts = line.split(', ')
                if len(parts) >= 3:
                    report.append(f"GPU: {parts[0]}")
                    report.append(f"  Memory: {parts[1]}")
                    report.append(f"  Driver: {parts[2]}")
                    if len(parts) >= 4:
                        report.append(f"  Temperature: {parts[3]}")
                    if len(parts) >= 5:
                        report.append(f"  Utilization: {parts[4]}")
    else:
        report.append("NVIDIA GPU not detected or nvidia-smi not available")
    report.append("")
    
    # Network Info
    report.append("## NETWORK INFORMATION")
    net_io = psutil.net_io_counters()
    report.append(f"Bytes Sent: {net_io.bytes_sent / (1024**2):.2f} MB")
    report.append(f"Bytes Received: {net_io.bytes_recv / (1024**2):.2f} MB")
    report.append(f"Packets Sent: {net_io.packets_sent}")
    report.append(f"Packets Received: {net_io.packets_recv}")
    report.append("")
    
    # Network Interfaces
    report.append("## NETWORK INTERFACES")
    for name, addresses in psutil.net_if_addrs().items():
        for addr in addresses:
            if addr.family == 2:  # IPv4
                report.append(f"{name}: {addr.address}")
    report.append("")
    
    # Running Processes (Top 20 by memory)
    report.append("## TOP 20 PROCESSES BY MEMORY")
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent']):
        try:
            pinfo = proc.info
            processes.append(pinfo)
        except:
            pass
    
    processes.sort(key=lambda x: x['memory_info'].rss if x['memory_info'] else 0, reverse=True)
    for proc in processes[:20]:
        mem_mb = proc['memory_info'].rss / (1024**2) if proc['memory_info'] else 0
        report.append(f"{proc['name'][:30]:30} PID:{proc['pid']:6} {mem_mb:8.1f} MB")
    report.append("")
    
    # Installed Software (Windows)
    report.append("## INSTALLED SOFTWARE (First 50)")
    try:
        result = run_command('wmic product get Name,Version /format:csv')
        lines = result.strip().split('\n')[2:]  # Skip header
        for line in lines[:50]:
            if line.strip() and ',' in line:
                parts = line.split(',')
                if len(parts) >= 2:
                    report.append(f"{parts[1]} {parts[2] if len(parts) > 2 else ''}")
    except:
        report.append("Unable to retrieve installed software list")
    report.append("")
    
    # Services (Running)
    report.append("## RUNNING SERVICES (First 20)")
    try:
        result = run_command('sc query state= running')
        lines = result.split('\n')
        count = 0
        for line in lines:
            if 'SERVICE_NAME:' in line and count < 20:
                service_name = line.split(':')[1].strip()
                report.append(service_name)
                count += 1
    except:
        report.append("Unable to retrieve services list")
    report.append("")
    
    # Environment Variables
    report.append("## KEY ENVIRONMENT VARIABLES")
    import os
    report.append(f"PATH entries: {len(os.environ.get('PATH', '').split(';'))}")
    report.append(f"USERNAME: {os.environ.get('USERNAME', 'N/A')}")
    report.append(f"COMPUTERNAME: {os.environ.get('COMPUTERNAME', 'N/A')}")
    report.append(f"SystemRoot: {os.environ.get('SystemRoot', 'N/A')}")
    report.append(f"ProgramFiles: {os.environ.get('ProgramFiles', 'N/A')}")
    report.append("")
    
    # Python Packages
    report.append("## INSTALLED PYTHON PACKAGES (First 30)")
    try:
        import pkg_resources
        installed_packages = [(d.project_name, d.version) for d in pkg_resources.working_set]
        installed_packages.sort()
        for package, version in installed_packages[:30]:
            report.append(f"{package}=={version}")
    except:
        report.append("Unable to retrieve Python packages")
    report.append("")
    
    report.append("=" * 60)
    report.append("END OF SCAN")
    report.append("=" * 60)
    
    return '\n'.join(report)

if __name__ == "__main__":
    print("Starting full system scan...")
    report = get_system_info()
    
    # Save to file
    output_path = Path("c:/AsimNexus/full_system_scan_report.txt")
    output_path.write_text(report, encoding='utf-8')
    
    print(f"Scan complete! Report saved to: {output_path}")
    print("\n--- SCAN SUMMARY ---")
    print(report[:2000] + "\n... [truncated for display] ...")
