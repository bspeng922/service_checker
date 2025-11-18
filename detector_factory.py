from typing import Dict, Any
from detectors import DETECTOR_REGISTRY, BaseDetector


class DetectorFactory:
    """检测器工厂类"""

    def __init__(self, ssh_servers_config: Dict[str, Any] = None):
        self.ssh_servers_config = ssh_servers_config or {}

    def create_detector(self, service_config: Dict[str, Any]) -> BaseDetector:
        """根据服务配置创建检测器实例"""
        service_type = service_config.get('type')
        service_name = service_config.get('name')
        config = service_config.get('config', {})
        server_name = service_config.get('server')

        if service_type not in DETECTOR_REGISTRY:
            raise ValueError(f"Unsupported service type: {service_type}")

        # 获取SSH服务器配置
        server_config = None
        if server_name:
            if server_name not in self.ssh_servers_config:
                raise ValueError(f"Unknown server: {server_name}")
            server_config = self.ssh_servers_config[server_name]

        detector_class = DETECTOR_REGISTRY[service_type]
        return detector_class(service_name, config, server_config)

    @staticmethod
    def register_detector(service_type: str, detector_class):
        """注册自定义检测器"""
        DETECTOR_REGISTRY[service_type] = detector_class