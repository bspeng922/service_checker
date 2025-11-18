#!/usr/bin/env python3
"""
服务监控系统桌面客户端启动脚本
使用pywebview封装Web界面为桌面应用
"""
import sys
import os

import webview
import threading
import logging

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from service_monitor import ServiceMonitor


class App:
    def __init__(self):
        self.monitor = ServiceMonitor()
        self.window = None
        self.monitor_thread = None

    def start_monitor(self):
        """启动监控服务 - 使用service_monitor原有的run方法"""
        # 在单独线程中启动监控服务
        self.monitor_thread = threading.Thread(target=self.monitor.run, daemon=True)
        self.monitor_thread.start()
        logging.info("监控服务已启动")

    def stop_monitor(self):
        """停止监控服务"""
        if self.monitor:
            self.monitor.running = False
        logging.info("监控服务已停止")

    def on_closed(self):
        """窗口关闭时的清理"""
        self.stop_monitor()


def main():
    # 创建应用实例
    app = App()

    # 获取配置
    host = app.monitor.config.get('web_host', '127.0.0.1')
    port = app.monitor.config.get('web_port', 5000)
    url = f"http://{host}:{port}"

    # 创建窗口
    window = webview.create_window(
        title=app.monitor.config.get('window_title', '服务监控系统'),
        url=url,
        width=app.monitor.config.get('window_width', 1200),
        height=app.monitor.config.get('window_height', 800),
        resizable=True
    )

    # 设置关闭事件
    window.events.closed += app.on_closed

    # 启动监控服务
    app.start_monitor()

    # 启动GUI
    webview.start()


if __name__ == "__main__":
    main()
