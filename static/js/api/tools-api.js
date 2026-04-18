var ToolsAPI = {
    replay: function(data, callback) {
        $.ajax({
            url: '/api/tools/replay',
            type: 'POST',
            data: data,
            success: callback
        });
    },

    encode: {
        base64: function(text, callback) {
            $.ajax({
                url: '/api/tools/encode/base64',
                type: 'POST',
                data: { text: text },
                success: callback
            });
        },

        url: function(text, callback) {
            $.ajax({
                url: '/api/tools/encode/url',
                type: 'POST',
                data: { text: text },
                success: callback
            });
        }
    },

    decode: {
        base64: function(text, callback) {
            $.ajax({
                url: '/api/tools/decode/base64',
                type: 'POST',
                data: { text: text },
                success: callback
            });
        },

        url: function(text, callback) {
            $.ajax({
                url: '/api/tools/decode/url',
                type: 'POST',
                data: { text: text },
                success: callback
            });
        }
    },

    clipboard: {
        list: function(callback) {
            $.ajax({
                url: '/api/tools/clipboard',
                type: 'GET',
                success: callback
            });
        },

        add: function(text, callback) {
            $.ajax({
                url: '/api/tools/clipboard',
                type: 'POST',
                data: { text: text },
                success: callback
            });
        },

        delete: function(index, callback) {
            $.ajax({
                url: '/api/tools/clipboard/' + index,
                type: 'DELETE',
                success: callback
            });
        }
    },

    portScan: function(data, callback) {
        $.ajax({
            url: '/api/tools/port-scan',
            type: 'POST',
            data: data,
            success: callback
        });
    }
};