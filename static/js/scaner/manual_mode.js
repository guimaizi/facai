/**
 * 漏洞扫描器 - 手动模式
 * 现代化设计：卡片布局 + 平铺展示
 */

function ScanerManualModeModule() {
    var self = this;
    
    this.render = function(data, container) {
        container.html(`
<div class="manual-page">
    <!-- 页面头部 -->
    <div class="page-header">
        <div class="header-content">
            <h2 class="page-title">手动扫描</h2>
            <p class="page-desc">粘贴HTTP请求，快速检测安全漏洞</p>
        </div>
        <div class="header-actions">
            <button class="btn btn-light" id="clearBtn">
                <span>清空</span>
            </button>
            <button class="btn btn-primary" id="scanBtn">
                <span>开始扫描</span>
            </button>
        </div>
    </div>

    <!-- 主要内容区 -->
    <div class="main-content">
        <!-- 左侧：输入区域 -->
        <div class="input-panel">
            <div class="panel-header">
                <div class="panel-tabs">
                    <button class="mode-tab active" data-mode="burp">
                        <span class="mode-icon">📋</span>
                        Burp格式
                    </button>
                    <button class="mode-tab" data-mode="json">
                        <span class="mode-icon">{ }</span>
                        JSON格式
                    </button>
                </div>
            </div>
            <div class="panel-body">
                <div class="input-wrapper" id="burpWrapper">
                    <textarea id="burpText" placeholder="粘贴 Burp Suite 的原始请求...&#10;&#10;示例：&#10;GET /api/user?id=123 HTTP/1.1&#10;Host: example.com&#10;User-Agent: Mozilla/5.0&#10;&#10;请求体内容"></textarea>
                    <div class="input-hint">
                        <span class="hint-icon">💡</span>
                        <span>支持直接粘贴 Burp Suite 复制的请求，按 Ctrl+Enter 快速扫描</span>
                    </div>
                </div>
                <div class="input-wrapper" id="jsonWrapper" style="display:none;">
                    <textarea id="jsonText" placeholder='输入 JSON 格式请求...&#10;&#10;示例：&#10;{&#10;  "method": "GET",&#10;  "url": "https://example.com/api/user?id=123",&#10;  "headers": {&#10;    "Cookie": "session=abc123"&#10;  },&#10;  "body": ""&#10;}'></textarea>
                    <div class="input-hint">
                        <span class="hint-icon">💡</span>
                        <span>JSON 格式便于程序化调用，按 Ctrl+Enter 快速扫描</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- 右侧：结果区域 -->
        <div class="result-panel">
            <div class="panel-header">
                <h3 class="panel-title">扫描结果</h3>
                <div class="panel-status" id="scanStatus" style="display:none;">
                    <div class="status-spinner"></div>
                    <span id="statusText">扫描中...</span>
                </div>
            </div>
            <div class="panel-body" id="resultBody">
                <div class="empty-state">
                    <div class="empty-icon">🔍</div>
                    <h4>等待扫描</h4>
                    <p>粘贴请求内容后点击"开始扫描"</p>
                </div>
            </div>
        </div>
    </div>
</div>
        `);
        
        this.bindEvents(container);
        
        // 从本地存储恢复之前保存的状态
        this.restoreFromStorage(container);
    };
    
    this.bindEvents = function(container) {
        var self = this;
        
        // 模式切换并保存
        container.find('.mode-tab').off('click').on('click', function() {
            container.find('.mode-tab').removeClass('active');
            $(this).addClass('active');
            
            var mode = $(this).data('mode');
            if (mode === 'burp') {
                container.find('#burpWrapper').show();
                container.find('#jsonWrapper').hide();
                self.jsonToBurp(container);
            } else {
                container.find('#burpWrapper').hide();
                container.find('#jsonWrapper').show();
                self.burpToJson(container);
            }
            
            // 保存模式切换
            self.saveToStorage(container);
        });
        
        // Burp输入自动同步并保存
        container.find('#burpText').off('input').on('input', function() {
            self.burpToJson(container);
            self.saveToStorage(container);
        });
        
        // JSON输入自动同步并保存
        container.find('#jsonText').off('input').on('input', function() {
            self.jsonToBurp(container);
            self.saveToStorage(container);
        });
        
        // 开始扫描
        container.find('#scanBtn').off('click').on('click', function() {
            self.startScan(container);
        });
        
        // 清空
        container.find('#clearBtn').off('click').on('click', function() {
            self.clearAll(container);
        });
        
        // 快捷键
        container.find('textarea').off('keydown').on('keydown', function(e) {
            if (e.ctrlKey && e.key === 'Enter') {
                self.startScan(container);
            }
        });
    };
    
    this.burpToJson = function(container) {
        var burpText = container.find('#burpText').val();
        if (!burpText.trim()) return;
        
        try {
            var lines = burpText.split('\n');
            var firstLine = lines[0].trim();
            var match = firstLine.match(/^([A-Z]+)\s+(.+?)\s+HTTP\/\d\.\d$/i);
            
            if (match) {
                var method = match[1];
                var url = match[2];
                var headers = {};
                var body = '';
                var emptyLineIndex = -1;
                
                for (var i = 1; i < lines.length; i++) {
                    var line = lines[i];
                    if (line.trim() === '') {
                        emptyLineIndex = i;
                        break;
                    }
                    var parts = line.split(':');
                    if (parts.length >= 2) {
                        headers[parts[0].trim()] = parts.slice(1).join(':').trim();
                    }
                }
                
                if (emptyLineIndex > 0 && emptyLineIndex < lines.length - 1) {
                    body = lines.slice(emptyLineIndex + 1).join('\n');
                }
                
                if (url && !url.match(/^https?:\/\//i)) {
                    var host = headers['Host'] || headers['host'];
                    if (host) {
                        var protocol = 'http';
                        if (host.indexOf(':443') > 0) protocol = 'https';
                        url = protocol + '://' + host + url;
                    }
                }
                
                container.find('#jsonText').val(JSON.stringify({
                    method: method,
                    url: url,
                    headers: headers,
                    body: body
                }, null, 2));
            }
        } catch (e) {}
    };
    
    this.jsonToBurp = function(container) {
        var jsonText = container.find('#jsonText').val();
        if (!jsonText.trim()) return;
        
        try {
            var data = JSON.parse(jsonText);
            var burp = (data.method || 'GET') + ' ' + (data.url || '') + ' HTTP/1.1\n';
            var headers = data.headers || {};
            for (var key in headers) {
                burp += key + ': ' + headers[key] + '\n';
            }
            burp += '\n';
            if (data.body) burp += data.body;
            
            container.find('#burpText').val(burp);
        } catch (e) {}
    };
    
    this.startScan = function(container) {
        var self = this;
        
        var isBurpMode = container.find('#burpWrapper').is(':visible');
        var requestData = null;
        
        if (isBurpMode) {
            this.burpToJson(container);
            var jsonText = container.find('#jsonText').val().trim();
            if (!jsonText) {
                this.showError(container, '请输入请求内容');
                return;
            }
            try {
                requestData = JSON.parse(jsonText);
            } catch (e) {
                this.showError(container, '请求格式错误');
                return;
            }
        } else {
            var jsonText = container.find('#jsonText').val().trim();
            if (!jsonText) {
                this.showError(container, '请输入请求内容');
                return;
            }
            try {
                requestData = JSON.parse(jsonText);
            } catch (e) {
                this.showError(container, 'JSON格式错误');
                return;
            }
        }
        
        if (!requestData.url) {
            this.showError(container, '缺少URL');
            return;
        }
        
        // 直接执行扫描（与 test_vuln_scanner.py 保持一致）
        container.find('#scanStatus').show();
        container.find('#statusText').text('扫描中...');
        self.executeScan(container, requestData);
    };
    
    this.executeScan = function(container, requestData) {
        var self = this;
        
        $.ajax({
            url: '/api/scaner/manual/start',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ request: requestData }),
            success: function(response) {
                container.find('#scanStatus').hide();
                if (response.success) {
                    self.showResults(container, response.data);
                } else {
                    self.showError(container, response.message);
                }
            },
            error: function(xhr) {
                container.find('#scanStatus').hide();
                var msg = '扫描失败';
                if (xhr.responseJSON && xhr.responseJSON.message) {
                    msg = xhr.responseJSON.message;
                }
                self.showError(container, msg);
            }
        });
    };
    
    this.showResults = function(container, data) {
        var self = this;
        var resultBody = container.find('#resultBody');
        
        if (!data.details || data.details.length === 0) {
            resultBody.html(`
                <div class="success-state">
                    <div class="success-icon">✅</div>
                    <h4>扫描完成</h4>
                    <p>未发现漏洞</p>
                    <div class="result-meta">
                        <span>目标: ${self.escapeHtml(data.url || '-')}</span>
                    </div>
                </div>
            `);
            return;
        }
        
        var vulns = data.details.filter(function(v) { return v !== null; });
        
        var html = `
            <div class="result-summary">
                <div class="summary-item danger">
                    <span class="summary-value">${vulns.length}</span>
                    <span class="summary-label">发现漏洞</span>
                </div>
            </div>
            <div class="vuln-list">
        `;
        
        vulns.forEach(function(vuln, index) {
            var level = vuln.level || 'medium';
            var levelClass = level === 'high' ? 'danger' : (level === 'medium' ? 'warning' : 'info');
            var levelText = level === 'high' ? '高危' : (level === 'medium' ? '中危' : '低危');
            
            html += `
                <div class="vuln-card ${level}">
                    <div class="vuln-header">
                        <span class="vuln-level vuln-badge-${levelClass}">${levelText}</span>
                        <span class="vuln-type">${self.escapeHtml(vuln.vuln_type_detail || vuln.vuln_type || '未知')}</span>
                    </div>
                    <div class="vuln-info">
                        <div class="info-item">
                            <span class="info-label">参数</span>
                            <code class="info-value">${self.escapeHtml(vuln.paramname || '-')}</code>
                        </div>
                        <div class="info-item">
                            <span class="info-label">网站</span>
                            <span class="info-value">${self.escapeHtml(vuln.website || '-')}</span>
                        </div>
                        <div class="info-item full-width">
                            <span class="info-label">URL</span>
                            <code class="info-value url">${self.escapeHtml(vuln.url || '-')}</code>
                        </div>
                    </div>
                    <div class="vuln-footer">
                        <button class="btn btn-sm btn-outline-${levelClass}" onclick="window.open('/api/scaner/results', '_blank')">查看详情</button>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        resultBody.html(html);
    };
    
    this.showError = function(container, message) {
        container.find('#resultBody').html(`
            <div class="error-state">
                <div class="error-icon">⚠️</div>
                <h4>扫描失败</h4>
                <p>${this.escapeHtml(message)}</p>
            </div>
        `);
    };
    
    this.clearAll = function(container) {
        container.find('#burpText').val('');
        container.find('#jsonText').val('');
        container.find('#scanStatus').hide();
        container.find('#resultBody').html(`
            <div class="empty-state">
                <div class="empty-icon">🔍</div>
                <h4>等待扫描</h4>
                <p>粘贴请求内容后点击"开始扫描"</p>
            </div>
        `);
    };
    
    this.escapeHtml = function(text) {
        if (!text) return '';
        var div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    };
    
    /**
     * 保存到本地存储
     */
    this.saveToStorage = function(container) {
        try {
            var state = {
                burpText: container.find('#burpText').val(),
                jsonText: container.find('#jsonText').val(),
                mode: container.find('.mode-tab.active').data('mode')
            };
            sessionStorage.setItem('manual_mode_state', JSON.stringify(state));
        } catch (e) {
            console.warn('保存状态失败:', e);
        }
    };
    
    /**
     * 从本地存储恢复
     */
    this.restoreFromStorage = function(container) {
        try {
            var stateStr = sessionStorage.getItem('manual_mode_state');
            if (!stateStr) return;
            
            var state = JSON.parse(stateStr);
            if (!state) return;
            
            // 恢复输入内容
            if (state.burpText) {
                container.find('#burpText').val(state.burpText);
            }
            if (state.jsonText) {
                container.find('#jsonText').val(state.jsonText);
            }
            
            // 恢复模式（Burp/JSON）
            if (state.mode) {
                container.find('.mode-tab').removeClass('active');
                container.find('.mode-tab[data-mode="' + state.mode + '"]').addClass('active');
                
                if (state.mode === 'burp') {
                    container.find('#burpWrapper').show();
                    container.find('#jsonWrapper').hide();
                } else {
                    container.find('#burpWrapper').hide();
                    container.find('#jsonWrapper').show();
                }
            }
        } catch (e) {
            console.warn('恢复状态失败:', e);
        }
    };
}

console.log('[Scaner] ScanerManualModeModule loaded');
