from .base import BaseDetector, CheckResult, ServiceStatus


class SupervisorDetector(BaseDetector):
    """Supervisor 服务检测器（支持SSH远程）"""

    def check(self) -> CheckResult:
        process_name = self.config.get('process_name')
        supervisor_url = self.config.get('supervisor_url', 'unix:///var/run/supervisor.sock')
        expected_state = self.config.get('expected_state', 'RUNNING')
        server_name = self.get_server_name()

        try:
            if self.is_remote:
                return self._check_remote_supervisor(process_name, expected_state, server_name)
            else:
                return self._check_local_supervisor(process_name, supervisor_url, expected_state, server_name)

        except Exception as e:
            return CheckResult(
                service_name=self.name,
                service_type="supervisor",
                status=ServiceStatus.UNKNOWN,
                message=f"Error checking supervisor process {process_name}: {str(e)}",
                server=server_name
            )

    def _check_local_supervisor(self, process_name: str, supervisor_url: str, expected_state: str,
                                server_name: str) -> CheckResult:
        """本地Supervisor检测"""
        from xmlrpc.client import ServerProxy

        with ServerProxy(supervisor_url) as server:
            process_info = server.supervisor.getProcessInfo(process_name)
            actual_state = process_info.get('statename')

            if actual_state == expected_state:
                return CheckResult(
                    service_name=self.name,
                    service_type="supervisor",
                    status=ServiceStatus.HEALTHY,
                    message=f"Supervisor process {process_name} is {actual_state}",
                    server=server_name,
                    details={
                        "actual_state": actual_state,
                        "pid": process_info.get('pid'),
                        "server": server_name
                    }
                )
            else:
                return CheckResult(
                    service_name=self.name,
                    service_type="supervisor",
                    status=ServiceStatus.UNHEALTHY,
                    message=f"Supervisor process {process_name} is {actual_state}, expected {expected_state}",
                    server=server_name,
                    details={
                        "actual_state": actual_state,
                        "expected_state": expected_state,
                        "server": server_name
                    }
                )

    def _check_remote_supervisor(self, process_name: str, expected_state: str, server_name: str) -> CheckResult:
        """远程Supervisor检测"""
        # 使用supervisorctl检查状态
        command = f"supervisorctl status {process_name}"
        return_code, output, error = self.execute_command(command, timeout=10)

        if return_code == 0:
            # 解析supervisorctl输出
            lines = output.strip().split('\n')
            for line in lines:
                if line.startswith(process_name):
                    parts = line.split()
                    if len(parts) >= 2:
                        actual_state = parts[1].upper()
                        if actual_state == expected_state.upper():
                            return CheckResult(
                                service_name=self.name,
                                service_type="supervisor",
                                status=ServiceStatus.HEALTHY,
                                message=f"Supervisor process {process_name} is {actual_state}",
                                server=server_name,
                                details={
                                    "actual_state": actual_state,
                                    "server": server_name
                                }
                            )
                        else:
                            return CheckResult(
                                service_name=self.name,
                                service_type="supervisor",
                                status=ServiceStatus.UNHEALTHY,
                                message=f"Supervisor process {process_name} is {actual_state}, expected {expected_state}",
                                server=server_name,
                                details={
                                    "actual_state": actual_state,
                                    "expected_state": expected_state,
                                    "server": server_name
                                }
                            )

            return CheckResult(
                service_name=self.name,
                service_type="supervisor",
                status=ServiceStatus.UNHEALTHY,
                message=f"Supervisor process {process_name} not found in output",
                server=server_name
            )
        else:
            return CheckResult(
                service_name=self.name,
                service_type="supervisor",
                status=ServiceStatus.UNHEALTHY,
                message=f"Failed to check supervisor process {process_name}: {error}",
                server=server_name
            )