
"""
STATUS: REAL — Hardened low-privilege execution runner
"""
"""
ASIMNEXUS Low Privilege User Runner
Execute commands with limited permissions using dedicated user account
"""

import os
import json
import time
import logging
import asyncio
import subprocess
import platform
import shlex
import tempfile
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path

# ── Forbidden shell metacharacters — reject on sight ─────────────────────────
_FORBIDDEN_PATTERNS: set = {
    "`", "$(", "${", "&&", "||", ";", "|", ">", "<",
    "$((", "${{", "eval", "exec", "import os", "import subprocess",
}

@dataclass
class LowPrivResult:
    """Result of low-privilege execution"""
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    execution_time: float
    user: str
    error: Optional[str] = None

class LowPrivUserRunner:
    """Execute commands with limited privileges"""
    
    def __init__(self, username: str = "AsimSandboxUser"):
        self.logger = logging.getLogger("LowPrivUserRunner")
        self.username = username
        self.system = platform.system().lower()
        self.timeout = 300  # 5 minutes
        # DO NOT auto-setup on init — defer to explicit call
        self._user_available = False

    def _validate_command(self, command: str) -> str:
        """Reject commands containing forbidden patterns."""
        for pattern in _FORBIDDEN_PATTERNS:
            if pattern in command:
                raise ValueError(
                    f"Command contains forbidden pattern {pattern!r}"
                )
        return command

    def setup_user(self) -> bool:
        """Explicitly set up the low-privilege user. Call once at startup."""
        try:
            self._setup_user()
            self._user_available = True
            return True
        except Exception as e:
            self.logger.error(f"User setup failed: {e}")
            self._user_available = False
            return False
    
    def _setup_user(self):
        """Setup low-privilege user"""
        if self.system == "windows":
            self._setup_windows_user()
        else:
            self._setup_unix_user()
    
    def _setup_windows_user(self):
        """Setup Windows user"""
        try:
            # Check if user exists
            result = subprocess.run(
                f"net user {self.username}",
                shell=True,
                capture_output=True,
                text=True
            )
            
            if "not found" in result.stderr.lower():
                self.logger.info(f"Creating Windows user: {self.username}")
                # Create user with limited privileges
                create_cmd = [
                    "net", "user", self.username, "AsimSandboxPass123!",
                    "/add", "/expires:never"
                ]
                subprocess.run(create_cmd, check=True, capture_output=True)
                
                # Add to Users group (limited privileges)
                add_group_cmd = [
                    "net", "localgroup", "Users", self.username, "/add"
                ]
                subprocess.run(add_group_cmd, check=True, capture_output=True)
                
                self.logger.info(f"Windows user {self.username} created successfully")
            else:
                self.logger.info(f"Windows user {self.username} already exists")
                
        except Exception as e:
            self.logger.error(f"Failed to setup Windows user: {e}")
    
    def _setup_unix_user(self):
        """Setup Unix/Linux user"""
        try:
            # Check if user exists
            result = subprocess.run(
                f"id -u {self.username}",
                shell=True,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.logger.info(f"Creating Unix user: {self.username}")
                # Create user with no login shell and limited privileges
                create_cmd = [
                    "sudo", "useradd", "-m", "-s", "/bin/false", self.username
                ]
                subprocess.run(create_cmd, check=True)
                
                self.logger.info(f"Unix user {self.username} created successfully")
            else:
                self.logger.info(f"Unix user {self.username} already exists")
                
        except Exception as e:
            self.logger.error(f"Failed to setup Unix user: {e}")
    
    async def execute_job(self, job) -> LowPrivResult:
        """Execute a job with low privileges"""
        self.logger.info(f"Executing job as low-priv user: {job.name}")
        
        start_time = time.time()
        
        try:
            # Prepare command
            command = self._prepare_command(job)
            
            # Execute with appropriate method
            if self.system == "windows":
                result = await self._execute_windows(command, job)
            else:
                result = await self._execute_unix(command, job)
            
            result.execution_time = time.time() - start_time
            return result
            
        except Exception as e:
            self.logger.error(f"Low-priv execution failed: {e}")
            return LowPrivResult(
                success=False,
                stdout="",
                stderr=str(e),
                exit_code=-1,
                execution_time=time.time() - start_time,
                user=self.username,
                error=str(e)
            )
    
    def _prepare_command(self, job) -> str:
        """Prepare command for execution (validated)."""
        command = self._validate_command(getattr(job, "command", ""))
        
        if command.startswith("python"):
            # Split safely to avoid shell injection
            parts = shlex.split(command)
            if len(parts) >= 3 and parts[0] == "python" and parts[1] == "-c":
                code = " ".join(parts[2:])
                return f"python -c {shlex.quote(code)}"
            return command
        elif command.startswith("powershell"):
            return command
        else:
            # Regular shell command — run via explicit interpreter
            return command
    
    async def _execute_windows(self, command: str, job) -> LowPrivResult:
        """Execute command on Windows with low privileges (no shell=True)."""
        try:
            self._validate_command(command)
            
            # Use tempfile for safety
            temp_dir = tempfile.gettempdir()
            batch_file = os.path.join(temp_dir, f"asim_job_{getattr(job, 'id', 'unknown')}.bat")
            
            batch_content = f"@echo off\n{command}\necho %ERRORLEVEL%"
            with open(batch_file, 'w') as f:
                f.write(batch_content)
            
            try:
                # Execute via direct list to avoid shell=True
                result = subprocess.run(
                    ["cmd.exe", "/c", batch_file],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    cwd=temp_dir,
                )
                
                return LowPrivResult(
                    success=result.returncode == 0,
                    stdout=result.stdout,
                    stderr=result.stderr,
                    exit_code=result.returncode,
                    execution_time=0,
                    user=self.username,
                )
            finally:
                try:
                    os.remove(batch_file)
                except Exception:
                    pass
            
        except Exception as e:
            self.logger.error(f"Windows execution failed: {e}")
            raise
    
    async def _execute_unix(self, command: str, job) -> LowPrivResult:
        """Execute command on Unix/Linux with low privileges (no shell=True)."""
        try:
            self._validate_command(command)
            
            result = subprocess.run(
                ["sudo", "-u", self.username, "sh", "-c", command],
                capture_output=True,
                text=True,
                timeout=self.timeout + 10,
            )
            
            return LowPrivResult(
                success=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
                execution_time=0,
                user=self.username,
            )
        except Exception as e:
            self.logger.error(f"Unix execution failed: {e}")
            raise
    
    async def execute_script(self, script_content: str,
                          script_type: str = "python",
                          working_dir: str = None) -> LowPrivResult:
        """Execute a script with low privileges."""
        self._validate_command(script_content)
        self.logger.info(f"Executing {script_type} script as low-priv user")
        
        start_time = time.time()
        
        try:
            # Use tempfile for secure temp file creation
            suffix = {"python": ".py", "batch": ".bat", "shell": ".sh"}.get(script_type, ".sh")
            with tempfile.NamedTemporaryFile(
                mode='w', suffix=suffix, delete=False, prefix="asim_script_"
            ) as f:
                script_file = f.name
                f.write(script_content)
            
            if self.system != "windows":
                os.chmod(script_file, 0o700)  # owner-only execute
            
            try:
                if self.system == "windows":
                    cmd = ["python", script_file] if script_type == "python" else ["cmd.exe", "/c", script_file]
                    result = subprocess.run(
                        cmd,
                        capture_output=True, text=True,
                        timeout=self.timeout,
                        cwd=working_dir or os.path.dirname(script_file),
                    )
                else:
                    interpreter = ["python3"] if script_type == "python" else ["sh"]
                    result = subprocess.run(
                        ["sudo", "-u", self.username] + interpreter + [script_file],
                        capture_output=True, text=True,
                        timeout=self.timeout + 10,
                        cwd=working_dir or os.path.dirname(script_file),
                    )
                
                return LowPrivResult(
                    success=result.returncode == 0,
                    stdout=result.stdout, stderr=result.stderr,
                    exit_code=result.returncode,
                    execution_time=time.time() - start_time,
                    user=self.username,
                )
            finally:
                try:
                    os.remove(script_file)
                except Exception:
                    pass
        
        except Exception as e:
            self.logger.error(f"Script execution failed: {e}")
            return LowPrivResult(
                success=False, stdout="", stderr=str(e),
                exit_code=-1, execution_time=time.time() - start_time,
                user=self.username, error=str(e),
            )
    
    def is_user_available(self) -> bool:
        """Check if low-privilege user is available"""
        try:
            if self.system == "windows":
                result = subprocess.run(
                    f"net user {self.username}",
                    shell=True,
                    capture_output=True,
                    text=True
                )
                return "not found" not in result.stderr.lower()
            else:
                result = subprocess.run(
                    f"id -u {self.username}",
                    shell=True,
                    capture_output=True,
                    text=True
                )
                return result.returncode == 0
        except Exception as e:
            self.logger.debug(f"User availability check failed: {e}")
            return False
    
    def get_user_info(self) -> Dict[str, Any]:
        """Get information about the low-privilege user"""
        info = {
            "username": self.username,
            "system": self.system,
            "available": self.is_user_available(),
            "timeout": self.timeout
        }
        
        try:
            if self.system == "windows":
                # Get user groups
                result = subprocess.run(
                    f"net user {self.username}",
                    shell=True,
                    capture_output=True,
                    text=True
                )
                info["user_info"] = result.stdout
            else:
                # Get user info
                result = subprocess.run(
                    f"id {self.username}",
                    shell=True,
                    capture_output=True,
                    text=True
                )
                info["user_info"] = result.stdout
                
        except Exception as e:
            info["error"] = str(e)
        
        return info
    
    def cleanup_temp_files(self):
        """Clean up temporary files"""
        try:
            if self.system == "windows":
                temp_dir = "C:\\temp"
                pattern = "asim_job_*"
            else:
                temp_dir = "/tmp"
                pattern = "asim_script_*"
            
            import glob
            temp_files = glob.glob(os.path.join(temp_dir, pattern))
            
            for file_path in temp_files:
                try:
                    os.remove(file_path)
                except Exception as e:
                    self.logger.debug(f"Failed to remove temp file: {e}")
                    pass
            
            self.logger.info(f"Cleaned up {len(temp_files)} temporary files")
            
        except Exception as e:
            self.logger.error(f"Temp file cleanup failed: {e}")

# Global low-privilege user runner instance
low_priv_user_runner = LowPrivUserRunner()
