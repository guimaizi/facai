/**
 * 漏洞扫描器模块 - 主入口
 * 参考 AssetsModule 的实现方式
 */

function ScanerModule() {
    this.render = function(data, container) {
        var subModule = data.subModule || 'overview';

        switch(subModule) {
            case 'overview':
                this.renderOverview(container);
                break;
            case 'settings':
                this.renderSettings(container);
                break;
            case 'config':
                this.renderConfig(container);
                break;
            case 'auto':
                this.renderAutoMode(container);
                break;
            case 'manual':
                this.renderManualMode(container);
                break;
            case 'results':
                this.renderResults(container);
                break;
            case 'logs':
                this.renderLogs(container);
                break;
            default:
                this.renderOverview(container);
        }
    };

    this.renderOverview = function(container) {
        var overviewModule = new ScanerOverviewModule();
        overviewModule.render({}, container);
    };

    this.renderSettings = function(container) {
        var settingsModule = new ScanerSettingsModule();
        settingsModule.render({}, container);
    };

    this.renderConfig = function(container) {
        var configModule = new ScanerConfigModule();
        configModule.render({}, container);
    };

    this.renderAutoMode = function(container) {
        var autoModeModule = new ScanerAutoModeModule();
        autoModeModule.render({}, container);
    };

    this.renderManualMode = function(container) {
        var manualModeModule = new ScanerManualModeModule();
        manualModeModule.render({}, container);
    };

    this.renderResults = function(container) {
        var resultsModule = new ScanerResultsModule();
        resultsModule.render({}, container);
    };

    this.renderLogs = function(container) {
        var logsModule = new ScanerLogsModule();
        logsModule.render({}, container);
    };
}

console.log('[Scaner] ScanerModule loaded');
