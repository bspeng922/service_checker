from .base import BaseDetector, CheckResult, ServiceStatus


class SystemdDetector(BaseDetector):
    """Systemd 服务检测器（支持SSH远程）"""

    def check(self) -> CheckResult:
        service_name = self.config.get('service_name')
        expected_status = self.config.get('expected_status', 'active')
        server_name = self.get_server_name()

        try:
            # 使用systemctl检查服务状态
            command = f"systemctl is-active {service_name}"
            return_code, output, error = self.execute_command(command, timeout=10)

            actual_status = output.strip()

            if return_code == 0 and actual_status == expected_status:
                return CheckResult(
                    service_name=self.name,
                    service_type="systemd",
                    status=ServiceStatus.HEALTHY,
                    message=f"Service {service_name} is {actual_status}",
                    server=server_name,
                    details={
                        "actual_status": actual_status,
                        "server": server_name
                    }
                )
            else:
                return CheckResult(
                    service_name=self.name,
                    service_type="systemd",
                    status=ServiceStatus.UNHEALTHY,
                    message=f"Service {service_name} is {actual_status}, expected {expected_status}",
                    server=server_name,
                    details={
                        "actual_status": actual_status,
                        "expected_status": expected_status,
                        "error": error,
                        "server": server_name
                    }
                )

        except TimeoutError as e:
            return CheckResult(
                service_name=self.name,
                service_type="systemd",
                status=ServiceStatus.UNHEALTHY,
                message=f"Timeout checking systemd service {service_name}",
                server=server_name
            )
        except Exception as e:
            return CheckResult(
                service_name=self.name,
                service_type="systemd",
                status=ServiceStatus.UNKNOWN,
                message=f"Error checking systemd service {service_name}: {str(e)}",
                server=server_name
            )