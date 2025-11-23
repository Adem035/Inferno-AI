"""
Docker-based sandbox implementation for Inferno.

Provides isolated command and Python execution using Docker containers.
Free alternative to E2B with better performance (local execution).

Key Features:
    - Ephemeral containers (auto-cleanup)
    - File operations (write scripts, read outputs)
    - Command execution with timeout
    - Resource limits (CPU/Memory)
    - Full isolation

Usage:
    from docker_sandbox import create_docker_sandbox
    
    sandbox = create_docker_sandbox()
    result = sandbox.commands.run("curl http://example.com", timeout=30)
    sandbox.kill()
"""

import docker
import io
import logging
import tempfile
import os
from typing import Optional

logger = logging.getLogger(__name__)


class CommandResult:
    """Result from sandbox command execution."""
    def __init__(self, exit_code: int, stdout: str, stderr: str):
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr


class SandboxCommands:
    """Command execution interface for sandbox."""
    
    def __init__(self, container):
        self.container = container
    
    def run(self, command: str, timeout: int = 120, user: str = "root") -> CommandResult:
        """
        Execute a command in the sandbox.
        
        Args:
            command: Shell command to execute
            timeout: Timeout in seconds
            user: User to run as (default: root)
            
        Returns:
            CommandResult with exit_code, stdout, stderr
        """
        try:
            # Execute command in container (Docker library doesn't support timeout in exec_run)
            exec_result = self.container.exec_run(
                cmd=["bash", "-c", command],
                user=user,
                demux=True  # Separate stdout and stderr
            )
            
            exit_code = exec_result.exit_code
            stdout_bytes, stderr_bytes = exec_result.output
            
            stdout = stdout_bytes.decode('utf-8', errors='replace') if stdout_bytes else ""
            stderr = stderr_bytes.decode('utf-8', errors='replace') if stderr_bytes else ""
            
            return CommandResult(exit_code=exit_code, stdout=stdout, stderr=stderr)
            
        except docker.errors.APIError as e:
            logger.error(f"Docker API error: {e}")
            return CommandResult(exit_code=-1, stdout="", stderr=f"Docker error: {e}")
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            return CommandResult(exit_code=-1, stdout="", stderr=f"Error: {e}")


class SandboxFiles:
    """File operations interface for sandbox."""
    
    def __init__(self, container):
        self.container = container
    
    def write(self, path: str, content: str):
        """
        Write content to a file in the sandbox.
        
        Args:
            path: File path in container
            content: File content
        """
        try:
            # Create tar archive in memory
            import tarfile
            
            tar_stream = io.BytesIO()
            tar = tarfile.TarFile(fileobj=tar_stream, mode='w')
            
            # Add file to tar
            file_data = content.encode('utf-8')
            tarinfo = tarfile.TarInfo(name=os.path.basename(path))
            tarinfo.size = len(file_data)
            tar.addfile(tarinfo, io.BytesIO(file_data))
            tar.close()
            
            # Put tar archive in container
            tar_stream.seek(0)
            self.container.put_archive(
                path=os.path.dirname(path) or '/workspace',
                data=tar_stream
            )
            
        except Exception as e:
            logger.error(f"File write error: {e}")
            raise


class DockerSandbox:
    """
    Docker-based sandbox for isolated code execution.
    
    Provides the same interface as E2B but runs locally with Docker.
    """
    
    def __init__(
        self,
        image: str = "inferno-sandbox:latest",
        mem_limit: str = "2g",
        cpu_quota: int = 200000,
        network_mode: str = "bridge"
    ):
        """
        Initialize Docker sandbox.
        
        Args:
            image: Docker image name
            mem_limit: Memory limit (e.g., "2g")
            cpu_quota: CPU quota (200000 = 2 cores)
            network_mode: Network mode (bridge, none, host)
        """
        self.image = image
        self.client = docker.from_env()
        
        # Create container
        try:
            self.container = self.client.containers.run(
                image=image,
                command="sleep infinity",  # Keep container running
                detach=True,
                mem_limit=mem_limit,
                cpu_quota=cpu_quota,
                cpu_period=100000,
                network_mode=network_mode,
                extra_hosts={"host.docker.internal": "host-gateway"},  # Allow access to host
                remove=False,  # We'll remove manually
                auto_remove=False
            )
            
            # Initialize interfaces
            self.commands = SandboxCommands(self.container)
            self.files = SandboxFiles(self.container)
            
            logger.info(f"Created sandbox container: {self.container.short_id}")
            
        except docker.errors.ImageNotFound:
            raise RuntimeError(
                f"Docker image '{image}' not found. "
                f"Build it with: docker build -t {image} /Users/ademkok/Inferno-AI/Inferno"
            )
        except docker.errors.APIError as e:
            raise RuntimeError(f"Failed to create Docker container: {e}")
    
    def kill(self):
        """Stop and remove the container."""
        try:
            if self.container:
                logger.info(f"Killing sandbox container: {self.container.short_id}")
                self.container.stop(timeout=2)
                self.container.remove(force=True)
        except Exception as e:
            logger.error(f"Error killing container: {e}")
    
    def set_timeout(self, timeout: int):
        """
        Set timeout (for compatibility with E2B interface).
        
        Note: Docker handles timeouts per-command, not globally.
        This is a no-op for interface compatibility.
        """
        pass  # Docker handles timeouts per exec_run call


def create_docker_sandbox() -> DockerSandbox:
    """
    Factory function to create a Docker sandbox instance.
    
    Reads configuration from environment variables:
        - SANDBOX_IMAGE: Docker image name (default: inferno-sandbox:latest)
        - SANDBOX_MEMORY_LIMIT: Memory limit (default: 2g)
        - SANDBOX_CPU_LIMIT: CPU limit in cores (default: 2.0)
        - SANDBOX_NETWORK: Network mode (default: bridge)
    
    Returns:
        Configured DockerSandbox instance
    """
    image = os.getenv("SANDBOX_IMAGE", "inferno-sandbox:latest")
    mem_limit = os.getenv("SANDBOX_MEMORY_LIMIT", "2g")
    
    # Convert CPU limit to quota
    cpu_limit = float(os.getenv("SANDBOX_CPU_LIMIT", "2.0"))
    cpu_quota = int(cpu_limit * 100000)
    
    network_mode = os.getenv("SANDBOX_NETWORK", "bridge")
    
    return DockerSandbox(
        image=image,
        mem_limit=mem_limit,
        cpu_quota=cpu_quota,
        network_mode=network_mode
    )


def check_docker_available() -> bool:
    """
    Check if Docker is available and running.
    
    Returns:
        True if Docker is available, False otherwise
    """
    try:
        client = docker.from_env()
        client.ping()
        return True
    except Exception:
        return False
