
"""
STATUS: CONCEPT — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Process Tools
Safe process and application management with OpenClaw-style security
"""

import os
import sys
import time
import logging
import psutil
import subprocess
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

try:
    import pywinauto
    import pyautogui
    import pynput
    AUTOMATION_AVAILABLE = True
except ImportError:
    AUTOMATION_AVAILABLE = False

@dataclass
class ProcessInfo:
    """Process information structure"""
    pid: int
    name: str
    cpu_percent: float
    memory_percent: float
    status: str
    create_time: float
    exe_path: Optional[str] = None
    cmdline: Optional[List[str]] = None

class ProcessTools:
    """Safe process management tools for ASIMNEXUS"""
    
    def __init__(self):
        self.logger = logging.getLogger("ProcessTools")
        self.automation_available = AUTOMATION_AVAILABLE
        self.safe_processes = {
            'notepad.exe', 'calc.exe', 'mspaint.exe', 'explorer.exe',
            'chrome.exe', 'firefox.exe', 'code.exe', 'python.exe'
        }
        self.dangerous_processes = {
            'system.exe', 'csrss.exe', 'winlogon.exe', 'lsass.exe',
            'services.exe', 'svchost.exe'
        }
    
    def list_processes(self, filter_name: str = None) -> List[ProcessInfo]:
        """List running processes with safety filtering"""
        processes = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 
                                           'status', 'create_time', 'exe', 'cmdline']):
                try:
                    proc_info = proc.info
                    
                    # Apply filter if specified
                    if filter_name and filter_name.lower() not in proc_info['name'].lower():
                        continue
                    
                    process = ProcessInfo(
                        pid=proc_info['pid'],
                        name=proc_info['name'],
                        cpu_percent=proc_info['cpu_percent'] or 0.0,
                        memory_percent=proc_info['memory_percent'] or 0.0,
                        status=proc_info['status'],
                        create_time=proc_info['create_time'],
                        exe_path=proc_info['exe'],
                        cmdline=proc_info['cmdline']
                    )
                    processes.append(process)
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
        except Exception as e:
            self.logger.error(f"Failed to list processes: {e}")
        
        return processes
    
    def get_process_by_name(self, name: str) -> Optional[ProcessInfo]:
        """Get process by name"""
        processes = self.list_processes(filter_name=name)
        return processes[0] if processes else None
    
    def is_safe_to_manage(self, process: ProcessInfo) -> Tuple[bool, str]:
        """Check if process is safe to manage"""
        # Check dangerous processes
        if process.name.lower() in self.dangerous_processes:
            return False, f"Process {process.name} is critical system process"
        
        # Check if process is owned by current user
        try:
            current_user = os.getlogin()
            proc_owner = psutil.Process(process.pid).username()
            if current_user not in proc_owner:
                return False, f"Process {process.name} owned by different user: {proc_owner}"
        except Exception as e:
            self.logger.debug(f"Cannot verify process ownership: {e}")
            return False, f"Cannot verify process {process.name} ownership"
        
        return True, "Process is safe to manage"
    
    def focus_window(self, window_title: str) -> bool:
        """Focus specific window (safe automation)"""
        if not self.automation_available:
            self.logger.warning("Automation libraries not available")
            return False
        
        try:
            import pywinauto
            app = pywinauto.Desktop(backend="uia")
            
            # Find window by title
            windows = []
            for window in app.windows():
                if window_title.lower() in window.window_text().lower():
                    windows.append(window)
            
            if windows:
                windows[0].set_focus()
                self.logger.info(f"Focused window: {window_title}")
                return True
            else:
                self.logger.warning(f"Window not found: {window_title}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to focus window {window_title}: {e}")
            return False
    
    def close_application(self, app_name: str, force: bool = False) -> bool:
        """Safely close application"""
        processes = self.list_processes(filter_name=app_name)
        
        if not processes:
            self.logger.warning(f"No process found for: {app_name}")
            return False
        
        success = True
        for process in processes:
            safe, reason = self.is_safe_to_manage(process)
            if not safe:
                self.logger.warning(f"Cannot close {process.name}: {reason}")
                success = False
                continue
            
            try:
                proc = psutil.Process(process.pid)
                
                if force:
                    proc.kill()
                    self.logger.info(f"Force killed process: {process.name} (PID: {process.pid})")
                else:
                    proc.terminate()
                    proc.wait(timeout=5)
                    self.logger.info(f"Terminated process: {process.name} (PID: {process.pid})")
                    
            except psutil.NoSuchProcess:
                self.logger.info(f"Process already terminated: {process.name}")
            except psutil.TimeoutExpired:
                self.logger.warning(f"Process {process.name} did not terminate gracefully")
                if not force:
                    # Try force kill
                    try:
                        proc.kill()
                        self.logger.info(f"Force killed process: {process.name}")
                    except Exception as e:
                        self.logger.debug(f"Force kill failed: {e}")
                        success = False
            except Exception as e:
                self.logger.error(f"Failed to close process {process.name}: {e}")
                success = False
        
        return success
    
    def start_application(self, app_path: str, arguments: List[str] = None) -> bool:
        """Start application safely"""
        try:
            # Validate path
            if not os.path.exists(app_path):
                self.logger.error(f"Application path not found: {app_path}")
                return False
            
            # Check if it's executable
            if not app_path.lower().endswith(('.exe', '.bat', '.cmd')):
                self.logger.warning(f"File may not be executable: {app_path}")
            
            # Build command
            cmd = [app_path]
            if arguments:
                cmd.extend(arguments)
            
            # Start process
            subprocess.Popen(cmd, shell=False)
            self.logger.info(f"Started application: {app_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start application {app_path}: {e}")
            return False
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system process information"""
        try:
            # Process counts by status
            process_counts = {}
            total_cpu = 0
            total_memory = 0
            
            for proc in psutil.process_iter(['status', 'cpu_percent', 'memory_percent']):
                try:
                    status = proc.info['status']
                    process_counts[status] = process_counts.get(status, 0) + 1
                    total_cpu += proc.info['cpu_percent'] or 0
                    total_memory += proc.info['memory_percent'] or 0
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return {
                "total_processes": sum(process_counts.values()),
                "process_counts": process_counts,
                "total_cpu_usage": total_cpu,
                "total_memory_usage": total_memory,
                "automation_available": self.automation_available
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get system info: {e}")
            return {}
    
    def safe_automation_check(self) -> Tuple[bool, str]:
        """Check if safe automation is available"""
        if not self.automation_available:
            return False, "Automation libraries not installed. Install with: pip install pywinauto pyautogui pynput"
        
        # Test basic automation
        try:
            current_pos = pyautogui.position()
            return True, "Automation system ready"
        except Exception as e:
            return False, f"Automation system error: {e}"
    
    def record_simple_macro(self, name: str, duration_seconds: int = 10) -> bool:
        """Record simple mouse/keyboard macro (future enhancement)"""
        if not self.automation_available:
            self.logger.warning("Automation not available")
            return False
        
        # This would implement macro recording
        # For now, just log the request
        self.logger.info(f"Macro recording requested: {name} ({duration_seconds}s)")
        return True
    
    def play_simple_macro(self, name: str) -> bool:
        """Play recorded macro (future enhancement)"""
        if not self.automation_available:
            self.logger.warning("Automation not available")
            return False
        
        # This would implement macro playback
        self.logger.info(f"Macro playback requested: {name}")
        return True

# Global process tools instance
process_tools = ProcessTools()
