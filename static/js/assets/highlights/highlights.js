function HighlightsModule() {
    this.currentPage = 1;
    this.pageSize = 20;
    this.searchKeyword = '';
    this.searchType = 'url';
    this.sortBy = 'time';
    this.sortOrder = -1;

    this.render = function(data, container) {
        // 保存容器引用
        this.container = container;

        container.html(`
            <div class="card">
                <div class="card-header">
                    <div class="row">
                        <div class="col-md-6">重点资产管理</div>
                        <div class="col-md-6 text-right">
                            <button class="btn btn-success" id="addHighlight">添加资产</button>
                            <button class="btn btn-primary" id="refreshHighlights">刷新</button>
                            <button class="btn btn-warning" id="clearHighlights">清空</button>
                        </div>
                    </div>
                </div>
                <div class="form-group p-3">
                    <div class="row mb-3">
                        <div class="col-md-2">
                            <select class="form-control" id="searchType">
                                <option value="url">URL</option>
                                <option value="title">标题</option>
                                <option value="tags">标签</option>
                                <option value="type">类型</option>
                            </select>
                        </div>
                        <div class="col-md-4">
                            <input type="text" class="form-control" id="searchHighlight" placeholder="搜索URL、标题、标签...">
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
                                    <th class="sortable" data-sort="type" style="width: 100px;">类型 <span class="sort-icon"></span></th>
                                    <th class="sortable" data-sort="url">URL <span class="sort-icon"></span></th>
                                    <th class="sortable" data-sort="title" style="width: 150px;">标题 <span class="sort-icon"></span></th>
                                    <th style="width: 200px;">标签</th>
                                    <th class="sortable" data-sort="time" style="width: 150px;">时间 <span class="sort-icon"></span></th>
                                    <th style="width: 150px;">操作</th>
                                </tr>
                            </thead>
                            <tbody id="highlightsList"></tbody>
                        </table>
                    </div>
                    <div id="pagination"></div>
                </div>
            </div>
        `);
        this.updateSortIcons();
        this.loadHighlights();
        this.bindEvents();
    };

    this.loadHighlights = function() {
        var self = this;
        $.ajax({
            url: '/api/assets/highlights',
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
                var tbody = $('#highlightsList');
                tbody.empty();
                if (data.data && data.data.length > 0) {
                    data.data.forEach(function(item) {
                        // 处理类型显示
                        var typeDisplay = self.getTypeDisplay(item.type);
                        var typeColor = self.getTypeColor(item.type);

                        // 处理标签显示
                        var tagsHtml = '';
                        if (item.tags && item.tags.length > 0) {
                            item.tags.forEach(function(tag) {
                                tagsHtml += `<span class="highlight-tag">${tag}</span>`;
                            });
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
                                <td><span class="badge badge-${typeColor}">${typeDisplay}</span></td>
                                <td><a href="${item.url || '#'}" target="_blank" title="${item.url || ''}">${urlDisplay}</a></td>
                                <td title="${item.title || ''}">${titleDisplay}</td>
                                <td>${tagsHtml}</td>
                                <td>${item.time || ''}</td>
                                <td>
                                    <button class="btn btn-info btn-sm hl-view-detail" data-id="${item._id}">详情</button>
                                    <button class="btn btn-warning btn-sm hl-edit" data-id="${item._id}">编辑</button>
                                    <button class="btn btn-danger btn-sm hl-delete" data-id="${item._id}">删除</button>
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
                            self.loadHighlights();
                        }
                    });
                    $('#pagination').html(paginationHtml);
                } else {
                    tbody.append('<tr><td colspan="6" class="text-center text-muted">暂无重点资产数据</td></tr>');
                    $('#pagination').html('');
                }
            },
            error: function(xhr) {
                var tbody = $('#highlightsList');
                tbody.empty();
                if (xhr.status === 404 || xhr.status === 500) {
                    tbody.append('<tr><td colspan="6" class="text-center text-muted">暂无项目或暂无数据</td></tr>');
                } else {
                    tbody.append('<tr><td colspan="6" class="text-center text-danger">加载失败，请重试</td></tr>');
                }
                $('#pagination').html('');
            }
        });
    };

    this.getTypeDisplay = function(type) {
        var typeMap = {
            'web': 'Web',
            'win_client': 'Win客户端',
            'mac_client': 'Mac客户端',
            'android_client': 'Android',
            'ios_client': 'iOS',
            'mini_client': '小程序'
        };
        return typeMap[type] || type || '未知';
    };

    this.getTypeColor = function(type) {
        var colorMap = {
            'web': 'primary',
            'win_client': 'info',
            'mac_client': 'secondary',
            'android_client': 'success',
            'ios_client': 'warning',
            'mini_client': 'danger'
        };
        return colorMap[type] || 'secondary';
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
                self.sortOrder = self.sortOrder === 1 ? -1 : 1;
            } else {
                self.sortBy = field;
                self.sortOrder = -1;
            }
            
            self.updateSortIcons();
            self.currentPage = 1;
            self.loadHighlights();
        });

        // 添加资产按钮
        $('#addHighlight').on('click', function() {
            self.showAddModal();
        });

        // 刷新按钮
        $('#refreshHighlights').on('click', function() {
            self.currentPage = 1;
            self.loadHighlights();
        });

        // 清空按钮
        $('#clearHighlights').on('click', function() {
            if (confirm('确定要清空所有重点资产数据吗？')) {
                $.ajax({
                    url: '/api/assets/highlights/clear',
                    type: 'POST',
                    success: function(data) {
                        if (data.success) {
                            alert(data.message);
                            self.currentPage = 1;
                            self.loadHighlights();
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
            self.searchKeyword = $('#searchHighlight').val();
            self.currentPage = 1;
            self.loadHighlights();
        });

        // 清除搜索按钮
        $('#clearSearchBtn').on('click', function() {
            $('#searchHighlight').val('');
            self.searchKeyword = '';
            self.currentPage = 1;
            self.loadHighlights();
        });

        // 搜索框回车搜索
        $('#searchHighlight').on('keypress', function(e) {
            if (e.which === 13) {
                $('#searchBtn').click();
            }
        });

        // 查看详情
        this.container.on('click', '.hl-view-detail', function() {
            var id = $(this).data('id');
            self.showDetailModal(id);
        });

        // 编辑
        this.container.on('click', '.hl-edit', function() {
            var id = $(this).data('id');
            self.showEditModal(id);
        });

        // 删除
        this.container.on('click', '.hl-delete', function() {
            var id = $(this).data('id');
            if (confirm('确定要删除这条重点资产数据吗？')) {
                $.ajax({
                    url: '/api/assets/highlights/' + id,
                    type: 'DELETE',
                    success: function(data) {
                        if (data.success) {
                            alert(data.message);
                            self.loadHighlights();
                        } else {
                            alert(data.message);
                        }
                    }
                });
            }
        });
    };

    this.showAddModal = function() {
        var self = this;
        var modalHtml = `
            <div class="modal" id="highlightModal">
                <div class="modal-content" style="max-width: 800px;">
                    <div class="modal-header">
                        <h5 class="modal-title">添加重点资产</h5>
                        <button type="button" class="modal-close">&times;</button>
                    </div>
                    <div class="modal-body">
                        <form id="highlightForm">
                            <div class="form-group">
                                <label>URL *</label>
                                <input type="text" class="form-control" id="hl_url" required>
                            </div>
                            <div class="row">
                                <div class="col-md-3">
                                    <div class="form-group">
                                        <label>类型 *</label>
                                        <select class="form-control" id="hl_type" required>
                                            <option value="web">Web</option>
                                            <option value="win_client">Win客户端</option>
                                            <option value="mac_client">Mac客户端</option>
                                            <option value="android_client">Android</option>
                                            <option value="ios_client">iOS</option>
                                            <option value="mini_client">小程序</option>
                                        </select>
                                    </div>
                                </div>
                                <div class="col-md-9">
                                    <div class="form-group">
                                        <label>标题</label>
                                        <input type="text" class="form-control" id="hl_title">
                                    </div>
                                </div>
                            </div>
                            <div class="form-group">
                                <label>来源URL</label>
                                <input type="text" class="form-control" id="hl_referer_url">
                            </div>
                            <div class="form-group">
                                <label>标签（逗号分隔）</label>
                                <input type="text" class="form-control" id="hl_tags" placeholder="登录点, 敏感接口, 后台...">
                            </div>
                            <div class="form-group">
                                <label>描述</label>
                                <textarea class="form-control" id="hl_desc" rows="2"></textarea>
                            </div>
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="form-group">
                                        <label>平台</label>
                                        <input type="text" class="form-control" id="hl_platform">
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="form-group">
                                        <label>版本</label>
                                        <input type="text" class="form-control" id="hl_version">
                                    </div>
                                </div>
                            </div>
                            <div class="form-group">
                                <label>下载URL</label>
                                <input type="text" class="form-control" id="hl_download_url">
                            </div>
                            <div class="form-group">
                                <label>HTTP请求</label>
                                <textarea class="form-control" id="hl_http_request" rows="3" style="font-family: monospace;"></textarea>
                            </div>
                            <div class="form-group">
                                <label>HTTP响应</label>
                                <textarea class="form-control" id="hl_http_response" rows="3" style="font-family: monospace;"></textarea>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-primary" id="saveHighlight">保存</button>
                        <button type="button" class="btn btn-secondary modal-close-btn">取消</button>
                    </div>
                </div>
            </div>
        `;

        $('body').append(modalHtml);
        $('#highlightModal').addClass('active');

        // 保存按钮
        $('#saveHighlight').on('click', function() {
            var tagsStr = $('#hl_tags').val();
            var tags = tagsStr ? tagsStr.split(',').map(function(t) { return t.trim(); }).filter(function(t) { return t; }) : [];

            var data = {
                url: $('#hl_url').val(),
                type: $('#hl_type').val(),
                title: $('#hl_title').val(),
                referer_url: $('#hl_referer_url').val(),
                tags: tags,
                desc: $('#hl_desc').val(),
                platform: $('#hl_platform').val(),
                version: $('#hl_version').val(),
                download_url: $('#hl_download_url').val(),
                http_request: $('#hl_http_request').val(),
                http_response: $('#hl_http_response').val()
            };

            $.ajax({
                url: '/api/assets/highlights',
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify(data),
                success: function(result) {
                    if (result.success) {
                        alert(result.message);
                        $('#highlightModal').removeClass('active');
                        setTimeout(function() {
                            $('#highlightModal').remove();
                        }, 300);
                        self.loadHighlights();
                    } else {
                        alert(result.message);
                    }
                }
            });
        });

        // 关闭modal
        $('#highlightModal').on('click', '.modal-close, .modal-close-btn', function() {
            $('#highlightModal').removeClass('active');
            setTimeout(function() {
                $('#highlightModal').remove();
            }, 300);
        });

        // 点击modal外部关闭
        $('#highlightModal').on('click', function(e) {
            if (e.target === this) {
                $(this).removeClass('active');
                setTimeout(function() {
                    $(this).remove();
                }, 300);
            }
        });
    };

    this.showEditModal = function(id) {
        var self = this;
        $.ajax({
            url: '/api/assets/highlights/' + id,
            type: 'GET',
            success: function(data) {
                if (data.success && data.highlight) {
                    var hl = data.highlight;
                    var tagsStr = (hl.tags || []).join(', ');

                    var modalHtml = `
                        <div class="modal" id="highlightModal">
                            <div class="modal-content" style="max-width: 800px;">
                                <div class="modal-header">
                                    <h5 class="modal-title">编辑重点资产</h5>
                                    <button type="button" class="modal-close">&times;</button>
                                </div>
                                <div class="modal-body">
                                    <form id="highlightForm">
                                        <div class="form-group">
                                            <label>URL *</label>
                                            <input type="text" class="form-control" id="hl_url" value="${hl.url || ''}" required>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-3">
                                                <div class="form-group">
                                                    <label>类型 *</label>
                                                    <select class="form-control" id="hl_type" required>
                                                        <option value="web" ${hl.type === 'web' ? 'selected' : ''}>Web</option>
                                                        <option value="win_client" ${hl.type === 'win_client' ? 'selected' : ''}>Win客户端</option>
                                                        <option value="mac_client" ${hl.type === 'mac_client' ? 'selected' : ''}>Mac客户端</option>
                                                        <option value="android_client" ${hl.type === 'android_client' ? 'selected' : ''}>Android</option>
                                                        <option value="ios_client" ${hl.type === 'ios_client' ? 'selected' : ''}>iOS</option>
                                                        <option value="mini_client" ${hl.type === 'mini_client' ? 'selected' : ''}>小程序</option>
                                                    </select>
                                                </div>
                                            </div>
                                            <div class="col-md-9">
                                                <div class="form-group">
                                                    <label>标题</label>
                                                    <input type="text" class="form-control" id="hl_title" value="${hl.title || ''}">
                                                </div>
                                            </div>
                                        </div>
                                        <div class="form-group">
                                            <label>来源URL</label>
                                            <input type="text" class="form-control" id="hl_referer_url" value="${hl.referer_url || ''}">
                                        </div>
                                        <div class="form-group">
                                            <label>标签（逗号分隔）</label>
                                            <input type="text" class="form-control" id="hl_tags" value="${tagsStr}" placeholder="登录点, 敏感接口, 后台...">
                                        </div>
                                        <div class="form-group">
                                            <label>描述</label>
                                            <textarea class="form-control" id="hl_desc" rows="2">${hl.desc || ''}</textarea>
                                        </div>
                                        <div class="row">
                                            <div class="col-md-6">
                                                <div class="form-group">
                                                    <label>平台</label>
                                                    <input type="text" class="form-control" id="hl_platform" value="${hl.platform || ''}">
                                                </div>
                                            </div>
                                            <div class="col-md-6">
                                                <div class="form-group">
                                                    <label>版本</label>
                                                    <input type="text" class="form-control" id="hl_version" value="${hl.version || ''}">
                                                </div>
                                            </div>
                                        </div>
                                        <div class="form-group">
                                            <label>下载URL</label>
                                            <input type="text" class="form-control" id="hl_download_url" value="${hl.download_url || ''}">
                                        </div>
                                        <div class="form-group">
                                            <label>HTTP请求</label>
                                            <textarea class="form-control" id="hl_http_request" rows="3" style="font-family: monospace;">${hl.http_request || ''}</textarea>
                                        </div>
                                        <div class="form-group">
                                            <label>HTTP响应</label>
                                            <textarea class="form-control" id="hl_http_response" rows="3" style="font-family: monospace;">${hl.http_response || ''}</textarea>
                                        </div>
                                    </form>
                                </div>
                                <div class="modal-footer">
                                    <button type="button" class="btn btn-primary" id="updateHighlight">更新</button>
                                    <button type="button" class="btn btn-secondary modal-close-btn">取消</button>
                                </div>
                            </div>
                        </div>
                    `;

                    $('body').append(modalHtml);
                    $('#highlightModal').addClass('active');

                    // 更新按钮
                    $('#updateHighlight').on('click', function() {
                        var tagsStr = $('#hl_tags').val();
                        var tags = tagsStr ? tagsStr.split(',').map(function(t) { return t.trim(); }).filter(function(t) { return t; }) : [];

                        var updateData = {
                            url: $('#hl_url').val(),
                            type: $('#hl_type').val(),
                            title: $('#hl_title').val(),
                            referer_url: $('#hl_referer_url').val(),
                            tags: tags,
                            desc: $('#hl_desc').val(),
                            platform: $('#hl_platform').val(),
                            version: $('#hl_version').val(),
                            download_url: $('#hl_download_url').val(),
                            http_request: $('#hl_http_request').val(),
                            http_response: $('#hl_http_response').val()
                        };

                        $.ajax({
                            url: '/api/assets/highlights/' + id,
                            type: 'POST',
                            contentType: 'application/json',
                            data: JSON.stringify(updateData),
                            success: function(result) {
                                if (result.success) {
                                    alert(result.message);
                                    $('#highlightModal').removeClass('active');
                                    setTimeout(function() {
                                        $('#highlightModal').remove();
                                    }, 300);
                                    self.loadHighlights();
                                } else {
                                    alert(result.message);
                                }
                            }
                        });
                    });

                    // 关闭modal
                    $('#highlightModal').on('click', '.modal-close, .modal-close-btn', function() {
                        $('#highlightModal').removeClass('active');
                        setTimeout(function() {
                            $('#highlightModal').remove();
                        }, 300);
                    });

                    // 点击modal外部关闭
                    $('#highlightModal').on('click', function(e) {
                        if (e.target === this) {
                            $(this).removeClass('active');
                            setTimeout(function() {
                                $(this).remove();
                            }, 300);
                        }
                    });
                } else {
                    alert('获取数据失败');
                }
            }
        });
    };

    this.showDetailModal = function(id) {
        var self = this;
        $.ajax({
            url: '/api/assets/highlights/' + id,
            type: 'GET',
            success: function(data) {
                if (data.success && data.highlight) {
                    var hl = data.highlight;
                    
                    // 处理标签显示
                    var tagsText = (hl.tags && hl.tags.length > 0) ? hl.tags.join(', ') : '无';
                    
                    // 类型显示
                    var typeDisplay = self.getTypeDisplay(hl.type);

                    var modalHtml = `
                        <div class="modal" id="detailModal">
                            <div class="modal-content highlight-detail-modal" style="max-width: 1000px;">
                                <div class="modal-header">
                                    <h5 class="modal-title">重点资产详情</h5>
                                    <button type="button" class="modal-close">&times;</button>
                                </div>
                                <div class="modal-body">
                                    <ul class="nav nav-tabs mb-3" id="detailTabs">
                                        <li class="nav-item">
                                            <a class="nav-link active" data-toggle="tab" href="#basicInfo">基本信息</a>
                                        </li>
                                        <li class="nav-item">
                                            <a class="nav-link" data-toggle="tab" href="#requestInfo">请求信息</a>
                                        </li>
                                        <li class="nav-item">
                                            <a class="nav-link" data-toggle="tab" href="#responseInfo">响应信息</a>
                                        </li>
                                    </ul>
                                    <div class="tab-content">
                                        <div class="tab-pane fade show active" id="basicInfo">
                                            <div class="row">
                                                <div class="col-md-8">
                                                    <div class="form-group">
                                                        <label>URL</label>
                                                        <input type="text" class="form-control" value="${hl.url || ''}" readonly>
                                                    </div>
                                                </div>
                                                <div class="col-md-4">
                                                    <div class="form-group">
                                                        <label>类型</label>
                                                        <input type="text" class="form-control" value="${typeDisplay}" readonly>
                                                    </div>
                                                </div>
                                            </div>
                                            <div class="row">
                                                <div class="col-md-8">
                                                    <div class="form-group">
                                                        <label>标题</label>
                                                        <input type="text" class="form-control" value="${hl.title || ''}" readonly>
                                                    </div>
                                                </div>
                                                <div class="col-md-4">
                                                    <div class="form-group">
                                                        <label>来源URL</label>
                                                        <input type="text" class="form-control" value="${hl.referer_url || ''}" readonly>
                                                    </div>
                                                </div>
                                            </div>
                                            <div class="form-group">
                                                <label>标签</label>
                                                <input type="text" class="form-control" value="${tagsText}" readonly>
                                            </div>
                                            <div class="form-group">
                                                <label>描述</label>
                                                <textarea class="form-control" rows="2" readonly>${hl.desc || ''}</textarea>
                                            </div>
                                            <div class="row">
                                                <div class="col-md-4">
                                                    <div class="form-group">
                                                        <label>平台</label>
                                                        <input type="text" class="form-control" value="${hl.platform || ''}" readonly>
                                                    </div>
                                                </div>
                                                <div class="col-md-4">
                                                    <div class="form-group">
                                                        <label>版本</label>
                                                        <input type="text" class="form-control" value="${hl.version || ''}" readonly>
                                                    </div>
                                                </div>
                                                <div class="col-md-4">
                                                    <div class="form-group">
                                                        <label>状态</label>
                                                        <input type="text" class="form-control" value="${hl.status || 0}" readonly>
                                                    </div>
                                                </div>
                                            </div>
                                            <div class="form-group">
                                                <label>下载URL</label>
                                                <input type="text" class="form-control" value="${hl.download_url || ''}" readonly>
                                            </div>
                                            <div class="row">
                                                <div class="col-md-6">
                                                    <div class="form-group">
                                                        <label>包名</label>
                                                        <input type="text" class="form-control" value="${hl.package_name || ''}" readonly>
                                                    </div>
                                                </div>
                                                <div class="col-md-6">
                                                    <div class="form-group">
                                                        <label>时间</label>
                                                        <input type="text" class="form-control" value="${hl.time || ''}" readonly>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                        <div class="tab-pane fade" id="requestInfo">
                                            <div class="form-group">
                                                <label>HTTP请求</label>
                                                <textarea class="form-control" rows="15" readonly style="font-family: 'Consolas', 'Monaco', 'Courier New', monospace; font-size: 12px;">${hl.http_request || ''}</textarea>
                                            </div>
                                        </div>
                                        <div class="tab-pane fade" id="responseInfo">
                                            <div class="form-group">
                                                <label>HTTP响应</label>
                                                <textarea class="form-control" rows="15" readonly style="font-family: 'Consolas', 'Monaco', 'Courier New', monospace; font-size: 12px;">${hl.http_response || ''}</textarea>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div class="modal-footer">
                                    <button type="button" class="btn btn-secondary modal-close-btn">关闭</button>
                                </div>
                            </div>
                        </div>
                    `;

                    $('body').append(modalHtml);
                    $('#detailModal').addClass('active');

                    // Tab切换
                    $('#detailModal').on('click', '#detailTabs .nav-link', function(e) {
                        e.preventDefault();
                        var target = $(this).attr('href');
                        
                        $('#detailTabs .nav-link').removeClass('active');
                        $(this).addClass('active');
                        
                        $('#detailModal .tab-pane').removeClass('show active');
                        $(target).addClass('show active');
                    });

                    // 关闭modal
                    $('#detailModal').on('click', '.modal-close, .modal-close-btn', function() {
                        $('#detailModal').removeClass('active');
                        setTimeout(function() {
                            $('#detailModal').remove();
                        }, 300);
                    });

                    // 点击modal外部关闭
                    $('#detailModal').on('click', function(e) {
                        if (e.target === this) {
                            $(this).removeClass('active');
                            setTimeout(function() {
                                $(this).remove();
                            }, 300);
                        }
                    });
                } else {
                    alert('获取数据失败');
                }
            }
        });
    };
}
