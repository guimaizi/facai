function TrafficModule() {
    this.currentPage = 1;
    this.pageSize = 20;
    this.sortBy = 'time';
    this.sortOrder = -1;
    this.searchUrl = '';

    this.render = function(data, container) {
        container.html(`
            <div class="card">
                <div class="card-header">
                    <div class="row">
                        <div class="col-md-6">HTTP流量</div>
                        <div class="col-md-6 text-right">
                            <button class="btn btn-primary" id="refreshTraffic">刷新</button>
                            <button class="btn btn-warning" id="clearTraffic">清空</button>
                        </div>
                    </div>
                </div>
                <div class="form-group p-3">
                    <div class="row mb-3">
                        <div class="col-md-4">
                            <input type="text" class="form-control" id="searchUrl" placeholder="搜索URL...">
                        </div>
                        <div class="col-md-2">
                            <button class="btn btn-primary" id="searchBtn">搜索</button>
                            <button class="btn btn-secondary" id="clearSearchBtn">清除</button>
                        </div>
                    </div>
                    <div class="table-responsive">
                        <table class="table">
                            <thead>
                                <tr>
                                    <th><a href="#" class="sort-link" data-sort="time">时间 <span class="sort-icon"></span></a></th>
                                    <th><a href="#" class="sort-link" data-sort="method">方法 <span class="sort-icon"></span></a></th>
                                    <th><a href="#" class="sort-link" data-sort="url">URL <span class="sort-icon"></span></a></th>
                                    <th><a href="#" class="sort-link" data-sort="website">Website <span class="sort-icon"></span></a></th>
                                    <th>状态</th>
                                    <th>扫描状态</th>
                                    <th>操作</th>
                                </tr>
                            </thead>
                            <tbody id="trafficList"></tbody>
                        </table>
                    </div>
                    <div id="pagination"></div>
                </div>
            </div>
        `);
        this.initSortIcon();
        this.loadTraffic();
        this.bindEvents();
    };

    this.initSortIcon = function() {
        // 初始化默认排序图标（时间降序）
        var icon = this.sortOrder === 1 ? '↑' : '↓';
        $(`[data-sort="${this.sortBy}"] .sort-icon`).text(icon);
    };

    this.loadTraffic = function() {
        var self = this;
        $.ajax({
            url: '/api/traffic/list',
            type: 'GET',
            data: {
                page: self.currentPage,
                page_size: self.pageSize,
                sort_by: self.sortBy,
                sort_order: self.sortOrder,
                search_url: self.searchUrl
            },
            success: function(data) {
                var tbody = $('#trafficList');
                tbody.empty();
                if (data.traffic) {
                    data.traffic.forEach(function(item) {
                        var scanerStatus = item.scaner_status === 1 ? '已扫描' : '未扫描';
                        var scanerClass = item.scaner_status === 1 ? 'text-success' : 'text-warning';
                        tbody.append(`
                            <tr>
                                <td>${item.time}</td>
                                <td>${item.method}</td>
                                <td class="url-cell">${item.url}</td>
                                <td class="website-cell">${item.website}</td>
                                <td>${item.status}</td>
                                <td class="${scanerClass}">${scanerStatus}</td>
                                <td>
                                    <button class="btn btn-primary btn-sm traffic-view-detail" data-id="${item._id}">详情</button>
                                    <button class="btn btn-success btn-sm traffic-replay-request" data-id="${item._id}">重放</button>
                                    <button class="btn btn-danger btn-sm delete-traffic" data-id="${item._id}">删除</button>
                                </td>
                            </tr>
                        `);
                    });
                }

                // 渲染分页
                var paginationHtml = PageUp.generatePagination({
                    currentPage: data.page,
                    totalPages: data.total_pages,
                    onPageChange: function(page) {
                        self.currentPage = page;
                        self.loadTraffic();
                    }
                });
                $('#pagination').html(paginationHtml);
            }
        });
    };

    this.bindEvents = function() {
        var self = this;

        // 刷新按钮
        $('#refreshTraffic').on('click', function() {
            self.loadTraffic();
        });

        // 清空按钮
        $('#clearTraffic').on('click', function() {
            if (confirm('确定要清空所有流量数据吗？')) {
                $.ajax({
                    url: '/api/traffic/clear',
                    type: 'POST',
                    success: function(data) {
                        alert(data.message);
                        self.loadTraffic();
                    }
                });
            }
        });

        // 搜索按钮
        $('#searchBtn').on('click', function() {
            self.searchUrl = $('#searchUrl').val();
            self.currentPage = 1; // 重置到第一页
            self.loadTraffic();
        });

        // 清除搜索按钮
        $('#clearSearchBtn').on('click', function() {
            $('#searchUrl').val('');
            self.searchUrl = '';
            self.currentPage = 1; // 重置到第一页
            self.loadTraffic();
        });

        // 搜索框回车搜索
        $('#searchUrl').on('keypress', function(e) {
            if (e.which === 13) { // Enter键
                $('#searchBtn').click();
            }
        });

        // 查看详情
        $(document).on('click', '.traffic-view-detail', function() {
            var id = $(this).data('id');
            self.showTrafficDetail(id);
        });

        // 重放请求
        $(document).on('click', '.traffic-replay-request', function() {
            var id = $(this).data('id');
            self.showReplay(id);
        });

        // 删除流量
        $(document).on('click', '.delete-traffic', function() {
            var id = $(this).data('id');
            if (confirm('确定要删除这条流量数据吗？')) {
                $.ajax({
                    url: '/api/traffic/delete/' + id,
                    type: 'POST',
                    success: function(data) {
                        if (data.success) {
                            alert(data.message);
                            self.loadTraffic();
                        } else {
                            alert(data.message);
                        }
                    }
                });
            }
        });

        // 排序功能
        $(document).on('click', '.sort-link', function(e) {
            e.preventDefault();
            var sortBy = $(this).data('sort');

            if (self.sortBy === sortBy) {
                // 切换排序顺序
                self.sortOrder = self.sortOrder === 1 ? -1 : 1;
            } else {
                // 新的排序字段
                self.sortBy = sortBy;
                self.sortOrder = 1;
            }

            // 更新排序图标
            $('.sort-icon').text('');
            var icon = self.sortOrder === 1 ? '↑' : '↓';
            $(this).find('.sort-icon').text(icon);

            // 重新加载数据
            self.currentPage = 1; // 重置到第一页
            self.loadTraffic();
        });
    };

    this.showTrafficDetail = function(id) {
        var self = this;
        $.ajax({
            url: '/api/traffic/detail/' + id,
            type: 'GET',
            success: function(data) {
                if (data.success) {
                    var traffic = data.traffic;
                    var modalHtml = `
                        <div class="modal" id="trafficDetailModal">
                            <div class="modal-content">
                                <div class="modal-header">
                                    <h5 class="modal-title">流量详情</h5>
                                    <button type="button" class="modal-close">&times;</button>
                                </div>
                                <div class="modal-body">
                                    <div class="view-mode-buttons">
                                        <button type="button" class="btn btn-primary view-mode-btn active" data-mode="json">JSON模式</button>
                                        <button type="button" class="btn btn-secondary view-mode-btn" data-mode="burp">Burp格式</button>
                                    </div>
                                    <div id="jsonView" class="mt-3 view-content">
                                        <pre>${JSON.stringify(traffic, null, 2)}</pre>
                                    </div>
                                    <div id="burpView" class="mt-3 view-content" style="display: none;">
                                        <pre>${self.formatAsBurp(traffic)}</pre>
                                    </div>
                                </div>
                                <div class="modal-footer">
                                    <button type="button" class="btn btn-secondary modal-close-btn">关闭</button>
                                </div>
                            </div>
                        </div>
                    `;

                    // 先移除已存在的modal
                    $('#trafficDetailModal').remove();
                    $('body').append(modalHtml);
                    setTimeout(function() {
                        $('#trafficDetailModal').addClass('active');
                    }, 10);

                    // 切换查看模式
                    $('#trafficDetailModal').on('click', '.view-mode-btn', function() {
                        var mode = $(this).data('mode');
                        $('#trafficDetailModal .view-mode-btn').removeClass('active');
                        $(this).addClass('active');

                        if (mode === 'json') {
                            $('#trafficDetailModal #jsonView').show();
                            $('#trafficDetailModal #burpView').hide();
                        } else {
                            $('#trafficDetailModal #jsonView').hide();
                            $('#trafficDetailModal #burpView').show();
                        }
                    });

                    // 关闭modal
                    $('#trafficDetailModal').on('click', '.modal-close, .modal-close-btn', function() {
                        $('#trafficDetailModal').removeClass('active');
                        setTimeout(function() {
                            $('#trafficDetailModal').remove();
                        }, 300);
                    });

                    // 点击modal外部关闭
                    $('#trafficDetailModal').on('click', function(e) {
                        if (e.target === this) {
                            $(this).removeClass('active');
                            setTimeout(function() {
                                $(this).remove();
                            }, 300);
                        }
                    });
                } else {
                    alert(data.message);
                }
            }
        });
    };

    this.formatAsBurp = function(traffic) {
        var method = traffic.method || 'GET';
        var url = traffic.url || '';
        var headers = traffic.headers || {};
        var body = traffic.body || '';

        var burpFormat = `${method} ${url} HTTP/1.1\n`;

        // 添加headers
        for (var key in headers) {
            burpFormat += `${key}: ${headers[key]}\n`;
        }

        burpFormat += '\n';

        // 添加body
        if (body) {
            burpFormat += body;
        }

        return burpFormat;
    };

    this.showReplay = function(id) {
        var self = this;
        $.ajax({
            url: '/api/traffic/detail/' + id,
            type: 'GET',
            success: function(data) {
                if (data.success) {
                    var traffic = data.traffic;

                    // 准备初始数据（同时提供JSON和Burp格式）
                    var initialData = {
                        mode: 'burp', // 默认使用burp模式
                        burpFormat: self.formatAsBurp(traffic),
                        jsonData: JSON.stringify(traffic, null, 2)
                    };

                    // 打开新的tab进行重放
                    TabManager.openTab('tools', 'HTTP请求重放', {
                        subModule: 'replay',
                        initialData: initialData
                    });
                } else {
                    alert(data.message);
                }
            }
        });
    };
}