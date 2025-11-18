import paramiko
import logging
from typing import Dict, Any, Optional
from contextlib import contextmanager


class SSHManager:
    """SSH连接管理器"""

    def __init__(self):
        self.connections: Dict[str, paramiko.SSHClient] = {}
        self.logger = logging.getLogger(self.__class__.__name__)

    def connect(self, server_config: Dict[str, Any]) -> paramiko.SSHClient:
        """建立SSH连接"""
        server_name = server_config.get('name', 'unknown')
        host = server_config['host']
        port = server_config.get('port', 22)
        username = server_config['username']

        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # 认证方式：优先使用密钥文件
            key_file = server_config.get('key_file')
            password = server_config.get('password')

            if key_file:
                # 扩展用户目录
                if key_file.startswith('~'):
                    import os
                    key_file = os.path.expanduser(key_file)

                client.connect(
                    hostname=host,
                    port=port,
                    username=username,
                    key_filename=key_file,
                    timeout=server_config.get('timeout', 10)
                )
            elif password:
                client.connect(
                    hostname=host,
                    port=port,
                    username=username,
                    password=password,
                    timeout=server_config.get('timeout', 10)
                )
            else:
                raise ValueError("Either key_file or password must be provided")

            self.connections[server_name] = client
            self.logger.info(f"SSH连接成功: {server_name} ({host}:{port})")
            return client

        except Exception as e:
            self.logger.error(f"SSH连接失败 {server_name}: {str(e)}")
            raise

    def get_connection(self, server_name: str, server_config: Dict[str, Any]) -> paramiko.SSHClient:
        """获取SSH连接，如果不存在则创建"""
        if server_name in self.connections:
            client = self.connections[server_name]
            # 检查连接是否仍然有效
            try:
                client.exec_command('echo "test"', timeout=5)
                return client
            except:
                self.logger.warning(f"SSH连接已断开，重新连接: {server_name}")
                del self.connections[server_name]

        return self.connect({**server_config, 'name': server_name})

    @contextmanager
    def get_ssh_client(self, server_config: Dict[str, Any]):
        """上下文管理器获取SSH客户端"""
        server_name = server_config.get('name', 'unknown')
        client = None
        try:
            client = self.get_connection(server_name, server_config)
            yield client
        except Exception as e:
            self.logger.error(f"SSH操作失败 {server_name}: {str(e)}")
            raise
        # 注意：不在这里关闭连接，保持连接复用

    def close_all(self):
        """关闭所有SSH连接"""
        for server_name, client in self.connections.items():
            try:
                client.close()
                self.logger.info(f"关闭SSH连接: {server_name}")
            except Exception as e:
                self.logger.error(f"关闭SSH连接失败 {server_name}: {str(e)}")
        self.connections.clear()


# 全局SSH管理器实例
ssh_manager = SSHManager()