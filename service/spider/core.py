# coding: utf-8

"""
爬虫核心模块
负责调度其他模块，协调整个爬虫流程
"""

from re import T
import time
from database.traffic_database import TrafficDatabase
from service.Class_Core_Function import Class_Core_Function
from service import Class_check
from service.spider.subdomain import SubdomainCollector
from service.spider.website import WebsiteCollector
from service.spider.http import HTTPCollector
from service.spider.html import HTMLCollector
from service.spider.dynamic_crawler import DynamicCrawler

class SpiderCore:
    """爬虫核心类"""

    def __init__(self, project_name=None):
        self.core_function = Class_Core_Function()
        self.class_check = Class_check.class_check()
        # 如果没有指定项目名，尝试获取当前运行中的项目
        if project_name:
            self.project_name = project_name
        else:
            running_project = self.core_function.callback_project_config()
            self.project_name = running_project.get('Project') if running_project else None

        if not self.project_name:
            raise ValueError('无法获取项目名称，请确保有运行中的项目')

        self.traffic_db = TrafficDatabase(self.project_name)
        self.subdomain_collector = SubdomainCollector(self.project_name)
        self.website_collector = WebsiteCollector(self.project_name)
        self.http_collector = HTTPCollector(self.project_name)
        self.html_collector = HTMLCollector(self.project_name)
        self.chrome_cdp = DynamicCrawler(self.project_name)
        self.is_running = True



    def check_pending_data(self):
        """
        检查是否有待处理数据
        检查 project_{name}_traffic、project_{name}_html、project_{name}_website 表
        :return: dict {'has_pending': bool, 'counts': dict, 'total': int}
        """
        try:
            counts = {}
            
            # 检查 traffic 表
            traffic_collection = f"project_{self.project_name}_traffic"
            traffic_count = self.traffic_db.db_handler.count_documents(
                traffic_collection,
                {'status': 0}
            )
            counts['traffic'] = traffic_count
            
            # 检查 html 表（status=0 表示未处理）
            html_collection = f"project_{self.project_name}_html"
            html_count = self.traffic_db.db_handler.count_documents(
                html_collection,
                {'status': 0}
            )
            counts['html'] = html_count
            
            # 检查 website 表（status=0 表示未处理）
            website_collection = f"project_{self.project_name}_website"
            website_count = self.traffic_db.db_handler.count_documents(
                website_collection,
                {'status': 0}
            )
            counts['website'] = website_count
            
            total = sum(counts.values())
            
            return {
                'has_pending': total > 0,
                'counts': counts,
                'total': total
            }
            
        except Exception as e:
            self.core_function.callback_logging().error(f"检查待处理数据失败: {e}")
            return {
                'has_pending': False,
                'counts': {},
                'total': 0
            }

    def run_dynamic_crawler(self, list_request=None):
        """
        运行动态爬虫
        :param list_request: 请求数据列表（可选，为空则自动从数据库获取）
        :return: {'success': bool, 'message': str, 'pages': int, 'urls': int, 'htmls': int}
        """
        return self.chrome_cdp.crawl(list_request)

    def fetch_unprocessed_traffic(self, limit=200):
        """
        获取未处理的流量数据

        Args:
            limit: 获取数量限制，默认200条

        Returns:
            dict: {'success': bool, 'count': int, 'data': list, 
                    'subdomains': list, 'websites': list, 'http_requests': list, 'message': str}
        """
        try:
            # 从 project_{name}_traffic 表获取 status=0 的未处理请求
            collection_name = f"project_{self.project_name}_traffic"
            query = {'status': 0}  # 0=未处理

            # 在数据库层面限制数量，只查询需要的条数
            traffic_list = self.traffic_db.db_handler.find(
                collection_name,
                query,
                projection={'_id': 1, 'url': 1, 'method': 1, 'headers': 1, 'body': 1, 'time': 1, 'website': 1},
                limit=limit
            )

            # 读取后将status设置为1（已处理）
            for traffic in traffic_list:
                if traffic.get('_id'):
                    self.traffic_db.db_handler.update_one(
                        collection_name,
                        {'_id': traffic['_id']},
                        {'status': 1}
                    )

            # http流量请求基础过滤,过滤出子域名、website、http流量
            list_subdomain = []
            list_website = []
            list_http = []
            # 去重get方式的 url
            list_url=[]

            for traffic in traffic_list:
                if self.class_check.check_url(traffic.get('url')):
                    list_subdomain.append(self.core_function.callback_split_url(traffic.get('url'), 2).lower())
                    list_website.append(traffic.get('website').lower())
                    if traffic.get('method') == 'GET' and traffic.get('url') not in list_url:
                        list_http.append(traffic)
                        list_url.append(traffic.get('url'))
                    else:
                        list_http.append(traffic)

            # 去重
            list_website = list(set(list_website))
            list_subdomain = list(set(list_subdomain))
            count = len(traffic_list)
            #print(list_http)
            return {
                'success': True,
                'count': count,
                'data': traffic_list,
                'subdomains': list_subdomain,
                'websites': list_website,
                'http_requests': list_http,
                'message': f'成功获取 {count} 条未处理的流量数据'
            }

        except Exception as e:
            return {
                'success': False,
                'count': 0,
                'data': [],
                'subdomains': [],
                'websites': [],
                'http_requests': [],
                'message': f'获取流量数据失败: {str(e)}'
            }

    def run(self):
        """
        运行爬虫主流程（持续循环）
        循环逻辑：
        1. 检查 spider_service 是否为 1（通过 callback_project_config）
        2. 检查 traffic、html、website 表是否有待处理数据
        3. 两个条件都满足才执行处理流程
        4. 任一条件不满足则睡眠10秒后继续检查
        """
        while self.is_running:
            try:
                # 1. 检查 spider_service 是否为 1
                project_config = self.core_function.callback_project_config()
                if not project_config:
                    print("未获取到项目配置，睡眠10秒...")
                    time.sleep(10)
                    continue

                service_lock = project_config.get('service_lock', {})
                spider_service = service_lock.get('spider_service', 0)

                # spider_service 不为 1，睡眠10秒重试
                if spider_service != 1:
                    print(f"爬虫服务未开启 (spider_service={spider_service})，睡眠10秒...")
                    time.sleep(10)
                    continue

                # 2. 检查是否有待处理数据
                pending = self.check_pending_data()

                if not pending['has_pending']:
                    # 没有待处理数据，睡眠10秒
                    counts = pending.get('counts', {})
                    print(f"没有待处理数据，睡眠10秒... (traffic: {counts.get('traffic', 0)}, "
                          f"html: {counts.get('html', 0)}, website: {counts.get('website', 0)})")
                    time.sleep(10)
                    continue

                # 有待处理数据，输出统计
                counts = pending.get('counts', {})
                if isinstance(counts, dict):
                    print(f"发现待处理数据 - traffic: {counts.get('traffic', 0)}, "
                          f"html: {counts.get('html', 0)}, website: {counts.get('website', 0)}")
                else:
                    print(f"发现待处理数据 - 总计: {pending.get('total', 0)}")

                # 执行处理流程
                self._process_once()

            except Exception as e:
                self.core_function.callback_logging().error(f"爬虫运行异常: {e}")
                print(f"爬虫运行异常: {e}")
                # 出错后睡眠10秒再继续
                time.sleep(10)

        return {'success': True, 'message': '爬虫服务已停止'}

    def _process_once(self):
        """
        执行一次完整的处理流程
        1. 获取未处理的流量数据
        2. 子域名收集
        3. 站点收集
        4. HTTP 请求响应收集
        5. 动态爬虫
        6. HTML 收集
        """
        try:
            # 1. 获取未处理的流量数据
            result = self.fetch_unprocessed_traffic(limit=200)
            if not result['success']:
                print(f"获取流量数据失败: {result['message']}")
                return

            traffic_list = result['data']
            count = result['count']

            if count == 0:
                # 没有流量数据，但可能有其他待处理数据
                pass
            else:
                # 获取过滤后的数据
                subdomains = result.get('subdomains', [])
                websites = result.get('websites', [])
                http_requests = result.get('http_requests', [])
                
                # 2. 子域名收集
                if subdomains:
                    subdomain_result = self.subdomain_collector.collect_and_save(subdomains)
                    print(f"子域名收集: {subdomain_result['message']}")
                
                # 3. 站点收集
                if websites:
                    website_result = self.website_collector.collect_and_save(websites)
                    print(f"站点收集: {website_result['message']}")

                # 4. HTTP 请求响应收集
                if http_requests:
                    http_result = self.http_collector.collect_and_save(http_requests)
                    print(f"HTTP收集: {http_result['message']}")

            # 5. 动态爬虫（自动从数据库获取未处理的URL）
            dynamic_result = self.run_dynamic_crawler()
            print(f"动态爬虫: {dynamic_result['message']}")

            # 6. HTML收集
            html_result = self.html_collector.process()
            print(f"HTML收集: {html_result['message']}")
            
        except Exception as e:
            self.core_function.callback_logging().error(f"处理流程异常: {e}")
            print(f"处理流程异常: {e}")



# 测试代码
if __name__ == '__main__':
    spider = SpiderCore('Tencent')
    print(f"项目名称: {spider.project_name}")

    # 检查待处理数据
    pending = spider.check_pending_data()
    print(f"待处理数据: {pending}")

    # 运行爬虫（会持续循环，依赖 spider_service 和待处理数据）
    print("\n开始运行爬虫...")
    try:
        result = spider.run()
        print(f"运行结果: {result['message']}")
    except KeyboardInterrupt:
        print("\n收到中断信号，停止爬虫...")
        spider.is_running = False
        print("爬虫已停止")

