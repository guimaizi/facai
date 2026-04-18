function PortScanModule() {
    this.render = function(data, container) {
        container.html(`
            <div class="port-scan-container">
                <div class="port-scan-header">
                    <h3>🔍 端口扫描</h3>
                    <div class="scan-actions">
                        <button class="btn btn-secondary btn-sm" id="clearResult">
                            <span class="btn-icon">🗑️</span>
                            <span>清空</span>
                        </button>
                        <button class="btn btn-success btn-sm" id="startScan">
                            <span class="btn-icon">🚀</span>
                            <span>开始扫描</span>
                        </button>
                    </div>
                </div>

                <div class="scan-form">
                    <div class="form-row">
                        <div class="form-group">
                            <label>目标IP</label>
                            <input type="text" id="scanTarget" placeholder="例如: 192.168.1.1 或 example.com">
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="form-group">
                            <label>Nmap参数</label>
                            <input type="text" id="scanArgs" placeholder="例如: -sV -O --script vuln" value="-sV">
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="form-group">
                            <label>端口范围</label>
                            <input type="text" id="scanPorts" placeholder="例如: 80,443,8080-8090">
                            <small class="text-muted">留空则使用项目默认端口配置</small>
                        </div>
                    </div>
                </div>

                <!-- 扫描结果 -->
                <div class="scan-result" id="scanResult">
                    <div class="empty-result">
                        <div class="empty-icon">📊</div>
                        <p>配置扫描参数后点击"开始扫描"</p>
                        <p class="empty-hint">扫描结果将在此显示</p>
                    </div>
                </div>
            </div>
        `);

        this.loadDefaultPorts();
        this.bindEvents();
    };

    this.loadDefaultPorts = function() {
        var self = this;

        // 获取当前运行的项目配置
        $.ajax({
            url: '/api/projects/status',
            type: 'GET',
            success: function(statusData) {
                if (statusData.running_project) {
                    // 获取项目列表以获取完整配置
                    $.ajax({
                        url: '/api/projects/list',
                        type: 'GET',
                        success: function(data) {
                            var project = data.projects.find(p => p.Project === statusData.running_project.Project);
                            if (project && project.port_target) {
                                $('#scanPorts').val(project.port_target);
                            }
                        }
                    });
                }
            }
        });
    };

    this.bindEvents = function() {
        var self = this;

        // 开始扫描
        $('#startScan').on('click', function() {
            self.startScan();
        });

        // 清空结果
        $('#clearResult').on('click', function() {
            if (confirm('确定要清空扫描结果吗？')) {
                self.clearResult();
            }
        });
    };

    this.startScan = function() {
        var self = this;
        var target = $('#scanTarget').val().trim();
        var args = $('#scanArgs').val().trim();
        var ports = $('#scanPorts').val().trim();

        // 验证必填字段
        if (!target) {
            this.showError('请输入目标IP地址或域名');
            return;
        }

        // 如果没有指定端口，使用项目默认端口
        if (!ports) {
            this.showError('请输入端口范围或等待加载项目默认端口配置');
            return;
        }

        // 显示加载状态
        this.showLoading();

        // 发送扫描请求
        $.ajax({
            url: '/api/tools/port-scan',
            type: 'POST',
            data: {
                ip: target,
                args: args,
                ports: ports
            },
            success: function(data) {
                if (data.error) {
                    self.showError(data.error);
                } else {
                    self.showResult(data);
                }
            },
            error: function(xhr) {
                var errorMsg = '扫描失败';
                if (xhr.responseJSON && xhr.responseJSON.error) {
                    errorMsg = xhr.responseJSON.error;
                } else if (xhr.responseText) {
                    errorMsg = '扫描失败: ' + xhr.responseText;
                }
                self.showError(errorMsg);
            }
        });
    };

    this.showLoading = function() {
        $('#scanResult').html(`
            <div class="loading-state">
                <div class="spinner"></div>
                <p>正在扫描中，请稍候...</p>
                <p class="text-muted">扫描时间可能较长，请耐心等待</p>
            </div>
        `);
    };

    this.showResult = function(data) {
        var resultHtml = '';

        // 显示扫描信息
        resultHtml += `
            <div class="result-section scan-info">
                <h4>📋 扫描信息</h4>
                <div class="info-grid">
                    <div class="info-item">
                        <label>目标</label>
                        <span>${this.escapeHtml(data.target || data.ip || 'N/A')}</span>
                    </div>
                    <div class="info-item">
                        <label>端口</label>
                        <span>${this.escapeHtml(data.ports || 'N/A')}</span>
                    </div>
                    <div class="info-item">
                        <label>扫描参数</label>
                        <span>${this.escapeHtml(data.args || 'N/A')}</span>
                    </div>
                </div>
            </div>
        `;

        // 显示扫描结果
        if (data.results && data.results.length > 0) {
            var openPorts = data.results.filter(r => r.status === 'open');

            resultHtml += `
                <div class="result-section">
                    <div class="section-header">
                        <h4>🎯 扫描结果</h4>
                        <div class="section-actions">
                            <span class="badge badge-success">${openPorts.length} 个开放端口</span>
                            <button class="btn btn-primary btn-sm" id="copyResult">
                                <span class="btn-icon">📋</span>
                                <span>复制</span>
                            </button>
                        </div>
                    </div>
                    <div class="scan-results-list">
                        ${data.results.map(function(item) {
                            var statusClass = item.status === 'open' ? 'status-open' : 'status-closed';
                            var statusIcon = item.status === 'open' ? '✅' : '❌';

                            return `
                                <div class="scan-result-item ${statusClass}">
                                    <div class="result-main">
                                        <span class="port-number">${item.port}</span>
                                        <span class="port-status status-badge ${statusClass}">${statusIcon} ${item.status}</span>
                                        <span class="port-service">${item.service || item.protocol || 'unknown'}</span>
                                    </div>
                                    ${item.version ? `<div class="result-detail">${this.escapeHtml(item.version)}</div>` : ''}
                                </div>
                            `;
                        }.bind(this)).join('')}
                    </div>
                </div>
            `;

            // 显示原始输出
            if (data.raw_output) {
                resultHtml += `
                    <div class="result-section">
                        <div class="section-header">
                            <h4>💻 原始输出</h4>
                            <button class="btn btn-secondary btn-sm" id="toggleRaw">
                                <span class="btn-icon">👁️</span>
                                <span>显示/隐藏</span>
                            </button>
                        </div>
                        <pre class="code-block raw-output" style="display: none;">${this.escapeHtml(data.raw_output)}</pre>
                    </div>
                `;
            }
        } else {
            resultHtml += `
                <div class="result-section">
                    <h4>🎯 扫描结果</h4>
                    <div class="empty-result">
                        <div class="empty-icon">🔍</div>
                        <p>未发现开放端口</p>
                    </div>
                </div>
            `;
        }

        $('#scanResult').html(resultHtml);

        // 绑定事件
        this.bindResultEvents();
    };

    this.bindResultEvents = function() {
        var self = this;

        // 复制结果
        $('#copyResult').on('click', function() {
            var results = $('.scan-result-item').map(function() {
                var port = $(this).find('.port-number').text();
                var status = $(this).find('.port-status').text();
                var service = $(this).find('.port-service').text();
                var version = $(this).find('.result-detail').text();
                return `${port} - ${status} - ${service}${version ? ' - ' + version : ''}`;
            }).get().join('\n');

            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(results).then(function() {
                    self.showToast('复制成功！');
                }).catch(function() {
                    self.fallbackCopy(results);
                });
            } else {
                self.fallbackCopy(results);
            }
        });

        // 切换原始输出显示
        $('#toggleRaw').on('click', function() {
            $('.raw-output').toggle();
        });
    };

    this.showError = function(message) {
        $('#scanResult').html(`
            <div class="error-state">
                <div class="error-icon">❌</div>
                <p>${this.escapeHtml(message)}</p>
            </div>
        `);
    };

    this.clearResult = function() {
        $('#scanResult').html(`
            <div class="empty-result">
                <div class="empty-icon">📊</div>
                <p>配置扫描参数后点击"开始扫描"</p>
                <p class="empty-hint">扫描结果将在此显示</p>
            </div>
        `);
    };

    this.escapeHtml = function(text) {
        var div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    };

    this.fallbackCopy = function(text) {
        var textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();

        try {
            document.execCommand('copy');
            this.showToast('复制成功！');
        } catch (err) {
            alert('复制失败，请手动复制');
        }

        document.body.removeChild(textarea);
    };

    this.showToast = function(message) {
        var toast = $('<div class="scan-toast">' + message + '</div>');
        $('body').append(toast);

        setTimeout(function() {
            toast.addClass('show');
        }, 10);

        setTimeout(function() {
            toast.removeClass('show');
            setTimeout(function() {
                toast.remove();
            }, 300);
        }, 2000);
    };
}
