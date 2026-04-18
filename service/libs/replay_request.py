# coding: utf-8

import requests
import json
import warnings

# 禁用SSL警告
warnings.filterwarnings('ignore', message='Unverified HTTPS request')


def send_http_request(request_data, timeout=5, allow_redirects=False):
    """
    发送HTTP请求（统一接口，用于扫描模块）
    
    Args:
        request_data (dict): HTTP请求数据
            {
                "url": "http://127.0.0.1/test?name=1",
                "method": "POST",
                "headers": {"User-Agent": "Mozilla/5.0"},
                "body": "aa=1&bb=a"
            }
        timeout (int): 超时时间（秒）
        allow_redirects (bool): 是否允许重定向
    
    Returns:
        requests.Response or None: HTTP响应对象，失败返回None
    """
    try:
        url = request_data.get('url', '')
        method = request_data.get('method', 'GET').upper()
        headers = request_data.get('headers', {})
        body = request_data.get('body')
        
        # 支持多种HTTP方法传递body
        methods_with_body = ['POST', 'PUT', 'PATCH', 'DELETE']
        
        # 智能处理body参数
        request_kwargs = {
            'method': method,
            'url': url,
            'headers': headers,
            'timeout': timeout,
            'allow_redirects': allow_redirects,
            'verify': False
        }
        
        if method in methods_with_body and body:
            if isinstance(body, (dict, list)):
                # 字典/列表 -> 使用json参数发送
                request_kwargs['json'] = body
            else:
                # 字符串或其他类型 -> 使用data参数
                request_kwargs['data'] = body
        
        response = requests.request(**request_kwargs)
        
        return response
    
    except Exception as e:
        return None


def replay_http_request(url, method='GET', headers=None, body=''):
    """
    执行HTTP请求重放
    
    Args:
        url (str): 请求URL
        method (str): HTTP方法 (GET, POST, PUT, DELETE, etc.)
        headers (dict): 请求头
        body (str): 请求体
    
    Returns:
        requests.Response: HTTP响应对象
    """
    if headers is None:
        headers = {}
    
    # 设置默认请求头
    default_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
    }
    
    # 合并请求头（用户提供的请求头优先）
    headers = {**default_headers, **headers}
    
    # 移除可能导致问题的请求头
    headers.pop('Host', None)
    headers.pop('Content-Length', None)
    
    # 准备请求参数
    request_kwargs = {
        'url': url,
        'method': method,
        'headers': headers,
        'timeout': 30,
        'verify': False,  # 禁用SSL验证
        'allow_redirects': True,
    }
    
    # 根据请求方法设置请求体
    if method.upper() in ['POST', 'PUT', 'PATCH']:
        # 尝试判断Content-Type
        content_type = headers.get('Content-Type', headers.get('content-type', ''))
        
        if 'application/json' in content_type:
            # JSON格式
            request_kwargs['json'] = body
        elif 'application/x-www-form-urlencoded' in content_type:
            # 表单格式
            request_kwargs['data'] = body
        else:
            # 其他格式，使用data
            request_kwargs['data'] = body
    
    # 发送请求
    try:
        response = requests.request(**request_kwargs)
        return response
    except requests.exceptions.RequestException as e:
        raise Exception(f'请求执行失败: {str(e)}')
