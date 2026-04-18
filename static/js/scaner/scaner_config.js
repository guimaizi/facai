/**
 * 漏洞扫描设置
 * DNSLog 设置 + 常用剪贴板
 */

function ScanerConfigModule() {
    this.currentProject = null;
    this.clipboardText = [];

    this.render = function(data, container) {
        var self = this;
        
        var html = `
<div class="scaner-config-container">
    <div class="scaner-config-page-header">
        <h3>⚙️ 漏洞扫描设置</h3>
    </div>

    <div class="scaner-config-grid">
        <!-- 已扫描接口统计 -->
        <div class="scaner-config-section">
            <div class="scaner-config-card">
                <div class="scaner-config-card-header">
                    <strong>📊 已扫描接口统计</strong>
                </div>
                <div class="scaner-config-card-body">
                    <div class="scaner-config-stats-row">
                        <div class="scaner-config-stat-item">
                            <div class="scaner-config-stat-label">已扫描接口数</div>
                            <div class="scaner-config-stat-value" id="scannedInterfaceCount">0</div>
                        </div>
                    </div>
                    <div class="scaner-config-form-actions">
                        <button class="scaner-config-btn scaner-config-btn-danger scaner-config-btn-sm" id="clearScannedData">
                            <span class="scaner-config-btn-icon">🗑️</span>
                            <span>清空已扫描数据</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- DNSLog设置 -->
        <div class="scaner-config-section">
            <div class="scaner-config-card">
                <div class="scaner-config-card-header">
                    <strong>🌐 DNSLog 设置</strong>
                </div>
                <div class="scaner-config-card-body">
                    <div class="scaner-config-form-group">
                        <label>DNSLog Domain <small>(用于RCE检测)</small></label>
                        <input type="text" class="scaner-config-form-control" id="dnslogDomain" placeholder="例如: {hash}.www.dnslog.com">
                        <small class="scaner-config-form-text">用于命令执行检测，系统会自动替换 {hash} 为随机标识</small>
                    </div>
                    <div class="scaner-config-form-group">
                        <label>DNSLog URL <small>(用于SSRF检测)</small></label>
                        <input type="text" class="scaner-config-form-control" id="dnslogUrl" placeholder="例如: http://www.dnslog.com/{hash}">
                        <small class="scaner-config-form-text">用于SSRF检测，系统会自动替换 {hash} 为随机标识</small>
                    </div>
                    <div class="scaner-config-form-actions">
                        <button class="scaner-config-btn scaner-config-btn-success scaner-config-btn-sm" id="saveDnslog">
                            <span class="scaner-config-btn-icon">💾</span>
                            <span>保存 DNSLog 设置</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- 常用剪贴板 -->
        <div class="scaner-config-section">
            <div class="scaner-config-card">
                <div class="scaner-config-card-header">
                    <strong>📋 常用剪贴板</strong>
                    <div class="scaner-config-clipboard-actions">
                        <button class="scaner-config-btn scaner-config-btn-primary scaner-config-btn-sm" id="addClipboard">
                            <span class="scaner-config-btn-icon">+</span>
                            <span>添加</span>
                        </button>
                        <button class="scaner-config-btn scaner-config-btn-success scaner-config-btn-sm" id="refreshClipboard">
                            <span class="scaner-config-btn-icon">↻</span>
                            <span>刷新</span>
                        </button>
                    </div>
                </div>
                <div class="scaner-config-card-body">
                    <!-- 添加文本区域 -->
                    <div class="scaner-config-clipboard-form" id="clipboardForm" style="display:none;">
                        <div class="scaner-config-form-group">
                            <label>添加常用文本</label>
                            <textarea id="clipboardInput" class="scaner-config-form-control" rows="3" placeholder="输入要添加的文本..."></textarea>
                        </div>
                        <div class="scaner-config-form-actions">
                            <button class="scaner-config-btn scaner-config-btn-secondary scaner-config-btn-sm" id="cancelAdd">取消</button>
                            <button class="scaner-config-btn scaner-config-btn-primary scaner-config-btn-sm" id="confirmAdd">确认添加</button>
                        </div>
                    </div>

                    <!-- 剪贴板列表 -->
                    <div class="scaner-config-clipboard-list" id="clipboardList">
                        <div class="scaner-config-empty-state">
                            <div class="scaner-config-empty-icon">📝</div>
                            <p>暂无剪贴板内容</p>
                            <p class="scaner-config-empty-hint">点击"添加"按钮添加常用文本</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
        `;

        container.html(html);
        this.loadProjectData();
        this.loadScannedStats();
        this.bindEvents();
    };

    // 加载项目数据
    this.loadProjectData = function() {
        var self = this;

        // 获取当前运行的项目
        $.ajax({
            url: '/api/projects/status',
            type: 'GET',
            success: function(statusData) {
                if (statusData.running_project) {
                    self.currentProject = statusData.running_project.Project;
                    self.loadProjectConfig();
                } else {
                    self.showToast('无运行项目，请先启动一个项目');
                }
            },
            error: function() {
                self.showToast('加载项目状态失败');
            }
        });
    };

    // 加载项目配置
    this.loadProjectConfig = function() {
        var self = this;

        $.ajax({
            url: '/api/projects/list',
            type: 'GET',
            success: function(data) {
                var project = data.projects.find(p => p.Project === self.currentProject);
                if (project) {
                    // 加载 DNSLog Domain
                    if (project.dnslog_domain) {
                        $('#dnslogDomain').val(project.dnslog_domain);
                    }
                    
                    // 加载 DNSLog URL
                    if (project.dnslog_url) {
                        $('#dnslogUrl').val(project.dnslog_url);
                    }
                    
                    // 加载剪贴板文本
                    if (project.clipboard_text && project.clipboard_text.length > 0) {
                        self.clipboardText = project.clipboard_text;
                        self.renderClipboardList();
                    } else {
                        self.showEmptyState();
                    }
                }
            },
            error: function() {
                self.showToast('加载项目配置失败');
            }
        });
    };

    // 加载已扫描接口统计
    this.loadScannedStats = function() {
        var self = this;

        $.ajax({
            url: '/api/scaner/stats',
            type: 'GET',
            success: function(response) {
                if (response.success) {
                    $('#scannedInterfaceCount').text(response.data.scanned_count || 0);
                }
            },
            error: function() {
                $('#scannedInterfaceCount').text('0');
            }
        });
    };

    // 清空已扫描数据
    this.clearScannedData = function() {
        var self = this;

        if (!confirm('确定要清空所有已扫描接口数据吗？清空后将无法恢复！')) {
            return;
        }

        $.ajax({
            url: '/api/scaner/params/clear',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({}),
            success: function(response) {
                if (response.success) {
                    self.showToast('已清空 ' + response.data.count + ' 条数据');
                    self.loadScannedStats();
                } else {
                    self.showToast('清空失败: ' + response.message);
                }
            },
            error: function() {
                self.showToast('清空失败');
            }
        });
    };

    // 渲染剪贴板列表
    this.renderClipboardList = function() {
        var self = this;
        var listContainer = $('#clipboardList');
        listContainer.empty();

        if (!this.clipboardText || this.clipboardText.length === 0) {
            this.showEmptyState();
            return;
        }

        this.clipboardText.forEach(function(text, index) {
            var itemHtml = `
                <div class="scaner-config-clipboard-item" data-index="${index}">
                    <div class="scaner-config-item-content">
                        <div class="scaner-config-item-text">${self.escapeHtml(text)}</div>
                    </div>
                    <div class="scaner-config-item-actions">
                        <button class="scaner-config-btn scaner-config-btn-success scaner-config-btn-sm scaner-config-btn-copy" title="复制到剪贴板">
                            <span class="scaner-config-btn-icon">📋</span>
                            <span>复制</span>
                        </button>
                        <button class="scaner-config-btn scaner-config-btn-danger scaner-config-btn-sm scaner-config-btn-delete" title="删除">
                            <span class="scaner-config-btn-icon">🗑️</span>
                        </button>
                    </div>
                </div>
            `;
            listContainer.append(itemHtml);
        });
    };

    // 显示空状态
    this.showEmptyState = function(message) {
        var listContainer = $('#clipboardList');
        listContainer.html(`
            <div class="scaner-config-empty-state">
                <div class="scaner-config-empty-icon">📝</div>
                <p>${message || '暂无剪贴板内容'}</p>
                <p class="scaner-config-empty-hint">点击"添加"按钮添加常用文本</p>
            </div>
        `);
    };

    // 保存 DNSLog 设置
    this.saveDnslog = function() {
        var self = this;
        var dnslogDomain = $('#dnslogDomain').val().trim();
        var dnslogUrl = $('#dnslogUrl').val().trim();

        if (!this.currentProject) {
            this.showToast('无运行项目');
            return;
        }

        $.ajax({
            url: '/api/projects/update',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                Project: this.currentProject,
                dnslog_domain: dnslogDomain,
                dnslog_url: dnslogUrl
            }),
            success: function(result) {
                if (result.success) {
                    self.showToast('DNSLog 设置已保存');
                } else {
                    self.showToast('保存失败: ' + result.message);
                }
            },
            error: function() {
                self.showToast('保存失败');
            }
        });
    };

    // 添加剪贴板项
    this.addClipboardItem = function(text) {
        var self = this;

        if (!this.currentProject) {
            this.showToast('无运行项目');
            return;
        }

        this.clipboardText.push(text);

        $.ajax({
            url: '/api/projects/update',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                Project: this.currentProject,
                clipboard_text: this.clipboardText
            }),
            success: function(result) {
                if (result.success) {
                    self.renderClipboardList();
                    self.toggleForm(false);
                    self.showToast('添加成功');
                } else {
                    self.showToast('添加失败: ' + result.message);
                }
            },
            error: function() {
                self.showToast('添加失败');
            }
        });
    };

    // 删除剪贴板项
    this.deleteClipboardItem = function(index) {
        var self = this;

        if (!confirm('确定要删除这条剪贴板内容吗？')) {
            return;
        }

        this.clipboardText.splice(index, 1);

        $.ajax({
            url: '/api/projects/update',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                Project: this.currentProject,
                clipboard_text: this.clipboardText
            }),
            success: function(result) {
                if (result.success) {
                    self.renderClipboardList();
                    self.showToast('删除成功');
                } else {
                    self.showToast('删除失败: ' + result.message);
                }
            },
            error: function() {
                self.showToast('删除失败');
            }
        });
    };

    // 复制到剪贴板
    this.copyToClipboard = function(text) {
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

    // 兼容旧浏览器的复制方法
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

    // 显示/隐藏表单
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

    // 显示 Toast 提示
    this.showToast = function(message) {
        var toast = $('<div class="scaner-config-toast">' + message + '</div>');
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

    // HTML 转义
    this.escapeHtml = function(text) {
        var div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    };

    // 绑定事件
    this.bindEvents = function() {
        var self = this;

        // 保存 DNSLog 设置
        $('#saveDnslog').off('click').on('click', function() {
            self.saveDnslog();
        });

        // 清空已扫描数据
        $('#clearScannedData').off('click').on('click', function() {
            self.clearScannedData();
        });

        // 显示添加表单
        $('#addClipboard').off('click').on('click', function() {
            self.toggleForm(true);
        });

        // 隐藏添加表单
        $('#cancelAdd').off('click').on('click', function() {
            self.toggleForm(false);
        });

        // 确认添加
        $('#confirmAdd').off('click').on('click', function() {
            var text = $('#clipboardInput').val().trim();
            if (!text) {
                self.showToast('请输入内容');
                return;
            }
            self.addClipboardItem(text);
        });

        // 回车键添加
        $('#clipboardInput').off('keydown').on('keydown', function(e) {
            if (e.ctrlKey && e.key === 'Enter') {
                $('#confirmAdd').click();
            }
        });

        // 刷新列表
        $('#refreshClipboard').off('click').on('click', function() {
            self.loadProjectData();
            self.showToast('已刷新');
        });

        // 复制按钮
        $(document).off('click', '.scaner-config-btn-copy').on('click', '.scaner-config-btn-copy', function() {
            var index = $(this).closest('.scaner-config-clipboard-item').data('index');
            if (self.clipboardText[index]) {
                self.copyToClipboard(self.clipboardText[index]);
            }
        });

        // 删除按钮
        $(document).off('click', '.scaner-config-btn-delete').on('click', '.scaner-config-btn-delete', function() {
            var index = $(this).closest('.scaner-config-clipboard-item').data('index');
            self.deleteClipboardItem(index);
        });
    };
}

console.log('[Scaner] ScanerConfigModule loaded');
