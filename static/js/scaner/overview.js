/**
 * 漏洞扫描器 - 扫描概览
 */

function ScanerOverviewModule() {
    this.render = function(data, container) {
        var self = this;
        
        var html = `
<div class="scaner-overview-container">
    <div class="scaner-page-header">
        <h3>📊 扫描概览</h3>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
        <div class="stat-card stat-success">
            <div class="stat-content">
                <div class="stat-label">已扫描接口</div>
                <div class="stat-value" id="totalScanned">0</div>
            </div>
        </div>
        <div class="stat-card stat-danger">
            <div class="stat-content">
                <div class="stat-label">发现漏洞</div>
                <div class="stat-value" id="totalVulns">0</div>
            </div>
        </div>
        <div class="stat-card stat-warning">
            <div class="stat-content">
                <div class="stat-label">高危漏洞</div>
                <div class="stat-value" id="highVulns">0</div>
            </div>
        </div>
        <div class="stat-card stat-info">
            <div class="stat-content">
                <div class="stat-label">扫描器状态</div>
                <div class="stat-value">
                    <span id="scannerStatus" class="status-badge status-stopped">加载中...</span>
                </div>
            </div>
        </div>
    </div>

    <!-- 最近发现的漏洞 -->
    <div class="scaner-card">
        <div class="scaner-card-header">
            <strong>最近发现的漏洞</strong>
        </div>
        <div class="scaner-card-body">
            <table class="scaner-table">
                <thead>
                    <tr>
                        <th>漏洞类型</th>
                        <th>危害等级</th>
                        <th>目标URL</th>
                        <th>发现时间</th>
                    </tr>
                </thead>
                <tbody id="recentVulns">
                    <tr><td colspan="4" class="text-center">加载中...</td></tr>
                </tbody>
            </table>
        </div>
    </div>
</div>
        `;

        container.html(html);
        this.loadData(container);
    };

    this.loadData = function(container) {
        var self = this;
        
        // 加载服务状态
        this.loadServiceStatus(container);
        
        // 加载统计数据
        $.get('/api/scaner/stats', function(response) {
            if (response.success) {
                container.find('#totalScanned').text(response.data.scanned_count || 0);
                container.find('#totalVulns').text(response.data.total_vulns || 0);
                container.find('#highVulns').text(response.data.high_vulns || 0);
            }
        }).fail(function() {
            // 如果API失败，显示默认值
            container.find('#totalScanned').text('0');
            container.find('#totalVulns').text('0');
            container.find('#highVulns').text('0');
        });

        // 加载最近漏洞
        $.get('/api/scaner/results', { page: 1, page_size: 10 }, function(response) {
            if (response.success && response.data.results) {
                var tbody = container.find('#recentVulns');
                tbody.empty();
                
                if (response.data.results.length === 0) {
                    tbody.append('<tr><td colspan="4" class="text-center">暂无数据</td></tr>');
                    return;
                }
                
                response.data.results.forEach(function(item) {
                    var self = this;
                    var levelColor = self.getSeverityColor(item.level);
                    var levelText = self.getSeverityText(item.level);
                    
                    // 使用jQuery创建DOM元素，避免XSS
                    var tr = $('<tr></tr>');
                    
                    // 漏洞类型
                    tr.append($('<td></td>').text(item.vuln_type || '-'));
                    
                    // 危害等级
                    var badge = $('<span class="badge"></span>')
                        .addClass('badge-' + levelColor)
                        .text(levelText);
                    tr.append($('<td></td>').append(badge));
                    
                    // 目标URL
                    tr.append($('<td></td>').text(self.truncate(item.url, 50)));
                    
                    // 发现时间
                    tr.append($('<td></td>').text(self.formatDateTime(item.time)));
                    
                    tbody.append(tr);
                }.bind(this));
            }
        }.bind(this)).fail(function() {
            container.find('#recentVulns').html('<tr><td colspan="4" class="text-center">加载失败</td></tr>');
        }.bind(this));
    };

    this.getSeverityColor = function(severity) {
        var colors = {
            'high': 'danger',
            'medium': 'warning',
            'low': 'info'
        };
        return colors[severity] || 'secondary';
    };

    this.getSeverityText = function(severity) {
        var texts = {
            'high': '高危',
            'medium': '中危',
            'low': '低危'
        };
        return texts[severity] || '未知';
    };

    this.truncate = function(str, length) {
        if (!str) return '-';
        return str.length > length ? str.substring(0, length) + '...' : str;
    };

    this.formatDateTime = function(dateStr) {
        if (!dateStr) return '-';
        var date = new Date(dateStr);
        return date.toLocaleString('zh-CN');
    };

    // 加载服务状态
    this.loadServiceStatus = function(container) {
        var self = this;
        
        // 获取当前运行的项目
        $.get('/api/projects/status', function(statusData) {
            if (statusData.running_project) {
                var projectName = statusData.running_project.Project;
                
                // 获取项目配置中的 service_lock
                $.get('/api/projects/list', function(data) {
                    var project = data.projects.find(p => p.Project === projectName);
                    if (project && project.service_lock) {
                        var scanerService = project.service_lock.scaner_service || 0;
                        self.updateServiceStatus(container, scanerService);
                    } else {
                        self.updateServiceStatus(container, 0);
                    }
                }).fail(function() {
                    self.updateServiceStatus(container, 0);
                });
            } else {
                self.updateServiceStatus(container, 0);
            }
        }).fail(function() {
            self.updateServiceStatus(container, 0);
        });
    };

    // 更新服务状态显示
    this.updateServiceStatus = function(container, status) {
        var $element = container.find('#scannerStatus');
        var isRunning = status == 1 || status === true;
        
        if (isRunning) {
            $element.removeClass('status-stopped').addClass('status-running').text('运行中');
        } else {
            $element.removeClass('status-running').addClass('status-stopped').text('已停止');
        }
    };
}

console.log('[Scaner] ScanerOverviewModule loaded');
