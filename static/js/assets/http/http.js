function HttpModule() {
    this.currentPage = 1;
    this.pageSize = 20;
    this.searchKeyword = '';
    this.searchType = 'url';
    this.sortBy = 'time_first';  // 默认按时间排序
    this.sortOrder = -1;  // 默认降序（最新的在前）

    this.render = function(data, container) {
        // 保存容器引用
        this.container = container;

        container.html(`
            <div class="http-grid-container">
                <div class="card">
                    <div class="card-header">
                        <div class="row">
                            <div class="col-md-6">HTTP请求响应管理</div>
                            <div class="col-md-6 text-right">
                                <button class="btn btn-primary" id="refreshHttp">刷新</button>
                                <button class="btn btn-warning" id="clearHttp">清空</button>
                            </div>
                        </div>
                    </div>
                    <div class="form-group p-3">
                        <div class="row mb-3">
                            <div class="col-md-3">
                                <select class="form-control" id="searchType">
                                    <option value="url">URL</option>
                                    <option value="title">标题</option>
                                    <option value="subdomain">子域名</option>
                                    <option value="key">Key</option>
                                </select>
                            </div>
                            <div class="col-md-4">
                                <input type="text" class="form-control" id="searchHttp" placeholder="搜索URL、标题、子域名或Key...">
                            </div>
                            <div class="col-md-3">
                                <button class="btn btn-primary" id="searchBtn">搜索</button>
                                <button class="btn btn-secondary" id="clearSearchBtn">清除</button>
                            </div>
                        </div>
                    <div class="table-responsive">
                        <table class="table">
                            <thead>
                                <tr>
                                    <th class="sortable" data-sort="method" style="width: 50px;">方法 <span class="sort-icon"></span></th>
                                    <th class="sortable" data-sort="url">URL <span class="sort-icon"></span></th>
                                    <th class="sortable" data-sort="title" style="width: 150px;">标题 <span class="sort-icon"></span></th>
                                    <th class="sortable" data-sort="subdomain" style="width: 120px;">子域名 <span class="sort-icon"></span></th>
                                    <th class="sortable" data-sort="http_status_code" style="width: 80px;">状态码 <span class="sort-icon"></span></th>
                                    <th class="sortable" data-sort="http_type" style="width: 100px;">类型 <span class="sort-icon"></span></th>
                                    <th class="sortable" data-sort="time_first" style="width: 150px;">时间 <span class="sort-icon"></span></th>
                                    <th style="width: 120px;">操作</th>
                                </tr>
                            </thead>
                            <tbody id="httpList"></tbody>
                        </table>
                    </div>
                    <div id="pagination"></div>
                </div>
            </div>
        </div>
        `);
        this.updateSortIcons();
        this.loadHttp();
        this.bindEvents();
    };

    this.loadHttp = function() {
        var self = this;
        $.ajax({
            url: '/api/assets/http',
            type: 'GET',
            data: {
                page: self.currentPage,
                page_size: self.pageSize,
                search_keyword: self.searchKeyword,
                search_type: self.searchType,
                sort_by: self.sortBy,
                sort_order: self.sortOrder
            },
            success: function(data) {
                var tbody = $('#httpList');
                tbody.empty();
                if (data.https && data.https.length > 0) {
                    data.https.forEach(function(item) {
                        // 处理状态码颜色
                        var statusColor = 'info';
                        if (item.http_status_code >= 200 && item.http_status_code < 300) {
                            statusColor = 'success';
                        } else if (item.http_status_code >= 300 && item.http_status_code < 400) {
                            statusColor = 'warning';
                        } else if (item.http_status_code >= 400) {
                            statusColor = 'danger';
                        }

                        // 处理方法颜色
                        var methodColor = 'secondary';
                        if (item.method === 'GET') {
                            methodColor = 'success';
                        } else if (item.method === 'POST') {
                            methodColor = 'primary';
                        } else if (item.method === 'PUT') {
                            methodColor = 'warning';
                        } else if (item.method === 'DELETE') {
                            methodColor = 'danger';
                        } else if (item.method === 'PATCH') {
                            methodColor = 'info';
                        }

                        // 处理http_type显示
                        var httpTypeDisplay = '未知';
                        var httpTypeColor = 'secondary';
                        if (item.http_type === 1) {
                            httpTypeDisplay = 'HTML';
                            httpTypeColor = 'success';
                        } else if (item.http_type === 2) {
                            httpTypeDisplay = '文件';
                            httpTypeColor = 'warning';
                        }

                        // 截取URL显示
                        var urlDisplay = item.url || '';
                        if (urlDisplay.length > 60) {
                            urlDisplay = urlDisplay.substring(0, 60) + '...';
                        }

                        // 截取标题显示
                        var titleDisplay = item.title || '';
                        if (titleDisplay.length > 20) {
                            titleDisplay = titleDisplay.substring(0, 20) + '...';
                        }

                        tbody.append(`
                            <tr>
                                <td><span class="badge badge-${methodColor}">${item.method || 'GET'}</span></td>
                                <td><a href="${item.url}" target="_blank" title="${item.url}">${urlDisplay}</a></td>
                                <td title="${item.title || ''}">${titleDisplay}</td>
                                <td>${item.subdomain || ''}</td>
                                <td><span class="badge badge-${statusColor}">${item.http_status_code || 'N/A'}</span></td>
                                <td><span class="badge badge-${httpTypeColor}">${httpTypeDisplay}</span></td>
                                <td>${item.time_first || ''}</td>
                                <td>
                                    <button class="btn btn-info btn-sm http-view-detail" data-id="${item._id}">详情</button>
                                    <button class="btn btn-success btn-sm http-replay-request" data-id="${item._id}">重放</button>
                                    <button class="btn btn-danger btn-sm http-delete" data-id="${item._id}">删除</button>
                                </td>
                            </tr>
                        `);
                    });

                    // 渲染分页
                    var paginationHtml = PageUp.generatePagination({
                        currentPage: data.page,
                        totalPages: data.total_pages,
                        onPageChange: function(page) {
                            self.currentPage = page;
                            self.loadHttp();
                        }
                    });
                    $('#pagination').html(paginationHtml);
                } else {
                    tbody.append('<tr><td colspan="8" class="text-center text-muted">暂无HTTP数据</td></tr>');
                    $('#pagination').html('');
                }
            },
            error: function(xhr) {
                var tbody = $('#httpList');
                tbody.empty();
                if (xhr.status === 404 || xhr.status === 500) {
                    tbody.append('<tr><td colspan="8" class="text-center text-muted">暂无项目或暂无数据</td></tr>');
                } else {
                    tbody.append('<tr><td colspan="8" class="text-center text-danger">加载失败，请重试</td></tr>');
                }
                $('#pagination').html('');
            }
        });
    };

    // 更新排序图标
    this.updateSortIcons = function() {
        var self = this;
        // 移除所有排序状态
        this.container.find('.sortable').removeClass('sort-asc sort-desc');
        this.container.find('.sort-icon').html('');

        // 设置当前排序字段的图标
        this.container.find('.sortable').each(function() {
            var field = $(this).data('sort');
            if (field === self.sortBy) {
                $(this).addClass(self.sortOrder === 1 ? 'sort-asc' : 'sort-desc');
                $(this).find('.sort-icon').html(self.sortOrder === 1 ? '▲' : '▼');
            }
        });
    };

    this.bindEvents = function() {
        var self = this;

        // 表头排序点击事件
        this.container.on('click', '.sortable', function() {
            var field = $(this).data('sort');
            
            if (self.sortBy === field) {
                // 同一字段，切换排序方向
                self.sortOrder = self.sortOrder === 1 ? -1 : 1;
            } else {
                // 不同字段，默认降序
                self.sortBy = field;
                self.sortOrder = -1;
            }
            
            self.updateSortIcons();
            self.currentPage = 1;
            self.loadHttp();
        });

        // 刷新按钮
        $('#refreshHttp').on('click', function() {
            self.currentPage = 1;
            self.loadHttp();
        });

        // 清空按钮
        $('#clearHttp').on('click', function() {
            if (confirm('确定要清空所有HTTP数据吗？')) {
                $.ajax({
                    url: '/api/assets/http/clear',
                    type: 'POST',
                    success: function(data) {
                        if (data.success) {
                            alert(data.message);
                            self.currentPage = 1;
                            self.loadHttp();
                        } else {
                            alert(data.message);
                        }
                    }
                });
            }
        });

        // 搜索按钮
        $('#searchBtn').on('click', function() {
            self.searchType = $('#searchType').val();
            self.searchKeyword = $('#searchHttp').val();
            self.currentPage = 1;
            self.loadHttp();
        });

        // 清除搜索按钮
        $('#clearSearchBtn').on('click', function() {
            $('#searchHttp').val('');
            self.searchKeyword = '';
            self.currentPage = 1;
            self.loadHttp();
        });

        // 搜索框回车搜索
        $('#searchHttp').on('keypress', function(e) {
            if (e.which === 13) {
                $('#searchBtn').click();
            }
        });

        // 查看详情 - 限制在HTTP容器内
        this.container.on('click', '.http-view-detail', function() {
            var id = $(this).data('id');
            self.showDetailModal(id);
        });

        // 重放请求 - 限制在HTTP容器内
        this.container.on('click', '.http-replay-request', function() {
            var id = $(this).data('id');
            self.showReplay(id);
        });

        // 删除HTTP - 限制在HTTP容器内
        this.container.on('click', '.http-delete', function() {
            var id = $(this).data('id');
            if (confirm('确定要删除这条HTTP数据吗？')) {
                $.ajax({
                    url: '/api/assets/http/' + id,
                    type: 'DELETE',
                    success: function(data) {
                        if (data.success) {
                            alert(data.message);
                            self.loadHttp();
                        } else {
                            alert(data.message);
                        }
                    }
                });
            }
        });
    };

        this.showDetailModal = function(id) {
        var self = this;
        $.ajax({
            url: '/api/assets/http/' + id,
            type: 'GET',
            success: function(data) {
                if (data.success && data.http) {
                    var http = data.http;
                    self.renderDetailModal(http);
                } else {
                    console.log('获取HTTP详情失败');
                }
            },
            error: function(xhr) {
                console.log('请求失败，状态码:', xhr.status);
            }
        });
    };
    
    this.renderDetailModal = function(http) {
        var self = this;
        
        // 移除已存在的modal
        $('#httpDetailModal').remove();
        
        // 处理标签显示
        var tagsHtml = '';
        if (http.tag && http.tag.length > 0) {
            tagsHtml = http.tag.map(function(tag) {
                return '<span class="http-tag">' + self.escapeHtml(tag) + '</span>';
            }).join(' ');
        } else {
            tagsHtml = '<span class="text-muted">无标签</span>';
        }
        
        // 处理状态码颜色
        var statusColor = 'info';
        if (http.http_status_code >= 200 && http.http_status_code < 300) {
            statusColor = 'success';
        } else if (http.http_status_code >= 300 && http.http_status_code < 400) {
            statusColor = 'warning';
        } else if (http.http_status_code >= 400) {
            statusColor = 'danger';
        }
        
        // 处理HTTP类型
        var httpTypeText = '未知';
        if (http.http_type === 1) {
            httpTypeText = 'HTML (可渲染)';
        } else if (http.http_type === 2) {
            httpTypeText = '文件 (不可渲染)';
        }
        
        // 格式化JSON
        var headersText = self.formatJson(http.headers);
        var bodyText = self.formatJson(http.body);
        var headersResponseText = self.formatJson(http.headers_response);
        var standardJson = self.formatJson({
            url_path: http.url_path,
            url_generalization: http.url_generalization,
            param_feature: http.param_feature,
            key: http.key,
            file_extension: http.file_extension
        });
        
        // 处理截图显示
        var screenshotHtml = '<span class="text-muted">无截图</span>';
        if (http.screenshot) {
            screenshotHtml = `
                <div class="screenshot-preview">
                    <img src="/${http.screenshot}" alt="页面截图" onclick="window.open('/${http.screenshot}', '_blank')">
                    <div class="screenshot-hint">点击查看大图</div>
                </div>
            `;
        }
        
        var modalHtml = `
            <div class="http-detail-modal" id="httpDetailModal">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">HTTP请求详情</h5>
                            <button type="button" class="close">&times;</button>
                        </div>
                        <div class="modal-body">
                            <div class="detail-tabs">
                                <button class="detail-tab active" data-tab="basic">基本信息</button>
                                <button class="detail-tab" data-tab="request">请求信息</button>
                                <button class="detail-tab" data-tab="response">响应信息</button>
                                <button class="detail-tab" data-tab="standard">标准化</button>
                            </div>
                            
                            <div class="detail-content active" id="basicTab">
                                <table class="detail-table">
                                    <tr><td class="label">URL</td><td class="value"><code>${self.escapeHtml(http.url || '-')}</code></td></tr>
                                    <tr><td class="label">当前URL</td><td class="value"><code>${self.escapeHtml(http.current_url || '-')}</code></td></tr>
                                    <tr><td class="label">标题</td><td class="value">${self.escapeHtml(http.title || '-')}</td></tr>
                                    <tr>
                                        <td class="label">方法</td>
                                        <td class="value"><span class="http-badge http-badge-method">${self.escapeHtml(http.method || '-')}</span></td>
                                    </tr>
                                    <tr>
                                        <td class="label">状态码</td>
                                        <td class="value"><span class="http-badge http-badge-${statusColor}">${http.http_status_code || '-'}</span></td>
                                    </tr>
                                    <tr><td class="label">HTTP类型</td><td class="value">${self.escapeHtml(httpTypeText)}</td></tr>
                                    <tr><td class="label">域名</td><td class="value">${self.escapeHtml(http.domain || '-')}</td></tr>
                                    <tr><td class="label">子域名</td><td class="value">${self.escapeHtml(http.subdomain || '-')}</td></tr>
                                    <tr><td class="label">端口</td><td class="value">${http.port || '-'}</td></tr>
                                    <tr><td class="label">服务器</td><td class="value">${self.escapeHtml(http.server || '-')}</td></tr>
                                    <tr><td class="label">Web指纹</td><td class="value">${self.escapeHtml(http.web_fingerprint || '-')}</td></tr>
                                    <tr><td class="label">标签</td><td class="value">${tagsHtml}</td></tr>
                                    <tr><td class="label">截图</td><td class="value">${screenshotHtml}</td></tr>
                                    <tr><td class="label">HTML长度</td><td class="value">${(http.html_len || 0).toLocaleString()} bytes</td></tr>
                                    <tr><td class="label">HTML MD5</td><td class="value"><code>${self.escapeHtml(http.html_md5 || '-')}</code></td></tr>
                                    <tr><td class="label">WAF</td><td class="value">${http.waf || '无'}</td></tr>
                                    <tr><td class="label">首次访问</td><td class="value">${self.escapeHtml(http.time_first || '-')}</td></tr>
                                    <tr><td class="label">更新时间</td><td class="value">${self.escapeHtml(http.time_update || '-')}</td></tr>
                                </table>
                            </div>
                            
                            <div class="detail-content" id="requestTab">
                                <div class="code-section">
                                    <h6>请求头</h6>
                                    <pre>${self.escapeHtml(headersText)}</pre>
                                </div>
                                <div class="code-section">
                                    <h6>请求体</h6>
                                    <pre>${self.escapeHtml(bodyText)}</pre>
                                </div>
                            </div>
                            
                            <div class="detail-content" id="responseTab">
                                <div class="code-section">
                                    <h6>响应头</h6>
                                    <pre>${self.escapeHtml(headersResponseText)}</pre>
                                </div>
                            </div>
                            
                            <div class="detail-content" id="standardTab">
                                <div class="code-section">
                                    <h6>标准化信息</h6>
                                    <pre>${self.escapeHtml(standardJson)}</pre>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary close-btn">关闭</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        $('body').append(modalHtml);
        
        // 显示动画
        setTimeout(function() {
            $('#httpDetailModal').addClass('active');
        }, 10);
        
        // Tab切换
        $('#httpDetailModal').on('click', '.detail-tab', function() {
            var tab = $(this).data('tab');
            $('#httpDetailModal .detail-tab').removeClass('active');
            $('#httpDetailModal .detail-content').removeClass('active');
            $(this).addClass('active');
            $('#' + tab + 'Tab').addClass('active');
        });
        
        // 关闭
        $('#httpDetailModal').on('click', '.close, .close-btn', function() {
            $('#httpDetailModal').removeClass('active');
            setTimeout(function() {
                $('#httpDetailModal').remove();
            }, 300);
        });
        
        // 点击背景关闭
        $('#httpDetailModal').on('click', function(e) {
            if (e.target === this) {
                $(this).removeClass('active');
                setTimeout(function() {
                    $('#httpDetailModal').remove();
                }, 300);
            }
        });
    };
    
    this.formatJson = function(obj) {
        if (!obj) return '';
        if (typeof obj === 'string') return obj;
        try {
            return JSON.stringify(obj, null, 2);
        } catch (e) {
            return String(obj);
        }
    };
    
    this.escapeHtml = function(text) {
        if (!text) return '';
        var div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    };
this.formatAsBurp = function(http) {
        var method = http.method || 'GET';
        var url = http.url || '';
        var headers = http.headers || {};
        var body = http.body || '';

        var burpFormat = `${method} ${url} HTTP/1.1\n`;

        // 添加headers
        if (typeof headers === 'object') {
            for (var key in headers) {
                if (headers.hasOwnProperty(key)) {
                    burpFormat += `${key}: ${headers[key]}\n`;
                }
            }
        }

        burpFormat += '\n';

        // 添加body
        if (body) {
            if (typeof body === 'object') {
                burpFormat += JSON.stringify(body, null, 2);
            } else {
                burpFormat += body;
            }
        }

        return burpFormat;
    };

    this.showReplay = function(id) {
        var self = this;
        $.ajax({
            url: '/api/assets/http/' + id,
            type: 'GET',
            success: function(data) {
                if (data.success && data.http) {
                    var http = data.http;

                    // 准备初始数据（同时提供JSON和Burp格式）
                    var initialData = {
                        mode: 'burp', // 默认使用burp模式
                        burpFormat: self.formatAsBurp(http),
                        jsonData: JSON.stringify(http, null, 2)
                    };

                    // 打开新的tab进行重放
                    TabManager.openTab('tools', 'HTTP请求重放', {
                        subModule: 'replay',
                        initialData: initialData
                    });
                } else {
                    alert('获取HTTP详情失败');
                }
            },
            error: function(xhr) {
                alert('请求失败，状态码: ' + xhr.status);
            }
        });
    };
}
