var PageUp = {
    /**
     * 生成翻页HTML
     * @param {Object} options 配置选项
     * @param {number} options.currentPage 当前页码
     * @param {number} options.totalPages 总页数
     * @param {function} options.onPageChange 页码变更回调函数
     * @param {number} options.visiblePages 可见页码数量（默认10）
     * @returns {string} 翻页HTML
     */
    generatePagination: function(options) {
        var defaults = {
            currentPage: 1,
            totalPages: 1,
            onPageChange: function() {},
            visiblePages: 10
        };
        
        var config = Object.assign({}, defaults, options);
        var { currentPage, totalPages, onPageChange, visiblePages } = config;
        
        if (totalPages <= 1) {
            return '';
        }
        
        var html = '<div class="pagination">';
        
        // 上一页
        var prevDisabled = currentPage === 1 ? 'disabled' : '';
        html += `<button class="pagination-btn prev ${prevDisabled}" data-page="${currentPage - 1}">上一页</button>`;
        
        // 页码导航
        var startPage = Math.max(1, currentPage - Math.floor(visiblePages / 2));
        var endPage = Math.min(totalPages, startPage + visiblePages - 1);
        
        // 调整起始页码，确保显示足够的页码
        if (endPage - startPage + 1 < visiblePages) {
            startPage = Math.max(1, endPage - visiblePages + 1);
        }
        
        // 第一页
        if (startPage > 1) {
            html += `<button class="pagination-btn page" data-page="1">1</button>`;
            if (startPage > 2) {
                html += `<span class="pagination-ellipsis">...</span>`;
            }
        }
        
        // 中间页码
        for (var i = startPage; i <= endPage; i++) {
            var activeClass = i === currentPage ? 'active' : '';
            html += `<button class="pagination-btn page ${activeClass}" data-page="${i}">${i}</button>`;
        }
        
        // 最后一页
        if (endPage < totalPages) {
            if (endPage < totalPages - 1) {
                html += `<span class="pagination-ellipsis">...</span>`;
            }
            html += `<button class="pagination-btn page" data-page="${totalPages}">${totalPages}</button>`;
        }
        
        // 下一页
        var nextDisabled = currentPage === totalPages ? 'disabled' : '';
        html += `<button class="pagination-btn next ${nextDisabled}" data-page="${currentPage + 1}">下一页</button>`;
        
        // 总页数和跳转
        html += `
            <div class="pagination-info">
                <span>共 ${totalPages} 页</span>
                <div class="pagination-jump">
                    <input type="number" class="pagination-input" min="1" max="${totalPages}" value="${currentPage}">
                    <button class="pagination-jump-btn">跳转</button>
                </div>
            </div>
        `;
        
        html += '</div>';
        
        // 绑定事件
        setTimeout(function() {
            $('.pagination-btn').off('click').on('click', function() {
                var page = parseInt($(this).data('page'));
                if (!isNaN(page) && page >= 1 && page <= totalPages) {
                    onPageChange(page);
                }
            });
            
            $('.pagination-jump-btn').off('click').on('click', function() {
                var page = parseInt($('.pagination-input').val());
                if (!isNaN(page) && page >= 1 && page <= totalPages) {
                    onPageChange(page);
                }
            });
            
            $('.pagination-input').off('keypress').on('keypress', function(e) {
                if (e.key === 'Enter') {
                    var page = parseInt($(this).val());
                    if (!isNaN(page) && page >= 1 && page <= totalPages) {
                        onPageChange(page);
                    }
                }
            });
        }, 0);
        
        return html;
    },
    
    /**
     * 样式
     */
    getStyles: function() {
        return `
            .pagination {
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                margin: 20px 0;
                flex-wrap: wrap;
            }
            
            .pagination-btn {
                padding: 8px 16px;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                background: #ffffff;
                color: #4a5568;
                cursor: pointer;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                font-size: 14px;
                font-weight: 500;
            }
            
            .pagination-btn:hover:not(.disabled) {
                background: #667eea;
                color: #ffffff;
                border-color: #667eea;
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
            }
            
            .pagination-btn.active {
                background: #667eea;
                color: #ffffff;
                border-color: #667eea;
            }
            
            .pagination-btn.disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }
            
            .pagination-ellipsis {
                padding: 8px 16px;
                color: #718096;
                font-size: 14px;
            }
            
            .pagination-info {
                margin-left: 20px;
                display: flex;
                align-items: center;
                gap: 12px;
                font-size: 14px;
                color: #718096;
            }
            
            .pagination-jump {
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .pagination-input {
                width: 60px;
                padding: 8px 12px;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                font-size: 14px;
                text-align: center;
            }
            
            .pagination-input:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }
            
            .pagination-jump-btn {
                padding: 8px 16px;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                background: #ffffff;
                color: #4a5568;
                cursor: pointer;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                font-size: 14px;
            }
            
            .pagination-jump-btn:hover {
                background: #667eea;
                color: #ffffff;
                border-color: #667eea;
            }
            
            @media (max-width: 768px) {
                .pagination {
                    gap: 4px;
                }
                
                .pagination-btn {
                    padding: 6px 12px;
                    font-size: 12px;
                }
                
                .pagination-ellipsis {
                    padding: 6px 12px;
                    font-size: 12px;
                }
                
                .pagination-info {
                    margin-left: 10px;
                    gap: 8px;
                    font-size: 12px;
                }
                
                .pagination-input {
                    width: 50px;
                    padding: 6px 10px;
                    font-size: 12px;
                }
                
                .pagination-jump-btn {
                    padding: 6px 12px;
                    font-size: 12px;
                }
            }
        `;
    },
    
    /**
     * 初始化样式
     */
    initStyles: function() {
        if (!$('#pageup-styles').length) {
            var style = $('<style id="pageup-styles"></style>');
            style.text(this.getStyles());
            $('head').append(style);
        }
    }
};

// 初始化样式
$(document).ready(function() {
    PageUp.initStyles();
});