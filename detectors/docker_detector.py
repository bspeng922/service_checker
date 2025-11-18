from typing import Dict, Any, Optional

import docker
from .base import BaseDetector, CheckResult, ServiceStatus


class DockerDetector(BaseDetector):
    """Docker 容器检测器（支持SSH远程）"""

    def __init__(self, name: str, config: Dict[str, Any], server_config: Optional[Dict[str, Any]] = None):
        super().__init__(name, config, server_config)
        self._docker_client = None

    @property
    def docker_client(self):
        if self._docker_client is None:
            try:
                if self.is_remote:
                    # 对于远程检测，我们使用SSH命令而不是Docker API
                    self._docker_client = None
                else:
                    self._docker_client = docker.from_env()
            except Exception as e:
                self.logger.error(f"Failed to initialize Docker client: {e}")
                raise
        return self._docker_client

    def check(self) -> CheckResult:
        container_name = self.config.get('container_name')
        expected_state = self.config.get('expected_state', 'running')
        server_name = self.get_server_name()

        try:
            if self.is_remote:
                return self._check_remote_docker(container_name, expected_state, server_name)
            else:
                return self._check_local_docker(container_name, expected_state, server_name)

        except Exception as e:
            return CheckResult(
                service_name=self.name,
                service_type="docker",
                status=ServiceStatus.UNKNOWN,
                message=f"Error checking container {container_name}: {str(e)}",
                server=server_name
            )

    def _check_local_docker(self, container_name: str, expected_state: str, server_name: str) -> CheckResult:
        """本地Docker检测"""
        container = self.docker_client.containers.get(container_name)
        actual_state = container.status.lower()

        if actual_state == expected_state.lower():
            return CheckResult(
                service_name=self.name,
                service_type="docker",
                status=ServiceStatus.HEALTHY,
                message=f"Container {container_name} is {actual_state}",
                server=server_name,
                details={
                    "actual_state": actual_state,
                    "image": container.image.tags,
                    "server": server_name
                }
            )
        else:
            return CheckResult(
                service_name=self.name,
                service_type="docker",
                status=ServiceStatus.UNHEALTHY,
                message=f"Container {container_name} is {actual_state}, expected {expected_state}",
                server=server_name,
                details={
                    "actual_state": actual_state,
                    "expected_state": expected_state,
                    "server": server_name
                }
            )

    def _check_remote_docker(self, container_name: str, expected_state: str, server_name: str) -> CheckResult:
        """远程Docker检测（通过SSH执行docker命令）"""
        command = f"docker inspect --format='{{{{.State.Status}}}}' {container_name}"
        return_code, output, error = self.execute_command(command, timeout=10)

        if return_code == 0:
            actual_state = output.strip().strip("'").lower()

            if actual_state == expected_state.lower():
                return CheckResult(
                    service_name=self.name,
                    service_type="docker",
                    status=ServiceStatus.HEALTHY,
                    message=f"Container {container_name} is {actual_state}",
                    server=server_name,
                    details={
                        "actual_state": actual_state,
                        "server": server_name
                    }
                )
            else:
                return CheckResult(
                    service_name=self.name,
                    service_type="docker",
                    status=ServiceStatus.UNHEALTHY,
                    message=f"Container {container_name} is {actual_state}, expected {expected_state}",
                    server=server_name,
                    details={
                        "actual_state": actual_state,
                        "expected_state": expected_state,
                        "server": server_name
                    }
                )
        else:
            # 检查容器是否存在
            check_exists_cmd = f"docker ps -a --filter 'name=^{container_name}$' --format '{{{{.Names}}}}'"
            return_code_exists, output_exists, _ = self.execute_command(check_exists_cmd, timeout=10)

            if return_code_exists == 0 and output_exists.strip() == container_name:
                return CheckResult(
                    service_name=self.name,
                    service_type="docker",
                    status=ServiceStatus.UNHEALTHY,
                    message=f"Container {container_name} exists but inspect failed: {error}",
                    server=server_name
                )
            else:
                return CheckResult(
                    service_name=self.name,
                    service_type="docker",
                    status=ServiceStatus.UNHEALTHY,
                    message=f"Container {container_name} not found",
                    server=server_name
                )
