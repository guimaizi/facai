function HtmlModule() {
    this.currentPage = 1;
    this.pageSize = 20;
    this.searchKeyword = '';
    this.searchType = 'md5';

    this.render = function(data, container) {
        // 保存容器引用
        this.container = container;

        container.html(`
            <div class="card">
                <div class="card-header">
                    <div class="row">
                        <div class="col-md-6">HTML大文件管理</div>
                        <div class="col-md-6 text-right">
                            <button class="btn btn-primary" id="refreshHtml">刷新</button>
                            <button class="btn btn-warning" id="clearHtml">清空</button>
                        </div>
                    </div>
                </div>
                <div class="form-group p-3">
                    <div class="row mb-3">
                        <div class="col-md-2">
                            <select class="form-control" id="searchType">
                                <option value="md5">MD5</option>
                                <option value="html">HTML内容</option>
                            </select>
                        </div>
                        <div class="col-md-4">
                            <input type="text" class="form-control" id="searchHtml" placeholder="搜索MD5或HTML内容...">
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
                                    <th>MD5</th>
                                    <th>HTML长度</th>
                                    <th>时间</th>
                                    <th>操作</th>
                                </tr>
                            </thead>
                            <tbody id="htmlList"></tbody>
                        </table>
                    </div>
                    <div id="pagination"></div>
                </div>
            </div>
        `);
        this.loadHtml();
        this.bindEvents();
    };

    this.loadHtml = function() {
        var self = this;
        $.ajax({
            url: '/api/assets/html',
            type: 'GET',
            data: {
                page: self.currentPage,
                page_size: self.pageSize,
                search_keyword: self.searchKeyword,
                search_type: self.searchType,
                sort_by: 'time',
                sort_order: -1
            },
            success: function(data) {
                var tbody = $('#htmlList');
                tbody.empty();
                if (data.htmls && data.htmls.length > 0) {
                    data.htmls.forEach(function(item) {
                        // 计算HTML长度显示
                        var sizeDisplay = item.html_len || 0;
                        if (sizeDisplay > 1024 * 1024) {
                            sizeDisplay = (sizeDisplay / 1024 / 1024).toFixed(2) + ' MB';
                        } else if (sizeDisplay > 1024) {
                            sizeDisplay = (sizeDisplay / 1024).toFixed(2) + ' KB';
                        } else {
                            sizeDisplay = sizeDisplay + ' B';
                        }

                        tbody.append(`
                            <tr>
                                <td><code>${item.html_md5 || 'N/A'}</code></td>
                                <td>${sizeDisplay}</td>
                                <td>${item.time || ''}</td>
                                <td>
                                    <button class="btn btn-info btn-sm view-detail" data-id="${item._id}">详情</button>
                                    <button class="btn btn-danger btn-sm delete-html" data-id="${item._id}">删除</button>
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
                            self.loadHtml();
                        }
                    });
                    $('#pagination').html(paginationHtml);
                } else {
                    tbody.append('<tr><td colspan="4" class="text-center text-muted">暂无HTML数据</td></tr>');
                    $('#pagination').html('');
                }
            },
            error: function(xhr) {
                var tbody = $('#htmlList');
                tbody.empty();
                if (xhr.status === 404 || xhr.status === 500) {
                    tbody.append('<tr><td colspan="4" class="text-center text-muted">暂无项目或暂无数据</td></tr>');
                } else {
                    tbody.append('<tr><td colspan="4" class="text-center text-danger">加载失败，请重试</td></tr>');
                }
                $('#pagination').html('');
            }
        });
    };

    this.bindEvents = function() {
        var self = this;

        // 刷新按钮
        $('#refreshHtml').on('click', function() {
            self.currentPage = 1;
            self.loadHtml();
        });

        // 清空按钮
        $('#clearHtml').on('click', function() {
            if (confirm('确定要清空所有HTML数据吗？')) {
                $.ajax({
                    url: '/api/assets/html/clear',
                    type: 'POST',
                    success: function(data) {
                        if (data.success) {
                            alert(data.message);
                            self.currentPage = 1;
                            self.loadHtml();
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
            self.searchKeyword = $('#searchHtml').val();
            self.currentPage = 1;
            self.loadHtml();
        });

        // 清除搜索按钮
        $('#clearSearchBtn').on('click', function() {
            $('#searchHtml').val('');
            self.searchKeyword = '';
            self.currentPage = 1;
            self.loadHtml();
        });

        // 搜索框回车搜索
        $('#searchHtml').on('keypress', function(e) {
            if (e.which === 13) {
                $('#searchBtn').click();
            }
        });

        // 查看详情 - 限制在HTML容器内
        this.container.on('click', '.view-detail', function() {
            var id = $(this).data('id');
            self.showDetailModal(id);
        });

        // 删除HTML - 限制在HTML容器内
        this.container.on('click', '.delete-html', function() {
            var id = $(this).data('id');
            if (confirm('确定要删除这条HTML数据吗？')) {
                $.ajax({
                    url: '/api/assets/html/' + id,
                    type: 'DELETE',
                    success: function(data) {
                        if (data.success) {
                            alert(data.message);
                            self.loadHtml();
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
            url: '/api/assets/html/' + id,
            type: 'GET',
            success: function(data) {
                if (data.success && data.html) {
                    var html = data.html;

                    // 计算HTML长度显示
                    var sizeDisplay = html.html_len || 0;
                    if (sizeDisplay > 1024 * 1024) {
                        sizeDisplay = (sizeDisplay / 1024 / 1024).toFixed(2) + ' MB';
                    } else if (sizeDisplay > 1024) {
                        sizeDisplay = (sizeDisplay / 1024).toFixed(2) + ' KB';
                    } else {
                        sizeDisplay = sizeDisplay + ' B';
                    }

                    var modalHtml = `
                        <div class="modal" id="htmlDetailModal">
                            <div class="modal-content" style="max-width: 900px;">
                                <div class="modal-header">
                                    <h5 class="modal-title">HTML详情</h5>
                                    <button type="button" class="modal-close">&times;</button>
                                </div>
                                <div class="modal-body">
                                    <div class="form-group">
                                        <label>MD5</label>
                                        <input type="text" class="form-control" value="${html.html_md5 || ''}" readonly>
                                    </div>
                                    <div class="form-group">
                                        <label>HTML长度</label>
                                        <input type="text" class="form-control" value="${sizeDisplay} (${html.html_len || 0} bytes)" readonly>
                                    </div>
                                    <div class="form-group">
                                        <label>时间</label>
                                        <input type="text" class="form-control" value="${html.time || ''}" readonly>
                                    </div>
                                    <div class="form-group">
                                        <label>HTML内容</label>
                                        <textarea class="form-control" rows="20" readonly style="font-family: 'Consolas', 'Monaco', 'Courier New', monospace; font-size: 12px;">${html.html || ''}</textarea>
                                    </div>
                                </div>
                                <div class="modal-footer">
                                    <button type="button" class="btn btn-secondary modal-close-btn">关闭</button>
                                </div>
                            </div>
                        </div>
                    `;

                    $('body').append(modalHtml);
                    $('#htmlDetailModal').addClass('active');

                    // 关闭modal - 直接绑定到元素上
                    $('#htmlDetailModal').on('click', '.modal-close, .modal-close-btn', function() {
                        $('#htmlDetailModal').removeClass('active');
                        setTimeout(function() {
                            $('#htmlDetailModal').remove();
                        }, 300);
                    });

                    // 点击modal外部关闭
                    $('#htmlDetailModal').on('click', function(e) {
                        if (e.target === this) {
                            $(this).removeClass('active');
                            setTimeout(function() {
                                $(this).remove();
                            }, 300);
                        }
                    });
                } else {
                    // 静默处理错误，不显示alert
                    console.log('获取HTML详情失败');
                }
            },
            error: function(xhr) {
                // 静默处理错误
                console.log('请求失败，状态码:', xhr.status);
            }
        });
    };
}
