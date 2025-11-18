import yaml
import time
import signal
import sys
import os
import logging
from typing import List, Dict, Any
from concurrent_checker import ConcurrentChecker
from logger import LogManager
from detector_factory import DetectorFactory
from ssh_manager import ssh_manager
from web_server import WebServer


class ServiceMonitor:
    """服务监控主类"""

    def __init__(self, config_file: str = "config.yaml"):
        self.config_file = config_file
        self.config = self._load_config()
        self.running = True
        self.services_config = self.config.get('services', [])

        # 初始化组件
        self.detector_factory = DetectorFactory(
            ssh_servers_config=self.config.get('ssh_servers', {})
        )
        self.checker = ConcurrentChecker(
            max_workers=self.config.get('max_workers', 5),
            detector_factory=self.detector_factory
        )
        self.log_manager = LogManager(
            log_level=self.config.get('log_level', 'INFO')
        )

        # 初始化Web服务器
        web_host = self.config.get('web_host', '0.0.0.0')
        web_port = self.config.get('web_port', 5000)
        self.web_server = WebServer(host=web_host, port=web_port, service_monitor=self)

        # 注册信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def run_health_check(self):
        """执行健康检查并更新Web界面"""
        try:
            self.log_manager.logger.info("开始服务检测...")
            # 使用checker的check_services方法
            results = self.checker.check_services(self.services_config)
            self.log_manager.log_results(results)
            self.web_server.update_results(results)
            return results
        except Exception as e:
            self.log_manager.logger.error(f"健康检查失败: {e}")
            return []

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading config file: {e}")
            sys.exit(1)

    def _signal_handler(self, signum, frame):
        """信号处理"""
        self.log_manager.logger.info("接收到停止信号，正在关闭监控服务...")
        self.running = False
        ssh_manager.close_all()

    def get_services_config(self):
        """获取服务配置（供Web服务器调用）"""
        return self.services_config

    def run_health_check(self):
        """执行健康检查并更新Web界面"""
        try:
            self.log_manager.logger.info("开始服务检测...")
            results = self.checker.check_services(self.services_config)
            self.log_manager.log_results(results)
            self.web_server.update_results(results)
            return results
        except Exception as e:
            self.log_manager.logger.error(f"健康检查失败: {e}")
            return []

    def run(self):
        """运行监控服务"""
        check_interval = self.config.get('check_interval', 30)

        self.log_manager.logger.info(f"启动服务监控，共 {len(self.services_config)} 个服务，检测间隔 {check_interval} 秒")

        # 启动Web服务器
        self.web_server.run_in_thread()

        # 立即执行第一次检查
        self.run_health_check()

        try:
            while self.running:
                # 等待下一次检测
                for _ in range(check_interval):
                    if not self.running:
                        break
                    time.sleep(1)

                if self.running:
                    self.run_health_check()

        except Exception as e:
            self.log_manager.logger.error(f"监控循环发生错误: {e}")
        finally:
            ssh_manager.close_all()
            self.log_manager.logger.info("服务监控已停止")


def main():
    """主函数"""
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    monitor = ServiceMonitor()
    monitor.run()


if __name__ == "__main__":
    main()
