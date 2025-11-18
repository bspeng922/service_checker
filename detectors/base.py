import abc
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class ServiceStatus(Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class CheckResult:
    service_name: str
    service_type: str
    status: ServiceStatus
    message: str
    server: str = "local"  # 新增服务器标识
    details: Optional[Dict[str, Any]] = None


class BaseDetector(abc.ABC):
    """基础检测器抽象类"""

    def __init__(self, name: str, config: Dict[str, Any], server_config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config
        self.server_config = server_config  # SSH服务器配置
        self.is_remote = server_config is not None
        self.logger = logging.getLogger(f"{self.__class__.__name__}.{name}")

    @abc.abstractmethod
    def check(self) -> CheckResult:
        """执行服务检测"""
        pass

    def execute_command(self, command: str, timeout: int = 30) -> tuple:
        """执行命令（本地或远程）"""
        if self.is_remote:
            return self._execute_remote_command(command, timeout)
        else:
            return self._execute_local_command(command, timeout)

    def _execute_local_command(self, command: str, timeout: int) -> tuple:
        """执行本地命令"""
        import subprocess
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            raise TimeoutError(f"Command timeout after {timeout}s: {command}")
        except Exception as e:
            raise RuntimeError(f"Local command failed: {str(e)}")

    def _execute_remote_command(self, command: str, timeout: int) -> tuple:
        """执行远程SSH命令"""
        from ssh_manager import ssh_manager

        with ssh_manager.get_ssh_client(self.server_config) as client:
            try:
                stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
                return_code = stdout.channel.recv_exit_status()
                output = stdout.read().decode('utf-8').strip()
                error = stderr.read().decode('utf-8').strip()
                return return_code, output, error
            except Exception as e:
                raise RuntimeError(f"SSH command failed: {str(e)}")

    def get_server_name(self) -> str:
        """获取服务器名称"""
        if self.is_remote:
            return self.server_config.get('name', 'unknown')
        return "local"