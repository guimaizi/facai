# coding: utf-8
"""
网站数据库操作
@Time :    3/15/2026
@Author:  facai
@File: website_database.py
@Software: VSCode
"""
from .mongodb_handler import MongoDBHandler
from bson import ObjectId
import time

class WebsiteDatabase:
    def __init__(self, project_name=None):
        self.db_handler = MongoDBHandler()
        self.project_name = project_name
        # 使用 project_{name}_website 表名（参考数据库结构文档）
        self.collection_name = f"project_{project_name}_website" if project_name else None

    def get_all_websites(self, page=1, page_size=20, sort_by='time_update', sort_order=-1, search_keyword='', search_field='url'):
        """获取网站列表（分页）"""
        if not self.collection_name:
            return []

        query = {}
        if search_keyword and search_keyword.strip():
            # 根据指定字段搜索
            query = {search_field: {'$regex': search_keyword, '$options': 'i'}}

        projection = None
        skip = (page - 1) * page_size

        # 构建排序参数
        sort = [(sort_by, sort_order)] if sort_by else [('time_update', -1)]

        # 在数据库层面完成排序、分页
        websites = self.db_handler.find(
            self.collection_name,
            query,
            projection,
            limit=page_size,
            sort=sort,
            skip=skip
        )

        return websites

    def get_website_by_id(self, website_id):
        """根据ID获取网站详情"""
        if not self.collection_name:
            return None
        return self.db_handler.find_one(self.collection_name, {'_id': website_id})

    def add_website(self, website_data):
        """添加网站"""
        if not self.collection_name:
            return None

        # 根据数据库结构文档，确保字段名称正确
        normalized_data = {
            'url': website_data.get('url'),
            'method': website_data.get('method', 'GET'),
            'body': website_data.get('body', ''),
            'headers': website_data.get('headers', {}),
            'subdomain': website_data.get('subdomain', ''),
            'domain': website_data.get('domain', ''),
            'waf': website_data.get('waf', 0),
            'title': website_data.get('title', ''),
            'port': website_data.get('port', 80),
            'current_url': website_data.get('current_url', ''),
            'headers_response': website_data.get('headers_response', {}),
            'server': website_data.get('server', ''),
            'web_fingerprint': website_data.get('web_fingerprint', 'Null'),
            'screenshot': website_data.get('screenshot', ''),
            'describe': website_data.get('describe', 'Null'),
            'tag': website_data.get('tag', []),
            'html_md5': website_data.get('html_md5', ''),
            'html_browser_md5': website_data.get('html_browser_md5', ''),
            'html_len': website_data.get('html_len', 0),
            'time_first': website_data.get('time_first', time.strftime('%Y-%m-%d %H:%M:%S')),
            'time_update': time.strftime('%Y-%m-%d %H:%M:%S'),
            'http_status_code': website_data.get('http_status_code', 0),
            'status': 0
        }

        # 检查是否已存在相同的URL
        existing = self.db_handler.find_one(self.collection_name, {'url': normalized_data.get('url')})
        if existing:
            # 更新现有记录
            return self.db_handler.update_one(
                self.collection_name,
                {'url': normalized_data.get('url')},
                {'$set': normalized_data}
            )
        else:
            # 插入新记录
            return self.db_handler.insert_one(self.collection_name, normalized_data)

    def delete_website(self, website_id):
        """删除网站"""
        if not self.collection_name:
            return None
        return self.db_handler.delete_one(self.collection_name, {'_id': website_id})

    def delete_all_websites(self):
        """删除所有网站"""
        if not self.collection_name:
            return False
        query = {}
        # 使用循环删除，因为MongoDBHandler没有提供删除所有的方法
        websites = self.db_handler.find(self.collection_name, query)
        for item in websites:
            self.db_handler.delete_one(self.collection_name, {'_id': item['_id']})
        return True

    def count_websites(self):
        """统计网站总数"""
        if not self.collection_name:
            return 0
        query = {}
        return self.db_handler.count_documents(self.collection_name, query)

    def search_websites_count(self, search_keyword, search_field='url'):
        """搜索结果数量"""
        if not self.collection_name:
            return 0

        if search_keyword and search_keyword.strip():
            query = {search_field: {'$regex': search_keyword, '$options': 'i'}}
        else:
            query = {}

        return self.db_handler.count_documents(self.collection_name, query)
