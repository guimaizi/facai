# coding: utf-8
"""
漏洞数据库操作
@Time :    4/6/2026
@Author:  facai
@File: vuln_database.py
@Software: VSCode
"""
from .mongodb_handler import MongoDBHandler
from service.Class_Core_Function import Class_Core_Function
import time


class VulnDatabase:
    def __init__(self, project_name=None):
        self.db_handler = MongoDBHandler()
        self.core_function = Class_Core_Function()
        
        # 如果未传入project_name，从当前运行项目配置中获取
        if not project_name:
            project_config = self.core_function.callback_project_config()
            if project_config and 'Project' in project_config:
                project_name = project_config['Project']
        
        self.project_name = project_name
        # 使用 project_{name}_vuln 表名
        self.collection_name = f"project_{project_name}_vuln" if project_name else None

    def add_vuln(self, vuln_data):
        """
        添加漏洞数据
        
        参数:
            vuln_data: 漏洞数据字典
            {
                "url": "http://127.0.0.1/test?name=1",
                "method": "POST",
                "headers": {...},
                "body": "aa=1&bb=a",
                "website": "http://127.0.0.1/",
                "subdomain": "127.0.0.1",
                "vuln_type": "xss",
                "vuln_type_detail": "xss-reflect",
                "level": "high",
                "paramname": "bb",
                "time": "2025-06-01 12:00:00"
            }
        
        返回:
            插入结果或None（如果已存在）
        """
        if not self.collection_name:
            return None

        # 自动添加时间戳
        if 'time' not in vuln_data:
            vuln_data['time'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

        return self.db_handler.insert_one(self.collection_name, vuln_data)

    def get_all_vuln(self, page=1, page_size=20, sort_by='time', sort_order=-1, 
                     search_keyword='', search_type='url', vuln_type=None, 
                     vuln_type_detail=None, level=None):
        """
        获取漏洞列表（分页）
        
        参数:
            page: 页码（从1开始）
            page_size: 每页数量
            sort_by: 排序字段（默认time）
            sort_order: 排序方式（-1降序，1升序）
            search_keyword: 搜索关键词
            search_type: 搜索类型（url, vuln_type, vuln_type_detail, level, subdomain, paramname）
            vuln_type: 漏洞大类过滤（xss/sql/rce/ssrf/leak-info）
            vuln_type_detail: 漏洞详细类型过滤
            level: 危害等级过滤
        
        返回:
            漏洞列表
        """
        if not self.collection_name:
            return []

        query = {}
        
        # 漏洞大类过滤
        if vuln_type:
            query['vuln_type'] = vuln_type
        
        # 漏洞详细类型过滤
        if vuln_type_detail:
            query['vuln_type_detail'] = vuln_type_detail
        
        # 危害等级过滤
        if level:
            query['level'] = level
        
        # 关键词搜索
        if search_keyword and search_keyword.strip():
            if search_type == 'url':
                query['url'] = {'$regex': search_keyword, '$options': 'i'}
            elif search_type == 'vuln_type':
                query['vuln_type'] = {'$regex': search_keyword, '$options': 'i'}
            elif search_type == 'vuln_type_detail':
                query['vuln_type_detail'] = {'$regex': search_keyword, '$options': 'i'}
            elif search_type == 'level':
                query['level'] = {'$regex': search_keyword, '$options': 'i'}
            elif search_type == 'subdomain':
                query['subdomain'] = {'$regex': search_keyword, '$options': 'i'}
            elif search_type == 'paramname':
                query['paramname'] = {'$regex': search_keyword, '$options': 'i'}
            else:
                query['$or'] = [
                    {'url': {'$regex': search_keyword, '$options': 'i'}},
                    {'vuln_type': {'$regex': search_keyword, '$options': 'i'}},
                    {'vuln_type_detail': {'$regex': search_keyword, '$options': 'i'}},
                    {'subdomain': {'$regex': search_keyword, '$options': 'i'}},
                    {'paramname': {'$regex': search_keyword, '$options': 'i'}}
                ]

        projection = None
        skip = (page - 1) * page_size

        vuln_list = self.db_handler.find(self.collection_name, query, projection)

        if sort_by:
            vuln_list.sort(key=lambda x: x.get(sort_by, ''), reverse=(sort_order == -1))
        else:
            vuln_list.sort(key=lambda x: x.get('time', ''), reverse=True)

        paginated_vuln = vuln_list[skip:skip + page_size]
        return paginated_vuln

    def get_vuln_by_id(self, vuln_id):
        """
        根据ID获取漏洞详情
        
        参数:
            vuln_id: 漏洞ID
        
        返回:
            漏洞详情或None
        """
        if not self.collection_name:
            return None
        try:
            from bson import ObjectId
            return self.db_handler.find_one(self.collection_name, {'_id': ObjectId(vuln_id)})
        except Exception:
            return self.db_handler.find_one(self.collection_name, {'_id': vuln_id})

    def get_vuln_by_url(self, url):
        """
        根据URL获取漏洞列表
        
        参数:
            url: 漏洞URL
        
        返回:
            漏洞列表
        """
        if not self.collection_name:
            return []
        return self.db_handler.find(self.collection_name, {'url': url})

    def delete_vuln(self, vuln_id):
        """
        删除漏洞
        
        参数:
            vuln_id: 漏洞ID
        
        返回:
            删除结果
        """
        if not self.collection_name:
            return None
        try:
            from bson import ObjectId
            return self.db_handler.delete_one(self.collection_name, {'_id': ObjectId(vuln_id)})
        except Exception:
            return self.db_handler.delete_one(self.collection_name, {'_id': vuln_id})

    def delete_all_vuln(self):
        """
        删除所有漏洞
        
        返回:
            删除结果
        """
        if not self.collection_name:
            return False
        return self.db_handler.delete_many(self.collection_name, {})

    def count_vuln(self, vuln_type=None, vuln_type_detail=None, level=None):
        """
        统计漏洞总数
        
        参数:
            vuln_type: 漏洞大类过滤
            vuln_type_detail: 漏洞详细类型过滤
            level: 危害等级过滤
        
        返回:
            漏洞数量
        """
        if not self.collection_name:
            return 0
        
        query = {}
        if vuln_type:
            query['vuln_type'] = vuln_type
        if vuln_type_detail:
            query['vuln_type_detail'] = vuln_type_detail
        if level:
            query['level'] = level
        
        return self.db_handler.count_documents(self.collection_name, query)

    def search_vuln_count(self, search_keyword='', search_type='url', vuln_type=None, 
                          vuln_type_detail=None, level=None):
        """
        搜索结果数量
        
        参数:
            search_keyword: 搜索关键词
            search_type: 搜索类型
            vuln_type: 漏洞大类过滤
            vuln_type_detail: 漏洞详细类型过滤
            level: 危害等级过滤
        
        返回:
            搜索结果数量
        """
        if not self.collection_name:
            return 0

        query = {}
        
        # 漏洞大类过滤
        if vuln_type:
            query['vuln_type'] = vuln_type
        
        # 漏洞详细类型过滤
        if vuln_type_detail:
            query['vuln_type_detail'] = vuln_type_detail
        
        # 危害等级过滤
        if level:
            query['level'] = level
        
        # 关键词搜索
        if search_keyword and search_keyword.strip():
            if search_type == 'url':
                query['url'] = {'$regex': search_keyword, '$options': 'i'}
            elif search_type == 'vuln_type':
                query['vuln_type'] = {'$regex': search_keyword, '$options': 'i'}
            elif search_type == 'vuln_type_detail':
                query['vuln_type_detail'] = {'$regex': search_keyword, '$options': 'i'}
            elif search_type == 'level':
                query['level'] = {'$regex': search_keyword, '$options': 'i'}
            elif search_type == 'subdomain':
                query['subdomain'] = {'$regex': search_keyword, '$options': 'i'}
            elif search_type == 'paramname':
                query['paramname'] = {'$regex': search_keyword, '$options': 'i'}
            else:
                query['$or'] = [
                    {'url': {'$regex': search_keyword, '$options': 'i'}},
                    {'vuln_type': {'$regex': search_keyword, '$options': 'i'}},
                    {'vuln_type_detail': {'$regex': search_keyword, '$options': 'i'}},
                    {'subdomain': {'$regex': search_keyword, '$options': 'i'}},
                    {'paramname': {'$regex': search_keyword, '$options': 'i'}}
                ]

        return self.db_handler.count_documents(self.collection_name, query)

    def get_vuln_statistics(self):
        """
        获取漏洞统计信息
        
        返回:
            {
                'total': 总数,
                'by_type': {'xss': 10, 'sql': 5, ...},
                'by_type_detail': {'xss-reflect': 5, 'xss-dom': 5, 'sqli-blind': 3, ...},
                'by_level': {'high': 8, 'medium': 5, 'low': 2}
            }
        """
        if not self.collection_name:
            return {
                'total': 0, 
                'by_type': {}, 
                'by_type_detail': {}, 
                'by_level': {}
            }
        
        all_vulns = self.db_handler.find(self.collection_name, {})
        
        stats = {
            'total': len(all_vulns),
            'by_type': {},
            'by_type_detail': {},
            'by_level': {}
        }
        
        for vuln in all_vulns:
            # 按漏洞大类统计
            vuln_type = vuln.get('vuln_type', 'unknown')
            stats['by_type'][vuln_type] = stats['by_type'].get(vuln_type, 0) + 1
            
            # 按漏洞详细类型统计
            vuln_type_detail = vuln.get('vuln_type_detail', 'unknown')
            stats['by_type_detail'][vuln_type_detail] = stats['by_type_detail'].get(vuln_type_detail, 0) + 1
            
            # 按危害等级统计
            level = vuln.get('level', 'unknown')
            stats['by_level'][level] = stats['by_level'].get(level, 0) + 1
        
        return stats

    def get_vuln_types(self):
        """
        获取所有漏洞大类列表（去重）
        
        返回:
            漏洞大类列表（xss/sql/rce/ssrf/leak-info）
        """
        if not self.collection_name:
            return []
        
        all_vulns = self.db_handler.find(self.collection_name, {})
        vuln_types = set()
        for vuln in all_vulns:
            vuln_type = vuln.get('vuln_type')
            if vuln_type:
                vuln_types.add(vuln_type)
        
        return sorted(list(vuln_types))

    def get_vuln_type_details(self):
        """
        获取所有漏洞详细类型列表（去重）
        
        返回:
            漏洞详细类型列表
        """
        if not self.collection_name:
            return []
        
        all_vulns = self.db_handler.find(self.collection_name, {})
        vuln_type_details = set()
        for vuln in all_vulns:
            vuln_type_detail = vuln.get('vuln_type_detail')
            if vuln_type_detail:
                vuln_type_details.add(vuln_type_detail)
        
        return sorted(list(vuln_type_details))

    def get_vuln_levels(self):
        """
        获取所有危害等级列表（去重）
        
        返回:
            危害等级列表
        """
        if not self.collection_name:
            return []
        
        all_vulns = self.db_handler.find(self.collection_name, {})
        levels = set()
        for vuln in all_vulns:
            level = vuln.get('level')
            if level:
                levels.add(level)
        
        return sorted(list(levels))

    def update_vuln(self, vuln_id, update_data):
        """
        更新漏洞信息
        
        参数:
            vuln_id: 漏洞ID
            update_data: 更新数据字典
        
        返回:
            更新结果
        """
        if not self.collection_name:
            return None
        try:
            from bson import ObjectId
            return self.db_handler.update_one(
                self.collection_name, 
                {'_id': ObjectId(vuln_id)}, 
                update_data
            )
        except Exception:
            return self.db_handler.update_one(
                self.collection_name, 
                {'_id': vuln_id}, 
                update_data
            )
