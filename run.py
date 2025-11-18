#!/usr/bin/env python3
"""
服务监控系统启动脚本
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from service_monitor import ServiceMonitor

if __name__ == "__main__":
    print("启动服务监控系统...")
    print("Web监控界面: http://localhost:5000")
    print("按 Ctrl+C 停止监控")

    monitor = ServiceMonitor()

    try:
        monitor.run()
    except KeyboardInterrupt:
        print("\n监控服务已停止")
    except Exception as e:
        print(f"监控服务异常: {e}")
        sys.exit(1)