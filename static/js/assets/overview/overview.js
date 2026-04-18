function OverviewModule() {
    this.render = function(data, container) {
        this.container = container;

        container.html(`
            <div class="facai-overview-container">
                <div class="facai-overview-header">
                    <h3>资产总览</h3>
                    <button class="btn btn-primary btn-sm" id="refreshOverview">刷新</button>
                </div>
                
                <div class="facai-overview-stats">
                    <div class="facai-stat-card" data-type="subdomains">
                        <div class="facai-stat-icon facai-subdomain-icon">
                            <svg viewBox="0 0 24 24" width="32" height="32">
                                <path fill="currentColor" d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
                            </svg>
                        </div>
                        <div class="facai-stat-info">
                            <div class="facai-stat-number" id="subdomainsCount">-</div>
                            <div class="facai-stat-label">子域名</div>
                        </div>
                    </div>
                    
                    <div class="facai-stat-card" data-type="websites">
                        <div class="facai-stat-icon facai-website-icon">
                            <svg viewBox="0 0 24 24" width="32" height="32">
                                <path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
                            </svg>
                        </div>
                        <div class="facai-stat-info">
                            <div class="facai-stat-number" id="websitesCount">-</div>
                            <div class="facai-stat-label">网站</div>
                        </div>
                    </div>
                    
                    <div class="facai-stat-card" data-type="http">
                        <div class="facai-stat-icon facai-http-icon">
                            <svg viewBox="0 0 24 24" width="32" height="32">
                                <path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/>
                            </svg>
                        </div>
                        <div class="facai-stat-info">
                            <div class="facai-stat-number" id="httpCount">-</div>
                            <div class="facai-stat-label">HTTP请求</div>
                        </div>
                    </div>
                    
                    <div class="facai-stat-card" data-type="html">
                        <div class="facai-stat-icon facai-html-icon">
                            <svg viewBox="0 0 24 24" width="32" height="32">
                                <path fill="currentColor" d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z"/>
                            </svg>
                        </div>
                        <div class="facai-stat-info">
                            <div class="facai-stat-number" id="htmlCount">-</div>
                            <div class="facai-stat-label">HTML文件</div>
                        </div>
                    </div>
                    
                    <div class="facai-stat-card" data-type="highlights">
                        <div class="facai-stat-icon facai-highlight-icon">
                            <svg viewBox="0 0 24 24" width="32" height="32">
                                <path fill="currentColor" d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z"/>
                            </svg>
                        </div>
                        <div class="facai-stat-info">
                            <div class="facai-stat-number" id="highlightsCount">-</div>
                            <div class="facai-stat-label">重点资产</div>
                        </div>
                    </div>
                    
                    <div class="facai-stat-card" data-type="ip_cidr">
                        <div class="facai-stat-icon facai-ip-icon">
                            <svg viewBox="0 0 24 24" width="32" height="32">
                                <path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                            </svg>
                        </div>
                        <div class="facai-stat-info">
                            <div class="facai-stat-number" id="ipCidrCount">-</div>
                            <div class="facai-stat-label">IP C段</div>
                        </div>
                    </div>
                    
                    <div class="facai-stat-card" data-type="ip">
                        <div class="facai-stat-icon facai-ip-single-icon">
                            <svg viewBox="0 0 24 24" width="32" height="32">
                                <path fill="currentColor" d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/>
                            </svg>
                        </div>
                        <div class="facai-stat-info">
                            <div class="facai-stat-number" id="ipCount">-</div>
                            <div class="facai-stat-label">IP资产</div>
                        </div>
                    </div>
                </div>
                
                <div class="facai-overview-charts">
                    <div class="facai-chart-card">
                        <div class="facai-chart-title">重点资产类型分布</div>
                        <div id="highlightTypeChart" class="facai-chart-content"></div>
                    </div>
                    <div class="facai-chart-card">
                        <div class="facai-chart-title">资产数据趋势</div>
                        <div id="trendChart" class="facai-chart-content">
                            <div class="facai-trend-placeholder">暂无趋势数据</div>
                        </div>
                    </div>
                </div>
                
                <div class="facai-overview-recent">
                    <div class="facai-recent-card">
                        <div class="facai-recent-title">最近添加的资产</div>
                        <div id="recentAssets" class="facai-recent-content"></div>
                    </div>
                </div>
            </div>
        `);

        this.loadOverview();
        this.bindEvents();
    };

    this.loadOverview = function() {
        var self = this;
        
        // 加载总览数据
        $.ajax({
            url: '/api/assets/overview',
            type: 'GET',
            success: function(data) {
                if (data.success) {
                    var overview = data.overview;
                    
                    // 更新数字，带动画效果
                    self.animateNumber('#subdomainsCount', overview.subdomains || 0);
                    self.animateNumber('#websitesCount', overview.websites || 0);
                    self.animateNumber('#httpCount', overview.http || 0);
                    self.animateNumber('#htmlCount', overview.html || 0);
                    self.animateNumber('#highlightsCount', overview.highlights || 0);
                    self.animateNumber('#ipCidrCount', overview.ip_cidr || 0);
                    self.animateNumber('#ipCount', overview.ip || 0);
                }
            }
        });

        // 加载详细统计数据
        $.ajax({
            url: '/api/assets/overview/detail',
            type: 'GET',
            success: function(data) {
                if (data.success) {
                    self.renderHighlightTypeChart(data.detail.highlight_type);
                }
            }
        });

        // 加载最近的资产
        this.loadRecentAssets();
    };

    this.animateNumber = function(selector, target) {
        var $elem = $(selector);
        var current = 0;
        var duration = 500;
        var step = Math.ceil(target / (duration / 16));
        
        var timer = setInterval(function() {
            current += step;
            if (current >= target) {
                current = target;
                clearInterval(timer);
            }
            $elem.text(current.toLocaleString());
        }, 16);
    };

    this.renderHighlightTypeChart = function(data) {
        var chartContainer = $('#highlightTypeChart');
        chartContainer.empty();

        if (!data || Object.keys(data).length === 0) {
            chartContainer.html('<div class="facai-chart-placeholder">暂无数据</div>');
            return;
        }

        var total = Object.values(data).reduce(function(a, b) { return a + b; }, 0);
        var colors = ['#667eea', '#10b981', '#f59e0b', '#ef4444', '#06b6d4', '#8b5cf6'];
        var typeNames = {
            'web': 'Web',
            'win_client': 'Win客户端',
            'mac_client': 'Mac客户端',
            'android_client': 'Android',
            'ios_client': 'iOS',
            'mini_client': '小程序'
        };

        var html = '<div class="facai-chart-bars">';
        var i = 0;
        for (var type in data) {
            var count = data[type];
            var percent = total > 0 ? (count / total * 100).toFixed(1) : 0;
            var color = colors[i % colors.length];
            var name = typeNames[type] || type;

            html += `
                <div class="facai-chart-bar-item">
                    <div class="facai-bar-label">${name}</div>
                    <div class="facai-bar-container">
                        <div class="facai-bar-fill" style="width: ${percent}%; background: ${color};"></div>
                    </div>
                    <div class="facai-bar-value">${count} (${percent}%)</div>
                </div>
            `;
            i++;
        }
        html += '</div>';

        chartContainer.html(html);
    };

    this.loadRecentAssets = function() {
        var self = this;
        var recentContainer = $('#recentAssets');
        
        // 并行请求获取各类型最新数据
        $.when(
            $.ajax({ url: '/api/assets/highlights', data: { page: 1, page_size: 3 } }),
            $.ajax({ url: '/api/assets/websites', data: { page: 1, page_size: 3 } }),
            $.ajax({ url: '/api/assets/http', data: { page: 1, page_size: 3 } })
        ).done(function(highlightsRes, websitesRes, httpRes) {
            var html = '<div class="facai-recent-list">';
            
            // 处理重点资产
            if (highlightsRes[0].data && highlightsRes[0].data.length > 0) {
                html += '<div class="facai-recent-section"><div class="facai-recent-section-title">重点资产</div>';
                highlightsRes[0].data.forEach(function(item) {
                    html += `
                        <div class="facai-recent-item" data-type="highlights">
                            <span class="facai-recent-badge highlight">重点</span>
                            <span class="facai-recent-url">${self.truncate(item.url || '', 50)}</span>
                            <span class="facai-recent-time">${item.time || ''}</span>
                        </div>
                    `;
                });
                html += '</div>';
            }

            // 处理网站
            if (websitesRes[0].websites && websitesRes[0].websites.length > 0) {
                html += '<div class="facai-recent-section"><div class="facai-recent-section-title">网站</div>';
                websitesRes[0].websites.forEach(function(item) {
                    html += `
                        <div class="facai-recent-item" data-type="websites">
                            <span class="facai-recent-badge website">网站</span>
                            <span class="facai-recent-url">${self.truncate(item.url || '', 50)}</span>
                            <span class="facai-recent-time">${item.time_update || ''}</span>
                        </div>
                    `;
                });
                html += '</div>';
            }

            // 处理HTTP
            if (httpRes[0].https && httpRes[0].https.length > 0) {
                html += '<div class="facai-recent-section"><div class="facai-recent-section-title">HTTP请求</div>';
                httpRes[0].https.forEach(function(item) {
                    html += `
                        <div class="facai-recent-item" data-type="http">
                            <span class="facai-recent-badge http">HTTP</span>
                            <span class="facai-recent-url">${self.truncate(item.url || '', 50)}</span>
                            <span class="facai-recent-time">${item.time_first || ''}</span>
                        </div>
                    `;
                });
                html += '</div>';
            }

            html += '</div>';
            recentContainer.html(html);
        }).fail(function() {
            recentContainer.html('<div class="facai-chart-placeholder">加载失败</div>');
        });
    };

    this.truncate = function(str, len) {
        if (!str) return '';
        return str.length > len ? str.substring(0, len) + '...' : str;
    };

    this.bindEvents = function() {
        var self = this;

        // 刷新按钮
        $('#refreshOverview').on('click', function() {
            self.loadOverview();
        });

        // 点击统计卡片跳转
        $('.facai-stat-card').on('click', function() {
            var type = $(this).data('type');
            var moduleMap = {
                'subdomains': 'assets/subdomains',
                'websites': 'assets/websites',
                'http': 'assets/http',
                'html': 'assets/html',
                'highlights': 'assets/highlights',
                'ip_cidr': 'assets/ip-cidr',
                'ip': 'assets/ip'
            };
            if (moduleMap[type]) {
                TabManager.openTab('assets', moduleMap[type].split('/')[1], {
                    subModule: moduleMap[type].split('/')[1]
                });
            }
        });

        // 点击最近资产跳转
        this.container.on('click', '.facai-recent-item', function() {
            var type = $(this).data('type');
            var moduleMap = {
                'highlights': 'highlights',
                'websites': 'websites',
                'http': 'http'
            };
            if (moduleMap[type]) {
                TabManager.openTab('assets', moduleMap[type], {
                    subModule: moduleMap[type]
                });
            }
        });
    };
}
