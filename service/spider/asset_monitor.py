# coding: utf-8
"""
资产监控模块
监控网站资产变化，检测HTML内容更新
功能：
1. 对websites表进行更新，把状态都更新为0待处理
2. 重新对websites表进行重放，把html导入进import_html，之后对比html长度变化
3. 如有长度变化进行动态爬取，更新title、截图数据、time_update字段
"""

import warnings
from bs4 import XMLParsedAsHTMLWarning
from urllib3.exceptions import InsecureRequestWarning
# 忽略HTTPS证书警告
warnings.filterwarnings('ignore', category=InsecureRequestWarning)
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

import time
import requests
from database.website_database import WebsiteDatabase
from database.html_database import HtmlDatabase
from database.project_database import ProjectDatabase
from service.Class_Core_Function import Class_Core_Function
from service.spider.dynamic_crawler import DynamicCrawler


class AssetMonitor:
    """资产监控器"""

    def __init__(self):
        self.core_function = Class_Core_Function()
        # 获取项目配置
        self.project_config = self.core_function.callback_project_config()
        if not self.project_config:
            raise ValueError('无法获取项目配置，请确保有运行中的项目')

        self.project_name = self.project_config.get('Project')
        if not self.project_name:
            raise ValueError('项目配置中缺少项目名称')

        self.website_db = WebsiteDatabase(self.project_name)
        self.html_db = HtmlDatabase(self.project_name)
        self.user_agent = self.project_config.get('user_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        self.timeout = self.project_config.get('timeout', 8)
        self.http_thread = self.project_config.get('http_thread', 10)
        self.browser_thread = self.project_config.get('browser_thread', 10)
        # 运行状态
        self.is_running = True

    def reset_websites_status(self):
        """
        重置所有网站状态为待处理（status=0）
        
        Returns:
            dict: {'success': bool, 'count': int, 'message': str}
        """
        try:
            if not self.website_db.collection_name:
                return {'success': False, 'count': 0, 'message': '未找到项目'}

            # 统计总数
            total_count = self.website_db.count_websites()

            if total_count == 0:
                return {'success': True, 'count': 0, 'message': '没有需要重置的网站'}

            # 批量更新所有记录的status为0
            result = self.website_db.db_handler.update_many(
                self.website_db.collection_name,
                {},  # 更新所有记录
                {'status': 0}
            )

            updated_count = result if result else total_count

            return {
                'success': True,
                'count': updated_count,
                'message': f'成功重置 {updated_count} 个网站状态为待处理'
            }

        except Exception as e:
            return {
                'success': False,
                'count': 0,
                'message': f'重置状态失败: {str(e)}'
            }

    def _fetch_website_html(self, website_data):
        """
        获取单个网站的HTML内容

        Args:
            website_data: 网站数据字典

        Returns:
            dict: {'url': str, 'html': str, 'html_md5': str, 'html_len': int, 'status_code': int}
        """
        url = website_data.get('url')
        if not url:
            return None

        try:
            # 使用 create_request 创建请求
            request_data = self.core_function.create_request(url)
            headers = request_data.get('headers', {})

            response = requests.get(url, headers=headers, timeout=self.timeout, verify=False)
            response.encoding = response.apparent_encoding

            html_text = response.text
            html_md5 = self.core_function.md5_convert(html_text) if html_text else ''
            html_len = len(html_text) if html_text else 0

            return {
                'url': url,
                'html': html_text,
                'html_md5': html_md5,
                'html_len': html_len,
                'status_code': response.status_code,
                'website_id': website_data.get('_id'),
                'old_html_len': website_data.get('html_len', 0)
            }

        except Exception:
            return None

    def replay_websites(self):
        """
        重放网站列表，检测HTML变化
        1. 获取所有待处理网站（status=0）
        2. 重新请求获取HTML
        3. 导入HTML到html表（通过import_html方法，MD5去重）
        4. 对比html_len变化

        Returns:
            dict: {'success': bool, 'total': int, 'changed': int, 'changed_urls': list, 'message': str}
        """
        try:
            if not self.website_db.collection_name:
                return {'success': False, 'total': 0, 'changed': 0, 'changed_urls': [], 'message': '未找到项目'}

            total_processed = 0
            changed_count = 0
            changed_urls = []

            # 分批处理，batch_size 使用 http_thread
            while True:
                # 获取待处理网站
                websites = self.website_db.db_handler.find(
                    self.website_db.collection_name,
                    {'status': 0},
                    projection={'_id': 1, 'url': 1, 'html_len': 1},
                    limit=self.http_thread
                )

                if not websites:
                    break

                # 多线程处理
                def process_website(website):
                    return self._fetch_website_html(website)

                results = []
                self.core_function.threadpool_Core_Function(
                    lambda w: results.append(process_website(w)),
                    websites,
                    self.http_thread
                )

                # 处理结果
                for result in results:
                    if not result:
                        continue

                    url = result['url']
                    html_content = result['html']
                    html_md5 = result['html_md5']
                    html_len = result['html_len']
                    old_html_len = result['old_html_len']
                    website_id = result['website_id']

                    # 导入HTML到html表（如果md5不存在则写入）
                    if html_md5 and html_content:
                        self.html_db.import_html({
                            'html': html_content,
                            'html_md5': html_md5,
                            'html_len': html_len,
                            'status': 0
                        })

                    # 检测长度变化（变化大于20%）
                    len_diff = abs(html_len - old_html_len)
                    if old_html_len > 0:
                        change_ratio = len_diff / old_html_len
                        # 变化大于20%
                        if change_ratio > 0.2:
                            changed_count += 1
                            changed_urls.append({
                                'url': url,
                                'old_len': old_html_len,
                                'new_len': html_len,
                                'diff': len_diff,
                                'change_ratio': f'{change_ratio * 100:.1f}%'
                            })
                    else:
                        # 旧长度为0，新长度不为0，视为变化
                        if html_len > 0:
                            changed_count += 1
                            changed_urls.append({
                                'url': url,
                                'old_len': old_html_len,
                                'new_len': html_len,
                                'diff': len_diff,
                                'change_ratio': '100%'
                            })

                    # 更新网站状态为已处理（status=1）和新的html_len、html_md5
                    self.website_db.db_handler.update_one(
                        self.website_db.collection_name,
                        {'_id': website_id},
                        {'status': 1, 'html_len': html_len, 'html_md5': html_md5}
                    )

                    total_processed += 1

            return {
                'success': True,
                'total': total_processed,
                'changed': changed_count,
                'changed_urls': changed_urls,
                'message': f'处理 {total_processed} 个网站，发现 {changed_count} 个变化'
            }

        except Exception as e:
            return {
                'success': False,
                'total': 0,
                'changed': 0,
                'changed_urls': [],
                'message': f'重放网站失败: {str(e)}'
            }

    def crawl_changed_websites(self, changed_urls):
        """
        对变化的网站进行动态爬取
        更新title、screenshot、html_browser_md5、time_update字段
        
        注意：请求数量需小于等于 browser_thread 配置值，避免浏览器队列溢出
        
        Args:
            changed_urls: 变化的URL列表 [{'url': str, ...}, ...]
            
        Returns:
            dict: {'success': bool, 'crawled': int, 'message': str}
        """
        try:
            if not changed_urls:
                return {'success': True, 'crawled': 0, 'message': '没有需要爬取的网站'}

            # 检查服务状态
            crawler = DynamicCrawler(self.project_name)
            services_status = crawler.check_services_status()

            if not services_status['can_run']:
                return {
                    'success': False,
                    'crawled': 0,
                    'message': f"服务未就绪: {services_status['message']}"
                }

            # 限制请求数量不超过 browser_thread（分批处理）
            total_crawled = 0
            batch_size = self.browser_thread  # 每批不超过 browser_thread

            for i in range(0, len(changed_urls), batch_size):
                batch_urls = changed_urls[i:i + batch_size]

                # 构建请求数据
                list_request = []
                for item in batch_urls:
                    url = item.get('url')
                    if url:
                        request_data = self.core_function.create_request(url)
                        request_data['_source'] = 'asset_monitor'  # 标记来源
                        list_request.append(request_data)

                if not list_request:
                    continue

                print(f"  正在爬取第 {i+1}-{min(i+batch_size, len(changed_urls))} 个网站...")
                
                # 调用动态爬虫
                # DynamicCrawler 会自动更新 title、screenshot、html_browser_md5、time_update 字段
                crawl_result = crawler.crawl(list_request)
                
                if crawl_result.get('success'):
                    total_crawled += crawl_result.get('pages', 0)
                else:
                    print(f"  警告: {crawl_result.get('message', '未知错误')}")

            return {
                'success': True,
                'crawled': total_crawled,
                'message': f'成功爬取 {total_crawled} 个变化的网站'
            }

        except Exception as e:
            return {
                'success': False,
                'crawled': 0,
                'message': f'动态爬取失败: {str(e)}'
            }

    def monitor(self):
        """
        执行完整的资产监控流程
        1. 重置所有网站状态为待处理
        2. 重放网站列表，检测HTML变化
        3. 对变化的网站进行动态爬取，更新title、截图、time_update等字段
        
        Returns:
            dict: {'success': bool, 'total': int, 'changed': int, 'crawled': int, 'message': str}
        """
        try:
            print("=" * 50)
            print("开始资产监控")
            print("=" * 50)

            # 1. 重置状态
            print("\n[1/3] 重置网站状态...")
            reset_result = self.reset_websites_status()
            print(f"  {reset_result['message']}")

            if not reset_result['success']:
                return {
                    'success': False,
                    'total': 0,
                    'changed': 0,
                    'crawled': 0,
                    'message': reset_result['message']
                }

            # 2. 重放网站，检测变化
            print("\n[2/3] 重放网站，检测HTML变化...")
            replay_result = self.replay_websites()
            print(f"  {replay_result['message']}")

            if not replay_result['success']:
                return {
                    'success': False,
                    'total': replay_result['total'],
                    'changed': 0,
                    'crawled': 0,
                    'message': replay_result['message']
                }

            # 3. 动态爬取变化的网站
            changed_urls_list = replay_result.get('changed_urls')
            changed_urls = changed_urls_list if isinstance(changed_urls_list, list) else []
            if changed_urls:
                print(f"\n[3/3] 动态爬取 {len(changed_urls)} 个变化的网站...")
                print(f"  并发限制: browser_thread={self.browser_thread}")
                crawl_result = self.crawl_changed_websites(changed_urls)
                print(f"  {crawl_result['message']}")
            else:
                print("\n[3/3] 没有检测到变化的网站，跳过动态爬取")
                crawl_result = {'success': True, 'crawled': 0, 'message': '无变化'}

            print("\n" + "=" * 50)
            print("资产监控完成")
            print(f"总计: {replay_result['total']} | 变化: {replay_result['changed']} | 爬取: {crawl_result.get('crawled', 0)}")
            print("=" * 50)

            return {
                'success': True,
                'total': replay_result['total'],
                'changed': replay_result['changed'],
                'crawled': crawl_result.get('crawled', 0),
                'changed_urls': changed_urls,
                'message': f"监控完成: 处理 {replay_result['total']} 个网站，发现 {replay_result['changed']} 个变化，爬取 {crawl_result.get('crawled', 0)} 个"
            }

        except Exception as e:
            return {
                'success': False,
                'total': 0,
                'changed': 0,
                'crawled': 0,
                'message': f'监控失败: {str(e)}'
            }

    def run(self):
        """
        运行资产监控服务（持续循环）
        循环逻辑：
        1. 检查 monitor_service 是否为 1（通过 callback_project_config）
        2. 如果为 1，执行监控流程
        3. 如果不为 1，睡眠10秒后继续检查
        """
        while self.is_running:
            try:
                # 检查 monitor_service 是否为 1
                project_config = self.core_function.callback_project_config()
                if not project_config:
                    print("未获取到项目配置，睡眠10秒...")
                    time.sleep(10)
                    continue

                service_lock = project_config.get('service_lock', {})
                monitor_service = service_lock.get('monitor_service', 0)

                # monitor_service 不为 1，睡眠10秒重试
                if monitor_service != 1:
                    print(f"资产监控服务未开启 (monitor_service={monitor_service})，睡眠10秒...")
                    time.sleep(10)
                    continue

                # 执行监控流程
                print("\n开始资产监控...")
                result = self.monitor()
                print(f"监控结果: {result['message']}")

                # 监控完成后，关闭监控服务，开启爬虫服务
                print("监控完成，切换服务状态: monitor_service=0, spider_service=1")
                project_db = ProjectDatabase()
                project_db.update_service_lock(self.project_name, 'monitor_service', 0)
                project_db.update_service_lock(self.project_name, 'spider_service', 1)

                # 监控完成后，睡眠一段时间再进行下一轮检查
                print("服务状态已切换，等待10秒后继续...")
                time.sleep(10)

            except Exception as e:
                self.core_function.callback_logging().error(f"资产监控运行异常: {e}")
                print(f"资产监控运行异常: {e}")
                # 出错后睡眠10秒再继续
                time.sleep(10)

        return {'success': True, 'message': '资产监控服务已停止'}


# 测试代码
if __name__ == '__main__':
    monitor = None
    try:
        monitor = AssetMonitor()
        print(f"项目名称: {monitor.project_name}")
        # 运行监控服务（持续循环，依赖 monitor_service）
        print("\n开始运行资产监控服务...")
        result = monitor.run()
        print(f"运行结果: {result['message']}")
    except KeyboardInterrupt:
        print("\n收到中断信号，停止监控...")
        if monitor:
            monitor.is_running = False
        print("监控已停止")
    except Exception as e:
        print(f"初始化失败: {e}")
