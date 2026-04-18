// 服务管理 API
var ServicesAPI = {
    /**
     * 获取所有服务状态
     */
    status: function(callback) {
        $.ajax({
            url: '/api/services/status',
            type: 'GET',
            success: callback
        });
    },

    /**
     * 爬虫服务
     */
    startSpider: function(callback) {
        $.ajax({
            url: '/api/services/spider/start',
            type: 'POST',
            success: callback
        });
    },

    stopSpider: function(callback) {
        $.ajax({
            url: '/api/services/spider/stop',
            type: 'POST',
            success: callback
        });
    },

    restartSpider: function(callback) {
        $.ajax({
            url: '/api/services/spider/restart',
            type: 'POST',
            success: callback
        });
    },

    /**
     * 资产监控服务
     */
    startMonitor: function(callback) {
        $.ajax({
            url: '/api/services/monitor/start',
            type: 'POST',
            success: callback
        });
    },

    stopMonitor: function(callback) {
        $.ajax({
            url: '/api/services/monitor/stop',
            type: 'POST',
            success: callback
        });
    },

    /**
     * 漏洞扫描服务
     */
    startScanner: function(callback) {
        $.ajax({
            url: '/api/services/scanner/start',
            type: 'POST',
            success: callback
        });
    },

    stopScanner: function(callback) {
        $.ajax({
            url: '/api/services/scanner/stop',
            type: 'POST',
            success: callback
        });
    },

    /**
     * Mitmproxy 服务
     */
    startMitmproxy: function(callback) {
        $.ajax({
            url: '/api/services/mitmproxy/start',
            type: 'POST',
            success: callback
        });
    },

    stopMitmproxy: function(callback) {
        $.ajax({
            url: '/api/services/mitmproxy/stop',
            type: 'POST',
            success: callback
        });
    },

    /**
     * Chrome CDP 服务
     */
    startChrome: function(callback) {
        $.ajax({
            url: '/api/services/chrome/start',
            type: 'POST',
            success: callback
        });
    },

    stopChrome: function(callback) {
        $.ajax({
            url: '/api/services/chrome/stop',
            type: 'POST',
            success: callback
        });
    },

    /**
     * 通用服务操作
     */
    serviceAction: function(url, data, callback) {
        $.ajax({
            url: url,
            type: 'POST',
            contentType: 'application/json',
            data: data ? JSON.stringify(data) : null,
            success: callback
        });
    }
};
