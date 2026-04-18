function ToolsModule() {
    this.render = function(data, container) {
        var subModule = data.subModule || 'replay';

        switch(subModule) {
            case 'replay':
                this.renderReplay(data, container);
                break;
            case 'encode-decode':
                this.renderEncodeDecode(data, container);
                break;
            case 'clipboard':
                this.renderClipboard(data, container);
                break;
            case 'port-scan':
                this.renderPortScan(container);
                break;
            default:
                this.renderReplay(data, container);
        }
    };

    this.renderReplay = function(data, container) {
        var replayModule = new ReplayModule();
        replayModule.render(data, container);
    };

    this.renderEncodeDecode = function(data, container) {
        var encodeDecodeModule = new EncodeDecodeModule();
        encodeDecodeModule.render(data, container);
    };

    this.renderClipboard = function(data, container) {
        var clipboardModule = new ClipboardModule();
        clipboardModule.render(data, container);
    };

    this.renderPortScan = function(container) {
        var portScanModule = new PortScanModule();
        portScanModule.render({}, container);
    };
}