var SystemAPI = {
    config: {
        get: function(callback) {
            $.ajax({
                url: '/api/system/config',
                type: 'GET',
                success: callback
            });
        },

        update: function(data, callback) {
            $.ajax({
                url: '/api/system/config',
                type: 'POST',
                data: data,
                success: callback
            });
        }
    },

    status: function(callback) {
        $.ajax({
            url: '/api/system/status',
            type: 'GET',
            success: callback
        });
    }
};