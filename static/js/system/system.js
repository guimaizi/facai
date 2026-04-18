function SystemModule() {
    this.render = function(data, container) {
        container.html(`
            <div class="card">
                <div class="card-header">系统配置</div>
                <div class="form-group">
                    <label>Chrome路径</label>
                    <input type="text" id="chromePath">
                </div>
                <div class="form-group">
                    <label>Burp路径</label>
                    <input type="text" id="burpPath">
                </div>
                <div class="form-group">
                    <label>Chrome CDP端口</label>
                    <input type="number" id="chromeCdpPort">
                </div>
                <div class="form-group">
                    <label>Mitmproxy端口</label>
                    <input type="number" id="mitmproxyPort">
                </div>
                <div class="form-group">
                    <label>MongoDB IP</label>
                    <input type="text" id="mongodbIp">
                </div>
                <div class="form-group">
                    <label>MongoDB端口</label>
                    <input type="number" id="mongodbPort">
                </div>
                <div class="form-group">
                    <label>MongoDB数据库名</label>
                    <input type="text" id="mongodbDbname">
                </div>
                <button class="btn btn-primary" id="saveConfig">保存配置</button>
            </div>
        `);
        this.loadConfig();
        this.bindEvents();
    };

    this.loadConfig = function() {
        $.ajax({
            url: '/api/system/config',
            type: 'GET',
            success: function(data) {
                if (data.config) {
                    $('#chromePath').val(data.config.chrome_path || '');
                    $('#burpPath').val(data.config.burp_path || '');
                    $('#chromeCdpPort').val(data.config.chrome_cdp_port || '');
                    $('#mitmproxyPort').val(data.config.mitmproxy_port || '');
                    if (data.config.mongodb) {
                        $('#mongodbIp').val(data.config.mongodb.ip || '');
                        $('#mongodbPort').val(data.config.mongodb.port || '');
                        $('#mongodbDbname').val(data.config.mongodb.dbname || '');
                    }
                }
            }
        });
    };

    this.bindEvents = function() {
        $('#saveConfig').on('click', function() {
            var config = {
                chrome_path: $('#chromePath').val(),
                burp_path: $('#burpPath').val(),
                chrome_cdp_port: parseInt($('#chromeCdpPort').val()),
                mitmproxy_port: parseInt($('#mitmproxyPort').val()),
                mongodb: {
                    ip: $('#mongodbIp').val(),
                    port: parseInt($('#mongodbPort').val()),
                    dbname: $('#mongodbDbname').val()
                }
            };
            
            $.ajax({
                url: '/api/system/config',
                type: 'POST',
                data: config,
                success: function(data) {
                    alert(data.message);
                }
            });
        });
    };
}