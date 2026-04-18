// 服务管理模块
(function() {
    'use strict';

    var ServicesModule = function() {};

    // 渲染服务管理界面
    ServicesModule.prototype.render = function(data, container) {
        container.html(`
            <div class="card">
                <div class="card-header">
                    服务状态
                    <button class="btn btn-sm btn-primary pull-right" id="refreshAllStatus">刷新状态</button>
                </div>

                <div class="services-container">
                    <!-- 爬虫服务 -->
                    <div class="service-section">
                        <div class="section-header">
                            <h3>🕷️ 爬虫服务</h3>
                        </div>
                        <div class="service-info">
                            <span class="info-label">状态:</span>
                            <span id="spiderServiceStatus" class="status-badge status-stopped">已停止</span>
                        </div>
                        <div class="service-info">
                            <span class="info-label">说明:</span>
                            <span class="info-value">自动爬取网站，解析HTML，提取链接和资源</span>
                        </div>
                        <div class="service-actions">
                            <button class="btn btn-success btn-sm" id="startSpiderService">开启</button>
                            <button class="btn btn-danger btn-sm" id="stopSpiderService">关闭</button>
                        </div>
                    </div>

                    <!-- 资产监控服务 -->
                    <div class="service-section">
                        <div class="section-header">
                            <h3>📊 资产监控服务</h3>
                        </div>
                        <div class="service-info">
                            <span class="info-label">状态:</span>
                            <span id="monitorServiceStatus" class="status-badge status-stopped">已停止</span>
                        </div>
                        <div class="service-info">
                            <span class="info-label">说明:</span>
                            <span class="info-value">监控网站资产变化，检测HTML更新，动态爬取变化页面</span>
                        </div>
                        <div class="service-actions">
                            <button class="btn btn-success btn-sm" id="startMonitorService">开启</button>
                            <button class="btn btn-danger btn-sm" id="stopMonitorService">关闭</button>
                        </div>
                    </div>

                    <!-- 漏洞扫描服务 -->
                    <div class="service-section">
                        <div class="section-header">
                            <h3>🔓 漏洞扫描服务</h3>
                        </div>
                        <div class="service-info">
                            <span class="info-label">状态:</span>
                            <span id="scannerServiceStatus" class="status-badge status-stopped">已停止</span>
                        </div>
                        <div class="service-info">
                            <span class="info-label">说明:</span>
                            <span class="info-value">自动扫描流量中的安全漏洞，检测SQL注入、XSS等漏洞</span>
                        </div>
                        <div class="service-actions">
                            <button class="btn btn-success btn-sm" id="startScannerService">开启</button>
                            <button class="btn btn-danger btn-sm" id="stopScannerService">关闭</button>
                        </div>
                    </div>

                    <!-- Mitmproxy 流量捕捉状态 -->
                    <div class="service-section">
                        <div class="section-header">
                            <h3>🔍 Mitmproxy 流量捕捉</h3>
                        </div>
                        <div class="service-info">
                            <span class="info-label">端口:</span>
                            <span id="mitmproxyPort" class="info-value">-</span>
                        </div>
                        <div class="service-info">
                            <span class="info-label">状态:</span>
                            <span id="mitmproxyStatus" class="status-badge">-</span>
                        </div>
                    </div>

                    <!-- Chrome CDP 状态 -->
                    <div class="service-section">
                        <div class="section-header">
                            <h3>🌐 Chrome CDP</h3>
                        </div>
                        <div class="service-info">
                            <span class="info-label">Headless:</span>
                            <span id="chromeHeadlessPort" class="info-value">-</span>
                            <span id="chromeHeadlessStatus" class="status-badge">-</span>
                        </div>
                        <div class="service-info">
                            <span class="info-label">Normal:</span>
                            <span id="chromeNormalPort" class="info-value">-</span>
                            <span id="chromeNormalStatus" class="status-badge">-</span>
                        </div>
                    </div>
                </div>
            </div>
        `);

        this.loadServiceStatus();
        this.bindEvents();
    };

    // 加载服务状态
    ServicesModule.prototype.loadServiceStatus = function() {
        var self = this;

        ServicesAPI.status(function(response) {
            console.log('Service status response:', response);  // 调试日志
            
            if (response.success) {
                var data = response.data;
                console.log('Service data:', data);  // 调试日志

                // 主动服务状态
                console.log('Updating spider_service:', data.spider_service);
                console.log('Updating monitor_service:', data.monitor_service);
                console.log('Updating scaner_service:', data.scaner_service);
                
                self.updateServiceStatus('spiderServiceStatus', data.spider_service);
                self.updateServiceStatus('monitorServiceStatus', data.monitor_service);
                self.updateServiceStatus('scannerServiceStatus', data.scaner_service);

                // Mitmproxy
                $('#mitmproxyPort').text(data.mitmproxy_port || '-');
                self.updateStatusBadge('mitmproxyStatus', data.mitmproxy);

                // Chrome Headless
                $('#chromeHeadlessPort').text(data.chrome_headless_port ? '端口 ' + data.chrome_headless_port : '-');
                self.updateStatusBadge('chromeHeadlessStatus', data.chrome_headless);

                // Chrome Normal
                $('#chromeNormalPort').text(data.chrome_normal_port ? '端口 ' + data.chrome_normal_port : '-');
                self.updateStatusBadge('chromeNormalStatus', data.chrome_normal);
            }
        });
    };

    // 更新主动服务状态
    ServicesModule.prototype.updateServiceStatus = function(elementId, status) {
        var $element = $('#' + elementId);
        var isRunning = status == 1 || status === true;
        
        if (isRunning) {
            $element.removeClass('status-stopped').addClass('status-running').text('运行中');
        } else {
            $element.removeClass('status-running').addClass('status-stopped').text('已停止');
        }
    };

    // 更新状态徽章
    ServicesModule.prototype.updateStatusBadge = function(elementId, isRunning) {
        var $element = $('#' + elementId);
        if (isRunning) {
            $element.removeClass('status-stopped').addClass('status-running').text('运行中');
        } else {
            $element.removeClass('status-running').addClass('status-stopped').text('已停止');
        }
    };

    // 绑定事件
    ServicesModule.prototype.bindEvents = function() {
        var self = this;

        // ========== 主动服务管理 ==========
        
        // 爬虫服务
        $('#startSpiderService').on('click', function() {
            ServicesAPI.startSpider(function(response) {
                if (response.success) {
                    alert('爬虫服务已启动！');
                    self.loadServiceStatus();
                } else {
                    alert('启动失败：' + response.message);
                }
            });
        });

        $('#stopSpiderService').on('click', function() {
            ServicesAPI.stopSpider(function(response) {
                if (response.success) {
                    alert('爬虫服务已关闭！');
                    self.loadServiceStatus();
                } else {
                    alert('关闭失败：' + response.message);
                }
            });
        });

        // 资产监控服务
        $('#startMonitorService').on('click', function() {
            ServicesAPI.startMonitor(function(response) {
                if (response.success) {
                    alert('资产监控服务已启动！');
                    self.loadServiceStatus();
                } else {
                    alert('启动失败：' + response.message);
                }
            });
        });

        $('#stopMonitorService').on('click', function() {
            ServicesAPI.stopMonitor(function(response) {
                if (response.success) {
                    alert('资产监控服务已关闭！');
                    self.loadServiceStatus();
                } else {
                    alert('关闭失败：' + response.message);
                }
            });
        });

        // 漏洞扫描服务
        $('#startScannerService').on('click', function() {
            ServicesAPI.startScanner(function(response) {
                if (response.success) {
                    alert('漏洞扫描服务已启动！');
                    self.loadServiceStatus();
                } else {
                    alert('启动失败：' + response.message);
                }
            });
        });

        $('#stopScannerService').on('click', function() {
            ServicesAPI.stopScanner(function(response) {
                if (response.success) {
                    alert('漏洞扫描服务已关闭！');
                    self.loadServiceStatus();
                } else {
                    alert('关闭失败：' + response.message);
                }
            });
        });

        // ========== 其他 ==========
        
        // 刷新所有状态
        $('#refreshAllStatus').on('click', function() {
            self.loadServiceStatus();
        });
    };

    // 导出到全局
    window.ServicesModule = ServicesModule;
})();
