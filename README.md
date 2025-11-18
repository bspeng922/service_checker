# 服务检测工具

一个基于Python的多功能服务状态检测工具，支持本地和远程服务器检测。

## 功能特性

- 🔍 **多服务类型支持**
  - Systemd 服务检测
  - Supervisor 进程检测
  - Docker 容器检测
  - REST API 健康检查

- 🎯 **用户友好界面**
  - 简洁的Web界面
  - 实时状态展示
  - 一键检测操作

## 快速开始

### 环境要求

- Python 3.7+
- 依赖包：见 `requirements.txt`

### 安装步骤

1. **克隆项目**

   bash

   ```
   git clone <项目地址>
   cd service_checker
   ```

   

2. **安装依赖**

   bash

   ```
   pip install -r requirements.txt
   ```
   

### 启动应用

bash

```
python run.py
```



启动后访问：[http://localhost:5000](http://localhost:5000/)

## 界面展示

### 主仪表板

![](static/image/dashboard.png)
*主界面显示所有配置服务的实时状态概览*


## 配置文件说明

`config.yaml` 主要配置项：

yaml

```
# 检测间隔（秒）
check_interval: 30
# 检测并发数量
max_workers: 5
# 日志等级
log_level: "INFO"

# SSH远程服务器配置
ssh_servers:
  web-server:
    name: "web-server"  
    host: "10.100.27.1"
    port: 22
    username: "root"
    password: "QWEasd123#"  # 建议使用key_file
    key_file: ""
    timeout: 10

# 服务配置
services:
  # 本地服务检测
  - name: "local-nginx"
    type: "systemd"
    server: "web-server"  # 引用ssh_servers中的配置
    config:
      service_name: "nginx"
      expected_status: "active"
    # 不指定server表示本地检测
```


## 使用说明

1. **配置检测目标**：在 `config.yaml` 中设置需要监控的服务
2. **启动应用**：运行 `python run.py` 启动Web服务
3. **访问界面**：通过浏览器访问管理界面 
4. **查看状态**：界面将自动显示各服务的实时状态
5. **手动检测**：支持手动触发即时检测

## 故障排除

### 常见问题

1. **SSH连接失败**
   - 检查网络连通性
   - 验证SSH认证信息
   - 确认防火墙设置
2. **服务检测超时**
   - 调整检测超时时间
   - 检查目标服务可访问性
3. **权限问题**
   - 确保有足够的系统权限
   - 检查Sudo配置（如需要）
