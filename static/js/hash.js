var HashManager = {
    init: function() {
        this.bindEvents();
        this.handleHashChange();
    },

    bindEvents: function() {
        var self = this;
        $(window).on('hashchange', function() {
            self.handleHashChange();
        });
    },

    handleHashChange: function() {
        var hash = window.location.hash.substring(1);
        if (!hash) {
            hash = 'projects';
        }
        this.loadModule(hash);
    },

    loadModule: function(hash) {
        var parts = hash.split('/');
        var moduleName = parts[0];
        var subModule = parts[1];

        var moduleMap = {
            'projects': { name: '项目管理', module: 'projects' },
            'services': { name: '服务管理', module: 'services' },
            'traffic': { name: 'HTTP流量', module: 'traffic' },
            'assets': { name: '资产管理', module: 'assets', hasSubmenu: true },
            'tools': { name: '工具与插件', module: 'tools', hasSubmenu: true },
            'spider': { name: '爬虫管理', module: 'spider' },
            'ai-agent': { name: 'AI Agent', module: 'ai-agent' },
            'scaner': { name: '漏洞扫描管理', module: 'scaner', hasSubmenu: true },
            'system': { name: '系统配置', module: 'system' }
        };

        if (moduleMap[moduleName]) {
            var moduleInfo = moduleMap[moduleName];
            
            // 如果模块有子菜单且没有指定子模块，则只展开菜单，不打开tab
            if (moduleInfo.hasSubmenu && !subModule) {
                // 只展开菜单
                var $menuItem = $('.menu a[href="#' + moduleName + '"]').parent();
                if ($menuItem.length && !$menuItem.hasClass('open')) {
                    $menuItem.addClass('open');
                }
                return;
            }
            
            // 打开tab
            if (subModule) {
                TabManager.openTab(moduleInfo.module + '/' + subModule, moduleInfo.name + ' - ' + subModule, { subModule: subModule });
            } else {
                TabManager.openTab(moduleInfo.module, moduleInfo.name, {});
            }
        }
    }
};

$(document).ready(function() {
    HashManager.init();
});