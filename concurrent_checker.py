import concurrent.futures
import logging
from typing import List, Dict, Any
from detectors.base import CheckResult, ServiceStatus
from detector_factory import DetectorFactory


class ConcurrentChecker:
    """并发服务检测器"""

    def __init__(self, max_workers: int = 5, detector_factory: DetectorFactory = None):
        self.max_workers = max_workers
        self.detector_factory = detector_factory or DetectorFactory()
        self.logger = logging.getLogger(self.__class__.__name__)

    def check_services(self, services_config: List[Dict[str, Any]]) -> List[CheckResult]:
        """并发检测所有服务"""
        results = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 创建检测任务
            future_to_service = {
                executor.submit(self._check_single_service, service_config): service_config
                for service_config in services_config
            }

            # 收集结果
            for future in concurrent.futures.as_completed(future_to_service):
                service_config = future_to_service[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as exc:
                    service_name = service_config.get('name', 'unknown')
                    server_name = service_config.get('server', 'local')
                    self.logger.error(f"Service {service_name} on {server_name} generated an exception: {exc}")
                    results.append(CheckResult(
                        service_name=service_name,
                        service_type=service_config.get('type', 'unknown'),
                        status=ServiceStatus.UNKNOWN,
                        message=f"Check failed with exception: {str(exc)}",
                        server=server_name
                    ))

        return results

    def _check_single_service(self, service_config: Dict[str, Any]) -> CheckResult:
        """检测单个服务"""
        try:
            detector = self.detector_factory.create_detector(service_config)
            return detector.check()
        except Exception as e:
            service_name = service_config.get('name', 'unknown')
            server_name = service_config.get('server', 'local')
            return CheckResult(
                service_name=service_name,
                service_type=service_config.get('type', 'unknown'),
                status=ServiceStatus.UNKNOWN,
                message=f"Failed to create or execute detector: {str(e)}",
                server=server_name
            )