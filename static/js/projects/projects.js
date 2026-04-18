function ProjectsModule() {
    this.render = function(data, container) {
        container.html(`
            <div class="card">
                <div class="card-header">
                    <div class="row">
                        <div class="col-md-6">
                            项目管理
                        </div>
                        <div class="col-md-6 text-right">
                            <span id="projectCount" class="mr-3"></span>
                            <span id="runningStatus" class="mr-3"></span>
                            <button class="btn btn-primary" id="addProject">添加项目</button>
                        </div>
                    </div>
                </div>
                <div class="form-group p-3">
                    <table class="table">
                        <thead>
                            <tr>
                                <th>项目名称</th>
                                <th>描述</th>
                                <th>状态</th>
                                <th>创建时间</th>
                                <th>操作</th>
                            </tr>
                        </thead>
                        <tbody id="projectList"></tbody>
                    </table>
                </div>
            </div>
        `);
        this.loadProjects();
        this.loadProjectStatus();
        this.bindEvents();
    };

    this.loadProjects = function() {
        var self = this;
        $.ajax({
            url: '/api/projects/list',
            type: 'GET',
            success: function(data) {
                var tbody = $('#projectList');
                tbody.empty();
                if (data.projects) {
                    data.projects.forEach(function(project) {
                        var statusText = project.status_code === 1 ? '运行中' : '未运行';
                        var statusClass = project.status_code === 1 ? 'text-success' : 'text-muted';
                        var startButton = project.status_code === 1 ? 
                            `<button class="btn btn-warning btn-sm stop-project" data-project="${project.Project}">停止</button>` : 
                            `<button class="btn btn-success btn-sm start-project" data-project="${project.Project}">启动</button>`;
                        tbody.append(`
                            <tr>
                                <td>${project.Project}</td>
                                <td>${project.Description || ''}</td>
                                <td class="${statusClass}">${statusText}</td>
                                <td>${project.created_at || ''}</td>
                                <td>
                                    ${startButton}
                                    <button class="btn btn-primary btn-sm edit-project" data-project="${project.Project}">编辑</button>
                                    <button class="btn btn-danger btn-sm delete-project" data-project="${project.Project}">删除</button>
                                </td>
                            </tr>
                        `);
                    });
                }
            }
        });
    };

    this.loadProjectStatus = function() {
        var self = this;
        // 获取项目总数
        $.ajax({
            url: '/api/projects/count',
            type: 'GET',
            success: function(data) {
                $('#projectCount').text(`项目总数: ${data.count}`);
            }
        });
        // 获取运行状态
        $.ajax({
            url: '/api/projects/status',
            type: 'GET',
            success: function(data) {
                if (data.running_project) {
                    $('#runningStatus').html(`<span class="text-success">运行中: ${data.running_project.Project}</span>`);
                } else {
                    $('#runningStatus').html(`<span class="text-muted">无运行项目</span>`);
                }
            }
        });
    };

    this.bindEvents = function() {
        var self = this;

        console.log('ProjectsModule.bindEvents() called');

        // 先解绑所有事件，防止重复绑定
        $(document).off('click', '#addProject');
        $(document).off('click', '.edit-project');
        $(document).off('click', '.delete-project');
        $(document).off('click', '.start-project');
        $(document).off('click', '.stop-project');
        $(document).off('click', '#saveProject');
        $(document).off('click', '#btnFormMode');
        $(document).off('click', '#btnJsonMode');
        $(document).off('change', '#projectJson');

        // 添加项目
        $(document).on('click', '#addProject', function(e) {
            console.log('Add project button clicked', e);
            self.showProjectModal();
        });

        // 编辑项目
        $(document).on('click', '.edit-project', function(e) {
            console.log('Edit project button clicked', e);
            var projectName = $(this).data('project');
            self.showProjectModal(projectName);
        });

        // 删除项目
        $(document).on('click', '.delete-project', function() {
            var projectName = $(this).data('project');
            if (confirm(`确定要删除项目 ${projectName} 吗？`)) {
                $.ajax({
                    url: '/api/projects/delete',
                    type: 'POST',
                    contentType: 'application/json',
                    data: JSON.stringify({ Project: projectName }),
                    success: function(data) {
                        if (data.success) {
                            alert(data.message);
                            self.loadProjects();
                            self.loadProjectStatus();
                        } else {
                            alert(data.message);
                        }
                    }
                });
            }
        });

        // 启动项目
        $(document).on('click', '.start-project', function() {
            var projectName = $(this).data('project');
            $.ajax({
                url: '/api/projects/start',
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ Project: projectName }),
                success: function(data) {
                    if (data.success) {
                        alert(data.message);
                        self.loadProjects();
                        self.loadProjectStatus();
                    } else {
                        alert(data.message);
                    }
                }
            });
        });

        // 停止项目
        $(document).on('click', '.stop-project', function() {
            var projectName = $(this).data('project');
            $.ajax({
                url: '/api/projects/stop',
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ Project: projectName }),
                success: function(data) {
                    if (data.success) {
                        alert(data.message);
                        self.loadProjects();
                        self.loadProjectStatus();
                    } else {
                        alert(data.message);
                    }
                }
            });
        });

        // 保存项目
        $(document).on('click', '#saveProject', function() {
            var projectData;
            var isJsonMode = $('#jsonMode').is(':visible');
            
            console.log('===== 保存项目 =====');
            console.log('当前模式:', isJsonMode ? 'JSON编辑模式' : '表单编辑模式');
            
            if (isJsonMode) {
                // JSON编辑模式：直接使用JSON编辑器的内容
                try {
                    var jsonStr = $('#projectJson').val().trim();
                    console.log('===== JSON编辑模式 =====');
                    console.log('原始JSON字符串:', jsonStr);
                    console.log('字符串长度:', jsonStr.length);
                    projectData = JSON.parse(jsonStr);
                    console.log('解析后的对象:', projectData);
                    console.log('personal_info:', projectData.personal_info);
                } catch (e) {
                    alert('JSON格式错误: ' + e.message);
                    console.error('===== JSON解析失败 =====');
                    console.error('错误信息:', e.message);
                    console.error('错误堆栈:', e.stack);
                    console.error('原始字符串:', $('#projectJson').val());
                    return;
                }
            } else {
                // 表单编辑模式：从表单字段读取数据
                var projectName = $('#projectName').val();
                var description = $('#projectDescription').val();
                var domainList = $('#projectDomains').val().split('\n').filter(item => item.trim() !== '');
                var portTarget = $('#projectPorts').val();
                var fileType = $('#projectFileTypes').val().split('\n').filter(item => item.trim() !== '');
                var fileTypeDisallowed = $('#projectDisallowedFileTypes').val().split('\n').filter(item => item.trim() !== '');
                var userAgent = $('#projectUserAgent').val();
                var clipboardText = $('#projectClipboard').val().split('\n').filter(item => item.trim() !== '');
                var browserThread = parseInt($('#projectBrowserThread').val()) || 10;
                var httpThread = parseInt($('#projectHttpThread').val()) || 10;
                var timeout = parseInt($('#projectTimeout').val()) || 8;
                var dnslogUrl = $('#projectDnslogUrl').val() || '';
                var dnslogDomain = $('#projectDnslogDomain').val() || '';
                var serviceLock = {
                    spider_service: $('#spiderService').is(':checked') ? 1 : 0,
                    monitor_service: $('#monitorService').is(':checked') ? 1 : 0,
                    scaner_service: $('#scanerService').is(':checked') ? 1 : 0
                };
                var dnsServers = [];
                $('#projectDnsServers .dns-server').each(function() {
                    var servers = $(this).val().split(',').filter(item => item.trim() !== '');
                    if (servers.length > 0) {
                        dnsServers.push(servers);
                    }
                });

                // 解析个人信息JSON
                var personalInfo = {};
                try {
                    var personalInfoStr = $('#projectPersonalInfo').val().trim();
                    console.log('===== 表单模式 - 解析personal_info =====');
                    console.log('personal_info字符串:', personalInfoStr);
                    if (personalInfoStr) {
                        personalInfo = JSON.parse(personalInfoStr);
                        console.log('解析后的personal_info:', personalInfo);
                        console.log('personal_info类型:', typeof personalInfo);
                    }
                } catch (e) {
                    alert('个人信息JSON格式错误: ' + e.message);
                    console.error('===== personal_info解析失败 =====');
                    console.error('错误信息:', e.message);
                    console.error('错误堆栈:', e.stack);
                    return;
                }

                projectData = {
                    Project: projectName,
                    Description: description,
                    domain_list: domainList,
                    port_target: portTarget,
                    file_type: fileType,
                    file_type_disallowed: fileTypeDisallowed,
                    user_agent: userAgent,
                    clipboard_text: clipboardText,
                    browser_thread: browserThread,
                    http_thread: httpThread,
                    timeout: timeout,
                    dnslog_url: dnslogUrl,
                    dnslog_domain: dnslogDomain,
                    service_lock: serviceLock,
                    dns_server: dnsServers,
                    personal_info: personalInfo
                };
                console.log('从表单获取数据:', projectData);
            }

            console.log('personal_info:', projectData.personal_info);
            console.log('personal_info类型:', typeof projectData.personal_info);
            console.log('=======================');

            var url = $('#projectModal').data('project') ? '/api/projects/update' : '/api/projects/add';
            $.ajax({
                url: url,
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify(projectData),
                success: function(data) {
                    if (data.success) {
                        alert(data.message);
                        FacaiCore.Modal.close('projectModal');
                        self.loadProjects();
                        self.loadProjectStatus();
                    } else {
                        alert(data.message);
                    }
                }
            });
        });

        // 切换编辑模式
        $(document).on('click', '#btnFormMode', function() {
            $('#btnFormMode').removeClass('btn-outline-secondary').addClass('btn-primary active');
            $('#btnJsonMode').removeClass('btn-primary active').addClass('btn-outline-secondary');
            self.switchToFormMode();
        });

        $(document).on('click', '#btnJsonMode', function() {
            $('#btnJsonMode').removeClass('btn-outline-secondary').addClass('btn-primary active');
            $('#btnFormMode').removeClass('btn-primary active').addClass('btn-outline-secondary');
            self.switchToJsonMode();
        });

        // JSON编辑变化时更新表单
        $(document).on('change', '#projectJson', function() {
            try {
                var jsonData = JSON.parse($(this).val());
                self.updateFormFromJson(jsonData);
            } catch (e) {
                // 忽略JSON解析错误
            }
        });
    };

    this.showProjectModal = function(projectName) {
        console.log('showProjectModal called with:', projectName);
        var self = this;
        var modalHtml = `
            <div class="modal-overlay" id="projectModal">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">${projectName ? '编辑项目' : '添加项目'}</h5>
                            <button type="button" class="close">&times;</button>
                        </div>
                        <div class="modal-body">
                            <div class="form-group">
                                <div class="d-flex justify-content-between align-items-center mb-3">
                                    <label class="mb-0 font-weight-bold">编辑模式</label>
                                    <div class="btn-group" role="group">
                                        <button type="button" class="btn btn-sm btn-primary active" id="btnFormMode" data-mode="form">
                                            <i class="fas fa-edit mr-1"></i>表单编辑
                                        </button>
                                        <button type="button" class="btn btn-sm btn-outline-secondary" id="btnJsonMode" data-mode="json">
                                            <i class="fas fa-code mr-1"></i>JSON编辑
                                        </button>
                                    </div>
                                </div>
                            </div>

                            <!-- 表单编辑模式 -->
                            <div id="formMode">
                                <div class="form-group">
                                    <label>项目名称</label>
                                    <input type="text" class="form-control" id="projectName" required>
                                </div>
                                <div class="form-group">
                                    <label>描述</label>
                                    <textarea class="form-control" id="projectDescription" rows="2"></textarea>
                                </div>
                                <div class="form-group">
                                    <label>域名列表（每行一个）</label>
                                    <textarea class="form-control" id="projectDomains" rows="5"></textarea>
                                </div>
                                <div class="form-group">
                                    <label>端口目标</label>
                                    <input type="text" class="form-control" id="projectPorts" value="21,22,80-89,443,1080,1433,1521,3000,3306,3389,5432,5900,6379,7001,8000,8069,8080-8099,8161,8888,9080,9081,9090,9200,9300,10000-10002,11211,11434,27016-27018,36000,50000,50070">
                                </div>
                                <div class="form-group">
                                    <label>文件类型（每行一个）</label>
                                    <textarea class="form-control" id="projectFileTypes" rows="5"></textarea>
                                </div>
                                <div class="form-group">
                                    <label>禁用文件类型（每行一个）</label>
                                    <textarea class="form-control" id="projectDisallowedFileTypes" rows="5"></textarea>
                                </div>
                                <div class="form-group">
                                    <label>User Agent</label>
                                    <input type="text" class="form-control" id="projectUserAgent" value="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/132.0.0.0">
                                </div>
                                <div class="form-group">
                                    <label>剪贴板文本（每行一个）</label>
                                    <textarea class="form-control" id="projectClipboard" rows="3"></textarea>
                                </div>
                                <div class="form-group">
                                    <label>浏览器线程</label>
                                    <input type="number" class="form-control" id="projectBrowserThread" value="10">
                                </div>
                                <div class="form-group">
                                    <label>HTTP线程</label>
                                    <input type="number" class="form-control" id="projectHttpThread" value="10">
                                </div>
                                <div class="form-group">
                                    <label>超时时间（秒）</label>
                                    <input type="number" class="form-control" id="projectTimeout" value="8">
                                </div>
                                <div class="form-group">
                                    <label>DNS日志URL</label>
                                    <input type="text" class="form-control" id="projectDnslogUrl" placeholder="例如: http://dnslog.example.com">
                                </div>
                                <div class="form-group">
                                    <label>DNSLOG域名</label>
                                    <input type="text" class="form-control" id="projectDnslogDomain" placeholder="例如: dnslog.example.com">
                                </div>
                                <div class="form-group">
                                    <label>服务锁状态</label>
                                    <div class="row">
                                        <div class="col-md-4">
                                            <div class="form-check">
                                                <input class="form-check-input" type="checkbox" id="spiderService">
                                                <label class="form-check-label" for="spiderService">爬虫服务</label>
                                            </div>
                                        </div>
                                        <div class="col-md-4">
                                            <div class="form-check">
                                                <input class="form-check-input" type="checkbox" id="monitorService">
                                                <label class="form-check-label" for="monitorService">资产监控</label>
                                            </div>
                                        </div>
                                        <div class="col-md-4">
                                            <div class="form-check">
                                                <input class="form-check-input" type="checkbox" id="scanerService">
                                                <label class="form-check-label" for="scanerService">漏洞扫描</label>
                                            </div>
                                        </div>
                                    </div>
                                    <small class="form-text text-muted">勾选表示服务开启（1），不勾选表示关闭（0）</small>
                                </div>
                                <div class="form-group">
                                    <label>个人信息配置（JSON格式）</label>
                                    <textarea class="form-control" id="projectPersonalInfo" rows="10" placeholder='{"name":"张三","email":"zhangsan@example.com",...}'></textarea>
                                    <small class="form-text text-muted">可选字段，用于自动化测试中的个人信息填充</small>
                                </div>
                                <div class="form-group">
                                    <label>DNS服务器（每行一组，逗号分隔）</label>
                                    <div id="projectDnsServers">
                                        <div class="input-group mb-2">
                                            <input type="text" class="form-control dns-server" value="119.29.29.29,119.28.28.28">
                                            <div class="input-group-append">
                                                <button class="btn btn-danger btn-sm remove-dns-server">删除</button>
                                            </div>
                                        </div>
                                        <div class="input-group mb-2">
                                            <input type="text" class="form-control dns-server" value="180.76.76.76,180.76.76.76">
                                            <div class="input-group-append">
                                                <button class="btn btn-danger btn-sm remove-dns-server">删除</button>
                                            </div>
                                        </div>
                                    </div>
                                    <button class="btn btn-sm btn-secondary mt-2" id="addDnsServer">添加DNS服务器</button>
                                </div>
                            </div>

                            <!-- JSON编辑模式 -->
                            <div id="jsonMode" style="display: none;">
                                <div class="form-group">
                                    <label>JSON配置</label>
                                    <textarea class="form-control" id="projectJson" rows="20"></textarea>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary modal-close">关闭</button>
                            <button type="button" class="btn btn-primary" id="saveProject">保存</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        $('body').append(modalHtml);
        $('#projectModal').data('project', projectName);

        if (projectName) {
            // 加载项目数据
            $.ajax({
                url: '/api/projects/list',
                type: 'GET',
                success: function(data) {
                    var project = data.projects.find(p => p.Project === projectName);
                    if (project) {
                        self.fillProjectForm(project);
                    }
                }
            });
        }

        FacaiCore.Modal.show('projectModal');

        // 先解绑再绑定DNS服务器相关事件，防止重复绑定
        $(document).off('click', '#addDnsServer');
        $(document).off('click', '.remove-dns-server');

        // 添加DNS服务器按钮
        $(document).on('click', '#addDnsServer', function() {
            $('#projectDnsServers').append(`
                <div class="input-group mb-2">
                    <input type="text" class="form-control dns-server">
                    <div class="input-group-append">
                        <button class="btn btn-danger btn-sm remove-dns-server">删除</button>
                    </div>
                </div>
            `);
        });

        // 删除DNS服务器
        $(document).on('click', '.remove-dns-server', function() {
            $(this).closest('.input-group').remove();
        });

        // 模态框关闭时清理
        $('#projectModal').on('close', function() {
            $(this).remove();
        });
    };

    this.fillProjectForm = function(project) {
        $('#projectName').val(project.Project);
        $('#projectDescription').val(project.Description || '');
        $('#projectDomains').val(project.domain_list ? project.domain_list.join('\n') : '');
        $('#projectPorts').val(project.port_target || '');
        $('#projectFileTypes').val(project.file_type ? project.file_type.join('\n') : '');
        $('#projectDisallowedFileTypes').val(project.file_type_disallowed ? project.file_type_disallowed.join('\n') : '');
        $('#projectUserAgent').val(project.user_agent || '');
        $('#projectClipboard').val(project.clipboard_text ? project.clipboard_text.join('\n') : '');
        $('#projectBrowserThread').val(project.browser_thread || 10);
        $('#projectHttpThread').val(project.http_thread || 10);
        $('#projectTimeout').val(project.timeout || 8);
        $('#projectDnslogUrl').val(project.dnslog_url || '');
        $('#projectDnslogDomain').val(project.dnslog_domain || '');

        // 填充服务锁状态
        if (project.service_lock) {
            $('#spiderService').prop('checked', project.service_lock.spider_service == 1 || project.service_lock.spider_service === true);
            $('#monitorService').prop('checked', project.service_lock.monitor_service == 1 || project.service_lock.monitor_service === true);
            $('#scanerService').prop('checked', project.service_lock.scaner_service == 1 || project.service_lock.scaner_service === true);
        }

        // 填充个人信息
        if (project.personal_info) {
            var personalInfoStr = typeof project.personal_info === 'string' 
                ? project.personal_info 
                : JSON.stringify(project.personal_info, null, 2);
            $('#projectPersonalInfo').val(personalInfoStr);
            console.log('填充personal_info:', personalInfoStr);
        }

        // 填充DNS服务器
        $('#projectDnsServers').empty();
        if (project.dns_server && Array.isArray(project.dns_server)) {
            project.dns_server.forEach(function(servers) {
                $('#projectDnsServers').append(`
                    <div class="input-group mb-2">
                        <input type="text" class="form-control dns-server" value="${servers.join(',')}">
                        <div class="input-group-append">
                            <button class="btn btn-danger btn-sm remove-dns-server">删除</button>
                        </div>
                    </div>
                `);
            });
        }

        // 填充JSON
        $('#projectJson').val(JSON.stringify(project, null, 2));
    };

    this.switchToJsonMode = function() {
        $('#formMode').hide();
        $('#jsonMode').show();
        $('#btnJsonMode').removeClass('btn-outline-secondary').addClass('btn-primary active');
        $('#btnFormMode').removeClass('btn-primary active').addClass('btn-outline-secondary');
        // 从表单更新JSON
        try {
            var projectData = this.getFormData();
            $('#projectJson').val(JSON.stringify(projectData, null, 2));
        } catch (e) {
            console.error('从表单获取数据失败:', e);
            // 切换回表单模式
            this.switchToFormMode();
        }
    };

    this.switchToFormMode = function() {
        $('#formMode').show();
        $('#jsonMode').hide();
        $('#btnFormMode').removeClass('btn-outline-secondary').addClass('btn-primary active');
        $('#btnJsonMode').removeClass('btn-primary active').addClass('btn-outline-secondary');
        // 从JSON更新表单
        try {
            var jsonData = JSON.parse($('#projectJson').val());
            this.updateFormFromJson(jsonData);
        } catch (e) {
            // 忽略JSON解析错误
        }
    };

    this.getFormData = function() {
        var projectName = $('#projectName').val();
        var description = $('#projectDescription').val();
        var domainList = $('#projectDomains').val().split('\n').filter(item => item.trim() !== '');
        var portTarget = $('#projectPorts').val();
        var fileType = $('#projectFileTypes').val().split('\n').filter(item => item.trim() !== '');
        var fileTypeDisallowed = $('#projectDisallowedFileTypes').val().split('\n').filter(item => item.trim() !== '');
        var userAgent = $('#projectUserAgent').val();
        var clipboardText = $('#projectClipboard').val().split('\n').filter(item => item.trim() !== '');
        var browserThread = parseInt($('#projectBrowserThread').val()) || 10;
        var httpThread = parseInt($('#projectHttpThread').val()) || 10;
        var timeout = parseInt($('#projectTimeout').val()) || 8;
        var dnslogUrl = $('#projectDnslogUrl').val() || '';
        var dnslogDomain = $('#projectDnslogDomain').val() || '';
        var serviceLock = {
            spider_service: $('#spiderService').is(':checked') ? 1 : 0,
            monitor_service: $('#monitorService').is(':checked') ? 1 : 0,
            scaner_service: $('#scanerService').is(':checked') ? 1 : 0
        };
        var dnsServers = [];
        $('#projectDnsServers .dns-server').each(function() {
            var servers = $(this).val().split(',').filter(item => item.trim() !== '');
            if (servers.length > 0) {
                dnsServers.push(servers);
            }
        });

        // 解析个人信息JSON
        var personalInfo = {};
        try {
            var personalInfoStr = $('#projectPersonalInfo').val().trim();
            if (personalInfoStr) {
                personalInfo = JSON.parse(personalInfoStr);
            }
        } catch (e) {
            console.error('个人信息JSON解析失败:', e);
            alert('个人信息JSON格式错误，请检查格式是否正确');
            throw e; // 抛出异常，阻止后续操作
        }

        return {
            Project: projectName,
            Description: description,
            domain_list: domainList,
            port_target: portTarget,
            file_type: fileType,
            file_type_disallowed: fileTypeDisallowed,
            user_agent: userAgent,
            clipboard_text: clipboardText,
            browser_thread: browserThread,
            http_thread: httpThread,
            timeout: timeout,
            dnslog_url: dnslogUrl,
            dnslog_domain: dnslogDomain,
            service_lock: serviceLock,
            dns_server: dnsServers,
            personal_info: personalInfo
        };
    };

    this.updateFormFromJson = function(jsonData) {
        if (jsonData.Project) $('#projectName').val(jsonData.Project);
        if (jsonData.Description) $('#projectDescription').val(jsonData.Description);
        if (jsonData.domain_list) $('#projectDomains').val(jsonData.domain_list.join('\n'));
        if (jsonData.port_target) $('#projectPorts').val(jsonData.port_target);
        if (jsonData.file_type) $('#projectFileTypes').val(jsonData.file_type.join('\n'));
        if (jsonData.file_type_disallowed) $('#projectDisallowedFileTypes').val(jsonData.file_type_disallowed.join('\n'));
        if (jsonData.user_agent) $('#projectUserAgent').val(jsonData.user_agent);
        if (jsonData.clipboard_text) $('#projectClipboard').val(jsonData.clipboard_text.join('\n'));
        if (jsonData.browser_thread) $('#projectBrowserThread').val(jsonData.browser_thread);
        if (jsonData.http_thread) $('#projectHttpThread').val(jsonData.http_thread);
        if (jsonData.timeout) $('#projectTimeout').val(jsonData.timeout);
        if (jsonData.dnslog_url) $('#projectDnslogUrl').val(jsonData.dnslog_url);
        if (jsonData.dnslog_domain) $('#projectDnslogDomain').val(jsonData.dnslog_domain);

        // 更新服务锁状态
        if (jsonData.service_lock) {
            $('#spiderService').prop('checked', jsonData.service_lock.spider_service == 1 || jsonData.service_lock.spider_service === true);
            $('#monitorService').prop('checked', jsonData.service_lock.monitor_service == 1 || jsonData.service_lock.monitor_service === true);
            $('#scanerService').prop('checked', jsonData.service_lock.scaner_service == 1 || jsonData.service_lock.scaner_service === true);
        }

        // 更新个人信息
        if (jsonData.personal_info) {
            var personalInfoStr = typeof jsonData.personal_info === 'string' 
                ? jsonData.personal_info 
                : JSON.stringify(jsonData.personal_info, null, 2);
            $('#projectPersonalInfo').val(personalInfoStr);
        }

        // 更新DNS服务器
        if (jsonData.dns_server && Array.isArray(jsonData.dns_server)) {
            $('#projectDnsServers').empty();
            jsonData.dns_server.forEach(function(servers) {
                $('#projectDnsServers').append(`
                    <div class="input-group mb-2">
                        <input type="text" class="form-control dns-server" value="${servers.join(',')}">
                        <div class="input-group-append">
                            <button class="btn btn-danger btn-sm remove-dns-server">删除</button>
                        </div>
                    </div>
                `);
            });
        }
    };
}