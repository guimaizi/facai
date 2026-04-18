var TabManager = {
    tabs: [],
    activeTab: null,

    init: function() {
        this.bindEvents();
    },

    bindEvents: function() {
        var self = this;
        $(document).on('click', '.tab-item', function() {
            var tabId = $(this).data('tab-id');
            self.activateTab(tabId);
        });

        $(document).on('click', '.tab-close', function(e) {
            e.stopPropagation();
            var tabId = $(this).parent().data('tab-id');
            self.closeTab(tabId);
        });
    },

    openTab: function(module, title, data) {
        // 检查是否已存在相同模块的tab
        var existingTab = this.tabs.find(function(tab) {
            return tab.module === module;
        });
        
        if (existingTab) {
            // 如果存在，激活该tab
            this.activateTab(existingTab.id);
            return existingTab.id;
        }
        
        // 不存在则创建新tab
        var tabId = module + '_' + Date.now();
        var tab = {
            id: tabId,
            module: module,
            title: title,
            data: data || {}
        };
        this.tabs.push(tab);
        this.renderTabs();
        this.activateTab(tabId);
        return tabId;
    },

    activateTab: function(tabId) {
        this.activeTab = tabId;
        this.renderTabs();
        this.renderTabContent();
    },

    closeTab: function(tabId) {
        var index = this.tabs.findIndex(function(tab) {
            return tab.id === tabId;
        });
        if (index > -1) {
            this.tabs.splice(index, 1);
            if (this.activeTab === tabId) {
                this.activeTab = this.tabs.length > 0 ? this.tabs[this.tabs.length - 1].id : null;
            }
            this.renderTabs();
            this.renderTabContent();
        }
    },

    refreshCurrentTab: function() {
        if (this.activeTab) {
            this.renderTabContent();
        }
    },

    renderTabs: function() {
        var self = this;
        var tabList = $('.tab-list');
        tabList.empty();
        this.tabs.forEach(function(tab) {
            var activeClass = tab.id === self.activeTab ? 'active' : '';
            tabList.append('<div class="tab-item ' + activeClass + '" data-tab-id="' + tab.id + '">' +
                '<span>' + tab.title + '</span>' +
                '<span class="tab-close">×</span>' +
                '</div>');
        });
    },

    renderTabContent: function() {
        var tabContent = $('.tab-content');
        tabContent.empty();
        if (this.activeTab) {
            var tab = this.tabs.find(function(t) {
                return t.id === this.activeTab;
            }.bind(this));
            if (tab) {
                // 处理带斜杠的模块路径（如 assets/config）
                var parts = tab.module.split('/');
                var moduleName = parts[0];
                var module = FacaiCore.modules[moduleName];
                if (module && module.render) {
                    module.render(tab.data, tabContent);
                }
            }
        }
    }
};

$(document).ready(function() {
    TabManager.init();
});