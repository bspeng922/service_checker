import logging
import sys
from typing import List
from detectors.base import CheckResult, ServiceStatus


class LogManager:
    """日志管理器"""

    def __init__(self, log_level: str = "INFO"):
        self.logger = logging.getLogger("ServiceMonitor")
        self._setup_logger(log_level)

    def _setup_logger(self, log_level: str):
        """配置日志"""
        self.logger.setLevel(getattr(logging, log_level.upper()))

        # 避免重复添加handler
        if not self.logger.handlers:
            # 控制台handler
            console_handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

    def log_results(self, results: List[CheckResult]):
        """记录检测结果"""
        healthy_count = 0
        unhealthy_count = 0
        unknown_count = 0

        for result in results:
            if result.status == ServiceStatus.HEALTHY:
                healthy_count += 1
                self.logger.info(f"✅ {result.server} {result.service_name} ({result.service_type}): {result.message}")
            elif result.status == ServiceStatus.UNHEALTHY:
                unhealthy_count += 1
                self.logger.error(f"❌ {result.server} {result.service_name} ({result.service_type}): {result.message}")
            else:
                unknown_count += 1
                self.logger.warning(f"⚠️ {result.server} {result.service_name} ({result.service_type}): {result.message}")

        # 汇总信息
        self.logger.info(
            f"检测完成: 健康 {healthy_count}, 异常 {unhealthy_count}, 未知 {unknown_count}, 总计 {len(results)}"
        )

        if unhealthy_count > 0:
            self.logger.error(f"发现 {unhealthy_count} 个异常服务，请及时处理！")