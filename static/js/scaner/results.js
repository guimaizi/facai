/**
 * 漏洞扫描器 - 扫描结果
 * 支持表头排序、翻页、URL搜索
 */

function ScanerResultsModule() {
    // 排序状态
    this.sortBy = 'time';
    this.sortOrder = -1; // -1降序，1升序
    
    // 分页状态
    this.currentPage = 1;
    this.pageSize = 20;
    this.totalCount = 0;
    this.totalPages = 0;
    
    // 搜索状态
    this.searchKeyword = '';
    
    // 缓存当前页数据
    this.currentResults = [];
    
    this.render = function(data, container) {
        var self = this;
        
        var html = `
<div class="scaner-results-container">
    <div class="scaner-page-header">
        <h3>📋 扫描结果</h3>
    </div>

    <div class="results-toolbar">
        <div class="btn-group">
            <button class="btn btn-secondary btn-sm" id="refreshResults">
                <span class="btn-icon">🔄</span>
                <span>刷新</span>
            </button>
            <button class="btn btn-secondary btn-sm" id="exportResults">
                <span class="btn-icon">📤</span>
                <span>导出</span>
            </button>
            <button class="btn btn-danger btn-sm" id="clearResults">
                <span class="btn-icon">🗑️</span>
                <span>清空</span>
            </button>
        </div>
        
        <div class="search-box">
            <input type="text" id="urlSearch" placeholder="搜索URL..." class="form-control">
            <button class="btn btn-primary btn-sm" id="searchBtn">搜索</button>
            <button class="btn btn-secondary btn-sm" id="clearSearch">清除</button>
        </div>
    </div>

    <div class="scaner-card">
        <div class="scaner-card-body">
            <table class="scaner-table">
                <thead>
                    <tr>
                        <th class="sortable" data-sort="level">危害等级 <span class="sort-icon"></span></th>
                        <th class="sortable" data-sort="vuln_type">漏洞类型 <span class="sort-icon"></span></th>
                        <th class="sortable" data-sort="website">网站 <span class="sort-icon"></span></th>
                        <th>参数名</th>
                        <th class="sortable" data-sort="time">发现时间 <span class="sort-icon"></span></th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody id="resultsBody">
                    <tr><td colspan="6" class="text-center">加载中...</td></tr>
                </tbody>
            </table>
            
            <!-- 翻页容器 -->
            <div id="paginationContainer"></div>
        </div>
    </div>
</div>
        `;

        container.html(html);
        this.loadResults(container);
        this.bindEvents(container);
    };

    this.loadResults = function(container) {
        var self = this;
        
        // 构建查询参数
        var params = {
            page: this.currentPage,
            page_size: this.pageSize,
            sort_by: this.sortBy,
            sort_order: this.sortOrder
        };
        
        // 添加搜索关键词
        if (this.searchKeyword) {
            params.search = this.searchKeyword;
            params.search_type = 'url';
        }
        
        $.get('/api/scaner/results', params, function(response) {
            if (response.success && response.data) {
                self.currentResults = response.data.results || [];
                self.totalCount = response.data.total || 0;
                self.totalPages = Math.ceil(self.totalCount / self.pageSize);
                
                self.renderResults(container);
                self.renderPagination(container);
            }
        }).fail(function() {
            container.find('#resultsBody').html('<tr><td colspan="6" class="text-center">加载失败</td></tr>');
        });
    };

    this.renderResults = function(container) {
        var self = this;
        var tbody = container.find('#resultsBody');
        tbody.empty();
        
        if (this.currentResults.length === 0) {
            var emptyMsg = this.searchKeyword 
                ? '未找到匹配的漏洞' 
                : '暂无数据';
            tbody.append('<tr><td colspan="6" class="text-center">' + emptyMsg + '</td></tr>');
            return;
        }
        
        // 渲染数据
        this.currentResults.forEach(function(item) {
            var tr = $('<tr></tr>');
            
            // 危害等级
            var levelColor = self.getSeverityColor(item.level);
            var levelText = self.getSeverityText(item.level);
            var badge = $('<span class="badge"></span>')
                .addClass('badge-' + levelColor)
                .text(levelText);
            tr.append($('<td></td>').append(badge));
            
            // 漏洞类型
            tr.append($('<td></td>').text(item.vuln_type_detail || item.vuln_type || '-'));
            
            // 网站
            tr.append($('<td></td>').text(item.website || '-'));
            
            // 参数名
            tr.append($('<td></td>').text(item.paramname || '-'));
            
            // 发现时间
            tr.append($('<td></td>').text(self.formatDateTime(item.time)));
            
            // 操作按钮
            var tdBtn = $('<td></td>');
            var btnDetail = $('<button class="btn btn-sm btn-info view-detail">详情</button>')
                .data('id', item.id);
            tdBtn.append(btnDetail);
            tr.append(tdBtn);
            
            tbody.append(tr);
        });
        
        // 更新排序图标
        this.updateSortIcons(container);
    };

    this.renderPagination = function(container) {
        var self = this;
        var paginationContainer = container.find('#paginationContainer');
        
        if (this.totalPages <= 1) {
            paginationContainer.empty();
            return;
        }
        
        var paginationHtml = PageUp.generatePagination({
            currentPage: this.currentPage,
            totalPages: this.totalPages,
            visiblePages: 10,
            onPageChange: function(page) {
                self.currentPage = page;
                self.loadResults(container);
            }
        });
        
        paginationContainer.html(paginationHtml);
    };

    this.updateSortIcons = function(container) {
        // 清除所有排序状态
        container.find('.sortable').removeClass('active sort-asc sort-desc');
        
        // 设置当前排序列
        var th = container.find('[data-sort="' + this.sortBy + '"]');
        th.addClass('active');
        if (this.sortOrder === 1) {
            th.addClass('sort-asc');
        } else {
            th.addClass('sort-desc');
        }
    };

    this.bindEvents = function(container) {
        var self = this;
        
        // 排序点击事件
        container.find('.sortable').off('click').on('click', function() {
            var sortBy = $(this).data('sort');
            
            // 如果点击同一列，切换排序方向
            if (self.sortBy === sortBy) {
                self.sortOrder = self.sortOrder === 1 ? -1 : 1;
            } else {
                // 不同列，默认降序
                self.sortBy = sortBy;
                self.sortOrder = -1;
            }
            
            // 重新加载当前页
            self.loadResults(container);
        });
        
        // 搜索按钮
        container.find('#searchBtn').off('click').on('click', function() {
            var keyword = container.find('#urlSearch').val().trim();
            self.searchKeyword = keyword;
            self.currentPage = 1; // 重置到第一页
            self.loadResults(container);
        });
        
        // 清除搜索
        container.find('#clearSearch').off('click').on('click', function() {
            container.find('#urlSearch').val('');
            self.searchKeyword = '';
            self.currentPage = 1;
            self.loadResults(container);
        });
        
        // 回车搜索
        container.find('#urlSearch').off('keypress').on('keypress', function(e) {
            if (e.which === 13) { // Enter键
                var keyword = $(this).val().trim();
                self.searchKeyword = keyword;
                self.currentPage = 1;
                self.loadResults(container);
            }
        });
        
        // 刷新
        container.find('#refreshResults').off('click').on('click', function() {
            self.loadResults(container);
        });
        
        // 导出
        container.find('#exportResults').off('click').on('click', function() {
            self.exportResults(container);
        });
        
        // 清空
        container.find('#clearResults').off('click').on('click', function() {
            if (confirm('确定要清空所有扫描结果吗？')) {
                $.post('/api/scaner/results/clear', function(response) {
                    if (response.success) {
                        alert('已清空');
                        self.currentPage = 1;
                        self.loadResults(container);
                    }
                });
            }
        });
        
        // 查看详情
        container.on('click', '.view-detail', function() {
            var id = $(this).data('id');
            self.showDetail(container, id);
        });
    };

    this.exportResults = function(container) {
        var self = this;
        
        // 导出所有结果（包括搜索结果）
        var params = {
            page_size: 10000 // 导出所有
        };
        
        if (this.searchKeyword) {
            params.search = this.searchKeyword;
            params.search_type = 'url';
        }
        
        $.get('/api/scaner/results', params, function(response) {
            if (response.success && response.data.results) {
                var exportData = response.data.results.map(function(item) {
                    return {
                        level: item.level,
                        vuln_type: item.vuln_type,
                        vuln_type_detail: item.vuln_type_detail,
                        website: item.website,
                        url: item.url,
                        paramname: item.paramname,
                        time: item.time
                    };
                });
                
                var dataStr = JSON.stringify(exportData, null, 2);
                var blob = new Blob([dataStr], { type: 'application/json' });
                var url = URL.createObjectURL(blob);
                var a = document.createElement('a');
                a.href = url;
                a.download = 'vuln_results_' + new Date().getTime() + '.json';
                a.click();
                URL.revokeObjectURL(url);
            }
        });
    };

    this.showDetail = function(container, id) {
        var self = this;
        
        // 从当前页数据中查找
        var vuln = this.currentResults.find(function(item) {
            return item.id === id;
        });
        
        if (vuln) {
            self.showVulnDetailModal(vuln);
        } else {
            // 如果缓存中没有，从API获取
            $.get('/api/scaner/results/' + id, function(response) {
                if (response.success) {
                    self.showVulnDetailModal(response.data);
                }
            });
        }
    };
    
    this.showVulnDetailModal = function(vuln) {
        $('#vulnDetailModal').remove();
        
        var self = this;
        
        var modal = $('<div class="modal-overlay" id="vulnDetailModal"></div>');
        var dialog = $('<div class="modal-dialog vuln-detail-modal" style="max-width: 1000px;"></div>');
        var content = $('<div class="modal-content"></div>');
        
        // 头部
        var header = $('<div class="modal-header"></div>');
        header.append($('<h5 class="modal-title">漏洞详情</h5>'));
        header.append($('<button type="button" class="close">&times;</button>'));
        content.append(header);
        
        // 主体
        var body = $('<div class="modal-body"></div>');
        
        // Tab切换
        var tabs = $('<div class="detail-tabs"></div>');
        tabs.append($('<button class="detail-tab active" data-tab="info">基本信息</button>'));
        tabs.append($('<button class="detail-tab" data-tab="request">请求详情</button>'));
        tabs.append($('<button class="detail-tab" data-tab="burp">Burp格式</button>'));
        body.append(tabs);
        
        // 基本信息Tab
        var infoContent = $('<div class="detail-content active" id="infoTab"></div>');
        var infoHtml = this.renderVulnInfo(vuln);
        infoContent.html(infoHtml);
        body.append(infoContent);
        
        // 请求详情Tab
        var requestContent = $('<div class="detail-content" id="requestTab"></div>');
        var requestPre = $('<pre></pre>');
        requestPre.text(JSON.stringify(vuln, null, 2));
        requestContent.append(requestPre);
        body.append(requestContent);
        
        // Burp格式Tab
        var burpContent = $('<div class="detail-content" id="burpTab"></div>');
        var burpPre = $('<pre></pre>');
        burpPre.text(this.generateBurpFormat(vuln));
        burpContent.append(burpPre);
        body.append(burpContent);
        
        content.append(body);
        dialog.append(content);
        modal.append(dialog);
        
        $('body').append(modal);
        FacaiCore.Modal.show('vulnDetailModal');
        
        // Tab切换事件
        modal.find('.detail-tab').off('click').on('click', function() {
            var tab = $(this).data('tab');
            modal.find('.detail-tab').removeClass('active');
            modal.find('.detail-content').removeClass('active');
            $(this).addClass('active');
            modal.find('#' + tab + 'Tab').addClass('active');
        });
    };
    
    this.renderVulnInfo = function(vuln) {
        var html = '<div style="padding: 10px;">';
        html += '<h4 style="margin-bottom: 10px; color: #2d3748;">漏洞信息</h4>';
        html += '<table class="vuln-info-table">';
        
        var infoItems = [
            { label: '危害等级', value: this.getSeverityText(vuln.level), badge: this.getSeverityColor(vuln.level) },
            { label: '漏洞类型', value: vuln.vuln_type_detail || vuln.vuln_type || '-' },
            { label: '网站', value: vuln.website || '-' },
            { label: 'URL', value: vuln.url || '-', code: true },
            { label: '参数名', value: vuln.paramname || '-' },
            { label: '请求方法', value: vuln.method || '-' },
            { label: '发现时间', value: this.formatDateTime(vuln.time) }
        ];
        
        infoItems.forEach(function(item) {
            html += '<tr>';
            html += '<td>' + item.label + '</td>';
            html += '<td>';
            
            if (item.badge) {
                html += '<span class="vuln-badge vuln-badge-' + item.badge + '">' + this.escapeHtml(item.value) + '</span>';
            } else if (item.code) {
                html += '<code style="background: #f7fafc; padding: 2px 6px; border-radius: 3px;">' + this.escapeHtml(item.value) + '</code>';
            } else {
                html += this.escapeHtml(item.value);
            }
            
            html += '</td>';
            html += '</tr>';
        }.bind(this));
        
        html += '</table>';
        html += '</div>';
        
        return html;
    };
    
    this.generateBurpFormat = function(vuln) {
        var burp = '';
        var method = vuln.method || 'GET';
        var url = vuln.url || '';
        var headers = vuln.headers || {};
        var body = vuln.body || '';
        
        try {
            // 请求行
            var urlObj = new URL(url);
            var path = urlObj.pathname + urlObj.search;
            burp += method + ' ' + path + ' HTTP/1.1\r\n';
            
            // Host
            burp += 'Host: ' + urlObj.host + '\r\n';
            
            // 请求头
            for (var key in headers) {
                burp += key + ': ' + headers[key] + '\r\n';
            }
            
            // 空行
            burp += '\r\n';
            
            // Body
            if (body) {
                burp += body;
            }
        } catch (e) {
            burp = 'URL解析失败: ' + url + '\r\n\r\n';
            burp += 'Method: ' + method + '\r\n';
            burp += 'Headers: ' + JSON.stringify(headers, null, 2) + '\r\n';
            burp += 'Body: ' + body + '\r\n';
        }
        
        return burp;
    };

    this.getSeverityColor = function(level) {
        var colors = {
            'high': 'danger',
            'medium': 'warning',
            'low': 'info'
        };
        return colors[level] || 'secondary';
    };

    this.getSeverityText = function(level) {
        var texts = {
            'high': '高危',
            'medium': '中危',
            'low': '低危'
        };
        return texts[level] || '未知';
    };

    this.formatDateTime = function(dateStr) {
        if (!dateStr) return '-';
        var date = new Date(dateStr);
        return date.toLocaleString('zh-CN');
    };
    
    this.escapeHtml = function(text) {
        if (!text) return '';
        var div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    };
}

console.log('[Scaner] ScanerResultsModule loaded');
