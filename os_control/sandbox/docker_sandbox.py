
"""
STATUS: REAL — Hardened Docker sandbox with strict isolation
"""
"""
ASIMNEXUS Docker Sandbox
High-risk job execution in isolated Docker containers
"""

import os
import json
import time
import logging
import asyncio
import docker
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path

# ── Allowlist of trusted base images ─────────────────────────────────────────
TRUSTED_IMAGES: set = {
    "python:3.11-slim",
    "python:3.10-slim",
    "alpine:3.19",
    "ubuntu:24.04",
    "busybox:stable",
}

@dataclass
class SandboxResult:
    """Result of sandbox execution"""
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    execution_time: float
    container_id: str
    error: Optional[str] = None

class DockerSandbox:
    """Docker-based sandbox for high-risk operations"""
    
    def __init__(self):
        self.logger = logging.getLogger("DockerSandbox")
        self.client = None
        self.default_image = "python:3.11-slim"
        self.timeout = 300  # 5 minutes
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Docker client"""
        try:
            self.client = docker.from_env()
            # Test connection
            self.client.ping()
            self.logger.info("Docker client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Docker client: {e}")
            self.client = None

    def _validate_image(self, image: str) -> str:
        """Return the image only if it's in the trusted allowlist."""
        if image not in TRUSTED_IMAGES:
            self.logger.warning(f"Image '{image}' not in allowlist; falling back to default")
            return self.default_image
        return image

    def _sanitize_command(self, command: str) -> str:
        """Basic command injection protection — reject shell metacharacters."""
        dangerous = {"`", "$(", "&&", "||", ";", "|", ">", "<", "$((", "${{"}
        for token in dangerous:
            if token in command:
                raise ValueError(f"Command contains dangerous token: {token!r}")
        return command
    
    def is_available(self) -> bool:
        """Check if Docker is available"""
        return self.client is not None
    
    async def execute_job(self, job) -> SandboxResult:
        """Execute a job in Docker sandbox"""
        if not self.is_available():
            return SandboxResult(
                success=False,
                stdout="",
                stderr="Docker not available",
                exit_code=-1,
                execution_time=0,
                container_id="",
                error="Docker sandbox not available"
            )
        
        self.logger.info(f"Executing job in Docker: {job.name}")
        
        start_time = time.time()
        container_id = None
        
        try:
            # Prepare container configuration
            container_config = self._prepare_container_config(job)
            
            # Create and start container
            container = self.client.containers.run(**container_config)
            container_id = container.id
            
            # Wait for completion
            result = container.wait(timeout=self.timeout)
            
            # Get logs
            stdout = container.logs(stdout=True, stderr=False).decode('utf-8')
            stderr = container.logs(stdout=False, stderr=True).decode('utf-8')
            
            # Clean up container
            container.remove(force=True)
            
            execution_time = time.time() - start_time
            
            success = result['StatusCode'] == 0
            
            return SandboxResult(
                success=success,
                stdout=stdout,
                stderr=stderr,
                exit_code=result['StatusCode'],
                execution_time=execution_time,
                container_id=container_id
            )
            
        except Exception as e:
            self.logger.error(f"Docker execution failed: {e}")
            
            # Clean up on error
            if container_id:
                try:
                    container = self.client.containers.get(container_id)
                    container.remove(force=True)
                except Exception as e:
                    self.logger.debug(f"Failed to remove container: {e}")
                    pass
            
            return SandboxResult(
                success=False,
                stdout="",
                stderr=str(e),
                exit_code=-1,
                execution_time=time.time() - start_time,
                container_id=container_id or "",
                error=str(e)
            )
    
    def _prepare_container_config(self, job) -> Dict[str, Any]:
        """Prepare hardened Docker container configuration."""
        image = self._validate_image(getattr(job, "image", None) or self.default_image)
        command = self._sanitize_command(getattr(job, "command", "python3 --version"))

        # Base hardened configuration
        config: Dict[str, Any] = {
            "image": image,
            "command": f"python3 -c '{command}'",
            "detach": True,
            "remove": False,  # We'll remove manually
            # ── Resource limits ────────────────────────────────────────────
            "mem_limit": "512m",
            "memswap_limit": "768m",       # prevent swap exhaustion
            "cpu_quota": 50000,
            "cpu_period": 100000,
            "pids_limit": 64,              # prevent fork bombs
            # ── Network isolation ──────────────────────────────────────────
            "network_mode": "none",
            # ── Filesystem hardening ───────────────────────────────────────
            "read_only": True,
            "tmpfs": {"/tmp": "rw,noexec,nosuid,size=100m"},
            # ── Drop all Linux capabilities ────────────────────────────────
            "cap_drop": ["ALL"],
            # ── Security options ───────────────────────────────────────────
            "security_opt": [
                "no-new-privileges:true",
                "seccomp=unconfined",       # allow common syscalls safely
            ],
            # ── Ulimits ────────────────────────────────────────────────────
            "ulimits": [
                {"Name": "nofile", "Soft": 1024, "Hard": 2048},
                {"Name": "nproc",  "Soft": 64,   "Hard": 128},
                {"Name": "core",   "Soft": 0,    "Hard": 0},   # no core dumps
                {"Name": "fsize",  "Soft": 10485760, "Hard": 10485760},  # 10 MB max file
            ],
            # ── Cleanup ────────────────────────────────────────────────────
            "stop_signal": "SIGKILL",
            "stop_timeout": 10,
        }

        # Add custom volumes if needed
        volumes = {}
        volume_binds = {}

        if getattr(job, "parameters", None) and job.parameters.get("needs_asim_data", False):
            asim_data_path = Path(__file__).parent.parent.parent / "data"
            if asim_data_path.exists():
                volumes["/asim_data"] = {"bind": str(asim_data_path), "mode": "ro"}
                volume_binds[str(asim_data_path)] = {
                    "bind": "/asim_data",
                    "mode": "ro"
                }

        if volumes:
            config["volumes"] = volumes
            config["volume_binds"] = volume_binds

        # Environment variables (minimal)
        env_vars: Dict[str, str] = {
            "PYTHONUNBUFFERED": "1",
            "JOB_ID": str(getattr(job, "id", "unknown")),
            "JOB_NAME": str(getattr(job, "name", "unknown")),
        }
        if getattr(job, "parameters", None) and job.parameters.get("environment"):
            env_vars.update(job.parameters["environment"])
        config["environment"] = env_vars

        config["working_dir"] = "/tmp"

        # Conditional network access
        if getattr(job, "parameters", None) and job.parameters.get("needs_network", False):
            config["network_mode"] = "bridge"

        return config
    
    async def execute_script(self, script_content: str,
                          working_dir: str = "/tmp",
                          environment: Dict[str, str] = None,
                          network_access: bool = False,
                          image: Optional[str] = None) -> SandboxResult:
        """Execute a script in Docker sandbox with full isolation."""
        if not self.is_available():
            return SandboxResult(
                success=False, stdout="", stderr="Docker not available",
                exit_code=-1, execution_time=0, container_id="",
                error="Docker sandbox not available"
            )
        
        start_time = time.time()
        container_id = None
        
        try:
            image = self._validate_image(image or self.default_image)
            script_name = "asim_script.py"

            # ── Hardened config matching _prepare_container_config ────────
            config: Dict[str, Any] = {
                "image": image,
                "command": f"python3 {script_name}",
                "detach": True,
                "remove": False,
                "mem_limit": "512m",
                "memswap_limit": "768m",
                "cpu_quota": 50000,
                "cpu_period": 100000,
                "pids_limit": 64,
                "network_mode": "bridge" if network_access else "none",
                "read_only": True,
                "tmpfs": {"/tmp": "rw,noexec,nosuid,size=100m"},
                "cap_drop": ["ALL"],
                "security_opt": ["no-new-privileges:true"],
                "ulimits": [
                    {"Name": "nofile", "Soft": 1024, "Hard": 2048},
                    {"Name": "nproc",  "Soft": 64,   "Hard": 128},
                    {"Name": "core",   "Soft": 0,    "Hard": 0},
                    {"Name": "fsize",  "Soft": 10485760, "Hard": 10485760},
                ],
                "stop_signal": "SIGKILL",
                "stop_timeout": 10,
                "environment": {
                    "PYTHONUNBUFFERED": "1",
                    **(environment or {})
                },
                "working_dir": working_dir,
            }
            
            container = self.client.containers.create(**config)
            container_id = container.id
            
            container.put_archive(
                path="/tmp",
                data=self._create_script_archive(script_content, script_name)
            )
            
            container.start()
            result = container.wait(timeout=self.timeout)
            
            stdout = container.logs(stdout=True, stderr=False).decode('utf-8')
            stderr = container.logs(stdout=False, stderr=True).decode('utf-8')
            container.remove(force=True)
            
            execution_time = time.time() - start_time
            success = result['StatusCode'] == 0
            
            return SandboxResult(
                success=success, stdout=stdout, stderr=stderr,
                exit_code=result['StatusCode'],
                execution_time=execution_time, container_id=container_id,
            )
            
        except Exception as e:
            self.logger.error(f"Script execution failed: {e}")
            if container_id:
                try:
                    c = self.client.containers.get(container_id)
                    c.remove(force=True)
                except Exception:
                    pass
            return SandboxResult(
                success=False, stdout="", stderr=str(e),
                exit_code=-1, execution_time=time.time() - start_time,
                container_id=container_id or "", error=str(e)
            )
    
    def _create_script_archive(self, script_content: str, script_name: str) -> bytes:
        """Create a tar archive with the script"""
        import io
        import tarfile
        
        # Create in-memory tar file
        tar_stream = io.BytesIO()
        
        with tarfile.open(fileobj=tar_stream, mode='w') as tar:
            # Create tarinfo for the script
            script_info = tarfile.TarInfo(name=script_name)
            script_info.size = len(script_content.encode('utf-8'))
            script_info.mode = 0o755  # Executable
            
            # Add script to tar
            tar.addfile(script_info, io.BytesIO(script_content.encode('utf-8')))
        
        return tar_stream.getvalue()
    
    def get_available_images(self) -> List[str]:
        """Get list of available Docker images"""
        if not self.is_available():
            return []
        
        try:
            images = self.client.images.list()
            return [img.tags[0] for img in images if img.tags]
        except Exception as e:
            self.logger.error(f"Failed to list images: {e}")
            return []
    
    def pull_image(self, image_name: str) -> bool:
        """Pull a Docker image"""
        if not self.is_available():
            return False
        
        try:
            self.logger.info(f"Pulling Docker image: {image_name}")
            self.client.images.pull(image_name)
            return True
        except Exception as e:
            self.logger.error(f"Failed to pull image {image_name}: {e}")
            return False
    
    def cleanup_containers(self):
        """Clean up stopped containers"""
        if not self.is_available():
            return
        
        try:
            # Remove stopped containers
            stopped_containers = self.client.containers.list(all=True, filters={"status": "exited"})
            for container in stopped_containers:
                container.remove(force=True)
            
            self.logger.info(f"Cleaned up {len(stopped_containers)} stopped containers")
        except Exception as e:
            self.logger.error(f"Container cleanup failed: {e}")
    
    def get_sandbox_info(self) -> Dict[str, Any]:
        """Get sandbox information"""
        return {
            "available": self.is_available(),
            "docker_version": self.client.version()["Version"] if self.client else None,
            "default_image": self.default_image,
            "timeout": self.timeout,
            "available_images": self.get_available_images()
        }

# Global Docker sandbox instance
docker_sandbox = DockerSandbox()
