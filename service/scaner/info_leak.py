# coding: utf-8
"""
信息泄露扫描模块（密钥泄露、配置文件、源码泄露）
@Time :    3/27/2026
@Author:  facai
@File: info_leak.py
"""

import re
from service.Class_Core_Function import Class_Core_Function


class InfoLeakScanner:
    """信息泄露扫描器"""
    
    def __init__(self):
        # 泄露特征
        self.leak_patterns = {
            # 云服务密钥
            'AWS Access Key': r'AKIA[0-9A-Z]{16}',
            'AWS Secret Key': r'(?i)aws(.{0,20})?["\'][0-9a-zA-Z/+=]{40}["\']',
            'Aliyun AccessKey': r'LTAI[0-9a-zA-Z]{12,20}',
            'Tencent SecretId': r'AKID[0-9a-zA-Z]{32}',
            'Tencent SecretKey': r'(?i)secret[_-]?key["\']?\s*[:=]\s*["\']?[0-9a-zA-Z]{32,}',
            
            # JWT
            'JWT Token': r'eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*',
            
            # 数据库
            'Database Password': r'(?i)(password|passwd|pwd)\s*[=:]\s*["\']([^\s]+)["\']',
            'MySQL Connection': r'(?i)mysql://[^:]+:[^@]+@[^/]+',
            'Redis Connection': r'(?i)redis://[^:]*:[^@]+@[^/]+',
            
            # API密钥
            'API Key': r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\']([0-9a-zA-Z\-_]{20,})["\']',
            'Secret Key': r'(?i)secret[_-]?key\s*[=:]\s*["\']([0-9a-zA-Z\-_]{20,})["\']',
            
            # GitHub Token
            'GitHub Token': r'ghp_[0-9a-zA-Z]{36}',
            
            # 私钥
            'Private Key': r'-----BEGIN (RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----',
        }
        
        # 敏感文件
        self.sensitive_files = {
            '.git泄露': r'/.git/(config|HEAD|index)',
            '.env泄露': r'\.env',
            '配置备份': r'\.(bak|backup|old|swp|save)$',
            'DS_Store': r'\.DS_Store',
        }
    
    def scan_response(self, response_text, url):
        """
        扫描响应内容中的信息泄露
        :param response_text: 响应内容
        :param url: 请求URL
        :return: list - 泄露信息列表
        """
        leaks = []
        
        # 1. 密钥泄露检测
        for leak_type, pattern in self.leak_patterns.items():
            matches = re.findall(pattern, response_text)
            if matches:
                leaks.append({
                    'url': url,
                    'method': 'GET',
                    'headers': {},
                    'body': '',
                    'website': '',
                    'subdomain': '',
                    'vuln_type': 'leak-info',
                    'vuln_type_detail': leak_type,
                    'level': 'high',
                    'paramname': '',
                    'payload': '',
                    'evidence': str(matches[0])[:100],
                    'description': f'检测到{leak_type}泄露',
                    'time': time.strftime('%Y-%m-%d %H:%M:%S')
                })
        
        # 2. 敏感文件检测
        for file_type, pattern in self.sensitive_files.items():
            if re.search(pattern, url, re.IGNORECASE):
                leaks.append({
                    'url': url,
                    'method': 'GET',
                    'headers': {},
                    'body': '',
                    'website': '',
                    'subdomain': '',
                    'vuln_type': 'leak-info',
                    'vuln_type_detail': file_type,
                    'level': 'medium',
                    'paramname': '',
                    'payload': '',
                    'evidence': f'检测到{file_type}',
                    'description': f'{file_type}泄露',
                    'time': time.strftime('%Y-%m-%d %H:%M:%S')
                })
        
        return leaks
    
    def scan(self, request_data, param_info, send_request_func):
        """
        参数级信息泄露扫描（暂时不实现）
        信息泄露主要在响应级别检测
        """
        return None
