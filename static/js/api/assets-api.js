var AssetsAPI = {
    overview: function(callback) {
        $.ajax({
            url: '/api/assets/overview',
            type: 'GET',
            success: callback
        });
    },

    config: {
        get: function(callback) {
            $.ajax({
                url: '/api/assets/config',
                type: 'GET',
                success: callback
            });
        },

        update: function(data, callback) {
            $.ajax({
                url: '/api/assets/config',
                type: 'POST',
                data: data,
                success: callback
            });
        }
    },

    subdomains: {
        list: function(params, callback) {
            $.ajax({
                url: '/api/assets/subdomains',
                type: 'GET',
                data: params,
                success: callback
            });
        },

        add: function(data, callback) {
            $.ajax({
                url: '/api/assets/subdomains',
                type: 'POST',
                data: data,
                success: callback
            });
        },

        delete: function(id, callback) {
            $.ajax({
                url: '/api/assets/subdomains/' + id,
                type: 'DELETE',
                success: callback
            });
        }
    },

    websites: {
        list: function(params, callback) {
            $.ajax({
                url: '/api/assets/websites',
                type: 'GET',
                data: params,
                success: callback
            });
        },

        detail: function(id, callback) {
            $.ajax({
                url: '/api/assets/websites/' + id,
                type: 'GET',
                success: callback
            });
        },

        delete: function(id, callback) {
            $.ajax({
                url: '/api/assets/websites/' + id,
                type: 'DELETE',
                success: callback
            });
        }
    },

    http: {
        list: function(params, callback) {
            $.ajax({
                url: '/api/assets/http',
                type: 'GET',
                data: params,
                success: callback
            });
        },

        detail: function(id, callback) {
            $.ajax({
                url: '/api/assets/http/' + id,
                type: 'GET',
                success: callback
            });
        },

        delete: function(id, callback) {
            $.ajax({
                url: '/api/assets/http/' + id,
                type: 'DELETE',
                success: callback
            });
        }
    },

    html: {
        list: function(params, callback) {
            $.ajax({
                url: '/api/assets/html',
                type: 'GET',
                data: params,
                success: callback
            });
        },

        detail: function(md5, callback) {
            $.ajax({
                url: '/api/assets/html/' + md5,
                type: 'GET',
                success: callback
            });
        },

        delete: function(md5, callback) {
            $.ajax({
                url: '/api/assets/html/' + md5,
                type: 'DELETE',
                success: callback
            });
        }
    },

    ipCidr: {
        list: function(params, callback) {
            $.ajax({
                url: '/api/assets/ip-cidr',
                type: 'GET',
                data: params,
                success: callback
            });
        },

        add: function(data, callback) {
            $.ajax({
                url: '/api/assets/ip-cidr',
                type: 'POST',
                data: data,
                success: callback
            });
        },

        delete: function(id, callback) {
            $.ajax({
                url: '/api/assets/ip-cidr/' + id,
                type: 'DELETE',
                success: callback
            });
        }
    },

    ip: {
        list: function(params, callback) {
            $.ajax({
                url: '/api/assets/ip',
                type: 'GET',
                data: params,
                success: callback
            });
        },

        add: function(data, callback) {
            $.ajax({
                url: '/api/assets/ip',
                type: 'POST',
                data: data,
                success: callback
            });
        },

        delete: function(id, callback) {
            $.ajax({
                url: '/api/assets/ip/' + id,
                type: 'DELETE',
                success: callback
            });
        }
    },

    highlights: {
        list: function(params, callback) {
            $.ajax({
                url: '/api/assets/highlights',
                type: 'GET',
                data: params,
                success: callback
            });
        },

        add: function(data, callback) {
            $.ajax({
                url: '/api/assets/highlights',
                type: 'POST',
                data: data,
                success: callback
            });
        },

        update: function(id, data, callback) {
            $.ajax({
                url: '/api/assets/highlights/' + id,
                type: 'POST',
                data: data,
                success: callback
            });
        },

        delete: function(id, callback) {
            $.ajax({
                url: '/api/assets/highlights/' + id,
                type: 'DELETE',
                success: callback
            });
        }
    }
};