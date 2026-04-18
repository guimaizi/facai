// 资产管理配置模块
(function() {
    'use strict';

    var AssetsConfigModule = function() {};

    // 渲染配置界面
    AssetsConfigModule.prototype.render = function(data, container) {
        container.html(`
            <div class="card">
                <div class="card-header">资产管理配置</div>

                <div class="config-grid">
                    <!-- 资产导入区域 -->
                    <div class="form-section">
                        <div class="section-header">
                            <h3>📥 资产导入</h3>
                        </div>
                        <div class="form-group">
                            <label>导入类型</label>
                            <div class="import-type-buttons">
                                <button class="btn btn-outline-primary import-type-btn active" data-type="subdomains">子域名导入</button>
                                <button class="btn btn-outline-primary import-type-btn" data-type="urls">URL导入</button>
                            </div>
                        </div>
                        <div class="form-group">
                            <label id="importLabel">子域名列表</label>
                            <textarea id="importContent" rows="8" placeholder="每行一个子域名或URL"></textarea>
                        </div>
                        <div class="form-group">
                            <label>上传TXT文件</label>
                            <input type="file" id="importFile" accept=".txt" class="form-file-input">
                        </div>
                        <div class="form-actions">
                            <button class="btn btn-primary" id="executeImport">执行导入</button>
                            <button class="btn btn-danger" id="clearImport">清空</button>
                        </div>
                        <div id="importResult" class="import-result"></div>
                    </div>
                    
                    <!-- 域名白名单 -->
                    <div class="form-section">
                        <div class="section-header">
                            <h3>📋 域名白名单</h3>
                            <button class="btn btn-primary btn-sm" id="refreshWhitelistDomain">刷新</button>
                        </div>
                        <div class="form-group">
                            <textarea id="whitelistDomain" rows="8" placeholder="每行一个域名，例如：&#10;example.com&#10;www.example.com"></textarea>
                        </div>
                        <div class="form-actions">
                            <button class="btn btn-success" id="saveWhitelistDomain">保存</button>
                        </div>
                    </div>

                    <!-- 域名黑名单 -->
                    <div class="form-section">
                        <div class="section-header">
                            <h3>🚫 域名黑名单</h3>
                            <button class="btn btn-primary btn-sm" id="refreshBlocklistDomain">刷新</button>
                        </div>
                        <div class="form-group">
                            <textarea id="blocklistDomain" rows="8" placeholder="每行一个域名，例如：&#10;bad.com&#10;spam.com"></textarea>
                        </div>
                        <div class="form-actions">
                            <button class="btn btn-success" id="saveBlocklistDomain">保存</button>
                        </div>
                    </div>

                    <!-- URL黑名单 -->
                    <div class="form-section">
                        <div class="section-header">
                            <h3>🔗 URL黑名单</h3>
                            <button class="btn btn-primary btn-sm" id="refreshBlocklistUrl">刷新</button>
                        </div>
                        <div class="form-group">
                            <textarea id="blocklistUrl" rows="8" placeholder="每行一个URL，例如：&#10;http://example.com/page1&#10;http://example.com/page2"></textarea>
                        </div>
                        <div class="form-actions">
                            <button class="btn btn-success" id="saveBlocklistUrl">保存</button>
                        </div>
                    </div>
                </div>
            </div>
        `);
        
        this.loadAllConfig();
        this.bindEvents();
    };

    // 加载所有配置
    AssetsConfigModule.prototype.loadAllConfig = function() {
        $.ajax({
            url: '/api/assets/config/all',
            method: 'GET',
            success: function(response) {
                if (response.success) {
                    $('#whitelistDomain').val(response.data.whitelist_domain.join('\n'));
                    $('#blocklistDomain').val(response.data.blocklist_domain.join('\n'));
                    $('#blocklistUrl').val(response.data.blocklist_url.join('\n'));
                }
            },
            error: function() {
                alert('加载配置失败');
            }
        });
    };

    // 绑定事件
    AssetsConfigModule.prototype.bindEvents = function() {
        var self = this;

        // 保存域名白名单
        $('#saveWhitelistDomain').on('click', function() {
            self.saveWhitelistDomain();
        });

        // 刷新域名白名单
        $('#refreshWhitelistDomain').on('click', function() {
            self.loadWhitelistDomain();
        });

        // 保存域名黑名单
        $('#saveBlocklistDomain').on('click', function() {
            self.saveBlocklistDomain();
        });

        // 刷新域名黑名单
        $('#refreshBlocklistDomain').on('click', function() {
            self.loadBlocklistDomain();
        });

        // 保存URL黑名单
        $('#saveBlocklistUrl').on('click', function() {
            self.saveBlocklistUrl();
        });

        // 刷新URL黑名单
        $('#refreshBlocklistUrl').on('click', function() {
            self.loadBlocklistUrl();
        });

        // 导入类型按钮切换
        $('.import-type-btn').on('click', function() {
            $('.import-type-btn').removeClass('active');
            $(this).addClass('active');
            var type = $(this).data('type');
            $('#importLabel').text(type === 'subdomains' ? '子域名列表' : 'URL列表');
        });

        // 文件上传处理
        $('#importFile').on('change', function(e) {
            var file = e.target.files[0];
            if (!file) return;

            var reader = new FileReader();
            reader.onload = function(e) {
                $('#importContent').val(e.target.result);
            };
            reader.readAsText(file);
        });

        // 执行导入
        $('#executeImport').on('click', function() {
            var type = $('.import-type-btn.active').data('type');
            var content = $('#importContent').val();
            
            var items = content.split('\n');
            
            if (type === 'subdomains') {
                self.importSubdomains(items);
            } else {
                self.importUrls(items);
            }
        });

        // 清空导入区域
        $('#clearImport').on('click', function() {
            $('#importContent').val('');
            $('#importFile').val('');
            $('#importResult').empty();
        });
    };

    // 保存域名白名单
    AssetsConfigModule.prototype.saveWhitelistDomain = function() {
        var domains = $('#whitelistDomain').val().split('\n');
        domains = domains.filter(function(d) { return d.trim(); });
        
        $.ajax({
            url: '/api/assets/config/whitelist/domain',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ domains: domains }),
            success: function(response) {
                if (response.success) {
                    alert('域名白名单保存成功！');
                } else {
                    alert('保存失败：' + response.message);
                }
            },
            error: function() {
                alert('保存失败，请重试');
            }
        });
    };

    // 加载域名白名单
    AssetsConfigModule.prototype.loadWhitelistDomain = function() {
        $.ajax({
            url: '/api/assets/config/whitelist/domain',
            method: 'GET',
            success: function(response) {
                if (response.success) {
                    $('#whitelistDomain').val(response.data.join('\n'));
                }
            },
            error: function() {
                alert('加载失败');
            }
        });
    };

    // 保存域名黑名单
    AssetsConfigModule.prototype.saveBlocklistDomain = function() {
        var domains = $('#blocklistDomain').val().split('\n');
        domains = domains.filter(function(d) { return d.trim(); });
        
        $.ajax({
            url: '/api/assets/config/blocklist/domain',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ domains: domains }),
            success: function(response) {
                if (response.success) {
                    alert('域名黑名单保存成功！');
                } else {
                    alert('保存失败：' + response.message);
                }
            },
            error: function() {
                alert('保存失败，请重试');
            }
        });
    };

    // 加载域名黑名单
    AssetsConfigModule.prototype.loadBlocklistDomain = function() {
        $.ajax({
            url: '/api/assets/config/blocklist/domain',
            method: 'GET',
            success: function(response) {
                if (response.success) {
                    $('#blocklistDomain').val(response.data.join('\n'));
                }
            },
            error: function() {
                alert('加载失败');
            }
        });
    };

    // 保存URL黑名单
    AssetsConfigModule.prototype.saveBlocklistUrl = function() {
        var urls = $('#blocklistUrl').val().split('\n');
        urls = urls.filter(function(u) { return u.trim(); });
        
        $.ajax({
            url: '/api/assets/config/blocklist/url',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ urls: urls }),
            success: function(response) {
                if (response.success) {
                    alert('URL黑名单保存成功！');
                } else {
                    alert('保存失败：' + response.message);
                }
            },
            error: function() {
                alert('保存失败，请重试');
            }
        });
    };

    // 加载URL黑名单
    AssetsConfigModule.prototype.loadBlocklistUrl = function() {
        $.ajax({
            url: '/api/assets/config/blocklist/url',
            method: 'GET',
            success: function(response) {
                if (response.success) {
                    $('#blocklistUrl').val(response.data.join('\n'));
                }
            },
            error: function() {
                alert('加载失败');
            }
        });
    };

    // 导入子域名
    AssetsConfigModule.prototype.importSubdomains = function(subdomains) {
        if (!subdomains || subdomains.length === 0) {
            alert('请输入子域名');
            return;
        }

        $('#importResult').html('<div class="loading">正在导入...</div>');

        // 去重处理：提取、去空、去重
        var uniqueSubdomains = [];
        var seen = new Set();
        subdomains.forEach(function(subdomain) {
            subdomain = subdomain.trim();
            if (subdomain && !seen.has(subdomain)) {
                seen.add(subdomain);
                uniqueSubdomains.push(subdomain);
            }
        });

        if (uniqueSubdomains.length === 0) {
            $('#importResult').html('<div class="error">没有有效的子域名</div>');
            return;
        }

        // 构建HTTP请求列表
        var requests = uniqueSubdomains.map(function(subdomain) {
            return {
                url: subdomain,
                source: 1  // url生成
            };
        });

        // 一次性导入所有请求
        $.ajax({
            url: '/api/import/request',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(requests),
            success: function(response) {
                if (response.success) {
                    $('#importResult').html(
                        '<div class="success">导入完成！<br>总计: ' + response.total + '，成功: ' + response.imported + '，跳过: ' + response.skipped + '</div>'
                    );
                } else {
                    $('#importResult').html('<div class="error">导入失败：' + response.message + '</div>');
                }
            },
            error: function() {
                $('#importResult').html('<div class="error">导入失败，请重试</div>');
            }
        });
    };

    // 导入URL
    AssetsConfigModule.prototype.importUrls = function(urls) {
        if (!urls || urls.length === 0) {
            alert('请输入URL');
            return;
        }

        $('#importResult').html('<div class="loading">正在导入...</div>');

        // 去重处理：提取、去空、去重
        var uniqueUrls = [];
        var seen = new Set();
        urls.forEach(function(url) {
            url = url.trim();
            if (url && !seen.has(url)) {
                seen.add(url);
                uniqueUrls.push(url);
            }
        });

        if (uniqueUrls.length === 0) {
            $('#importResult').html('<div class="error">没有有效的URL</div>');
            return;
        }

        // 构建HTTP请求列表
        var requests = uniqueUrls.map(function(url) {
            return {
                url: url,
                source: 1  // url生成
            };
        });

        // 一次性导入所有请求
        $.ajax({
            url: '/api/import/request',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(requests),
            success: function(response) {
                if (response.success) {
                    $('#importResult').html(
                        '<div class="success">导入完成！<br>总计: ' + response.total + '，成功: ' + response.imported + '，跳过: ' + response.skipped + '</div>'
                    );
                } else {
                    $('#importResult').html('<div class="error">导入失败：' + response.message + '</div>');
                }
            },
            error: function() {
                $('#importResult').html('<div class="error">导入失败，请重试</div>');
            }
        });
    };

    // 导出到全局
    window.AssetsConfigModule = AssetsConfigModule;
})();
