function ReplayModule() {
    this.render = function(data, container) {
        var initialData = data.initialData || {};
        var activeMode = initialData.mode || 'burp'; // 默认为burp模式

        container.html(`
            <div class="replay-container">
                <div class="replay-header">
                    <h3>🔄 HTTP请求重放</h3>
                    <div class="replay-actions">
                        <button class="btn btn-secondary btn-sm" id="clearAll">
                            <span class="btn-icon">🗑️</span>
                            <span>清空</span>
                        </button>
                        <button class="btn btn-success btn-sm" id="sendRequest">
                            <span class="btn-icon">📤</span>
                            <span>发送请求</span>
                        </button>
                    </div>
                </div>

                <!-- 模式切换按钮 -->
                <div class="mode-switcher">
                    <button class="mode-btn ${activeMode === 'json' ? 'active' : ''}" data-mode="json">json格式</button>
                    <button class="mode-btn ${activeMode === 'burp' ? 'active' : ''}" data-mode="burp">Burp格式</button>
                </div>

                <!-- json格式 -->
                <div class="input-mode" id="jsonMode" style="display: ${activeMode === 'json' ? 'block' : 'none'};">
                    <div class="form-group">
                        <label>JSON格式请求</label>
                        <textarea id="jsonInput" rows="15" placeholder='{"method": "GET", "url": "https://example.com/api", "headers": {}, "body": ""}'></textarea>
                    </div>
                </div>

                <!-- Burp格式 -->
                <div class="input-mode" id="burpMode" style="display: ${activeMode === 'burp' ? 'block' : 'none'};">
                    <div class="form-group">
                        <label>Burp格式请求（Raw格式）</label>
                        <textarea id="burpInput" rows="15" placeholder="GET /api HTTP/1.1&#10;Host: example.com&#10;User-Agent: Mozilla/5.0&#10;&#10;"></textarea>
                    </div>
                </div>

                <!-- 响应结果 -->
                <div class="replay-result" id="replayResult">
                    <div class="empty-result">
                        <div class="empty-icon">📨</div>
                        <p>发送请求后在此显示响应结果</p>
                    </div>
                </div>
            </div>
        `);

        // 如果有初始数据，填充表单
        if (initialData.burpFormat) {
            $('#burpInput').val(initialData.burpFormat);
            // 将Burp格式转换为JSON格式
            this.burpToJson(initialData.burpFormat);
        } else if (initialData.jsonData) {
            $('#jsonInput').val(initialData.jsonData);
            // 将JSON格式转换为Burp格式
            this.jsonToBurp(initialData.jsonData);
        }

        this.bindEvents();
    };

    this.setHeadersText = function(headers) {
        var text = '';
        if (typeof headers === 'object') {
            for (var key in headers) {
                text += key + ': ' + headers[key] + '\n';
            }
        } else if (typeof headers === 'string') {
            text = headers;
        }
        $('#replayHeaders').val(text.trim());
    };

    this.getHeadersObject = function() {
        var headers = {};
        var lines = $('#replayHeaders').val().split('\n');

        lines.forEach(function(line) {
            var parts = line.split(':');
            if (parts.length >= 2) {
                var key = parts[0].trim();
                var value = parts.slice(1).join(':').trim();
                if (key) {
                    headers[key] = value;
                }
            }
        });

        return headers;
    };

    // Burp格式转换为JSON格式
    this.burpToJson = function(burpText) {
        if (!burpText || burpText.trim() === '') {
            return;
        }

        var lines = burpText.split('\n');
        var firstLine = lines[0].trim();

        // 解析请求行: METHOD URL HTTP/1.1
        var match = firstLine.match(/^([A-Z]+)\s+(.+?)\s+HTTP\/\d\.\d$/i);
        if (match) {
            var method = match[1];
            var url = match[2];

            // 解析headers和body
            var headers = {};
            var body = '';
            var emptyLineIndex = -1;

            for (var i = 1; i < lines.length; i++) {
                var line = lines[i];

                if (line.trim() === '') {
                    emptyLineIndex = i;
                    break;
                }

                var parts = line.split(':');
                if (parts.length >= 2) {
                    var key = parts[0].trim();
                    var value = parts.slice(1).join(':').trim();
                    headers[key] = value;
                }
            }

            // 提取body
            if (emptyLineIndex > 0 && emptyLineIndex < lines.length - 1) {
                body = lines.slice(emptyLineIndex + 1).join('\n');
            }

            // 构建JSON对象
            var jsonData = {
                method: method,
                url: url,
                headers: headers,
                body: body
            };

            $('#jsonInput').val(JSON.stringify(jsonData, null, 2));
        }
    };

    // JSON格式转换为Burp格式
    this.jsonToBurp = function(jsonText) {
        if (!jsonText || jsonText.trim() === '') {
            return;
        }

        try {
            var jsonData = JSON.parse(jsonText);
            var method = jsonData.method || 'GET';
            var url = jsonData.url || '';
            var headers = jsonData.headers || {};
            var body = jsonData.body || '';

            var burpFormat = `${method} ${url} HTTP/1.1\n`;

            // 添加headers
            for (var key in headers) {
                burpFormat += `${key}: ${headers[key]}\n`;
            }

            burpFormat += '\n';

            // 添加body
            if (body) {
                burpFormat += body;
            }

            $('#burpInput').val(burpFormat);
        } catch (e) {
            // JSON解析失败，不做处理
        }
    };

    this.sendRequest = function() {
        var self = this;

        // 检查当前是哪种模式
        var isJsonMode = $('#jsonMode').is(':visible');

        var url, method, headers, body;

        if (isJsonMode) {
            // 从JSON格式获取数据
            var jsonText = $('#jsonInput').val().trim();
            if (!jsonText) {
                this.showError('请输入JSON格式的请求数据');
                return;
            }

        try {
            var jsonData = JSON.parse(jsonText);
            url = jsonData.url;
            method = jsonData.method;
            headers = jsonData.headers || {};
            body = jsonData.body || '';
            
            // 如果body是对象，转换为JSON字符串
            if (typeof body === 'object') {
                body = JSON.stringify(body);
            }
        } catch (e) {
            this.showError('JSON格式错误：' + e.message);
            return;
        }
        } else {
            // 从Burp格式获取数据
            var burpText = $('#burpInput').val().trim();
            if (!burpText) {
                this.showError('请输入Burp格式的请求数据');
                return;
            }

            var lines = burpText.split('\n');
            var firstLine = lines[0].trim();
            var match = firstLine.match(/^([A-Z]+)\s+(.+?)\s+HTTP\/\d\.\d$/i);

            if (!match) {
                this.showError('Burp格式错误：无法解析请求行');
                return;
            }

            method = match[1];
            url = match[2];
            headers = {};
            body = '';

            var emptyLineIndex = -1;
            for (var i = 1; i < lines.length; i++) {
                var line = lines[i];

                if (line.trim() === '') {
                    emptyLineIndex = i;
                    break;
                }

                var parts = line.split(':');
                if (parts.length >= 2) {
                    var key = parts[0].trim();
                    var value = parts.slice(1).join(':').trim();
                    headers[key] = value;
                }
            }

            if (emptyLineIndex > 0 && emptyLineIndex < lines.length - 1) {
                body = lines.slice(emptyLineIndex + 1).join('\n');
            }
        }

        // 验证URL
        if (!url) {
            this.showError('请输入请求URL');
            return;
        }

        if (!url.startsWith('http://') && !url.startsWith('https://')) {
            this.showError('URL必须以http://或https://开头');
            return;
        }

        // 显示加载状态
        this.showLoading();

        $.ajax({
            url: '/api/tools/replay',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                url: url,
                method: method,
                headers: headers,
                body: body
            }),
            success: function(data) {
                self.showResult(data);
            },
            error: function(xhr) {
                self.showError('请求失败：' + (xhr.responseJSON ? xhr.responseJSON.message : '未知错误'));
            }
        });
    };

    this.showLoading = function() {
        $('#replayResult').html(`
            <div class="loading-state">
                <div class="spinner"></div>
                <p>正在发送请求...</p>
            </div>
        `);
    };

    this.showResult = function(data) {
        var resultHtml = '';

        // 显示请求信息
        resultHtml += `
            <div class="result-section request-info">
                <h4>📤 请求信息</h4>
                <div class="info-grid">
                    <div class="info-item">
                        <label>状态码</label>
                        <span class="status-badge ${this.getStatusClass(data.status_code)}">${data.status_code || 'N/A'}</span>
                    </div>
                    <div class="info-item">
                        <label>响应时间</label>
                        <span>${data.response_time || 'N/A'}</span>
                    </div>
                </div>
            </div>
        `;

        // 显示响应头
        if (data.response_headers) {
            resultHtml += `
                <div class="result-section">
                    <h4>📋 响应头</h4>
                    <pre class="code-block headers">${this.formatHeaders(data.response_headers)}</pre>
                </div>
            `;
        }

        // 显示响应体
        if (data.response_body) {
            var contentType = data.response_headers && data.response_headers['Content-Type'];
            var isJson = contentType && contentType.includes('application/json');

            resultHtml += `
                <div class="result-section">
                    <div class="section-header">
                        <h4>📄 响应体</h4>
                        <div class="section-actions">
                            <button class="btn btn-primary btn-sm" id="copyResponse">
                                <span class="btn-icon">📋</span>
                                <span>复制</span>
                            </button>
                            ${isJson ? `
                                <button class="btn btn-secondary btn-sm" id="formatJson">
                                    <span class="btn-icon">✨</span>
                                    <span>格式化</span>
                                </button>
                            ` : ''}
                        </div>
                    </div>
                    <pre class="code-block response">${this.escapeHtml(data.response_body)}</pre>
                </div>
            `;
        }

        $('#replayResult').html(resultHtml);
    };

    this.showError = function(message) {
        $('#replayResult').html(`
            <div class="error-state">
                <div class="error-icon">❌</div>
                <p>${this.escapeHtml(message)}</p>
            </div>
        `);
    };

    this.getStatusClass = function(statusCode) {
        if (!statusCode) return 'status-unknown';
        if (statusCode >= 200 && statusCode < 300) return 'status-success';
        if (statusCode >= 300 && statusCode < 400) return 'status-redirect';
        if (statusCode >= 400 && statusCode < 500) return 'status-client-error';
        if (statusCode >= 500) return 'status-server-error';
        return 'status-unknown';
    };

    this.formatHeaders = function(headers) {
        var text = '';
        for (var key in headers) {
            text += key + ': ' + headers[key] + '\n';
        }
        return text || '(无响应头)';
    };

    this.escapeHtml = function(text) {
        var div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    };

    this.clearForm = function() {
        $('#jsonInput').val('');
        $('#burpInput').val('');
        $('#replayResult').html(`
            <div class="empty-result">
                <div class="empty-icon">📨</div>
                <p>发送请求后在此显示响应结果</p>
            </div>
        `);
    };

    this.bindEvents = function() {
        var self = this;

        // 模式切换
        $('.mode-btn').on('click', function() {
            var mode = $(this).data('mode');
            $('.mode-btn').removeClass('active');
            $(this).addClass('active');

            if (mode === 'burp') {
                $('#burpMode').show();
                $('#jsonMode').hide();
                // 从JSON格式同步到Burp格式
                self.jsonToBurp($('#jsonInput').val());
            } else {
                $('#burpMode').hide();
                $('#jsonMode').show();
                // 从Burp格式同步到JSON格式
                self.burpToJson($('#burpInput').val());
            }
        });

        // 发送请求
        $('#sendRequest').on('click', function() {
            self.sendRequest();
        });

        // Ctrl+Enter 快捷发送
        $('#jsonInput, #burpInput').on('keydown', function(e) {
            if (e.ctrlKey && e.key === 'Enter') {
                self.sendRequest();
            }
        });

        // Burp格式输入变化时自动同步到JSON格式
        $('#burpInput').on('input', function() {
            self.burpToJson($(this).val());
        });

        // JSON格式输入变化时自动同步到Burp格式
        $('#jsonInput').on('input', function() {
            self.jsonToBurp($(this).val());
        });

        // 清空表单
        $('#clearAll').on('click', function() {
            if (confirm('确定要清空所有内容吗？')) {
                self.clearForm();
            }
        });

        // 复制响应
        $(document).on('click', '#copyResponse', function() {
            var response = $('.response').text();
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(response).then(function() {
                    self.showToast('复制成功！');
                }).catch(function() {
                    self.fallbackCopy(response);
                });
            } else {
                self.fallbackCopy(response);
            }
        });

        // 格式化JSON
        $(document).on('click', '#formatJson', function() {
            try {
                var response = $('.response').text();
                var json = JSON.parse(response);
                $('.response').text(JSON.stringify(json, null, 2));
            } catch (e) {
                self.showToast('JSON格式错误');
            }
        });
    };

    this.fallbackCopy = function(text) {
        var textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();

        try {
            document.execCommand('copy');
            this.showToast('复制成功！');
        } catch (err) {
            alert('复制失败，请手动复制');
        }

        document.body.removeChild(textarea);
    };

    this.showToast = function(message) {
        var toast = $('<div class="replay-toast">' + message + '</div>');
        $('body').append(toast);

        setTimeout(function() {
            toast.addClass('show');
        }, 10);

        setTimeout(function() {
            toast.removeClass('show');
            setTimeout(function() {
                toast.remove();
            }, 300);
        }, 2000);
    };
}
