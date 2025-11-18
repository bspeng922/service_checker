class ServiceMonitor {
    constructor() {
        this.autoRefreshInterval = 30000; // 30秒自动刷新
        this.countdownInterval = null;
        this.countdownValue = 30;
        this.currentModalHost = null;

        this.init();
    }

    init() {
        this.bindEvents();
        this.loadStatus();
        this.startAutoRefresh();
    }

    bindEvents() {
        // 手动刷新按钮
        document.getElementById('refreshBtn').addEventListener('click', () => {
            this.manualRefresh();
        });

        // 模态框关闭事件
        const modal = document.getElementById('hostDetailModal');
        if (modal) {
            modal.addEventListener('hidden.bs.modal', () => {
                this.currentModalHost = null;
            });
        }
    }

    async loadStatus() {
        try {
            const response = await fetch('/api/status');
            if (!response.ok) {
                throw new Error(`HTTP错误: ${response.status}`);
            }
            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            this.updateDashboard(data);
        } catch (error) {
            console.error('加载状态失败:', error);
            this.showError('加载状态失败: ' + error.message);
        }
    }

    async manualRefresh() {
        const btn = document.getElementById('refreshBtn');
        const spinner = btn.querySelector('.loading-spinner');
        const text = btn.querySelector('span');

        // 显示加载状态
        spinner.style.display = 'inline-block';
        text.textContent = '刷新中...';
        btn.disabled = true;

        try {
            const response = await fetch('/api/refresh', { method: 'POST' });
            const result = await response.json();

            if (result.success) {
                // 重新加载状态
                await this.loadStatus();
                this.resetCountdown();
                this.showToast('刷新成功', 'success');
            } else {
                throw new Error(result.message);
            }
        } catch (error) {
            console.error('刷新失败:', error);
            this.showToast('刷新失败: ' + error.message, 'error');
        } finally {
            // 恢复按钮状态
            spinner.style.display = 'none';
            text.textContent = '刷新状态';
            btn.disabled = false;
        }
    }

    updateDashboard(data) {
        // 更新总体统计
        this.updateOverallStats(data);

        // 更新主机网格
        this.updateHostsGrid(data.hosts);

        // 更新时间
        this.updateTimeInfo(data);

        // 显示/隐藏空状态
        this.toggleEmptyState(data.hosts.length === 0);
    }

    updateOverallStats(data) {
        document.getElementById('healthyCount').textContent = data.total_healthy;
        document.getElementById('unhealthyCount').textContent = data.total_unhealthy;
        document.getElementById('unknownCount').textContent = data.total_unknown;
        document.getElementById('hostCount').textContent = data.hosts.length;

        // 更新总体状态徽章
        const overallStatusEl = document.getElementById('overallStatus');
        overallStatusEl.innerHTML = this.getStatusBadge(data.overall_status, this.getStatusText(data.overall_status));
    }

    updateHostsGrid(hosts) {
        const container = document.getElementById('hostsContainer');

        if (hosts.length === 0) {
            container.innerHTML = '<div class="text-center py-5"><p class="text-muted">暂无主机数据</p></div>';
            return;
        }

        container.innerHTML = `
            <div class="host-grid">
                ${hosts.map(host => this.renderHostCard(host)).join('')}
            </div>
        `;

        // 绑定卡片点击事件
        hosts.forEach(host => {
            const card = document.getElementById(`host-card-${this.escapeHtml(host.host_name)}`);
            if (card) {
                card.addEventListener('click', () => this.showHostDetails(host));
            }
        });
    }

    renderHostCard(host) {
        const healthScore = this.calculateHealthScore(host);
        const progressWidth = (host.healthy_count / host.total_services) * 100;

        return `
            <div class="card status-card host-card host-${host.health_status}" id="host-card-${this.escapeHtml(host.host_name)}">
                <div class="host-card-body">
                    <div class="text-center host-icon">
                        <i class="fas fa-server"></i>
                    </div>
                    
                    <h5 class="text-center mb-3">${this.escapeHtml(host.host_name)}</h5>
                    
                    <div class="health-score text-${this.getHealthScoreColor(healthScore)}">
                        ${healthScore}%
                    </div>
                    
                    <div class="progress">
                        <div class="progress-bar bg-success" style="width: ${progressWidth}%"></div>
                    </div>
                    
                    <div class="host-stats">
                        <div class="row text-center">
                            <div class="col-4">
                                <div class="text-success">
                                    <i class="fas fa-check-circle"></i>
                                    <div class="fw-bold">${host.healthy_count}</div>
                                    <small>健康</small>
                                </div>
                            </div>
                            <div class="col-4">
                                <div class="text-danger">
                                    <i class="fas fa-times-circle"></i>
                                    <div class="fw-bold">${host.unhealthy_count}</div>
                                    <small>异常</small>
                                </div>
                            </div>
                            <div class="col-4">
                                <div class="text-warning">
                                    <i class="fas fa-exclamation-circle"></i>
                                    <div class="fw-bold">${host.unknown_count}</div>
                                    <small>未知</small>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="text-center mt-3">
                        <span class="host-type-badge">${this.escapeHtml(host.host_type)}</span>
                        <small class="text-muted d-block mt-1">${host.host_address || '本地主机'}</small>
                    </div>
                    
                    <div class="text-center mt-3">
                        <button class="btn btn-sm btn-outline-primary" onclick="event.stopPropagation(); serviceMonitor.showHostDetails(${JSON.stringify(host).replace(/"/g, '&quot;')})">
                            <i class="fas fa-search me-1"></i>查看详情
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    showHostDetails(host) {
        this.currentModalHost = host;
        const modal = new bootstrap.Modal(document.getElementById('hostDetailModal'));

        // 更新模态框内容
        document.getElementById('modalHostName').textContent = host.host_name;
        document.getElementById('modalHostType').textContent = host.host_type;
        document.getElementById('modalHostAddress').textContent = host.host_address || '本地主机';
        document.getElementById('modalTotalServices').textContent = host.total_services;

        // 更新服务列表
        this.updateModalServices(host.services);

        // 更新连接信息
        this.updateConnectionInfo(host);

        modal.show();
    }

    updateModalServices(services) {
        const container = document.getElementById('modalServicesList');

        if (services.length === 0) {
            container.innerHTML = '<p class="text-muted text-center">该主机暂无服务</p>';
            return;
        }

        container.innerHTML = services.map(service => `
            <div class="modal-service-item service-${service.status}">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <h6 class="mb-1">
                            <i class="fas ${this.getServiceStatusIcon(service.status)} service-status-icon"></i>
                            ${this.escapeHtml(service.name)}
                        </h6>
                        <div class="d-flex align-items-center mb-2">
                            <span class="service-type-badge me-2">${this.escapeHtml(service.type)}</span>
                            ${this.getStatusBadge(service.status, this.getStatusText(service.status))}
                        </div>
                        <div class="service-details">
                            ${this.escapeHtml(service.message)}
                        </div>
                        ${this.renderServiceDetails(service.details)}
                    </div>
                </div>
            </div>
        `).join('');
    }

    updateConnectionInfo(host) {
        const container = document.getElementById('modalConnectionInfo');

        // 这里可以根据实际的主机配置信息显示更多连接详情
        container.innerHTML = `
            <div class="connection-detail">
                <span class="connection-label">主机名:</span>
                <span class="connection-value">${this.escapeHtml(host.host_name)}</span>
            </div>
            <div class="connection-detail">
                <span class="connection-label">类型:</span>
                <span class="connection-value">${this.escapeHtml(host.host_type)}</span>
            </div>
            <div class="connection-detail">
                <span class="connection-label">地址:</span>
                <span class="connection-value">${this.escapeHtml(host.host_address || '本地')}</span>
            </div>
            <div class="connection-detail">
                <span class="connection-label">服务数:</span>
                <span class="connection-value">${host.total_services} 个</span>
            </div>
        `;
    }

    calculateHealthScore(host) {
        if (host.total_services === 0) return 0;
        return Math.round((host.healthy_count / host.total_services) * 100);
    }

    getHealthScoreColor(score) {
        if (score >= 90) return 'success';
        if (score >= 70) return 'warning';
        return 'danger';
    }

    getServiceStatusIcon(status) {
        const icons = {
            healthy: 'fa-check-circle text-success',
            unhealthy: 'fa-times-circle text-danger',
            warning: 'fa-exclamation-circle text-warning',
            unknown: 'fa-question-circle text-secondary'
        };
        return icons[status] || 'fa-question-circle text-secondary';
    }

    renderServiceDetails(details) {
        if (!details || Object.keys(details).length === 0) {
            return '';
        }

        const detailItems = Object.entries(details)
            .filter(([key]) => key !== 'server')
            .map(([key, value]) =>
                `<span class="badge bg-light text-dark me-1 mb-1">${key}: ${value}</span>`
            ).join('');

        return detailItems ? `<div class="service-details mt-2">${detailItems}</div>` : '';
    }

    getStatusBadge(status, text) {
        const icons = {
            healthy: 'fa-check-circle',
            unhealthy: 'fa-times-circle',
            warning: 'fa-exclamation-circle',
            unknown: 'fa-question-circle'
        };

        return `
            <span class="status-badge badge-${status}">
                <i class="fas ${icons[status] || 'fa-question-circle'} me-1"></i>
                ${text}
            </span>
        `;
    }

    getStatusText(status) {
        const statusMap = {
            healthy: '健康',
            unhealthy: '异常',
            warning: '警告',
            unknown: '未知'
        };
        return statusMap[status] || status;
    }

    updateTimeInfo(data) {
        const lastUpdateEl = document.getElementById('lastUpdateTime');
        if (data.last_check_time) {
            const date = new Date(data.last_check_time * 1000);
            lastUpdateEl.textContent = date.toLocaleString('zh-CN');
        } else {
            lastUpdateEl.textContent = '--';
        }
    }

    toggleEmptyState(show) {
        const emptyState = document.getElementById('emptyState');
        const hostsContainer = document.getElementById('hostsContainer');

        if (show) {
            emptyState.style.display = 'block';
            hostsContainer.style.display = 'none';
        } else {
            emptyState.style.display = 'none';
            hostsContainer.style.display = 'block';
        }
    }

    startAutoRefresh() {
        this.countdownInterval = setInterval(() => {
            this.countdownValue--;
            document.getElementById('autoRefreshCountdown').textContent = this.countdownValue;

            if (this.countdownValue <= 0) {
                this.loadStatus();
                this.resetCountdown();
            }
        }, 1000);
    }

    resetCountdown() {
        this.countdownValue = 30;
        document.getElementById('autoRefreshCountdown').textContent = this.countdownValue;
    }

    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
        toast.style.position = 'fixed';
        toast.style.top = '20px';
        toast.style.right = '20px';
        toast.style.zIndex = '9999';
        toast.style.minWidth = '300px';
        toast.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(toast);

        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 3000);
    }

    showError(message) {
        this.showToast(message, 'error');
    }

    escapeHtml(unsafe) {
        if (unsafe === null || unsafe === undefined) return '';
        return unsafe.toString()
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
}

// 全局实例
let serviceMonitor;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    serviceMonitor = new ServiceMonitor();
});