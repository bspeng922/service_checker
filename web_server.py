from flask import Flask, render_template, jsonify
import threading
import time
import logging
import os
from typing import Dict, List, Any
from detectors.base import CheckResult, ServiceStatus


class WebServer:
    """Web监控服务器"""

    def __init__(self, host='0.0.0.0', port=5000, service_monitor=None):
        self.host = host
        self.port = port
        self.service_monitor = service_monitor

        # 创建Flask应用，明确指定静态文件目录
        self.app = Flask(
            __name__,
            template_folder='templates',
            static_folder='static'
        )

        self.last_results: List[CheckResult] = []
        self.last_check_time = None
        self.setup_routes()

    def setup_routes(self):
        """设置路由"""

        @self.app.route('/')
        def index():
            return render_template('index.html')

        @self.app.route('/api/status')
        def get_status():
            """获取服务状态API"""
            try:
                status_data = self._format_status_data()
                return jsonify(status_data)
            except Exception as e:
                logging.error(f"API错误: {e}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/api/refresh', methods=['POST'])
        def refresh():
            """手动刷新状态"""
            try:
                if self.service_monitor:
                    # 正确的调用方法 - 使用 run_health_check
                    results = self.service_monitor.run_health_check()
                    if results is not None:
                        self.last_results = results
                        self.last_check_time = time.time()
                        return jsonify({
                            'success': True,
                            'message': f'刷新成功，检测了 {len(results)} 个服务'
                        })
                    else:
                        return jsonify({'success': False, 'message': '健康检查返回空结果'})
                else:
                    return jsonify({'success': False, 'message': '监控服务未初始化'})
            except Exception as e:
                logging.error(f"刷新错误: {e}")
                return jsonify({'success': False, 'message': f'刷新失败: {str(e)}'}), 500

    def _format_status_data(self) -> Dict[str, Any]:
        """格式化状态数据 - 按主机聚合"""
        # 如果没有结果，返回空数据
        if not self.last_results:
            return {
                'hosts': [],
                'overall_status': 'unknown',
                'total_services': 0,
                'total_healthy': 0,
                'total_unhealthy': 0,
                'total_unknown': 0,
                'last_check_time': self.last_check_time,
                'current_time': time.time()
            }

        # 按主机分组
        hosts_data = {}

        for result in self.last_results:
            host_name = result.server
            if host_name not in hosts_data:
                # 获取主机配置信息
                host_config = self._get_host_config(host_name)
                hosts_data[host_name] = {
                    'host_name': host_name,
                    'host_address': host_config.get('host', 'N/A'),
                    'host_type': self._get_host_type(host_config),
                    'services': [],
                    'health_status': 'healthy',
                    'healthy_count': 0,
                    'unhealthy_count': 0,
                    'unknown_count': 0,
                    'total_services': 0
                }

            host_data = hosts_data[host_name]
            service_data = {
                'name': result.service_name,
                'type': result.service_type,
                'status': result.status.value,
                'message': result.message,
                'details': result.details or {},
                'timestamp': time.time()
            }

            host_data['services'].append(service_data)
            host_data['total_services'] += 1

            # 统计服务状态
            if result.status == ServiceStatus.HEALTHY:
                host_data['healthy_count'] += 1
            elif result.status == ServiceStatus.UNHEALTHY:
                host_data['unhealthy_count'] += 1
                host_data['health_status'] = 'unhealthy'
            else:
                host_data['unknown_count'] += 1
                if host_data['health_status'] == 'healthy':
                    host_data['health_status'] = 'warning'

        # 转换为列表并排序
        hosts_list = list(hosts_data.values())
        hosts_list.sort(key=lambda x: x['host_name'])

        # 总体统计
        total_services = len(self.last_results)
        total_healthy = sum(host['healthy_count'] for host in hosts_list)
        total_unhealthy = sum(host['unhealthy_count'] for host in hosts_list)
        total_unknown = sum(host['unknown_count'] for host in hosts_list)

        overall_status = 'healthy' if total_unhealthy == 0 else 'unhealthy'
        if total_unhealthy == 0 and total_unknown > 0:
            overall_status = 'warning'

        return {
            'hosts': hosts_list,
            'overall_status': overall_status,
            'total_services': total_services,
            'total_healthy': total_healthy,
            'total_unhealthy': total_unhealthy,
            'total_unknown': total_unknown,
            'last_check_time': self.last_check_time,
            'current_time': time.time()
        }

    def _get_host_config(self, host_name: str) -> Dict[str, Any]:
        """获取主机配置信息"""
        if (self.service_monitor and
                hasattr(self.service_monitor, 'detector_factory') and
                hasattr(self.service_monitor.detector_factory, 'ssh_servers_config')):
            return self.service_monitor.detector_factory.ssh_servers_config.get(host_name, {})
        return {}

    def _get_host_type(self, host_config: Dict[str, Any]) -> str:
        """获取主机类型"""
        if not host_config:
            return "本地主机"
        return "SSH远程主机"

    def update_results(self, results: List[CheckResult]):
        """更新检测结果"""
        self.last_results = results
        self.last_check_time = time.time()
        logging.info(f"更新Web界面数据: {len(results)}个服务状态")

    def run(self):
        """运行Web服务器"""
        logging.info(f"启动Web监控界面: http://{self.host}:{self.port}")
        self.app.run(host=self.host, port=self.port, debug=False)

    def run_in_thread(self):
        """在后台线程中运行Web服务器"""
        thread = threading.Thread(target=self.run, daemon=True)
        thread.start()
        return thread