# coding: utf-8
"""
HTML 收集模块
从HTML中提取URL，导入traffic表
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from urlextract import URLExtract
from database.mongodb_handler import MongoDBHandler
from database.project_database import ProjectDatabase
from database.traffic_database import TrafficDatabase
from service.Class_Core_Function import Class_Core_Function


# ---------------------------------------------------------
# 1. 初始化URL提取器 (基于TLD数据库，线程安全)
# ---------------------------------------------------------

# 全局URLExtract实例（线程安全，基于公开后缀列表）
URL_EXTRACTOR = URLExtract()

# 性能配置
MAX_HTML_SIZE = 2 * 1024 * 1024  # 单个HTML最大2MB
BATCH_SIZE = 100  # 每批处理的HTML数量
MAX_WORKERS = 8  # 线程池大小


# ---------------------------------------------------------
# 2. 辅助函数 (纯函数，线程安全)
# ---------------------------------------------------------
def extract_urls(text):
    """
    从文本中提取URL（纯函数，线程安全）
    使用 urlextract 库基于TLD数据库，更准确高效
    
    :param text: HTML文本
    :return: set(urls)
    """
    if not text or len(text) == 0:
        return set()
    
    # 截断超大文本
    if len(text) > MAX_HTML_SIZE:
        text = text[:MAX_HTML_SIZE]
    
    urls = set()
    
    # 使用 urlextract 提取URL（基于TLD数据库，自动识别域名边界）
    for url in URL_EXTRACTOR.gen_urls(text):
        if len(url) > 10:  # 过滤太短的URL
            # 清理URL末尾的特殊字符
            url = url.rstrip('.,;:!?\'"<>)]}')
            urls.add(url)
    
    return urls


# ---------------------------------------------------------
# 3. HTMLCollector 主类
# ---------------------------------------------------------
class HTMLCollector:
    """HTML收集器 - 从HTML表中提取URL，导入traffic表"""

    def __init__(self, project_name=None):
        self.project_name = project_name
        self.db_handler = MongoDBHandler()
        self.project_db = ProjectDatabase()
        self.core_function = Class_Core_Function()
        self.traffic_db = TrafficDatabase(project_name)
        # 获取项目配置中的线程数
        self.project_config = self.core_function.callback_project_config()
        self.http_thread = self.project_config.get('http_thread', MAX_WORKERS) if self.project_config else MAX_WORKERS

    def _get_html_collection(self):
        """获取html表collection名称"""
        if not self.project_name:
            running_project = self.project_db.get_running_project()
            if running_project and 'Project' in running_project:
                self.project_name = running_project['Project']
            else:
                return None
        return f"project_{self.project_name}_html"

    def _get_traffic_collection(self):
        """获取traffic表collection名称"""
        if not self.project_name:
            return None
        return f"project_{self.project_name}_traffic"

    def _batch_extract(self, html_list):
        """
        批量提取URL（多线程）
        :param html_list: HTML文本列表
        :return: all_urls
        """
        if not html_list:
            return set()
        
        all_urls = set()
        
        # 使用配置的线程数
        workers = min(self.http_thread, len(html_list), 50)  # 最多50线程
        
        # 使用线程池并行处理
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(extract_urls, html): i 
                       for i, html in enumerate(html_list)}
            
            for future in as_completed(futures):
                try:
                    urls = future.result()
                    all_urls.update(urls)
                except Exception:
                    pass
        
        return all_urls

    def _batch_update_status(self, collection, html_ids):
        """批量更新HTML状态为已处理"""
        if not html_ids:
            return
        
        # 使用 $in 操作符批量更新
        self.db_handler.update_many(
            collection,
            {'_id': {'$in': html_ids}},
            {'status': 1}
        )

    def _batch_import_urls(self, urls, importer):
        """批量导入URL到traffic表"""
        if not urls:
            return 0
        
        # 转换为website格式
        websites = []
        for url in urls:
            website = self.core_function.callback_split_url(url, 0)
            if website:
                websites.append(website)
        
        # 去重
        websites = list(set(websites))
        
        # 数据库去重：检查哪些URL已存在
        existing_urls = self.traffic_db.urls_exist(websites)
        
        # 构建请求列表（只导入不存在的URL）
        request_list = []
        for website in websites:
            if website in existing_urls:
                continue
            url = website if website.endswith('/') else website + '/'
            request = self.core_function.create_request(url)
            request['source'] = 1  # 来源：HTML提取
            request_list.append(request)
        
        # 批量导入
        if request_list:
            result = importer.import_traffic_request(request_list, self.project_name)
            return result.get('imported', 0)
        return 0

    def process(self):
        """
        主流程（优化版）：
        1. 分批读取html表，获取未处理的html (status=0)
        2. 多线程并行提取URL
        3. 批量导入traffic表
        4. 批量更新HTML状态

        Returns:
            dict: {'success': bool, 'processed': int, 'url_count': int, 'message': str}
        """
        try:
            html_collection = self._get_html_collection()
            traffic_collection = self._get_traffic_collection()

            if not html_collection or not traffic_collection:
                return {'success': False, 'message': '未找到运行中的项目'}

            # 延迟导入，避免循环依赖
            from api.import_traffic_api import ImportTrafficAPI
            importer = ImportTrafficAPI()

            total_processed = 0
            total_url_imported = 0

            # 分批处理
            while True:
                # 1. 分批读取html表，只获取需要的字段
                unprocessed_htmls = self.db_handler.find(
                    html_collection,
                    {'status': 0},
                    projection={'html': 1},
                    limit=BATCH_SIZE
                )

                if not unprocessed_htmls:
                    break

                # 提取html内容和ID
                html_list = [item.get('html', '') for item in unprocessed_htmls]
                html_ids = [item.get('_id') for item in unprocessed_htmls if item.get('_id')]

                # 2. 多线程并行提取URL
                all_urls = self._batch_extract(html_list)

                # 3. 批量导入traffic表
                total_url_imported += self._batch_import_urls(all_urls, importer)

                # 4. 批量更新HTML状态
                self._batch_update_status(html_collection, html_ids)

                total_processed += len(unprocessed_htmls)

            return {
                'success': True,
                'processed': total_processed,
                'url_count': total_url_imported,
                'message': f'处理{total_processed}个HTML，导入{total_url_imported}个URL'
            }

        except Exception as e:
            return {'success': False, 'message': str(e)}
