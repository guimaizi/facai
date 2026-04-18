function ClipboardModule() {
    this.render = function(data, container) {
        container.html(`
            <div class="clipboard-container">
                <div class="clipboard-header">
                    <h3>📋 常用剪贴板</h3>
                    <div class="clipboard-actions">
                        <button class="btn btn-primary btn-sm" id="addClipboard">
                            <span class="btn-icon">+</span>
                            <span>添加</span>
                        </button>
                        <button class="btn btn-success btn-sm" id="refreshClipboard">
                            <span class="btn-icon">↻</span>
                            <span>刷新</span>
                        </button>
                    </div>
                </div>

                <!-- 添加文本区域 -->
                <div class="clipboard-form" id="clipboardForm">
                    <div class="form-group">
                        <label>添加常用文本</label>
                        <textarea id="clipboardInput" rows="3" placeholder="输入要添加的文本..."></textarea>
                    </div>
                    <div class="form-actions">
                        <button class="btn btn-secondary btn-sm" id="cancelAdd">取消</button>
                        <button class="btn btn-primary btn-sm" id="confirmAdd">确认添加</button>
                    </div>
                </div>

                <!-- 剪贴板列表 -->
                <div class="clipboard-list" id="clipboardList">
                    <div class="empty-state">
                        <div class="empty-icon">📝</div>
                        <p>暂无剪贴板内容</p>
                        <p class="empty-hint">点击"添加"按钮添加常用文本</p>
                    </div>
                </div>
            </div>
        `);

        this.loadClipboard();
        this.bindEvents();
    };

    this.loadClipboard = function() {
        var self = this;

        // 先获取当前运行的项目
        $.ajax({
            url: '/api/projects/status',
            type: 'GET',
            success: function(statusData) {
                if (statusData.running_project) {
                    // 获取项目配置中的剪贴板文本
                    self.loadProjectClipboard(statusData.running_project.Project);
                } else {
                    self.showEmptyState('无运行项目');
                }
            },
            error: function() {
                self.showEmptyState('加载失败');
            }
        });
    };

    this.loadProjectClipboard = function(projectName) {
        var self = this;

        $.ajax({
            url: '/api/projects/list',
            type: 'GET',
            success: function(data) {
                var project = data.projects.find(p => p.Project === projectName);
                self.renderClipboardList(project);
            },
            error: function() {
                self.showEmptyState('加载失败');
            }
        });
    };

    this.renderClipboardList = function(project) {
        var listContainer = $('#clipboardList');
        listContainer.empty();

        if (!project || !project.clipboard_text || project.clipboard_text.length === 0) {
            this.showEmptyState();
            return;
        }

        var items = project.clipboard_text;
        items.forEach(function(text, index) {
            var itemHtml = `
                <div class="clipboard-item" data-index="${index}">
                    <div class="item-content">
                        <div class="item-text">${this.escapeHtml(text)}</div>
                    </div>
                    <div class="item-actions">
                        <button class="btn btn-success btn-sm clipboard-btn-copy" title="复制到剪贴板">
                            <span class="btn-icon">📋</span>
                            <span>复制</span>
                        </button>
                        <button class="btn btn-danger btn-sm clipboard-btn-delete" title="删除">
                            <span class="btn-icon">🗑️</span>
                        </button>
                    </div>
                </div>
            `;
            listContainer.append(itemHtml);
        }.bind(this));
    };

    this.showEmptyState = function(message) {
        var listContainer = $('#clipboardList');
        listContainer.html(`
            <div class="empty-state">
                <div class="empty-icon">📝</div>
                <p>${message || '暂无剪贴板内容'}</p>
                <p class="empty-hint">点击"添加"按钮添加常用文本</p>
            </div>
        `);
    };

    this.addClipboardItem = function(text) {
        var self = this;

        // 先获取当前运行的项目
        $.ajax({
            url: '/api/projects/status',
            type: 'GET',
            success: function(statusData) {
                if (!statusData.running_project) {
                    alert('没有运行的项目，请先启动一个项目');
                    return;
                }

                // 获取项目配置
                $.ajax({
                    url: '/api/projects/list',
                    type: 'GET',
                    success: function(data) {
                        var project = data.projects.find(p => p.Project === statusData.running_project.Project);
                        if (project) {
                            var clipboardList = project.clipboard_text || [];
                            clipboardList.push(text);

                            // 更新项目配置
                            $.ajax({
                                url: '/api/projects/update',
                                type: 'POST',
                                contentType: 'application/json',
                                data: JSON.stringify({
                                    Project: project.Project,
                                    clipboard_text: clipboardList
                                }),
                                success: function(result) {
                                    if (result.success) {
                                        self.loadClipboard();
                                        self.toggleForm(false);
                                    } else {
                                        alert('添加失败: ' + result.message);
                                    }
                                },
                                error: function() {
                                    alert('添加失败');
                                }
                            });
                        }
                    }
                });
            },
            error: function() {
                alert('获取项目状态失败');
            }
        });
    };

    this.deleteClipboardItem = function(index) {
        var self = this;

        if (!confirm('确定要删除这条剪贴板内容吗？')) {
            return;
        }

        $.ajax({
            url: '/api/projects/status',
            type: 'GET',
            success: function(statusData) {
                if (!statusData.running_project) {
                    alert('没有运行的项目');
                    return;
                }

                $.ajax({
                    url: '/api/projects/list',
                    type: 'GET',
                    success: function(data) {
                        var project = data.projects.find(p => p.Project === statusData.running_project.Project);
                        if (project && project.clipboard_text) {
                            var clipboardList = project.clipboard_text.filter(function(_, i) {
                                return i !== index;
                            });

                            $.ajax({
                                url: '/api/projects/update',
                                type: 'POST',
                                contentType: 'application/json',
                                data: JSON.stringify({
                                    Project: project.Project,
                                    clipboard_text: clipboardList
                                }),
                                success: function(result) {
                                    if (result.success) {
                                        self.loadClipboard();
                                    } else {
                                        alert('删除失败: ' + result.message);
                                    }
                                }
                            });
                        }
                    }
                });
            }
        });
    };

    this.copyToClipboard = function(text) {
        // 使用现代 Clipboard API
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(text).then(function() {
                this.showToast('复制成功！');
            }.bind(this)).catch(function() {
                this.fallbackCopy(text);
            }.bind(this));
        } else {
            this.fallbackCopy(text);
        }
    };

    this.fallbackCopy = function(text) {
        // 兼容旧浏览器的复制方法
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
        var toast = $('<div class="clipboard-toast">' + message + '</div>');
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

    this.toggleForm = function(show) {
        var form = $('#clipboardForm');
        if (show) {
            form.slideDown(200);
            $('#clipboardInput').focus();
        } else {
            form.slideUp(200);
            $('#clipboardInput').val('');
        }
    };

    this.escapeHtml = function(text) {
        var div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    };

    this.bindEvents = function() {
        var self = this;

        // 显示添加表单
        $('#addClipboard').on('click', function() {
            self.toggleForm(true);
        });

        // 隐藏添加表单
        $('#cancelAdd').on('click', function() {
            self.toggleForm(false);
        });

        // 确认添加
        $('#confirmAdd').on('click', function() {
            var text = $('#clipboardInput').val().trim();
            if (!text) {
                alert('请输入内容');
                return;
            }
            self.addClipboardItem(text);
        });

        // 回车键添加
        $('#clipboardInput').on('keydown', function(e) {
            if (e.ctrlKey && e.key === 'Enter') {
                $('#confirmAdd').click();
            }
        });

        // 刷新列表
        $('#refreshClipboard').on('click', function() {
            self.loadClipboard();
            self.showToast('已刷新');
        });

        // 复制按钮
        $(document).on('click', '.btn-copy', function() {
            var item = $(this).closest('.clipboard-item');
            var index = item.data('index');
            
            // 获取当前项目的剪贴板列表
            $.ajax({
                url: '/api/projects/status',
                type: 'GET',
                success: function(statusData) {
                    if (statusData.running_project) {
                        $.ajax({
                            url: '/api/projects/list',
                            type: 'GET',
                            success: function(data) {
                                var project = data.projects.find(p => p.Project === statusData.running_project.Project);
                                if (project && project.clipboard_text && project.clipboard_text[index]) {
                                    self.copyToClipboard(project.clipboard_text[index]);
                                }
                            }
                        });
                    }
                }
            });
        });

        // 删除按钮
        $(document).on('click', '.btn-delete', function() {
            var index = $(this).closest('.clipboard-item').data('index');
            self.deleteClipboardItem(index);
        });
    };
}
