# coding: utf-8
"""
参数名爆破模块
@Time :    4/5/2026
@Author:  facai
@File: fuzz_paramname.py
@Software: VSCode

功能说明：
1. 统一接口格式：接受HTTP请求JSON和参数列表JSON
2. 爆破常见参数名，判断参数是否存在
3. 使用 ParamHandler.set_param_value 修改参数
"""

import requests
from service.scaner.param_handler import ParamHandler


class ParamNameFuzzer:
    """参数名爆破器"""
    
    def __init__(self, timeout=5):
        self.timeout = timeout
        self.param_handler = ParamHandler()
        
        # 常见参数名字典
        self.common_params = [
            'id', 'user', 'username', 'name', 'email', 'password', 'pass', 'pwd',
            'uid', 'userid', 'user_id', 'account', 'admin', 'token', 'key', 'apikey',
            'api_key', 'access_token', 'auth', 'authorization', 'session', 'sid',
            'session_id', 'file', 'path', 'url', 'link', 'src', 'source', 'dest',
            'target', 'redirect', 'callback', 'return', 'next', 'go', 'goto',
            'page', 'p', 'limit', 'offset', 'count', 'size', 'per_page', 'page_size',
            'sort', 'order', 'by', 'field', 'column', 'query', 'q', 'search', 'keyword',
            'kw', 'filter', 'type', 'category', 'tag', 'status', 'state', 'action',
            'method', 'func', 'function', 'do', 'task', 'job', 'process', 'step',
            'data', 'content', 'text', 'message', 'msg', 'body', 'payload', 'input',
            'value', 'val', 'v', 'param', 'params', 'arg', 'args', 'option', 'options',
            'config', 'conf', 'settings', 'setting', 'format', 'mode', 'style',
            'lang', 'language', 'locale', 'region', 'country', 'currency', 'money',
            'price', 'amount', 'total', 'sum', 'count', 'num', 'number', 'index',
            'idx', 'pos', 'position', 'start', 'end', 'from', 'to', 'begin', 'finish',
            'width', 'height', 'w', 'h', 'x', 'y', 'z', 'lat', 'lon', 'latitude', 'longitude',
            'date', 'time', 'timestamp', 'created', 'updated', 'deleted', 'modified',
            'year', 'month', 'day', 'hour', 'minute', 'second', 'week', 'weekday',
        ]
    
    def scan(self, request_data, params_list=None, send_request_func=None, positions=None):
        """
        参数名爆破
        
        Args:
            request_data: dict - HTTP请求数据
                {
                    "url": "http://127.0.0.1/test?name=1",
                    "method": "POST",
                    "headers": {"User-Agent": "Mozilla/5.0"},
                    "body": "aa=1&bb=a"
                }
            
            params_list: list - 参数列表（可选，如果为None则自动提取）
            
            send_request_func: function - 自定义发送请求函数（可选）
            
            positions: list - 要爆破的位置（可选，如 ['GET', 'POST']）
        
        Returns:
            list - 发现的参数列表
                [
                    {
                        'param_name': 'id',
                        'position': 'GET',
                        'evidence': '参数存在性检测通过',
                        'response_diff': '响应长度差异: +123字节'
                    }
                ]
        """
        discovered_params = []
        
        # 如果没有提供参数列表，自动提取参数
        if params_list is None:
            params_list = self.param_handler.callback_list_param(request_data)
        
        # 如果没有提供发送请求函数，使用默认
        if send_request_func is None:
            send_request_func = self._send_request
        
        # 确定要爆破的位置
        if positions is None:
            positions = ['GET', 'POST']
        
        # 获取基准响应
        baseline_response = send_request_func(request_data)
        baseline_length = len(baseline_response.text) if baseline_response else 0
        
        # 遍历所有常见参数名
        for param_name in self.common_params:
            # 检查参数是否已存在
            exists = any(p['param_name'] == param_name for p in params_list)
            if exists:
                continue
            
            # 在不同位置测试参数
            for position in positions:
                try:
                    # 添加新参数
                    test_request = self._add_param(request_data, param_name, 'test', position)
                    
                    response = send_request_func(test_request)
                    
                    if response:
                        # 分析响应差异
                        response_length = len(response.text)
                        length_diff = response_length - baseline_length
                        
                        # 如果响应长度有明显差异，可能存在该参数
                        if abs(length_diff) > 50:  # 阈值：50字节
                            discovered_params.append({
                                'param_name': param_name,
                                'position': position,
                                'evidence': '参数存在性检测通过',
                                'response_diff': f'响应长度差异: {length_diff:+d}字节'
                            })
                
                except Exception as e:
                    continue
        
        return discovered_params
    
    def _add_param(self, request_data, param_name, param_value, position):
        """添加新参数到请求中"""
        test_request = request_data.copy()
        test_request['headers'] = request_data.get('headers', {}).copy()
        
        if position == 'GET':
            url = test_request.get('url', '')
            if '?' in url:
                test_request['url'] = f"{url}&{param_name}={param_value}"
            else:
                test_request['url'] = f"{url}?{param_name}={param_value}"
        
        elif position == 'POST':
            body = test_request.get('body', '')
            if body:
                test_request['body'] = f"{body}&{param_name}={param_value}"
            else:
                test_request['body'] = f"{param_name}={param_value}"
        
        return test_request
    
    def _send_request(self, request_data):
        """默认的发送请求函数"""
        try:
            url = request_data.get('url', '')
            method = request_data.get('method', 'GET').upper()
            headers = request_data.get('headers', {})
            body = request_data.get('body')
            
            # 支持多种HTTP方法传递body
            methods_with_body = ['POST', 'PUT', 'PATCH', 'DELETE']
            
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                data=body if method in methods_with_body else None,
                timeout=self.timeout,
                allow_redirects=False,
                verify=False
            )
            
            return response
        
        except Exception:
            return None


if __name__ == "__main__":
    # 测试代码
    fuzzer = ParamNameFuzzer()
    
    # 测试HTTP请求
    test_request = {
        "url": "http://127.0.0.1/test631",
        "method": "GET",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    }
    
    print("参数名爆破测试")
    print(f"HTTP请求: {test_request}")
    print("\n开始爆破...")
    
    # 执行爆破（只测试GET参数）
    results = fuzzer.scan(test_request, positions=['GET'])
    
    print(f"\n发现 {len(results)} 个潜在参数:")
    for param in results:
        print(f"  [{param['position']}] {param['param_name']}")
        print(f"    证据: {param['evidence']}")
        print(f"    {param['response_diff']}")
