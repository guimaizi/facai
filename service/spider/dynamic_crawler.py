# coding: utf-8
"""
动态爬虫控制器（与数据库交互）
@Time :    3/14/2025 11:05
@Author:  fff
@File: dynamic_crawler.py
@Software: PyCharm

功能说明：
1. 从数据库获取未处理的URL（website/http表）
2. 调用 BrowserCDP 进行动态爬取
3. 将爬取结果保存到数据库（traffic/html表）
4. 更新数据处理状态
"""

import socket
import time
from service.spider.browser_cdp import BrowserCDP
from service.Class_Core_Function import Class_Core_Function
from api.import_traffic_api import ImportTrafficAPI
from database.html_database import HtmlDatabase
from database.mongodb_handler import MongoDBHandler
from database.project_database import ProjectDatabase
from database.traffic_database import TrafficDatabase
from service.libs.chrome_manage import ChromeService
from mitmproxy_service import MitmproxyService


class DynamicCrawler:
    """
    动态爬虫控制器
    负责数据库交互，调用 BrowserCDP 进行爬取
    """
    
    def __init__(self, project_name=None):
        """
        初始化动态爬虫控制器
        :param project_name: 项目名称
        """
        self.Core_Function = Class_Core_Function()
        self.project_name = project_name
        
        # 获取项目配置
        self.project_config = self.Core_Function.callback_project_config()
        self.browser_thread = self.project_config.get('browser_thread', 10) if self.project_config else 10
        
        # 数据库相关 - 在初始化时创建连接
        self.db_handler = MongoDBHandler()
        self.project_db = ProjectDatabase()
        self.import_traffic = ImportTrafficAPI()
        
        # 项目相关的数据库实例
        self.html_db = HtmlDatabase(self.project_name) if self.project_name else None
        self.traffic_db = TrafficDatabase(self.project_name)
        
        # CDP 浏览器实例
        self.browser_cdp = None

    def _check_port_in_use(self, port):
        """检查端口是否被占用"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex(('localhost', port)) == 0
        except:
            return False

    def check_services_status(self):
        """
        检测 Chrome 和 Mitmproxy 服务状态
        :return: dict - {'chrome_running': bool, 'mitmproxy_running': bool, 'can_run': bool, 'message': str}
        """
        config = self.Core_Function.callback_config()
        chrome_port = config.get('chrome_cdp_port', 19227) if config else 19227
        mitmproxy_port = config.get('mitmproxy_port', 18081) if config else 18081

        chrome_running = self._check_port_in_use(chrome_port)
        mitmproxy_running = self._check_port_in_use(mitmproxy_port)

        # 两个服务必须同时运行才能进行动态爬取
        can_run = chrome_running and mitmproxy_running

        messages = []
        if not chrome_running:
            messages.append(f'Chrome CDP (端口 {chrome_port}) 未运行')
        if not mitmproxy_running:
            messages.append(f'Mitmproxy (端口 {mitmproxy_port}) 未运行')

        message = ' | '.join(messages) if messages else '服务状态正常'

        return {
            'chrome_running': chrome_running,
            'mitmproxy_running': mitmproxy_running,
            'can_run': can_run,
            'message': message
        }

    def ensure_services_running(self):
        """
        确保 Chrome 和 Mitmproxy 服务运行
        如果未运行则提示用户重启程序
        :return: dict - {'success': bool, 'message': str}
        """
        chrome_service = ChromeService()
        mitmproxy_service = MitmproxyService()

        # 检测当前状态
        chrome_status = chrome_service.get_status()
        mitmproxy_status = mitmproxy_service.get_status()

        messages = []

        # Mitmproxy必须运行
        if not mitmproxy_status['is_running']:
            return {
                'success': False,
                'message': 'Mitmproxy服务未启动，请重启主程序'
            }

        # 启动 Chrome
        if not chrome_status['is_running']:
            self.Core_Function.callback_logging().info("动态爬虫: 正在启动 Chrome...")
            result = chrome_service.start(mode='normal')
            if result['success']:
                messages.append('Chrome 已启动')
                time.sleep(3)  # 等待 Chrome 完全启动
            else:
                return {
                    'success': False,
                    'message': f"Chrome 启动失败: {result['message']}"
                }

        # 再次验证服务状态
        chrome_status = chrome_service.get_status()
        mitmproxy_status = mitmproxy_service.get_status()

        if chrome_status['is_running'] and mitmproxy_status['is_running']:
            return {
                'success': True,
                'message': ' | '.join(messages) if messages else '服务已运行'
            }
        else:
            return {
                'success': False,
                'message': 'Mitmproxy服务未启动，请重启程序'
            }

    # ==================== 数据库操作 ====================
    
    def fetch_unprocessed_urls(self, limit=None):
        """
        获取未处理的URL用于动态爬取
        从 project_{name}_website 表读取未处理数据
        
        :param limit: 读取数量限制，默认使用项目配置 browser_thread
        :return: list - 符合条件的URL信息列表
        """
        if not self.project_name:
            return []

        if limit is None:
            limit = self.browser_thread

        url_list = []

        # 从 website 表获取未处理数据
        website_collection = f"project_{self.project_name}_website"
        try:
            website_list = self.db_handler.find(
                website_collection,
                {'status': 0},  # 未处理
                limit=limit
            )
            for website in website_list:
                url = website.get('url', '')
                if url:
                    url_list.append({
                        'url': url,
                        'source': 'website',
                        '_id': website.get('_id')
                    })
        except Exception as e:
            self.Core_Function.callback_logging().error(f"读取website表失败: {e}")

        return url_list

    def _update_processed_status(self, url_info_list):
        """
        更新已处理数据的状态
        :param url_info_list: 已处理的URL信息列表
        """
        for url_info in url_info_list:
            try:
                source = url_info.get('source')
                _id = url_info.get('_id')
                if not _id or source != 'website':
                    continue

                collection = f"project_{self.project_name}_website"
                self.db_handler.update_one(
                    collection,
                    {'_id': _id},
                    {'status': 1}  # 标记为已处理
                )
            except Exception as e:
                self.Core_Function.callback_logging().error(f"更新状态失败: {e}")

    def _update_page_data(self, page_data_list):
        """
        更新页面数据到 website/http 表
        :param page_data_list: 页面数据列表（包含 screenshot, title, current_url 等）
        """
        if not page_data_list or not self.project_name:
            return
        
        for page_data in page_data_list:
            try:
                url = page_data.get('url', '')
                if not url:
                    continue
                
                # 准备更新数据
                update_data = {
                    'title': page_data.get('title', ''),
                    'current_url': page_data.get('current_url', ''),
                    'html_browser_md5': page_data.get('html_browser_md5', ''),
                    'html_len': page_data.get('html_len', 0),
                    'time_update': page_data.get('time', self.Core_Function.callback_time(0))
                }
                
                # 只有截图存在时才更新
                screenshot = page_data.get('screenshot', '')
                if screenshot:
                    update_data['screenshot'] = screenshot
                
                # 更新 website 表（按 URL 匹配）
                website_collection = f"project_{self.project_name}_website"
                result = self.db_handler.update_one(
                    website_collection,
                    {'url': url},
                    update_data
                )
                
                # 如果 website 表没有匹配，尝试更新 http 表
                if not result or result.matched_count == 0:
                    http_collection = f"project_{self.project_name}_http"
                    self.db_handler.update_one(
                        http_collection,
                        {'url': url},
                        update_data
                    )
                    
            except Exception as e:
                self.Core_Function.callback_logging().error(f"更新页面数据失败: {e}")

    def _save_crawled_data(self, urls, htmls):
        """
        保存爬取的数据
        :param urls: 提取的URL列表
        :param htmls: HTML数据列表
        """
        # 1. 保存URL到 traffic 表
        url_list = list(set(urls))
        
        # 数据库去重：检查哪些URL已存在
        existing_urls = self.traffic_db.urls_exist(url_list)
        url_list = [url for url in url_list if url not in existing_urls]
        
        self.Core_Function.callback_logging().info(f"开始保存爬取数据: URLs={len(url_list)}, HTMLs={len(htmls)}")
        url_imported = 0
        for url in url_list[:3000]:
            try:
                result = self.import_traffic.import_traffic_url(url, self.project_name)
                if result.get('success'):
                    url_imported += 1
            except Exception as e:
                self.Core_Function.callback_logging().error(f"导入URL失败: {url}, 错误: {e}")

        self.Core_Function.callback_logging().info(f"动态爬虫: 导入URL {url_imported}/{len(url_list)} 条")

        # 2. 保存HTML到 html 表
        html_saved = 0
        if self.html_db:
            for html_data in htmls:
                try:
                    result = self.html_db.import_html(html_data)
                    if result:
                        html_saved += 1
                except Exception as e:
                    self.Core_Function.callback_logging().error(f"保存HTML失败: {html_data.get('html_md5')}, 错误: {e}")

            self.Core_Function.callback_logging().info(f"动态爬虫: 保存HTML {html_saved}/{len(htmls)} 条")

    # ==================== 主要接口 ====================
    
    def crawl(self, list_request=None):
        """
        动态爬虫入口
        
        :param list_request: 请求数据列表（可选），如果为空则自动从数据库获取
        :return: {'success': bool, 'message': str, 'pages': int, 'urls': int, 'htmls': int}
        """
        try:
            # 确保服务运行（自动启动未运行的服务）
            service_result = self.ensure_services_running()
            if not service_result['success']:
                self.Core_Function.callback_logging().error(f"动态爬虫: {service_result['message']}")
                return {
                    'success': False,
                    'message': service_result['message'],
                    'pages': 0,
                    'urls': 0,
                    'htmls': 0
                }
            
            self.Core_Function.callback_logging().info(f"动态爬虫: {service_result['message']}")

            # 如果没有传入列表，自动从数据库获取未处理的URL
            if list_request is None:
                url_info_list = self.fetch_unprocessed_urls()
                if not url_info_list:
                    return {'success': True, 'message': '没有需要动态爬取的URL', 'pages': 0, 'urls': 0, 'htmls': 0}
                url_list = [item['url'] for item in url_info_list]
            else:
                url_info_list = []
                url_list = []
                for req in list_request:
                    url = req.get('url', '') if isinstance(req, dict) else str(req)
                    if url:
                        url_list.append(url)
                        url_info_list.append({'url': url})

            if not url_list:
                return {'success': False, 'message': '没有有效的URL', 'pages': 0, 'urls': 0, 'htmls': 0}

            # 创建 CDP 浏览器实例并爬取
            self.browser_cdp = BrowserCDP(browser_thread=self.browser_thread)
            result = self.browser_cdp.crawl(url_list)

            if not result['success']:
                return {
                    'success': False,
                    'message': result['message'],
                    'pages': 0,
                    'urls': 0,
                    'htmls': 0
                }

            print('爬取完成')
            # 保存爬取的数据
            self._save_crawled_data(result['urls'], result['htmls'])
            print('保存完成')
            # 更新页面数据（包含 screenshot）到 website/http 表
            self._update_page_data(result['pages'])
            print('更新完成')
            # 更新已处理数据的状态
            self._update_processed_status(url_info_list)
            print('更新状态完成')
            return {
                'success': True,
                'message': '动态爬取完成',
                'pages': len(result['pages']),
                'urls': len(result['urls']),
                'htmls': len(result['htmls'])
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'动态爬取失败: {str(e)}',
                'pages': 0,
                'urls': 0,
                'htmls': 0
            }

    def process(self):
        """
        处理入口 - 自动获取未处理数据并爬取
        与其他爬虫模块保持一致的接口
        """
        return self.crawl()


# 兼容旧接口
Class_Browser_cdp = DynamicCrawler


if __name__ == "__main__":
    crawler = DynamicCrawler(project_name='default')
    result = crawler.crawl()
    print(result)
