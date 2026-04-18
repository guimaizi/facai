# coding: utf-8
from flask import Blueprint, request, jsonify
import json
import time
from service.libs.replay_request import replay_http_request
from service.libs.port_scan import port_scan

tools_api = Blueprint('tools_api', __name__)

@tools_api.route('/api/tools/replay', methods=['POST'])
def tools_replay():
    """
    HTTP请求重放API
    接收JSON格式的请求数据，执行HTTP请求并返回响应
    """
    try:
        # 获取请求数据
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': '请求数据不能为空'
            }), 400
        
        # 验证必填字段
        url = data.get('url')
        method = data.get('method', 'GET').upper()
        headers = data.get('headers', {})
        body = data.get('body', '')
        
        if not url:
            return jsonify({
                'error': 'URL不能为空'
            }), 400
        
        # 验证URL格式
        if not url.startswith('http://') and not url.startswith('https://'):
            return jsonify({
                'error': 'URL必须以http://或https://开头'
            }), 400
        
        # 兼容处理：如果body是字典/列表对象，转换为JSON字符串
        if body and isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False)
        
        # 执行HTTP请求
        start_time = time.time()
        response = replay_http_request(
            url=url,
            method=method,
            headers=headers,
            body=body
        )
        end_time = time.time()
        
        # 计算响应时间（毫秒）
        response_time = int((end_time - start_time) * 1000)
        
        # 构建响应数据
        result = {
            'status_code': response.status_code,
            'response_time': f'{response_time}ms',
            'response_headers': dict(response.headers),
            'response_body': response.text
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'error': f'请求失败: {str(e)}'
        }), 500


@tools_api.route('/api/tools/port-scan', methods=['POST'])
def tools_port_scan():
    """
    端口扫描API
    使用nmap进行端口扫描
    参数: ip (目标IP), args (nmap参数), ports (端口范围)
    """
    try:
        # 获取请求数据
        ip = request.form.get('ip') or request.get_json().get('ip') if request.is_json else request.form.get('ip')
        args = request.form.get('args') or request.get_json().get('args') if request.is_json else request.form.get('args')
        ports = request.form.get('ports') or request.get_json().get('ports') if request.is_json else request.form.get('ports')
        
        # 如果是JSON格式请求
        if request.is_json:
            data = request.get_json()
            ip = data.get('ip')
            args = data.get('args', '')
            ports = data.get('ports', '')
        
        # 验证必填字段
        if not ip:
            return jsonify({
                'error': '请输入目标IP地址或域名'
            }), 400
        
        if not ports:
            return jsonify({
                'error': '请输入端口范围'
            }), 400
        
        # 执行端口扫描
        result = port_scan(
            target=ip,
            args=args,
            ports=ports
        )
        
        if result.get('error'):
            return jsonify(result), 400
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'error': f'扫描失败: {str(e)}'
        }), 500

