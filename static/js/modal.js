var Modal = {
    show: function(modalId) {
        var modal = $('#' + modalId);
        modal.css('display', 'flex');
        modal.css('justify-content', 'center');
        modal.css('align-items', 'center');
        $('body').css('overflow', 'hidden');
    },

    hide: function(modalId) {
        var modal = $('#' + modalId);
        modal.css('display', 'none');
        modal.css('justify-content', '');
        modal.css('align-items', '');
        $('body').css('overflow', '');
        modal.trigger('close');
    },

    close: function(modalId) {
        this.hide(modalId);
    },

    init: function() {
        // 点击关闭按钮
        $(document).on('click', '.modal-close, .close', function() {
            var modal = $(this).closest('.modal-overlay');
            Modal.hide(modal.attr('id'));
        });

        // 点击遮罩层关闭
        $(document).on('click', '.modal-overlay', function(e) {
            if (e.target === this) {
                Modal.hide($(this).attr('id'));
            }
        });

        // ESC键关闭
        $(document).on('keydown', function(e) {
            if (e.key === 'Escape') {
                var modal = $('.modal-overlay[style*="display: flex"]');
                if (modal.length > 0) {
                    Modal.hide(modal.attr('id'));
                }
            }
        });
    }
};

$(document).ready(function() {
    Modal.init();
});
