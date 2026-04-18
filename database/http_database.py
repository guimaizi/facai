# coding: utf-8
"""
HTTP数据库操作
@Time :    3/21/2026
@Author:  facai
@File: http_database.py
@Software: VSCode
"""
from .mongodb_handler import MongoDBHandler
from service.Class_Core_Function import Class_Core_Function
import time


class HttpDatabase:
    def __init__(self, project_name=None):
        self.db_handler = MongoDBHandler()
        self.core_function = Class_Core_Function()
        
        # 如果未传入project_name，从当前运行项目配置中获取
        if not project_name:
            project_config = self.core_function.callback_project_config()
            if project_config and 'Project' in project_config:
                project_name = project_config['Project']
        
        self.project_name = project_name
        # 使用 project_{name}_http 表名
        self.collection_name = f"project_{project_name}_http" if project_name else None

    def get_all_http(self, page=1, page_size=20, sort_by='time_first', sort_order=-1, search_keyword='', search_type='url'):
        """获取HTTP列表（分页）"""
        if not self.collection_name:
            return []

        query = {}
        if search_keyword and search_keyword.strip():
            if search_type == 'url':
                query = {'url': {'$regex': search_keyword, '$options': 'i'}}
            elif search_type == 'title':
                query = {'title': {'$regex': search_keyword, '$options': 'i'}}
            elif search_type == 'subdomain':
                query = {'subdomain': {'$regex': search_keyword, '$options': 'i'}}
            elif search_type == 'key':
                query = {'key': {'$regex': search_keyword, '$options': 'i'}}
            else:
                query = {'$or': [
                    {'url': {'$regex': search_keyword, '$options': 'i'}},
                    {'title': {'$regex': search_keyword, '$options': 'i'}},
                    {'subdomain': {'$regex': search_keyword, '$options': 'i'}}
                ]}

        projection = None
        skip = (page - 1) * page_size

        http_list = self.db_handler.find(self.collection_name, query, projection)

        if sort_by:
            http_list.sort(key=lambda x: x.get(sort_by, ''), reverse=(sort_order == -1))
        else:
            http_list.sort(key=lambda x: x.get('time_first', ''), reverse=True)

        paginated_http = http_list[skip:skip + page_size]
        return paginated_http

    def get_http_by_id(self, http_id):
        """根据ID获取HTTP详情"""
        if not self.collection_name:
            return None
        try:
            from bson import ObjectId
            return self.db_handler.find_one(self.collection_name, {'_id': ObjectId(http_id)})
        except Exception:
            return self.db_handler.find_one(self.collection_name, {'_id': http_id})

    def get_http_by_key(self, key):
        """根据key获取HTTP详情"""
        if not self.collection_name:
            return None
        return self.db_handler.find_one(self.collection_name, {'key': key})

    def exists_by_key(self, key):
        """根据key判断HTTP是否存在"""
        if not self.collection_name:
            return False
        existing = self.db_handler.find_one(self.collection_name, {'key': key})
        return existing is not None

    def add_http(self, http_data):
        """添加HTTP数据，如果key不存在则写入"""
        if not self.collection_name:
            return None

        key = http_data.get('key', '')
        if key and self.exists_by_key(key):
            return None

        return self.db_handler.insert_one(self.collection_name, http_data)

    def import_http(self, http_data):
        """
        导入HTTP数据接口（如果key不存在则写入）
        与add_http功能相同，提供更直观的接口名
        """
        return self.add_http(http_data)

    def delete_http(self, http_id):
        """删除HTTP"""
        if not self.collection_name:
            return None
        try:
            from bson import ObjectId
            return self.db_handler.delete_one(self.collection_name, {'_id': ObjectId(http_id)})
        except Exception:
            return self.db_handler.delete_one(self.collection_name, {'_id': http_id})

    def delete_all_http(self):
        """删除所有HTTP"""
        if not self.collection_name:
            return False
        return self.db_handler.delete_many(self.collection_name, {})

    def count_http(self):
        """统计HTTP总数"""
        if not self.collection_name:
            return 0
        return self.db_handler.count_documents(self.collection_name, {})

    def search_http_count(self, search_keyword, search_type='url'):
        """搜索结果数量"""
        if not self.collection_name:
            return 0

        if search_keyword and search_keyword.strip():
            if search_type == 'url':
                query = {'url': {'$regex': search_keyword, '$options': 'i'}}
            elif search_type == 'title':
                query = {'title': {'$regex': search_keyword, '$options': 'i'}}
            elif search_type == 'subdomain':
                query = {'subdomain': {'$regex': search_keyword, '$options': 'i'}}
            else:
                query = {'$or': [
                    {'url': {'$regex': search_keyword, '$options': 'i'}},
                    {'title': {'$regex': search_keyword, '$options': 'i'}},
                    {'subdomain': {'$regex': search_keyword, '$options': 'i'}}
                ]}
        else:
            query = {}

        return self.db_handler.count_documents(self.collection_name, query)
