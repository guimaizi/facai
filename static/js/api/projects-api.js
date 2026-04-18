var ProjectsAPI = {
    list: function(callback) {
        $.ajax({
            url: '/api/projects/list',
            type: 'GET',
            success: callback
        });
    },

    add: function(data, callback) {
        $.ajax({
            url: '/api/projects/add',
            type: 'POST',
            data: data,
            success: callback
        });
    },

    update: function(project, data, callback) {
        $.ajax({
            url: '/api/projects/update/' + project,
            type: 'POST',
            data: data,
            success: callback
        });
    },

    delete: function(project, callback) {
        $.ajax({
            url: '/api/projects/delete/' + project,
            type: 'DELETE',
            success: callback
        });
    },

    get: function(project, callback) {
        $.ajax({
            url: '/api/projects/get/' + project,
            type: 'GET',
            success: callback
        });
    }
};