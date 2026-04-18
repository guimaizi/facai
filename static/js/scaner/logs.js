/**
 * 漏洞扫描器 - 盲打日志
 */

function ScanerLogsModule() {
    this.currentPage = 1;
    this.pageSize = 20;
    
    this.render = function(data, container) {
        var self = this;

        var html = `
<div class="scaner-logs-scope">
<div class="scaner-logs-container">
    <div class="scaner-page-header">
        <h3> \u0020🔍 盲打日志（RCE/SSRF）</h3>
    </div>

    <div class="scaner-toolbar">
        <div class="scaner-btn-group">
            <button class="btn btn-secondary" id="refreshLogs">\u0020
                <span class="btn-icon">🔄</span>
                <span>刷新</span>
            </button>
            <button class="btn btn-danger" id="clearLogs">
                <span class="btn-icon">🗑️</span>
                <span>清空</span>
            </button>
        </div>

        <div class="search-box">
            <input type="text" id="hashSearch" placeholder="输入 vuln_hash 搜索..." class="form-control">
            <button class="btn btn-primary" id="searchByHash">搜索</button>
        </div>

        <select class="form-control status-filter" id="statusFilter">
            <option value="">全部状态</option>
            <option value="0">未验证</option>
            <option value="1">已验证</option>
        </select>
    </div>

    <div class="scaner-card">
        <div class="scaner-card-body">
            <table class="scaner-table">
                <thead>
                    <tr>
                        <th>vuln_hash</th>
                        <th>漏洞类型</th>
                        <th>参数名</th>
                        <th>目标URL</th>
                        <th>状态</th>
                        <th>时间</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody id="logsBody">
                    <tr><td colspan="7" class="text-center">加载中...</td></tr>
                </tbody>
            </table>
            <div id="pagination"></div>
        </div>
    </div>
</div>
</div>
        `;

        container.html(html);
        this.loadLogs(container);
        this.bindEvents(container);
    };

    this.loadLogs = function(container) {
        var self = this;
        var status = container.find('#statusFilter').val();
        
        $.get('/api/scaner/logs', { 
            status: status, 
            page: self.currentPage,
            page_size: self.pageSize
        }, function(response) {
            if (response.success && response.data.logs) {
                var tbody = container.find('#logsBody');
                tbody.empty();
                
                if (response.data.logs.length === 0) {
                    tbody.append('<tr><td colspan="7" class="text-center">暂无数据</td></tr>');
                    container.find('#pagination').empty();
                    return;
                }
                
                response.data.logs.forEach(function(item) {
                    // 使用jQuery创建DOM元素，避免XSS
                    var tr = $('<tr></tr>');
                    
                    // vuln_hash
                    var code = $('<code></code>').text(item.vuln_hash || '-');
                    tr.append($('<td></td>').append(code));
                    
                    // 漏洞类型
                    var typeColor = item.vuln_type === 'rce' ? 'danger' : 'info';
                    var typeBadge = $('<span class="badge"></span>')
                        .addClass('badge-' + typeColor)
                        .text(item.vuln_type || '-');
                    tr.append($('<td></td>').append(typeBadge));
                    
                    // 参数名
                    tr.append($('<td></td>').text(item.param_name || '-'));
                    
                    // 目标URL
                    var url = item.request ? item.request.url : '';
                    tr.append($('<td></td>').text(self.truncate(url, 50)));
                    
                    // 状态
                    var statusBadge = item.status === 1 
                        ? $('<span class="badge badge-success">已验证</span>')
                        : $('<span class="badge badge-warning">未验证</span>');
                    tr.append($('<td></td>').append(statusBadge));
                    
                    // 时间
                    tr.append($('<td></td>').text(self.formatDateTime(item.time)));
                    
                    // 操作按钮
                    var tdBtn = $('<td></td>');
                    
                    var btnDetail = $('<button class="btn btn-sm btn-info view-log">详情</button>')
                        .data('hash', item.vuln_hash);
                    
                    tdBtn.append(btnDetail);
                    
                    if (item.status === 0) {
                        var btnVerify = $('<button class="btn btn-sm btn-success verify-log">验证</button>')
                            .data('hash', item.vuln_hash);
                        tdBtn.append(' ').append(btnVerify);
                    }
                    
                    tr.append(tdBtn);
                    tbody.append(tr);
                });
                
                // 渲染分页
                var paginationHtml = PageUp.generatePagination({
                    currentPage: response.data.page,
                    totalPages: response.data.total_pages,
                    onPageChange: function(page) {
                        self.currentPage = page;
                        self.loadLogs(container);
                    }
                });
                container.find('#pagination').html(paginationHtml);
            }
        }).fail(function() {
            container.find('#logsBody').html('<tr><td colspan="7" class="text-center">加载失败</td></tr>');
        });
    };

    this.bindEvents = function(container) {
        var self = this;
        
        container.find('#refreshLogs').off('click').on('click', function() {
            self.loadLogs(container);
        });
        
        container.find('#clearLogs').off('click').on('click', function() {
            if (confirm('确定要清空所有日志吗？')) {
                $.post('/api/scaner/logs/clear', function(response) {
                    if (response.success) {
                        alert('已清空');
                        self.loadLogs(container);
                    }
                });
            }
        });
        
        container.find('#statusFilter').off('change').on('change', function() {
            self.currentPage = 1; // 重置到第一页
            self.loadLogs(container);
        });
        
        container.find('#searchByHash').off('click').on('click', function() {
            var hash = container.find('#hashSearch').val().trim();
            if (hash) {
                self.searchByHash(container, hash);
            }
        });
        
        container.find('#hashSearch').off('keypress').on('keypress', function(e) {
            if (e.which === 13) {  // Enter键
                var hash = $(this).val().trim();
                if (hash) {
                    self.searchByHash(container, hash);
                }
            }
        });
        
        container.on('click', '.view-log', function() {
            var hash = $(this).data('hash');
            self.showLogDetail(container, hash);
        });
        
        container.on('click', '.verify-log', function() {
            var hash = $(this).data('hash');
            self.verifyLog(container, hash);
        });
    };

    this.searchByHash = function(container, hash) {
        var self = this;
        
        $.get('/api/scaner/logs/search', { vuln_hash: hash }, function(response) {
            if (response.success) {
                var item = response.data;
                var tbody = container.find('#logsBody');
                tbody.empty();
                
                // 使用jQuery创建DOM元素，避免XSS
                var tr = $('<tr></tr>');
                
                // vuln_hash
                var code = $('<code></code>').text(item.vuln_hash || '-');
                tr.append($('<td></td>').append(code));
                
                // 漏洞类型
                var typeColor = item.vuln_type === 'rce' ? 'danger' : 'info';
                var typeBadge = $('<span class="badge"></span>')
                    .addClass('badge-' + typeColor)
                    .text(item.vuln_type || '-');
                tr.append($('<td></td>').append(typeBadge));
                
                // 参数名
                tr.append($('<td></td>').text(item.param_name || '-'));
                
                // 目标URL
                var url = item.request ? item.request.url : '';
                tr.append($('<td></td>').text(self.truncate(url, 50)));
                
                // 状态
                var statusBadge = item.status === 1 
                    ? $('<span class="badge badge-success">已验证</span>')
                    : $('<span class="badge badge-warning">未验证</span>');
                tr.append($('<td></td>').append(statusBadge));
                
                // 时间
                tr.append($('<td></td>').text(self.formatDateTime(item.time)));
                
                // 操作按钮
                var tdBtn = $('<td></td>');
                
                var btnDetail = $('<button class="btn btn-sm btn-info view-log">详情</button>')
                    .data('hash', item.vuln_hash);
                
                tdBtn.append(btnDetail);
                
                if (item.status === 0) {
                    var btnVerify = $('<button class="btn btn-sm btn-success verify-log">验证</button>')
                        .data('hash', item.vuln_hash);
                    tdBtn.append(' ').append(btnVerify);
                }
                
                tr.append(tdBtn);
                tbody.append(tr);
            }
        }).fail(function(xhr) {
            var msg = xhr.responseJSON ? xhr.responseJSON.message : '查询失败';
            alert('搜索失败: ' + msg);
        });
    };

    this.showLogDetail = function(container, hash) {
        var self = this;
        $.get('/api/scaner/logs/search', { vuln_hash: hash }, function(response) {
            if (response.success) {
                var log = response.data;
                self.showLogDetailModal(log);
            }
        });
    };
    
    this.showLogDetailModal = function(log) {
        // 移除已存在的模态框
        $('#logDetailModal').remove();

        var self = this;
        var request = log.request || {};

        // 安全创建模态框
        var modal = $('<div class="modal-overlay" id="logDetailModal"></div>');
        var dialog = $('<div class="modal-dialog"></div>');
        var content = $('<div class="modal-content"></div>');

        // 头部
        var header = $('<div class="modal-header"></div>');
        var title = $('<h5 class="modal-title">日志详情 - </h5>');
        title.append($('<span></span>').text(log.vuln_hash));
        header.append(title);
        header.append($('<button type="button" class="close">&times;</button>'));
        content.append(header);

        // 主体
        var body = $('<div class="modal-body"></div>');

        // Tab切换
        var tabs = $('<div class="detail-tabs"></div>');
        tabs.append($('<button class="tab-btn active" data-tab="request">请求详情</button>'));
        tabs.append($('<button class="tab-btn" data-tab="burp">Burp格式</button>'));
        body.append(tabs);

        // 请求详情
        var requestContent = $('<div class="tab-content active" id="requestTab"></div>');
        var requestPre = $('<pre></pre>');
        requestPre.text(JSON.stringify(log, null, 2)); // 使用.text()避免XSS
        requestContent.append(requestPre);
        body.append(requestContent);

        // Burp格式
        var burpContent = $('<div class="tab-content" id="burpTab"></div>');
        var burpPre = $('<pre></pre>');
        burpPre.text(self.generateBurpFormat(request)); // 使用.text()避免XSS
        burpContent.append(burpPre);
        body.append(burpContent);

        content.append(body);
        dialog.append(content);
        modal.append(dialog);

        $('body').append(modal);

        // 显示模态框
        modal.addClass('active');

        // 关闭按钮事件
        modal.find('.close').off('click').on('click', function() {
            modal.removeClass('active');
            setTimeout(function() {
                modal.remove();
            }, 300);
        });

        // 点击遮罩关闭
        modal.off('click').on('click', function(e) {
            if (e.target === modal[0]) {
                modal.removeClass('active');
                setTimeout(function() {
                    modal.remove();
                }, 300);
            }
        });

        // Tab切换事件
        modal.find('.tab-btn').off('click').on('click', function() {
            var tab = $(this).data('tab');
            modal.find('.tab-btn').removeClass('active');
            modal.find('.tab-content').removeClass('active');
            $(this).addClass('active');
            modal.find('#' + tab + 'Tab').addClass('active');
        });
    };
    
    this.generateBurpFormat = function(request) {
        var burp = '';
        var method = request.method || 'GET';
        var url = request.url || '';
        var headers = request.headers || {};
        var body = request.body || '';
        
        // 如果body是对象，转成JSON字符串
        if (typeof body === 'object') {
            body = JSON.stringify(body);
        }
        
        try {
            // 请求行
            var urlObj = new URL(url);
            var path = urlObj.pathname + urlObj.search;
            burp += method + ' ' + path + ' HTTP/1.1\n';
            
            // Host
            burp += 'Host: ' + urlObj.host + '\n';
            
            // 请求头
            for (var key in headers) {
                burp += key + ': ' + headers[key] + '\n';
            }
            
            // 空行和body
            if (body) {
                burp += '\n';
                burp += body;
            }
        } catch (e) {
            burp += '无法解析URL: ' + url + '\n\n';
            burp += 'Method: ' + method + '\n';
            burp += 'Headers: ' + JSON.stringify(headers, null, 2) + '\n';
            burp += 'Body: ' + body + '\n';
        }
        
        return burp;
    };

    this.verifyLog = function(container, hash) {
        var self = this;
        $.post('/api/scaner/logs/' + hash + '/verify', function(response) {
            if (response.success) {
                alert('已标记为验证');
                self.loadLogs(container);
            }
        }).fail(function(xhr) {
            var msg = xhr.responseJSON ? xhr.responseJSON.message : '验证失败';
            alert('验证失败: ' + msg);
        });
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
}

console.log('[Scaner] ScanerLogsModule loaded');
