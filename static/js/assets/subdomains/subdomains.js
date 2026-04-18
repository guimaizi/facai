function SubdomainsModule() {
    this.currentPage = 1;
    this.pageSize = 20;
    this.searchKeyword = '';

    this.render = function(data, container) {
        // 保存容器引用
        this.container = container;

        container.html(`
            <div class="card">
                <div class="card-header">
                    <div class="row">
                        <div class="col-md-6">子域名管理</div>
                        <div class="col-md-6 text-right">
                            <button class="btn btn-primary" id="refreshSubdomains">刷新</button>
                            <button class="btn btn-warning" id="clearSubdomains">清空</button>
                        </div>
                    </div>
                </div>
                <div class="form-group p-3">
                    <div class="row mb-3">
                        <div class="col-md-4">
                            <input type="text" class="form-control" id="searchSubdomain" placeholder="搜索子域名...">
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
                                    <th>子域名</th>
                                    <th>域名</th>
                                    <th>DNS数据</th>
                                    <th>端口列表</th>
                                    <th>时间</th>
                                    <th>操作</th>
                                </tr>
                            </thead>
                            <tbody id="subdomainList"></tbody>
                        </table>
                    </div>
                    <div id="pagination"></div>
                </div>
            </div>
        `);
        this.loadSubdomains();
        this.bindEvents();
    };

    this.loadSubdomains = function() {
        var self = this;
        $.ajax({
            url: '/api/assets/subdomains',
            type: 'GET',
            data: {
                page: self.currentPage,
                page_size: self.pageSize,
                search_keyword: self.searchKeyword,
                sort_by: 'time',
                sort_order: -1
            },
            success: function(data) {
                var tbody = $('#subdomainList');
                tbody.empty();
                if (data.subdomains && data.subdomains.length > 0) {
                    data.subdomains.forEach(function(item) {
                        // 处理DNS数据显示
                        var dnsData = '';
                        if (item.dns_data && item.dns_data.length > 0) {
                            var dnsItems = [];
                            item.dns_data.forEach(function(dns) {
                                if (dns.A) {
                                    dnsItems.push('A:' + dns.A);
                                } else if (dns.CNAME) {
                                    dnsItems.push('CNAME:' + dns.CNAME);
                                }
                            });
                            dnsData = dnsItems.join(', ');
                        }

                        // 处理端口列表显示
                        var portList = '';
                        if (item.port_list && item.port_list.length > 0) {
                            portList = item.port_list.map(p => p.port + (p.service ? '(' + p.service + ')' : '')).join(', ');
                        }

                        tbody.append(`
                            <tr>
                                <td>${item.subdomain}</td>
                                <td>${item.domain || ''}</td>
                                <td>${dnsData}</td>
                                <td>${portList}</td>
                                <td>${item.time || ''}</td>
                                <td>
                                    <button class="btn btn-info btn-sm view-detail" data-id="${item._id}">详情</button>
                                    <button class="btn btn-danger btn-sm delete-subdomain" data-id="${item._id}">删除</button>
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
                            self.loadSubdomains();
                        }
                    });
                    $('#pagination').html(paginationHtml);
                } else {
                    tbody.append('<tr><td colspan="6" class="text-center">暂无数据</td></tr>');
                }
            },
            error: function() {
                $('#subdomainList').append('<tr><td colspan="6" class="text-center text-danger">加载失败</td></tr>');
            }
        });
    };

    this.bindEvents = function() {
        var self = this;

        // 刷新按钮
        $('#refreshSubdomains').on('click', function() {
            self.currentPage = 1;
            self.loadSubdomains();
        });

        // 清空按钮
        $('#clearSubdomains').on('click', function() {
            if (confirm('确定要清空所有子域名数据吗？')) {
                $.ajax({
                    url: '/api/assets/subdomains/clear',
                    type: 'POST',
                    success: function(data) {
                        if (data.success) {
                            alert(data.message);
                            self.currentPage = 1;
                            self.loadSubdomains();
                        } else {
                            alert(data.message);
                        }
                    }
                });
            }
        });

        // 搜索按钮
        $('#searchBtn').on('click', function() {
            self.searchKeyword = $('#searchSubdomain').val();
            self.currentPage = 1;
            self.loadSubdomains();
        });

        // 清除搜索按钮
        $('#clearSearchBtn').on('click', function() {
            $('#searchSubdomain').val('');
            self.searchKeyword = '';
            self.currentPage = 1;
            self.loadSubdomains();
        });

        // 搜索框回车搜索
        $('#searchSubdomain').on('keypress', function(e) {
            if (e.which === 13) {
                $('#searchBtn').click();
            }
        });

        // 查看详情 - 限制在子域名容器内
        this.container.on('click', '.view-detail', function() {
            var id = $(this).data('id');
            self.showDetailModal(id);
        });

        // 删除子域名 - 限制在子域名容器内
        this.container.on('click', '.delete-subdomain', function() {
            var id = $(this).data('id');
            if (confirm('确定要删除这条子域名数据吗？')) {
                $.ajax({
                    url: '/api/assets/subdomains/' + id,
                    type: 'DELETE',
                    success: function(data) {
                        if (data.success) {
                            alert(data.message);
                            self.loadSubdomains();
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
            url: '/api/assets/subdomains/' + id,
            type: 'GET',
            success: function(data) {
                if (data.success && data.subdomain) {
                    var subdomain = data.subdomain;

                    // 处理DNS数据显示
                    var dnsDataText = '';
                    if (subdomain.dns_data && subdomain.dns_data.length > 0) {
                        var dnsItems = subdomain.dns_data.map(function(dns) {
                            if (dns.A) {
                                return 'A: ' + dns.A;
                            } else if (dns.CNAME) {
                                return 'CNAME: ' + dns.CNAME;
                            }
                            return '';
                        }).filter(function(item) { return item; });
                        dnsDataText = dnsItems.join('\n');
                    }

                    // 处理端口列表显示
                    var portListText = '';
                    if (subdomain.port_list && subdomain.port_list.length > 0) {
                        portListText = subdomain.port_list.map(function(p) {
                            var line = p.port;
                            if (p.service) {
                                line += '|' + p.service;
                            }
                            if (p.version) {
                                line += '|' + p.version;
                            }
                            return line;
                        }).join('\n');
                    }

                    var modalHtml = `
                        <div class="modal" id="subdomainDetailModal">
                            <div class="modal-content">
                                <div class="modal-header">
                                    <h5 class="modal-title">子域名详情</h5>
                                    <button type="button" class="modal-close">&times;</button>
                                </div>
                                <div class="modal-body">
                                    <div class="form-group">
                                        <label>子域名</label>
                                        <input type="text" class="form-control" value="${subdomain.subdomain}" readonly>
                                    </div>
                                    <div class="form-group">
                                        <label>域名</label>
                                        <input type="text" class="form-control" value="${subdomain.domain || ''}" readonly>
                                    </div>
                                    <div class="form-group">
                                        <label>DNS数据</label>
                                        <textarea class="form-control" rows="5" readonly>${dnsDataText}</textarea>
                                    </div>
                                    <div class="form-group">
                                        <label>端口列表</label>
                                        <textarea class="form-control" rows="5" readonly>${portListText}</textarea>
                                    </div>
                                    <div class="form-group">
                                        <label>状态</label>
                                        <input type="text" class="form-control" value="${subdomain.status || 0}" readonly>
                                    </div>
                                    <div class="form-group">
                                        <label>时间</label>
                                        <input type="text" class="form-control" value="${subdomain.time || ''}" readonly>
                                    </div>
                                </div>
                                <div class="modal-footer">
                                    <button type="button" class="btn btn-secondary modal-close-btn">关闭</button>
                                </div>
                            </div>
                        </div>
                    `;

                    $('body').append(modalHtml);
                    $('#subdomainDetailModal').addClass('active');

                    // 关闭modal - 直接绑定到元素上
                    $('#subdomainDetailModal').on('click', '.modal-close, .modal-close-btn', function() {
                        $('#subdomainDetailModal').removeClass('active');
                        setTimeout(function() {
                            $('#subdomainDetailModal').remove();
                        }, 300);
                    });

                    // 点击modal外部关闭
                    $('#subdomainDetailModal').on('click', function(e) {
                        if (e.target === this) {
                            $(this).removeClass('active');
                            setTimeout(function() {
                                $(this).remove();
                            }, 300);
                        }
                    });
                } else {
                    // 静默处理错误，不显示alert
                }
            },
            error: function() {
                alert('请求失败，请检查网络连接');
            }
        });
    };
}
