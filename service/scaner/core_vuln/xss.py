# coding: utf-8
"""
XSS基础检测模块（无害化）
@Time :    4/5/2026
@Author:  facai
@File: xss.py
@Software: VSCode

功能说明：
1. 统一接口格式：接受HTTP请求JSON和参数列表JSON
2. 仅使用基础payload进行回显检测
3. 不包含任何恶意XSS代码
4. 无害化检测，不触发WAF
5. 使用 ParamHandler.set_param_value 修改参数（默认追加模式）

接口格式：
HTTP请求：
{
   "url": "http://127.0.0.1/test631?name=1",
   "method": "POST",
   "headers": {
       "User-Agent": "Mozilla/5.0"
   },
   "body": "aa=1&bb=a"
}

参数列表：
[
  {"param_name":"name", "param_value":"1", "param_type":"int", "position":"GET"},
  {"param_name":"aa", "param_value":"1", "param_type":"int", "position":"POST"},
  {"param_name":"bb", "param_value":"a", "param_type":"string", "position":"POST"}
]
"""

import re
import requests
from service.scaner.param_handler import ParamHandler
from service.libs.replay_request import send_http_request


class XSSScanner:
    """XSS扫描器（无害化检测）"""
    
    def __init__(self, timeout=5):
        self.timeout = timeout
        self.param_handler = ParamHandler()
        
        # 仅使用无害的基础payload
        self.payloads = [
            "test631'\">",  # 基础回显检测
        ]
        
        # XSS回显检测特征（仅检测回显，不执行）
        self.detection_patterns = [
            (r"test631['\"]&gt;", "HTML实体编码回显"),
            (r"test631['\"]>", "原始回显（高危）"),
            (r"test631['\"]", "部分回显"),
        ]
    
    def scan(self, request_data, params_list=None, send_request_func=None):
        """
        XSS基础检测（无害化）
        
        Args:
            request_data: dict - HTTP请求数据
                {
                    "url": "http://127.0.0.1/test?name=1",
                    "method": "POST",
                    "headers": {"User-Agent": "Mozilla/5.0"},
                    "body": "aa=1&bb=a"
                }
            
            params_list: list - 参数列表（可选，如果为None则自动提取）
                [
                    {"param_name":"name", "param_value":"1", "param_type":"int", "position":"GET"},
                    {"param_name":"aa", "param_value":"1", "param_type":"int", "position":"POST"}
                ]
            
            send_request_func: function - 自定义发送请求函数（可选，如果为None则使用默认）
        
        Returns:
            list - 发现的漏洞列表
                [
                    {
                        'vuln_type': 'XSS疑似漏洞',
                        'xss_type': '反射型XSS（需人工验证）',
                        'param': 'name',
                        'position': 'GET',
                        'payload': 'test631\'">',
                        'evidence': '检测到原始回显（高危）',
                        'risk': '低风险-仅检测到回显，需人工验证是否可利用'
                    }
                ]
        """
        vulnerabilities = []
        
        # XSS 只扫描 GET 请求
        method = request_data.get('method', 'GET').upper()
        if method != 'GET':
            return vulnerabilities
        
        # 如果没有提供参数列表，自动提取参数
        if params_list is None:
            params_list = self.param_handler.callback_list_param(request_data)
        
        # 如果没有提供发送请求函数，使用默认
        if send_request_func is None:
            send_request_func = lambda req: send_http_request(req, timeout=self.timeout)
        
        # 遍历所有参数进行检测
        for param_info in params_list:
            for payload in self.payloads:
                try:
                    # 使用 ParamHandler.set_param_value 修改参数（追加模式）
                    test_request = self.param_handler.set_param_value(
                        request_data, 
                        param_info['param_name'], 
                        payload, 
                        mode=0  # mode=0 追加（默认）
                    )
                    
                    response = send_request_func(test_request)
                    
                    if response:
                        # 检测payload是否被回显
                        response_text = response.text if hasattr(response, 'text') else str(response)
                        
                        for pattern, desc in self.detection_patterns:
                            if re.search(pattern, response_text, re.IGNORECASE):
                                from service.Class_Core_Function import Class_Core_Function
                                core_func = Class_Core_Function()
                                
                                url = request_data.get('url', '')
                                vulnerabilities.append({
                                    'url': url,
                                    'method': request_data.get('method'),
                                    'headers': request_data.get('headers', {}),
                                    'body': request_data.get('body', ''),
                                    'website': core_func.callback_split_url(url, 0),
                                    'subdomain': core_func.callback_split_url(url, 2),
                                    'vuln_type': 'xss',
                                    'vuln_type_detail': 'xss-reflect',
                                    'level': 'medium',
                                    'paramname': param_info['param_name'],
                                    'payload': payload,
                                    'evidence': f'检测到{desc}，参数值被回显到响应中',
                                    'description': '反射型XSS疑似漏洞（需人工验证是否可利用）',
                                    'time': core_func.callback_time(0)
                                })
                                break  # 发现漏洞后跳出payload循环
                except Exception as e:
                    continue
        
        return vulnerabilities



if __name__ == "__main__":
    # 测试代码
    scanner = XSSScanner()
    
    # 测试HTTP请求
    test_request = {
        "url": "http://127.0.0.1/test631?name=test",
        "method": "POST",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        },
        "body": "aa=1&bb=a"
    }
    
    print("XSS扫描器测试")
    print(f"HTTP请求: {test_request}")
    print("\n开始扫描...")
    
    # 执行扫描（自动提取参数）
    results = scanner.scan(test_request)
    
    print(f"\n发现 {len(results)} 个漏洞:")
    for vuln in results:
        print(f"  [{vuln['vuln_type']}] {vuln['param']} - {vuln['payload']}")
        print(f"    位置: {vuln['position']}")
        print(f"    证据: {vuln['evidence']}")
