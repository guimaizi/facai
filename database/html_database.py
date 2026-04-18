# coding: utf-8
"""
HTML数据库操作
@Time :    3/15/2026
@Author:  facai
@File: html_database.py
@Software: VSCode
"""
from .mongodb_handler import MongoDBHandler
import time


class HtmlDatabase:
    def __init__(self, project_name=None):
        self.db_handler = MongoDBHandler()
        self.project_name = project_name
        # 使用 project_{name}_html 表名
        self.collection_name = f"project_{project_name}_html" if project_name else None

    def get_all_html(self, page=1, page_size=20, sort_by='time', sort_order=-1, search_keyword='', search_type='md5'):
        """获取HTML列表（分页）"""
        if not self.collection_name:
            return []

        query = {}
        if search_keyword and search_keyword.strip():
            if search_type == 'md5':
                query = {'html_md5': {'$regex': search_keyword, '$options': 'i'}}
            elif search_type == 'html':
                query = {'html': {'$regex': search_keyword, '$options': 'i'}}
            else:
                query = {'$or': [
                    {'html_md5': {'$regex': search_keyword, '$options': 'i'}},
                    {'html': {'$regex': search_keyword, '$options': 'i'}}
                ]}

        # 排除 html 字段，提升查询性能
        projection = {'html': 0}

        # 计算跳过的记录数
        skip = (page - 1) * page_size

        # 查询数据（排除html字段）
        htmls = self.db_handler.find(self.collection_name, query, projection)

        # 排序
        if sort_by:
            htmls.sort(key=lambda x: x.get(sort_by, ''), reverse=(sort_order == -1))
        else:
            # 默认按时间降序排序
            htmls.sort(key=lambda x: x.get('time', ''), reverse=True)

        # 分页
        paginated_htmls = htmls[skip:skip + page_size]

        return paginated_htmls

    def get_html_by_id(self, html_id):
        """根据ID获取HTML详情"""
        if not self.collection_name:
            return None
        try:
            from bson import ObjectId
            return self.db_handler.find_one(self.collection_name, {'_id': ObjectId(html_id)})
        except Exception:
            # 如果转换失败，尝试用字符串查询
            return self.db_handler.find_one(self.collection_name, {'_id': html_id})

    def get_html_by_md5(self, html_md5):
        """根据MD5获取HTML详情"""
        if not self.collection_name:
            return None
        return self.db_handler.find_one(self.collection_name, {'html_md5': html_md5})

    def add_html(self, html_data):
        """添加HTML，如果html_md5不存在则写入"""
        if not self.collection_name:
            return None

        # 根据数据库结构文档，确保字段名称正确
        normalized_data = {
            'html': html_data.get('html', ''),
            'html_md5': html_data.get('html_md5', ''),
            'html_len': html_data.get('html_len', 0),
            'time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'status': 0
        }

        # 检查是否已存在相同的MD5（只查询_id字段，更快）
        existing = self.db_handler.find_one(
            self.collection_name, 
            {'html_md5': normalized_data.get('html_md5')}, 
            projection={'_id': 1}
        )
        if existing:
            # 已存在则不插入，返回None
            return None
        else:
            # 不存在则插入新记录
            return self.db_handler.insert_one(self.collection_name, normalized_data)

    def import_html(self, html_data):
        """
        导入HTML数据接口（如果html_md5不存在则写入）
        与add_html功能相同，提供更直观的接口名
        """
        return self.add_html(html_data)

    def delete_html(self, html_id):
        """删除HTML"""
        if not self.collection_name:
            return None
        try:
            from bson import ObjectId
            return self.db_handler.delete_one(self.collection_name, {'_id': ObjectId(html_id)})
        except Exception:
            # 如果转换失败，尝试用字符串查询
            return self.db_handler.delete_one(self.collection_name, {'_id': html_id})

    def delete_all_html(self):
        """删除所有HTML"""
        if not self.collection_name:
            return False
        return self.db_handler.delete_many(self.collection_name, {})

    def count_html(self):
        """统计HTML总数"""
        if not self.collection_name:
            return 0
        query = {}
        return self.db_handler.count_documents(self.collection_name, query)

    def search_html_count(self, search_keyword):
        """搜索结果数量"""
        if not self.collection_name:
            return 0

        if search_keyword and search_keyword.strip():
            query = {'$or': [
                {'html_md5': {'$regex': search_keyword, '$options': 'i'}},
                {'html': {'$regex': search_keyword, '$options': 'i'}}
            ]}
        else:
            query = {}

        return self.db_handler.count_documents(self.collection_name, query)
