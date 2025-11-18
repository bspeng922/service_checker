import requests
from .base import BaseDetector, CheckResult, ServiceStatus


class RestApiDetector(BaseDetector):
    """REST API 服务检测器（支持SSH远程curl）"""

    def check(self) -> CheckResult:
        url = self.config.get('url')
        method = self.config.get('method', 'GET')
        timeout = self.config.get('timeout', 5)
        expected_status = self.config.get('expected_status', 200)
        verify_ssl = self.config.get('verify_ssl', True)
        server_name = self.get_server_name()

        try:
            if self.is_remote:
                # 在远程服务器上使用curl检测
                return self._check_remote_api(url, method, timeout, expected_status, server_name)
            else:
                # 本地检测
                return self._check_local_api(url, method, timeout, expected_status, verify_ssl, server_name)

        except Exception as e:
            return CheckResult(
                service_name=self.name,
                service_type="restapi",
                status=ServiceStatus.UNKNOWN,
                message=f"Error checking API {url}: {str(e)}",
                server=server_name
            )

    def _check_local_api(self, url: str, method: str, timeout: int, expected_status: int, verify_ssl: bool,
                         server_name: str) -> CheckResult:
        """本地API检测"""
        response = requests.request(
            method=method,
            url=url,
            timeout=timeout,
            verify=verify_ssl
        )

        if response.status_code == expected_status:
            return CheckResult(
                service_name=self.name,
                service_type="restapi",
                status=ServiceStatus.HEALTHY,
                message=f"API {url} returned status {response.status_code}",
                server=server_name,
                details={
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds(),
                    "server": server_name
                }
            )
        else:
            return CheckResult(
                service_name=self.name,
                service_type="restapi",
                status=ServiceStatus.UNHEALTHY,
                message=f"API {url} returned status {response.status_code}, expected {expected_status}",
                server=server_name,
                details={
                    "status_code": response.status_code,
                    "expected_status": expected_status,
                    "server": server_name
                }
            )

    def _check_remote_api(self, url: str, method: str, timeout: int, expected_status: int,
                          server_name: str) -> CheckResult:
        """远程API检测（通过SSH在目标服务器上执行curl）"""
        # 构建curl命令
        curl_command = f"curl -X {method} -s -o /dev/null -w '%{{http_code}}' --connect-timeout {timeout} --max-time {timeout} {url}"

        return_code, output, error = self.execute_command(curl_command, timeout=timeout + 5)

        if return_code == 0 and output.isdigit():
            status_code = int(output)
            if status_code == expected_status:
                return CheckResult(
                    service_name=self.name,
                    service_type="restapi",
                    status=ServiceStatus.HEALTHY,
                    message=f"API {url} returned status {status_code}",
                    server=server_name,
                    details={
                        "status_code": status_code,
                        "server": server_name
                    }
                )
            else:
                return CheckResult(
                    service_name=self.name,
                    service_type="restapi",
                    status=ServiceStatus.UNHEALTHY,
                    message=f"API {url} returned status {status_code}, expected {expected_status}",
                    server=server_name,
                    details={
                        "status_code": status_code,
                        "expected_status": expected_status,
                        "server": server_name
                    }
                )
        else:
            return CheckResult(
                service_name=self.name,
                service_type="restapi",
                status=ServiceStatus.UNHEALTHY,
                message=f"Failed to check API {url}: {error}",
                server=server_name
            )