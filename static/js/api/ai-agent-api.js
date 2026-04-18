// AI Agent API 接口
var AIAgentAPI = {
    
    // 基础 URL
    baseURL: '/api/ai-agent',

    // 获取 AI Agent 统计数据
    getStats: function(callback) {
        $.ajax({
            url: this.baseURL + '/stats',
            method: 'GET',
            dataType: 'json',
            success: function(response) {
                callback(response);
            },
            error: function(xhr, status, error) {
                console.error('获取 AI Agent 统计数据失败:', error);
                callback({
                    success: false,
                    message: '获取统计数据失败'
                });
            }
        });
    },

    // 获取任务列表
    getTasks: function(params, callback) {
        $.ajax({
            url: this.baseURL + '/tasks',
            method: 'GET',
            data: params || {},
            dataType: 'json',
            success: function(response) {
                callback(response);
            },
            error: function(xhr, status, error) {
                console.error('获取任务列表失败:', error);
                callback({
                    success: false,
                    message: '获取任务列表失败'
                });
            }
        });
    },

    // 创建 AI 任务
    createTask: function(task, callback) {
        $.ajax({
            url: this.baseURL + '/tasks',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(task),
            dataType: 'json',
            success: function(response) {
                callback(response);
            },
            error: function(xhr, status, error) {
                console.error('创建 AI 任务失败:', error);
                callback({
                    success: false,
                    message: '创建任务失败'
                });
            }
        });
    },

    // 获取任务详情
    getTaskDetail: function(taskId, callback) {
        $.ajax({
            url: this.baseURL + '/tasks/' + taskId,
            method: 'GET',
            dataType: 'json',
            success: function(response) {
                callback(response);
            },
            error: function(xhr, status, error) {
                console.error('获取任务详情失败:', error);
                callback({
                    success: false,
                    message: '获取任务详情失败'
                });
            }
        });
    },

    // 更新任务
    updateTask: function(taskId, taskData, callback) {
        $.ajax({
            url: this.baseURL + '/tasks/' + taskId,
            method: 'PUT',
            contentType: 'application/json',
            data: JSON.stringify(taskData),
            dataType: 'json',
            success: function(response) {
                callback(response);
            },
            error: function(xhr, status, error) {
                console.error('更新任务失败:', error);
                callback({
                    success: false,
                    message: '更新任务失败'
                });
            }
        });
    },

    // 删除任务
    deleteTask: function(taskId, callback) {
        $.ajax({
            url: this.baseURL + '/tasks/' + taskId,
            method: 'DELETE',
            dataType: 'json',
            success: function(response) {
                callback(response);
            },
            error: function(xhr, status, error) {
                console.error('删除任务失败:', error);
                callback({
                    success: false,
                    message: '删除任务失败'
                });
            }
        });
    },

    // 执行任务
    executeTask: function(taskId, callback) {
        $.ajax({
            url: this.baseURL + '/tasks/' + taskId + '/execute',
            method: 'POST',
            dataType: 'json',
            success: function(response) {
                callback(response);
            },
            error: function(xhr, status, error) {
                console.error('执行任务失败:', error);
                callback({
                    success: false,
                    message: '执行任务失败'
                });
            }
        });
    },

    // 停止任务
    stopTask: function(taskId, callback) {
        $.ajax({
            url: this.baseURL + '/tasks/' + taskId + '/stop',
            method: 'POST',
            dataType: 'json',
            success: function(response) {
                callback(response);
            },
            error: function(xhr, status, error) {
                console.error('停止任务失败:', error);
                callback({
                    success: false,
                    message: '停止任务失败'
                });
            }
        });
    },

    // 发送消息到 AI
    sendMessage: function(message, callback) {
        $.ajax({
            url: this.baseURL + '/chat',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ message: message }),
            dataType: 'json',
            success: function(response) {
                callback(response);
            },
            error: function(xhr, status, error) {
                console.error('发送消息失败:', error);
                callback({
                    success: false,
                    message: '发送消息失败'
                });
            }
        });
    },

    // 获取任务日志
    getTaskLogs: function(taskId, params, callback) {
        $.ajax({
            url: this.baseURL + '/tasks/' + taskId + '/logs',
            method: 'GET',
            data: params || {},
            dataType: 'json',
            success: function(response) {
                callback(response);
            },
            error: function(xhr, status, error) {
                console.error('获取任务日志失败:', error);
                callback({
                    success: false,
                    message: '获取任务日志失败'
                });
            }
        });
    },

    // 获取 AI 分析报告
    getAnalysisReport: function(reportId, callback) {
        $.ajax({
            url: this.baseURL + '/reports/' + reportId,
            method: 'GET',
            dataType: 'json',
            success: function(response) {
                callback(response);
            },
            error: function(xhr, status, error) {
                console.error('获取分析报告失败:', error);
                callback({
                    success: false,
                    message: '获取分析报告失败'
                });
            }
        });
    },

    // 生成分析报告
    generateReport: function(reportData, callback) {
        $.ajax({
            url: this.baseURL + '/reports',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(reportData),
            dataType: 'json',
            success: function(response) {
                callback(response);
            },
            error: function(xhr, status, error) {
                console.error('生成报告失败:', error);
                callback({
                    success: false,
                    message: '生成报告失败'
                });
            }
        });
    },

    // 获取 AI 配置
    getConfig: function(callback) {
        $.ajax({
            url: this.baseURL + '/config',
            method: 'GET',
            dataType: 'json',
            success: function(response) {
                callback(response);
            },
            error: function(xhr, status, error) {
                console.error('获取 AI 配置失败:', error);
                callback({
                    success: false,
                    message: '获取配置失败'
                });
            }
        });
    },

    // 更新 AI 配置
    updateConfig: function(config, callback) {
        $.ajax({
            url: this.baseURL + '/config',
            method: 'PUT',
            contentType: 'application/json',
            data: JSON.stringify(config),
            dataType: 'json',
            success: function(response) {
                callback(response);
            },
            error: function(xhr, status, error) {
                console.error('更新 AI 配置失败:', error);
                callback({
                    success: false,
                    message: '更新配置失败'
                });
            }
        });
    }
};
