# coding: utf-8
"""
重点资产数据库操作
@Time :    3/24/2026
@Author:  facai
@File: highlight_database.py
@Software: VSCode
"""
from .mongodb_handler import MongoDBHandler
from service.Class_Core_Function import Class_Core_Function
import time


class HighlightDatabase:
    def __init__(self, project_name=None):
        self.db_handler = MongoDBHandler()
        self.core_function = Class_Core_Function()
        
        # 如果未传入project_name，从当前运行项目配置中获取
        if not project_name:
            project_config = self.core_function.callback_project_config()
            if project_config and 'Project' in project_config:
                project_name = project_config['Project']
        
        self.project_name = project_name
        # 使用 project_{name}_data 表名
        self.collection_name = f"project_{project_name}_data" if project_name else None

    def get_all_highlights(self, page=1, page_size=20, sort_by='time', sort_order=-1, search_keyword='', search_type='url'):
        """获取重点资产列表（分页）"""
        if not self.collection_name:
            return []

        query = {}
        if search_keyword and search_keyword.strip():
            if search_type == 'url':
                query = {'url': {'$regex': search_keyword, '$options': 'i'}}
            elif search_type == 'title':
                query = {'title': {'$regex': search_keyword, '$options': 'i'}}
            elif search_type == 'tags':
                query = {'tags': {'$regex': search_keyword, '$options': 'i'}}
            elif search_type == 'type':
                query = {'type': {'$regex': search_keyword, '$options': 'i'}}
            else:
                query = {'$or': [
                    {'url': {'$regex': search_keyword, '$options': 'i'}},
                    {'title': {'$regex': search_keyword, '$options': 'i'}},
                    {'tags': {'$regex': search_keyword, '$options': 'i'}},
                    {'desc': {'$regex': search_keyword, '$options': 'i'}}
                ]}

        projection = None
        skip = (page - 1) * page_size

        highlight_list = self.db_handler.find(self.collection_name, query, projection)

        if sort_by:
            highlight_list.sort(key=lambda x: x.get(sort_by, ''), reverse=(sort_order == -1))
        else:
            highlight_list.sort(key=lambda x: x.get('time', ''), reverse=True)

        paginated_list = highlight_list[skip:skip + page_size]
        return paginated_list

    def get_highlight_by_id(self, highlight_id):
        """根据ID获取重点资产详情"""
        if not self.collection_name:
            return None
        try:
            from bson import ObjectId
            return self.db_handler.find_one(self.collection_name, {'_id': ObjectId(highlight_id)})
        except Exception:
            return self.db_handler.find_one(self.collection_name, {'_id': highlight_id})

    def get_highlight_by_url(self, url):
        """根据URL获取重点资产详情"""
        if not self.collection_name:
            return None
        return self.db_handler.find_one(self.collection_name, {'url': url})

    def exists_by_url(self, url):
        """根据URL判断重点资产是否存在"""
        if not self.collection_name:
            return False
        existing = self.db_handler.find_one(self.collection_name, {'url': url})
        return existing is not None

    def add_highlight(self, highlight_data):
        """添加重点资产数据"""
        if not self.collection_name:
            return None

        # 添加时间戳
        if 'time' not in highlight_data:
            highlight_data['time'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

        return self.db_handler.insert_one(self.collection_name, highlight_data)

    def update_highlight(self, highlight_id, highlight_data):
        """更新重点资产数据"""
        if not self.collection_name:
            return None
        try:
            from bson import ObjectId
            return self.db_handler.update_one(
                self.collection_name, 
                {'_id': ObjectId(highlight_id)}, 
                {'$set': highlight_data}
            )
        except Exception:
            return self.db_handler.update_one(
                self.collection_name, 
                {'_id': highlight_id}, 
                {'$set': highlight_data}
            )

    def delete_highlight(self, highlight_id):
        """删除重点资产"""
        if not self.collection_name:
            return None
        try:
            from bson import ObjectId
            return self.db_handler.delete_one(self.collection_name, {'_id': ObjectId(highlight_id)})
        except Exception:
            return self.db_handler.delete_one(self.collection_name, {'_id': highlight_id})

    def delete_all_highlights(self):
        """删除所有重点资产"""
        if not self.collection_name:
            return False
        return self.db_handler.delete_many(self.collection_name, {})

    def count_highlights(self):
        """统计重点资产总数"""
        if not self.collection_name:
            return 0
        return self.db_handler.count_documents(self.collection_name, {})

    def search_highlights_count(self, search_keyword, search_type='url'):
        """搜索结果数量"""
        if not self.collection_name:
            return 0

        if search_keyword and search_keyword.strip():
            if search_type == 'url':
                query = {'url': {'$regex': search_keyword, '$options': 'i'}}
            elif search_type == 'title':
                query = {'title': {'$regex': search_keyword, '$options': 'i'}}
            elif search_type == 'tags':
                query = {'tags': {'$regex': search_keyword, '$options': 'i'}}
            elif search_type == 'type':
                query = {'type': {'$regex': search_keyword, '$options': 'i'}}
            else:
                query = {'$or': [
                    {'url': {'$regex': search_keyword, '$options': 'i'}},
                    {'title': {'$regex': search_keyword, '$options': 'i'}},
                    {'tags': {'$regex': search_keyword, '$options': 'i'}},
                    {'desc': {'$regex': search_keyword, '$options': 'i'}}
                ]}
        else:
            query = {}

        return self.db_handler.count_documents(self.collection_name, query)

    def get_type_statistics(self):
        """获取各类型资产统计"""
        if not self.collection_name:
            return {}
        
        pipeline = [
            {'$group': {'_id': '$type', 'count': {'$sum': 1}}}
        ]
        
        result = self.db_handler.aggregate(self.collection_name, pipeline)
        stats = {}
        for item in result:
            type_name = item.get('_id', 'unknown')
            stats[type_name] = item.get('count', 0)
        return stats
