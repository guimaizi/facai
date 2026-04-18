from .mongodb_handler import MongoDBHandler
import time

class TrafficDatabase:
    def __init__(self, project_name=None):
        self.db_handler = MongoDBHandler()
        self.project_name = project_name
        # 使用 project_{name}_traffic 表名
        self.collection_name = f"project_{project_name}_traffic" if project_name else None

    def get_all_traffic(self, page=1, page_size=20, sort_by=None, sort_order=1, search_url=''):
        """获取所有流量数据，支持分页、排序和URL搜索"""
        if not self.collection_name:
            return [], 0

        query = {}
        projection = None

        # 如果有搜索条件，添加URL搜索
        if search_url and search_url.strip():
            query = {'url': {'$regex': search_url, '$options': 'i'}}

        # 计算跳过的记录数
        skip = (page - 1) * page_size

        # 构建排序参数
        sort = []
        if sort_by:
            sort = [(sort_by, sort_order)]
        else:
            # 默认按时间降序排序
            sort = [('time', -1)]

        # 在数据库层面完成排序、分页
        traffic = self.db_handler.find(
            self.collection_name,
            query,
            projection,
            limit=page_size,
            sort=sort,
            skip=skip
        )

        # 获取总数（用于分页计算）
        total = self.db_handler.count_documents(self.collection_name, query)

        return traffic, total

    def get_traffic_by_id(self, traffic_id):
        """根据ID获取流量数据"""
        if not self.collection_name:
            return None
        return self.db_handler.find_one(self.collection_name, {'_id': traffic_id})

    def add_traffic(self, traffic_data):
        """添加流量数据"""
        if not self.collection_name:
            return None
        traffic_data['time'] = traffic_data.get('time', time.strftime('%Y-%m-%d %H:%M:%S'))
        return self.db_handler.insert_one(self.collection_name, traffic_data)

    def delete_traffic(self, traffic_id):
        """删除流量数据"""
        if not self.collection_name:
            return None
        return self.db_handler.delete_one(self.collection_name, {'_id': traffic_id})

    def delete_all_traffic(self, project_name=None):
        """删除所有流量数据"""
        if not self.collection_name:
            return False
        # 添加 delete_many 方法到 MongoDBHandler 后使用
        return self.db_handler.delete_many(self.collection_name, {})

    def count_traffic(self, project_name=None):
        """获取流量数据总数"""
        if not self.collection_name:
            return 0
        query = {}
        return self.db_handler.count_documents(self.collection_name, query)

    def urls_exist(self, urls):
        """
        批量检查URL是否已存在
        :param urls: URL集合
        :return: 已存在的URL集合
        """
        if not self.collection_name or not urls:
            return set()
        
        existing = self.db_handler.find(
            self.collection_name,
            {'url': {'$in': list(urls)}},
            projection={'url': 1}
        )
        return {item['url'] for item in existing}
    
    def get_unscanned_traffic(self, limit=100):
        """
        获取未扫描的流量数据（用于自动扫描）
        :param limit: 最多获取多少条
        :return: 流量数据列表
        """
        if not self.collection_name:
            return []
        
        traffic_list = self.db_handler.find(
            self.collection_name,
            {'scaner_status': 0},
            limit=limit,
            sort=[('time', 1)]  # 按时间升序，先进先出
        )
        return traffic_list
    
    def mark_traffic_as_scanned(self, traffic_id):
        """
        标记流量为已扫描
        :param traffic_id: 流量ID
        :return: 是否更新成功
        """
        if not self.collection_name:
            return False
        
        result = self.db_handler.update_one(
            self.collection_name,
            {'_id': traffic_id},
            {'scaner_status': 1}
        )
        return result is not None