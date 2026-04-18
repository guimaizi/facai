# coding: utf-8
"""
子域名数据库管理
@Time :    3/15/2026
@Author:  facai
@File: subdomain_database.py
@Software: VSCode
"""
from .mongodb_handler import MongoDBHandler
import time


class SubdomainDatabase:
    def __init__(self, project_name=None):
        self.db_handler = MongoDBHandler()
        self.project_name = project_name
        # 使用 project_{name}_domain 表名（参考数据库结构文档）
        self.collection_name = f"project_{project_name}_domain" if project_name else None

    def get_all_subdomains(self, page=1, page_size=100, sort_by=None, sort_order=1, search_keyword=''):
        """获取所有子域名数据，支持分页、排序和搜索"""
        if not self.collection_name:
            return []

        # 构建查询条件
        query = {}
        if search_keyword and search_keyword.strip():
            query = {
                '$or': [
                    {'subdomain': {'$regex': search_keyword, '$options': 'i'}},
                    {'domain': {'$regex': search_keyword, '$options': 'i'}}
                ]
            }

        projection = None

        # 计算跳过的记录数
        skip = (page - 1) * page_size

        # 查询数据
        subdomains = self.db_handler.find(self.collection_name, query, projection)

        # 排序
        if sort_by:
            if sort_by == 'time':
                # 按时间字符串排序
                subdomains.sort(key=lambda x: x.get('time', ''), reverse=(sort_order == -1))
            else:
                # 按其他字段排序
                subdomains.sort(key=lambda x: x.get(sort_by, ''), reverse=(sort_order == -1))
        else:
            # 默认按时间降序排序
            subdomains.sort(key=lambda x: x.get('time', ''), reverse=True)

        # 分页
        paginated_subdomains = subdomains[skip:skip + page_size]

        return paginated_subdomains

    def get_subdomain_by_id(self, subdomain_id):
        """根据ID获取子域名数据"""
        if not self.collection_name:
            return None
        return self.db_handler.find_one(self.collection_name, {'_id': subdomain_id})

    def add_subdomain(self, subdomain_data):
        """添加子域名数据"""
        if not self.collection_name:
            return None

        # 根据数据库结构文档，确保字段名称正确
        normalized_data = {
            'subdomain': subdomain_data.get('subdomain'),
            'domain': subdomain_data.get('domain', ''),
            'time': subdomain_data.get('time', time.strftime('%Y-%m-%d %H:%M:%S')),
            'port_list': subdomain_data.get('port_list', []),
            'dns_data': subdomain_data.get('dns_data', []),
            'status': subdomain_data.get('status', 0)
        }

        # 如果提供了ip_list，转换为dns_data格式
        if 'ip_list' in subdomain_data and subdomain_data['ip_list']:
            if not normalized_data['dns_data']:
                normalized_data['dns_data'] = []
            for ip in subdomain_data['ip_list']:
                normalized_data['dns_data'].append({'A': ip})

        # 检查是否已存在相同的子域名
        existing = self.db_handler.find_one(self.collection_name, {'subdomain': normalized_data.get('subdomain')})
        if existing:
            # 更新现有记录
            return self.db_handler.update_one(
                self.collection_name,
                {'subdomain': normalized_data.get('subdomain')},
                {'$set': normalized_data}
            )
        else:
            # 插入新记录
            return self.db_handler.insert_one(self.collection_name, normalized_data)

    def delete_subdomain(self, subdomain_id):
        """删除子域名数据"""
        if not self.collection_name:
            return None
        return self.db_handler.delete_one(self.collection_name, {'_id': subdomain_id})

    def delete_all_subdomains(self):
        """删除所有子域名数据"""
        if not self.collection_name:
            return False
        return self.db_handler.delete_many(self.collection_name, {})

    def count_subdomains(self):
        """获取子域名数据总数"""
        if not self.collection_name:
            return 0
        query = {}
        return self.db_handler.count_documents(self.collection_name, query)

    def update_subdomain(self, subdomain_id, update_data):
        """更新子域名数据"""
        if not self.collection_name:
            return None

        update_data['time_update'] = time.strftime('%Y-%m-%d %H:%M:%S')
        return self.db_handler.update_one(
            self.collection_name,
            {'_id': subdomain_id},
            {'$set': update_data}
        )

    def search_subdomains(self, keyword):
        """搜索子域名"""
        if not self.collection_name:
            return []

        query = {
            '$or': [
                {'subdomain': {'$regex': keyword, '$options': 'i'}},
                {'domain': {'$regex': keyword, '$options': 'i'}},
            ]
        }

        subdomains = self.db_handler.find(self.collection_name, query)
        return subdomains

    def search_subdomains_count(self, keyword):
        """搜索子域名的数量"""
        if not self.collection_name:
            return 0

        query = {
            '$or': [
                {'subdomain': {'$regex': keyword, '$options': 'i'}},
                {'domain': {'$regex': keyword, '$options': 'i'}},
            ]
        }

        return self.db_handler.count_documents(self.collection_name, query)
