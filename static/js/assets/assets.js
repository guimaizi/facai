function AssetsModule() {
    this.render = function(data, container) {
        var subModule = data.subModule || 'overview';
        
        switch(subModule) {
            case 'overview':
                this.renderOverview(container);
                break;
            case 'config':
                var configModule = new AssetsConfigModule();
                configModule.render(data, container);
                break;
            case 'subdomains':
                this.renderSubdomains(container);
                break;
            case 'websites':
                this.renderWebsites(container);
                break;
            case 'http':
                this.renderHttp(container);
                break;
            case 'html':
                this.renderHtml(container);
                break;
            case 'ip-cidr':
                this.renderIpCidr(container);
                break;
            case 'ip':
                this.renderIp(container);
                break;
            case 'highlights':
                this.renderHighlights(container);
                break;
            default:
                this.renderOverview(container);
        }
    };

    this.renderOverview = function(container) {
        var overviewModule = new OverviewModule();
        overviewModule.render({}, container);
    };

    this.renderConfig = function(container) {
        var configModule = new AssetsConfigModule();
        configModule.render(container);
    };

    this.renderSubdomains = function(container) {
        var subdomainsModule = new SubdomainsModule();
        subdomainsModule.render({}, container);
    };

    this.renderWebsites = function(container) {
        var websitesModule = new WebsitesModule();
        websitesModule.render({}, container);
    };

    this.renderHttp = function(container) {
        var httpModule = new HttpModule();
        httpModule.render({}, container);
    };

    this.renderHtml = function(container) {
        var htmlModule = new HtmlModule();
        htmlModule.render({}, container);
    };

    this.renderIpCidr = function(container) {
        container.html(`
            <div class="card">
                <div class="card-header">IP C段资产</div>
                <div class="form-group">
                    <button class="btn btn-primary" id="refreshIpCidr">刷新</button>
                </div>
                <table class="table">
                    <thead>
                        <tr>
                            <th>C段</th>
                            <th>时间</th>
                        </tr>
                    </thead>
                    <tbody id="ipCidrList"></tbody>
                </table>
            </div>
        `);
        this.loadIpCidr();
    };

    this.renderIp = function(container) {
        container.html(`
            <div class="card">
                <div class="card-header">IP资产</div>
                <div class="form-group">
                    <button class="btn btn-primary" id="refreshIp">刷新</button>
                </div>
                <table class="table">
                    <thead>
                        <tr>
                            <th>IP</th>
                            <th>端口</th>
                            <th>服务类型</th>
                            <th>时间</th>
                        </tr>
                    </thead>
                    <tbody id="ipList"></tbody>
                </table>
            </div>
        `);
        this.loadIp();
    };

    this.renderHighlights = function(container) {
        var highlightsModule = new HighlightsModule();
        highlightsModule.render({}, container);
    };

    this.loadIpCidr = function() {
        $.ajax({
            url: '/api/assets/ip-cidr',
            type: 'GET',
            success: function(data) {
                var tbody = $('#ipCidrList');
                tbody.empty();
                if (data.ipc) {
                    data.ipc.forEach(function(item) {
                        tbody.append(`
                            <tr>
                                <td>${item.ipc}</td>
                                <td>${item.time}</td>
                            </tr>
                        `);
                    });
                }
            }
        });
    };

    this.loadIp = function() {
        $.ajax({
            url: '/api/assets/ip',
            type: 'GET',
            success: function(data) {
                var tbody = $('#ipList');
                tbody.empty();
                if (data.ip) {
                    data.ip.forEach(function(item) {
                        tbody.append(`
                            <tr>
                                <td>${item.ip}</td>
                                <td>${item.port}</td>
                                <td>${item.service_type || ''}</td>
                                <td>${item.time}</td>
                            </tr>
                        `);
                    });
                }
            }
        });
    };

    this.loadHighlights = function() {
        $.ajax({
            url: '/api/assets/highlights',
            type: 'GET',
            success: function(data) {
                var tbody = $('#highlightList');
                tbody.empty();
                if (data.data) {
                    data.data.forEach(function(item) {
                        tbody.append(`
                            <tr>
                                <td>${item.url}</td>
                                <td>${item.type}</td>
                                <td>${item.tags ? item.tags.join(', ') : ''}</td>
                                <td>${item.time}</td>
                            </tr>
                        `);
                    });
                }
            }
        });
    };
}