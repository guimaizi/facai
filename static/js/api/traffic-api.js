var TrafficAPI = {
    list: function(params, callback) {
        $.ajax({
            url: '/api/traffic/list',
            type: 'GET',
            data: params,
            success: callback
        });
    },

    detail: function(id, callback) {
        $.ajax({
            url: '/api/traffic/detail/' + id,
            type: 'GET',
            success: callback
        });
    },

    clear: function(callback) {
        $.ajax({
            url: '/api/traffic/clear',
            type: 'POST',
            success: callback
        });
    }
};