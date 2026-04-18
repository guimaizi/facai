// 资产管理配置 API
var AssetsConfigAPI = {
    
    // 获取所有配置
    getAllConfig: function(params, callback) {
        $.ajax({
            url: '/api/assets/config/all',
            method: 'GET',
            data: params || {},
            dataType: 'json',
            success: function(response) {
                callback(response);
            },
            error: function(xhr, status, error) {
                console.error('获取配置失败:', error);
                callback({
                    success: false,
                    message: '获取配置失败'
                });
            }
        });
    },

    // 获取域名白名单
    getWhitelistDomain: function(params, callback) {
        $.ajax({
            url: '/api/assets/config/whitelist/domain',
            method: 'GET',
            data: params || {},
            dataType: 'json',
            success: function(response) {
                callback(response);
            },
            error: function(xhr, status, error) {
                console.error('获取域名白名单失败:', error);
                callback({
                    success: false,
                    message: '获取域名白名单失败'
                });
            }
        });
    },

    // 保存域名白名单
    saveWhitelistDomain: function(domains, callback) {
        $.ajax({
            url: '/api/assets/config/whitelist/domain',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ domains: domains }),
            dataType: 'json',
            success: function(response) {
                callback(response);
            },
            error: function(xhr, status, error) {
                console.error('保存域名白名单失败:', error);
                callback({
                    success: false,
                    message: '保存域名白名单失败'
                });
            }
        });
    },

    // 获取域名黑名单
    getBlocklistDomain: function(params, callback) {
        $.ajax({
            url: '/api/assets/config/blocklist/domain',
            method: 'GET',
            data: params || {},
            dataType: 'json',
            success: function(response) {
                callback(response);
            },
            error: function(xhr, status, error) {
                console.error('获取域名黑名单失败:', error);
                callback({
                    success: false,
                    message: '获取域名黑名单失败'
                });
            }
        });
    },

    // 保存域名黑名单
    saveBlocklistDomain: function(domains, callback) {
        $.ajax({
            url: '/api/assets/config/blocklist/domain',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ domains: domains }),
            dataType: 'json',
            success: function(response) {
                callback(response);
            },
            error: function(xhr, status, error) {
                console.error('保存域名黑名单失败:', error);
                callback({
                    success: false,
                    message: '保存域名黑名单失败'
                });
            }
        });
    },

    // 获取URL黑名单
    getBlocklistUrl: function(params, callback) {
        $.ajax({
            url: '/api/assets/config/blocklist/url',
            method: 'GET',
            data: params || {},
            dataType: 'json',
            success: function(response) {
                callback(response);
            },
            error: function(xhr, status, error) {
                console.error('获取URL黑名单失败:', error);
                callback({
                    success: false,
                    message: '获取URL黑名单失败'
                });
            }
        });
    },

    // 保存URL黑名单
    saveBlocklistUrl: function(urls, callback) {
        $.ajax({
            url: '/api/assets/config/blocklist/url',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ urls: urls }),
            dataType: 'json',
            success: function(response) {
                callback(response);
            },
            error: function(xhr, status, error) {
                console.error('保存URL黑名单失败:', error);
                callback({
                    success: false,
                    message: '保存URL黑名单失败'
                });
            }
        });
    },

    // 导入域名到HTTP
    importDomains: function(domains, source, callback) {
        $.ajax({
            url: '/api/assets/config/import/domains',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ domains: domains, source: source }),
            dataType: 'json',
            success: function(response) {
                callback(response);
            },
            error: function(xhr, status, error) {
                console.error('导入域名失败:', error);
                callback({
                    success: false,
                    message: '导入域名失败'
                });
            }
        });
    },

    // 导入URL到HTTP
    importUrls: function(urls, source, callback) {
        $.ajax({
            url: '/api/assets/config/import/urls',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ urls: urls, source: source }),
            dataType: 'json',
            success: function(response) {
                callback(response);
            },
            error: function(xhr, status, error) {
                console.error('导入URL失败:', error);
                callback({
                    success: false,
                    message: '导入URL失败'
                });
            }
        });
    }
};
