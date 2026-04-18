// 编码解码工具模块
(function() {
    'use strict';

    var EncodeDecodeModule = function() {};

    // 编码解码工具函数集
    var Encoder = {
        // Base64 编码
        base64Encode: function(str) {
            try {
                return btoa(unescape(encodeURIComponent(str)));
            } catch(e) {
                return '编码失败: ' + e.message;
            }
        },

        // Base64 解码
        base64Decode: function(str) {
            try {
                return decodeURIComponent(escape(atob(str)));
            } catch(e) {
                return '解码失败: 输入不是有效的Base64字符串';
            }
        },

        // URL 编码
        urlEncode: function(str) {
            try {
                return encodeURIComponent(str);
            } catch(e) {
                return '编码失败: ' + e.message;
            }
        },

        // URL 解码
        urlDecode: function(str) {
            try {
                return decodeURIComponent(str);
            } catch(e) {
                return '解码失败: 输入不是有效的URL编码';
            }
        },

        // Hex 编码 (字符串转十六进制)
        hexEncode: function(str) {
            try {
                var result = '';
                for (var i = 0; i < str.length; i++) {
                    result += str.charCodeAt(i).toString(16).padStart(2, '0');
                }
                return result;
            } catch(e) {
                return '编码失败: ' + e.message;
            }
        },

        // Hex 解码 (十六进制转字符串)
        hexDecode: function(str) {
            try {
                str = str.replace(/\s+/g, ''); // 移除所有空格
                var result = '';
                for (var i = 0; i < str.length; i += 2) {
                    result += String.fromCharCode(parseInt(str.substr(i, 2), 16));
                }
                return result;
            } catch(e) {
                return '解码失败: 输入不是有效的十六进制字符串';
            }
        },

        // HTML 实体编码
        htmlEntityEncode: function(str) {
            try {
                return str.replace(/[\u00A0-\u9999<>\&]/g, function(i) {
                    return '&#' + i.charCodeAt(0) + ';';
                });
            } catch(e) {
                return '编码失败: ' + e.message;
            }
        },

        // HTML 实体解码
        htmlEntityDecode: function(str) {
            try {
                var textarea = document.createElement('textarea');
                textarea.innerHTML = str;
                return textarea.value;
            } catch(e) {
                return '解码失败: 输入不是有效的HTML实体';
            }
        },

        // Unicode 编码 (\uXXXX 格式)
        unicodeEncode: function(str) {
            try {
                return str.split('').map(function(char) {
                    return '\\u' + char.charCodeAt(0).toString(16).padStart(4, '0');
                }).join('');
            } catch(e) {
                return '编码失败: ' + e.message;
            }
        },

        // Unicode 解码
        unicodeDecode: function(str) {
            try {
                return JSON.parse('"' + str.replace(/\\u/g, '\\u') + '"');
            } catch(e) {
                return '解码失败: 输入不是有效的Unicode编码';
            }
        },

        // ASCII 编码 (显示字符的ASCII值)
        asciiEncode: function(str) {
            try {
                return str.split('').map(function(char) {
                    return char.charCodeAt(0).toString(10);
                }).join(' ');
            } catch(e) {
                return '编码失败: ' + e.message;
            }
        },

        // ASCII 解码
        asciiDecode: function(str) {
            try {
                return str.split(' ').map(function(code) {
                    return String.fromCharCode(parseInt(code, 10));
                }).join('');
            } catch(e) {
                return '解码失败: 输入不是有效的ASCII编码';
            }
        },

        // 二进制编码
        binaryEncode: function(str) {
            try {
                return str.split('').map(function(char) {
                    return char.charCodeAt(0).toString(2).padStart(8, '0');
                }).join(' ');
            } catch(e) {
                return '编码失败: ' + e.message;
            }
        },

        // 二进制解码
        binaryDecode: function(str) {
            try {
                return str.split(' ').map(function(bin) {
                    return String.fromCharCode(parseInt(bin, 2));
                }).join('');
            } catch(e) {
                return '解码失败: 输入不是有效的二进制编码';
            }
        },

        // MD5 编码
        md5Encode: function(str) {
            // 简单的MD5实现
            function md5(string) {
                function rotateLeft(value, shift) {
                    return (value << shift) | (value >>> (32 - shift));
                }
                function addUnsigned(x, y) {
                    var lsw = (x & 0xFFFF) + (y & 0xFFFF);
                    var msw = (x >> 16) + (y >> 16) + (lsw >> 16);
                    return (msw << 16) | (lsw & 0xFFFF);
                }
                function f(x, y, z) { return (x & y) | ((~x) & z); }
                function g(x, y, z) { return (x & z) | (y & (~z)); }
                function h(x, y, z) { return x ^ y ^ z; }
                function i(x, y, z) { return y ^ (x | (~z)); }
                function ff(a, b, c, d, x, s, ac) {
                    a = addUnsigned(a, addUnsigned(addUnsigned(f(b, c, d), x), ac));
                    return addUnsigned(rotateLeft(a, s), b);
                }
                function gg(a, b, c, d, x, s, ac) {
                    a = addUnsigned(a, addUnsigned(addUnsigned(g(b, c, d), x), ac));
                    return addUnsigned(rotateLeft(a, s), b);
                }
                function hh(a, b, c, d, x, s, ac) {
                    a = addUnsigned(a, addUnsigned(addUnsigned(h(b, c, d), x), ac));
                    return addUnsigned(rotateLeft(a, s), b);
                }
                function ii(a, b, c, d, x, s, ac) {
                    a = addUnsigned(a, addUnsigned(addUnsigned(i(b, c, d), x), ac));
                    return addUnsigned(rotateLeft(a, s), b);
                }
                function convertToWordArray(string) {
                    var lWordCount;
                    var lMessageLength = string.length;
                    var lNumberOfWords_temp1 = lMessageLength + 8;
                    var lNumberOfWords_temp2 = (lNumberOfWords_temp1 - (lNumberOfWords_temp1 % 64)) / 64;
                    var lNumberOfWords = (lNumberOfWords_temp2 + 1) * 16;
                    var lWordArray = Array(lNumberOfWords - 1);
                    var lBytePosition = 0;
                    var lByteCount = 0;
                    while (lByteCount < lMessageLength) {
                        lWordCount = (lByteCount - (lByteCount % 4)) / 4;
                        lBytePosition = (lByteCount % 4) * 8;
                        lWordArray[lWordCount] = (lWordArray[lWordCount] | (string.charCodeAt(lByteCount) << lBytePosition));
                        lByteCount++;
                    }
                    lWordCount = (lByteCount - (lByteCount % 4)) / 4;
                    lBytePosition = (lByteCount % 4) * 8;
                    lWordArray[lWordCount] = lWordArray[lWordCount] | (0x80 << lBytePosition);
                    lWordArray[lNumberOfWords - 2] = lMessageLength << 3;
                    lWordArray[lNumberOfWords - 1] = lMessageLength >>> 29;
                    return lWordArray;
                }
                function wordToHex(lValue) {
                    var wordToHexValue = "", wordToHexValue_temp = "", lByte, lCount;
                    for (lCount = 0; lCount <= 3; lCount++) {
                        lByte = (lValue >>> (lCount * 8)) & 255;
                        wordToHexValue_temp = "0" + lByte.toString(16);
                        wordToHexValue = wordToHexValue + wordToHexValue_temp.substr(wordToHexValue_temp.length - 2, 2);
                    }
                    return wordToHexValue;
                }
                var x = Array();
                var k, AA, BB, CC, DD, a, b, c, d;
                var S11 = 7, S12 = 12, S13 = 17, S14 = 22;
                var S21 = 5, S22 = 9, S23 = 14, S24 = 20;
                var S31 = 4, S32 = 11, S33 = 16, S34 = 23;
                var S41 = 6, S42 = 10, S43 = 15, S44 = 21;
                string = unescape(encodeURIComponent(string));
                var x = convertToWordArray(string);
                a = 0x67452301; b = 0xEFCDAB89; c = 0x98BADCFE; d = 0x10325476;
                for (k = 0; k < x.length; k += 16) {
                    AA = a; BB = b; CC = c; DD = d;
                    a = ff(a, b, c, d, x[k + 0], S11, 0xD76AA478);
                    d = ff(d, a, b, c, x[k + 1], S12, 0xE8C7B756);
                    c = ff(c, d, a, b, x[k + 2], S13, 0x242070DB);
                    b = ff(b, c, d, a, x[k + 3], S14, 0xC1BDCEEE);
                    a = ff(a, b, c, d, x[k + 4], S11, 0xF57C0FAF);
                    d = ff(d, a, b, c, x[k + 5], S12, 0x4787C62A);
                    c = ff(c, d, a, b, x[k + 6], S13, 0xA8304613);
                    b = ff(b, c, d, a, x[k + 7], S14, 0xFD469501);
                    a = ff(a, b, c, d, x[k + 8], S11, 0x698098D8);
                    d = ff(d, a, b, c, x[k + 9], S12, 0x8B44F7AF);
                    c = ff(c, d, a, b, x[k + 10], S13, 0xFFFF5BB1);
                    b = ff(b, c, d, a, x[k + 11], S14, 0x895CD7BE);
                    a = ff(a, b, c, d, x[k + 12], S11, 0x6B901122);
                    d = ff(d, a, b, c, x[k + 13], S12, 0xFD987193);
                    c = ff(c, d, a, b, x[k + 14], S13, 0xA679438E);
                    b = ff(b, c, d, a, x[k + 15], S14, 0x49B40821);
                    a = gg(a, b, c, d, x[k + 1], S21, 0xF61E2562);
                    d = gg(d, a, b, c, x[k + 6], S22, 0xC040B340);
                    c = gg(c, d, a, b, x[k + 11], S23, 0x265E5A51);
                    b = gg(b, c, d, a, x[k + 0], S24, 0xE9B6C7AA);
                    a = gg(a, b, c, d, x[k + 5], S21, 0xD62F105D);
                    d = gg(d, a, b, c, x[k + 10], S22, 0x02441453);
                    c = gg(c, d, a, b, x[k + 15], S23, 0xD8A1E681);
                    b = gg(b, c, d, a, x[k + 4], S24, 0xE7D3FBC8);
                    a = gg(a, b, c, d, x[k + 9], S21, 0x21E1CDE6);
                    d = gg(d, a, b, c, x[k + 14], S22, 0xC33707D6);
                    c = gg(c, d, a, b, x[k + 3], S23, 0xF4D50D87);
                    b = gg(b, c, d, a, x[k + 8], S24, 0x455A14ED);
                    a = gg(a, b, c, d, x[k + 13], S21, 0xA9E3E905);
                    d = gg(d, a, b, c, x[k + 2], S22, 0xFCEFA3F8);
                    c = gg(c, d, a, b, x[k + 7], S23, 0x676F02D9);
                    b = gg(b, c, d, a, x[k + 12], S24, 0x8D2A4C8A);
                    a = hh(a, b, c, d, x[k + 5], S31, 0xFFFA3942);
                    d = hh(d, a, b, c, x[k + 8], S32, 0x8771F681);
                    c = hh(c, d, a, b, x[k + 11], S33, 0x6D9D6122);
                    b = hh(b, c, d, a, x[k + 14], S34, 0xFDE5380C);
                    a = hh(a, b, c, d, x[k + 1], S31, 0xA4BEEA44);
                    d = hh(d, a, b, c, x[k + 4], S32, 0x4BDECFA9);
                    c = hh(c, d, a, b, x[k + 7], S33, 0xF6BB4B60);
                    b = hh(b, c, d, a, x[k + 10], S34, 0xBEBFBC70);
                    a = hh(a, b, c, d, x[k + 13], S31, 0x289B7EC6);
                    d = hh(d, a, b, c, x[k + 0], S32, 0xEAA127FA);
                    c = hh(c, d, a, b, x[k + 3], S33, 0xD4EF3085);
                    b = hh(b, c, d, a, x[k + 6], S34, 0x04881D05);
                    a = hh(a, b, c, d, x[k + 9], S31, 0xD9D4D039);
                    d = hh(d, a, b, c, x[k + 12], S32, 0xE6DB99E5);
                    c = hh(c, d, a, b, x[k + 15], S33, 0x1FA27CF8);
                    b = hh(b, c, d, a, x[k + 2], S34, 0xC4AC5665);
                    a = ii(a, b, c, d, x[k + 0], S41, 0xF4292244);
                    d = ii(d, a, b, c, x[k + 7], S42, 0x432AFF97);
                    c = ii(c, d, a, b, x[k + 14], S43, 0xAB9423A7);
                    b = ii(b, c, d, a, x[k + 5], S44, 0xFC93A039);
                    a = ii(a, b, c, d, x[k + 12], S41, 0x655B59C3);
                    d = ii(d, a, b, c, x[k + 3], S42, 0x8F0CCC92);
                    c = ii(c, d, a, b, x[k + 10], S43, 0xFFEFF47D);
                    b = ii(b, c, d, a, x[k + 1], S44, 0x85845DD1);
                    a = ii(a, b, c, d, x[k + 8], S41, 0x6FA87E4F);
                    d = ii(d, a, b, c, x[k + 15], S42, 0xFE2CE6E0);
                    c = ii(c, d, a, b, x[k + 6], S43, 0xA3014314);
                    b = ii(b, c, d, a, x[k + 13], S44, 0x4E0811A1);
                    a = ii(a, b, c, d, x[k + 4], S41, 0xF7537E82);
                    d = ii(d, a, b, c, x[k + 11], S42, 0xBD3AF235);
                    c = ii(c, d, a, b, x[k + 2], S43, 0x2AD7D2BB);
                    b = ii(b, c, d, a, x[k + 9], S44, 0xEB86D391);
                    a = addUnsigned(a, AA);
                    b = addUnsigned(b, BB);
                    c = addUnsigned(c, CC);
                    d = addUnsigned(d, DD);
                }
                return (wordToHex(a) + wordToHex(b) + wordToHex(c) + wordToHex(d)).toLowerCase();
            }
            return md5(str);
        },

        // SHA-1 编码
        sha1Encode: function(str) {
            // 简化的SHA-1实现
            function rotateLeft(n, s) { return (n << s) | (n >>> (32 - s)); }
            function sha1(msg) {
                var K = [0x5A827999, 0x6ED9EBA1, 0x8F1BBCDC, 0xCA62C1D6];
                msg = unescape(encodeURIComponent(msg));
                var ml = msg.length * 8;
                msg += String.fromCharCode(0x80);
                while ((msg.length * 8) % 512 != 448) msg += String.fromCharCode(0x00);
                msg += String.fromCharCode((ml >>> 24) & 0xFF);
                msg += String.fromCharCode((ml >>> 16) & 0xFF);
                msg += String.fromCharCode((ml >>> 8) & 0xFF);
                msg += String.fromCharCode(ml & 0xFF);
                var W = new Array(80);
                var H0 = 0x67452301, H1 = 0xEFCDAB89, H2 = 0x98BADCFE, H3 = 0x10325476, H4 = 0xC3D2E1F0;
                var blocks = [];
                for (var i = 0; i < msg.length; i += 64) {
                    blocks.push(msg.substring(i, i + 64));
                }
                for (var b = 0; b < blocks.length; b++) {
                    for (var j = 0; j < 16; j++) {
                        W[j] = (blocks[b].charCodeAt(j * 4) << 24) |
                               (blocks[b].charCodeAt(j * 4 + 1) << 16) |
                               (blocks[b].charCodeAt(j * 4 + 2) << 8) |
                               (blocks[b].charCodeAt(j * 4 + 3));
                    }
                    for (var j = 16; j < 80; j++) {
                        W[j] = rotateLeft(W[j - 3] ^ W[j - 8] ^ W[j - 14] ^ W[j - 16], 1);
                    }
                    var A = H0, B = H1, C = H2, D = H3, E = H4;
                    for (var j = 0; j < 80; j++) {
                        var temp;
                        if (j < 20) temp = rotateLeft(A, 5) + ((B & C) | ((~B) & D)) + E + K[0] + W[j];
                        else if (j < 40) temp = rotateLeft(A, 5) + (B ^ C ^ D) + E + K[1] + W[j];
                        else if (j < 60) temp = rotateLeft(A, 5) + ((B & C) | (B & D) | (C & D)) + E + K[2] + W[j];
                        else temp = rotateLeft(A, 5) + (B ^ C ^ D) + E + K[3] + W[j];
                        E = D; D = C; C = rotateLeft(B, 30); B = A; A = temp;
                    }
                    H0 = (H0 + A) & 0xFFFFFFFF;
                    H1 = (H1 + B) & 0xFFFFFFFF;
                    H2 = (H2 + C) & 0xFFFFFFFF;
                    H3 = (H3 + D) & 0xFFFFFFFF;
                    H4 = (H4 + E) & 0xFFFFFFFF;
                }
                var hex = '';
                for (var i = 0; i < 5; i++) {
                    var h = [H0, H1, H2, H3, H4][i];
                    hex += ((h >>> 28) & 0xF).toString(16) +
                           ((h >>> 24) & 0xF).toString(16) +
                           ((h >>> 20) & 0xF).toString(16) +
                           ((h >>> 16) & 0xF).toString(16) +
                           ((h >>> 12) & 0xF).toString(16) +
                           ((h >>> 8) & 0xF).toString(16) +
                           ((h >>> 4) & 0xF).toString(16) +
                           (h & 0xF).toString(16);
                }
                return hex;
            }
            return sha1(str);
        }
    };

    // 编码解码配置
    var encoders = [
        { name: 'Base64', encode: 'base64Encode', decode: 'base64Decode', icon: '🔐' },
        { name: 'URL', encode: 'urlEncode', decode: 'urlDecode', icon: '🔗' },
        { name: 'Hex', encode: 'hexEncode', decode: 'hexDecode', icon: '🔢' },
        { name: 'HTML实体', encode: 'htmlEntityEncode', decode: 'htmlEntityDecode', icon: '🏷️' },
        { name: 'Unicode', encode: 'unicodeEncode', decode: 'unicodeDecode', icon: '🌐' },
        { name: 'ASCII', encode: 'asciiEncode', decode: 'asciiDecode', icon: '📝' },
        { name: '二进制', encode: 'binaryEncode', decode: 'binaryDecode', icon: '💻' },
        { name: 'MD5', encode: 'md5Encode', decode: null, icon: '🔒' },
        { name: 'SHA-1', encode: 'sha1Encode', decode: null, icon: '🔑' }
    ];

    // 渲染编码解码界面
    EncodeDecodeModule.prototype.render = function(data, container) {
        container.html(`
            <div class="card">
                <div class="card-header">
                    <div class="encode-header">
                        <h3>🔧 编码解码工具</h3>
                        <p class="encode-desc">支持多种编码格式的快速转换</p>
                    </div>
                </div>

                <div class="encode-container">
                    <!-- 编码类型选择器 -->
                    <div class="encode-type-selector">
                        <div class="encode-type-title">选择编码类型</div>
                        <div class="encode-type-grid">
                            ${encoders.map((enc, index) => `
                                <div class="encode-type-item ${index === 0 ? 'active' : ''}" data-type="${index}">
                                    <div class="encode-type-icon">${enc.icon}</div>
                                    <div class="encode-type-name">${enc.name}</div>
                                </div>
                            `).join('')}
                        </div>
                    </div>

                    <!-- 输入输出区域 -->
                    <div class="encode-workspace">
                        <div class="encode-input-section">
                            <div class="encode-section-header">
                                <span class="encode-section-icon">📥</span>
                                <span class="encode-section-title">输入</span>
                                <button class="encode-clear-btn" id="clearInput">清空</button>
                            </div>
                            <textarea id="encodeInput" class="encode-textarea" placeholder="请输入需要编码或解码的内容..."></textarea>
                            <div class="encode-stats">
                                <span id="inputStats">字符数: 0</span>
                            </div>
                        </div>

                        <div class="encode-actions">
                            <button class="encode-action-btn encode-btn" id="encodeBtn">
                                <span class="encode-action-icon">⬇️</span>
                                <span>编码</span>
                            </button>
                            <button class="encode-action-btn decode-btn" id="decodeBtn">
                                <span class="encode-action-icon">⬆️</span>
                                <span>解码</span>
                            </button>
                        </div>

                        <div class="encode-output-section">
                            <div class="encode-section-header">
                                <span class="encode-section-icon">📤</span>
                                <span class="encode-section-title">输出</span>
                                <div class="encode-output-actions">
                                    <button class="encode-copy-btn" id="copyOutput">复制</button>
                                </div>
                            </div>
                            <textarea id="encodeOutput" class="encode-textarea" readonly placeholder="编码/解码结果将显示在这里..."></textarea>
                            <div class="encode-stats">
                                <span id="outputStats">字符数: 0</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `);

        this.currentEncoder = encoders[0];
        this.bindEvents();
    };

    // 绑定事件
    EncodeDecodeModule.prototype.bindEvents = function() {
        var self = this;

        // 编码类型选择
        $('.encode-type-item').on('click', function() {
            $('.encode-type-item').removeClass('active');
            $(this).addClass('active');
            var index = $(this).data('type');
            self.currentEncoder = encoders[index];

            // 更新按钮状态
            if (!self.currentEncoder.decode) {
                $('#decodeBtn').prop('disabled', true).addClass('disabled');
            } else {
                $('#decodeBtn').prop('disabled', false).removeClass('disabled');
            }
        });

        // 编码按钮
        $('#encodeBtn').on('click', function() {
            var input = $('#encodeInput').val();
            if (!input) {
                self.showError('请输入要编码的内容');
                return;
            }
            var result = Encoder[self.currentEncoder.encode](input);
            self.setOutput(result, false);
        });

        // 解码按钮
        $('#decodeBtn').on('click', function() {
            var input = $('#encodeInput').val();
            if (!input) {
                self.showError('请输入要解码的内容');
                return;
            }
            if (!self.currentEncoder.decode) {
                self.showError('当前编码类型不支持解码');
                return;
            }
            var result = Encoder[self.currentEncoder.decode](input);
            self.setOutput(result, result.startsWith('解码失败'));
        });

        // 清空输入
        $('#clearInput').on('click', function() {
            $('#encodeInput').val('');
            $('#encodeOutput').val('');
            self.updateStats();
        });

        // 复制输出
        $('#copyOutput').on('click', function() {
            var output = $('#encodeOutput').val();
            if (!output) return;

            if (navigator.clipboard) {
                navigator.clipboard.writeText(output).then(function() {
                    self.showSuccess('已复制到剪贴板');
                }).catch(function() {
                    self.fallbackCopy(output);
                });
            } else {
                self.fallbackCopy(output);
            }
        });

        // 实时统计字符数
        $('#encodeInput').on('input', function() {
            self.updateStats();
        });

        // 支持快捷键
        $(document).on('keydown', function(e) {
            if (e.ctrlKey || e.metaKey) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    $('#encodeBtn').click();
                }
            }
        });
    };

    // 设置输出
    EncodeDecodeModule.prototype.setOutput = function(result, isError) {
        $('#encodeOutput').val(result);
        if (isError) {
            $('#encodeOutput').addClass('error');
        } else {
            $('#encodeOutput').removeClass('error');
        }
        this.updateStats();
    };

    // 更新统计信息
    EncodeDecodeModule.prototype.updateStats = function() {
        var inputLength = $('#encodeInput').val().length;
        var outputLength = $('#encodeOutput').val().length;
        $('#inputStats').text('字符数: ' + inputLength);
        $('#outputStats').text('字符数: ' + outputLength);
    };

    // 显示错误
    EncodeDecodeModule.prototype.showError = function(message) {
        this.setOutput('❌ ' + message, true);
    };

    // 显示成功
    EncodeDecodeModule.prototype.showSuccess = function(message) {
        var btn = $('#copyOutput');
        var originalText = btn.text();
        btn.text('✓ ' + message);
        btn.addClass('success');
        setTimeout(function() {
            btn.text(originalText);
            btn.removeClass('success');
        }, 2000);
    };

    // 备用复制方法
    EncodeDecodeModule.prototype.fallbackCopy = function(text) {
        var textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        try {
            document.execCommand('copy');
            this.showSuccess('已复制到剪贴板');
        } catch(e) {
            this.showError('复制失败');
        }
        document.body.removeChild(textarea);
    };

    // 导出到全局
    window.EncodeDecodeModule = EncodeDecodeModule;
})();
