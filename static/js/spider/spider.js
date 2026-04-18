// 爬虫管理模块
function SpiderModule() {
    'use strict';

    // 渲染函数 - 由 TabManager 调用
    this.render = function(data, container) {
        const html = `
            <div class="spider-container">
                <div class="card">
                    <div class="card-body text-center py-5">
                        <div style="font-size: 80px; margin-bottom: 20px;">🚧</div>
                        <h3 class="text-muted">功能待建</h3>
                        <p class="text-muted mt-3">被动爬虫模块正在开发中，敬请期待...</p>
                    </div>
                </div>
            </div>
        `;
        container.html(html);
    };
}
