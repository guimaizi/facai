# coding: utf-8
"""
漏洞盲打日志数据库
用于存储需要DNSLog验证的漏洞测试请求
"""

import time
from .mongodb_handler import MongoDBHandler


class VulnLogDatabase:
    """漏洞盲打日志数据库"""
    
    def __init__(self, project_name):
        """
        初始化
        :param project_name: 项目名称
        """
        self.project_name = project_name
        self.db_handler = MongoDBHandler()
        self.collection_name = f"project_{project_name}_vuln_log"
    
    def add_vuln_log(self, vuln_hash, request_data, param_name, vuln_type):
        """
        添加盲打日志
        
        :param vuln_hash: DNSLog标识符（如 rce123456, ssrf123456）
        :param request_data: HTTP请求数据
            {
                "url": "http://example.com/test?param=value",
                "method": "POST",
                "headers": {...},
                "body": "..."
            }
        :param param_name: 测试的参数名
        :param vuln_type: 漏洞类型（rce/ssrf）
        :return: 插入结果
        """
        log_data = {
            'vuln_hash': vuln_hash,
            'request': request_data,
            'param_name': param_name,
            'vuln_type': vuln_type,
            'time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'status': 0  # 0=未验证, 1=已验证
        }
        
        return self.db_handler.insert_one(self.collection_name, log_data)
    
    def get_log_by_hash(self, vuln_hash):
        """
        根据hash获取日志
        :param vuln_hash: DNSLog标识符
        :return: 日志记录
        """
        return self.db_handler.find_one(
            self.collection_name, 
            {'vuln_hash': vuln_hash}
        )
    
    def verify_log(self, vuln_hash):
        """
        验证日志（标记为已验证）
        :param vuln_hash: DNSLog标识符
        :return: 更新结果
        """
        return self.db_handler.update_one(
            self.collection_name,
            {'vuln_hash': vuln_hash},
            {'status': 1}
        )
    
    def get_unverified_logs(self):
        """
        获取所有未验证的日志
        :return: 日志列表
        """
        return self.db_handler.find(
            self.collection_name,
            {'status': 0}
        )
    
    def get_all_logs(self, limit=100):
        """
        获取所有日志
        :param limit: 返回数量限制
        :return: 日志列表
        """
        return self.db_handler.find(
            self.collection_name,
            {},
            limit=limit,
            sort=[('time', -1)]
        )
    
    def delete_log(self, vuln_hash):
        """
        删除日志
        :param vuln_hash: DNSLog标识符
        :return: 删除结果
        """
        return self.db_handler.delete_one(
            self.collection_name,
            {'vuln_hash': vuln_hash}
        )
    
    def clear_all_logs(self):
        """
        清空所有日志
        :return: 删除结果
        """
        return self.db_handler.delete_many(
            self.collection_name,
            {}
        )
    
    def count_logs(self, status=None):
        """
        统计日志数量
        :param status: 状态过滤（None表示全部）
        :return: 数量
        """
        query = {}
        if status is not None:
            query['status'] = status
        
        return self.db_handler.count_documents(self.collection_name, query)
