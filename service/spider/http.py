"""
HTTP 请求响应收集模块
进行 HTTP 请求重放，收集响应数据
功能：
1. 接收list_http传参
2. 对list_http进行标准化处理，用key进行内存去重和数据库去重
3. 重放HTTP请求获取响应
4. 保存进入数据库
"""

import requests
import hashlib
from database.http_database import HttpDatabase
from database.html_database import HtmlDatabase
from service.Class_Core_Function import Class_Core_Function
from service.spider.http_standardization import standardize_request
from bs4 import BeautifulSoup
import warnings
from urllib3.exceptions import InsecureRequestWarning
warnings.filterwarnings('ignore', category=InsecureRequestWarning)


class HTTPCollector:
    """HTTP 收集器"""

    def __init__(self, project_name):
        self.project_name = project_name
        self.http_db = HttpDatabase(project_name)
        self.html_db = HtmlDatabase(project_name)
        self.core_function = Class_Core_Function()
        # 获取项目配置
        self.project_config = self.core_function.callback_project_config() or {}
        self.user_agent = self.project_config.get('user_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        self.timeout = self.project_config.get('timeout', 8)
        self.http_thread = self.project_config.get('http_thread', 10)
        self.domain_list = self.project_config.get('domain_list', [])
        # 文件类型配置
        self.file_type_allowed = self.project_config.get('file_type', [])
        self.file_type_disallowed = self.project_config.get('file_type_disallowed', [])

    def _extract_domain(self, url):
        """
        从网站URL中提取主域名，基于project_config中的domain_list进行匹配

        Args:
            url: URL

        Returns:
            str: 主域名
        """
        # 使用 callback_split_url(url, 2) 返回 www.xxx.com（不含端口）
        subdomain = self.core_function.callback_split_url(url, 2)
        if not subdomain:
            return ''

        # 如果没有domain_list，使用默认逻辑（取后两级）
        if not self.domain_list:
            parts = subdomain.split('.')
            if len(parts) >= 2:
                return '.'.join(parts[-2:])
            return subdomain

        # 从最长匹配开始（匹配更精确的域名优先）
        for domain in sorted(self.domain_list, key=len, reverse=True):
            if subdomain.endswith('.' + domain) or subdomain == domain:
                return domain

        # 未匹配到任何domain_list，返回默认后两级
        parts = subdomain.split('.')
        if len(parts) >= 2:
            return '.'.join(parts[-2:])
        return subdomain

    def _get_http_type(self, content_type='', file_extension=''):
        """
        判断 http_type
        0=未知, 1=HTML可渲染, 2=不可渲染文件
        使用项目配置中的 file_type（白名单）和 file_type_disallowed（黑名单）
        """
        ext = file_extension.lower() if file_extension else ''
        
        # 1. 黑名单（file_type_disallowed）-> 2
        if ext and ext in self.file_type_disallowed:
            return 2
        
        # 2. 白名单（file_type）-> 检查 content-type
        if ext and ext in self.file_type_allowed:
            if content_type and 'htm' in content_type.lower():
                return 1
            return 1  # 白名单文件默认可渲染
        
        # 3. content-type 判断
        if content_type:
            if 'htm' in content_type.lower():
                return 1
            return 2
        
        return 0

    def _replay_request(self, traffic):
        """
        重放 HTTP 请求

        Args:
            traffic: 流量数据字典（已包含标准化字段：key, url_path, url_generalization, param_feature, file_extension）

        Returns:
            dict: HTTP 响应数据
        """
        try:
            url = traffic.get('url', '')
            method = traffic.get('method', 'GET')
            headers = traffic.get('headers', {})
            body = traffic.get('body', '')

            # 添加User-Agent
            headers = dict(headers) if headers else {}
            headers['User-Agent'] = self.user_agent

            # 发送请求
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                data=body,
                timeout=self.timeout,
                allow_redirects=True,
                verify=False
            )

            # 自动识别网页编码，防止乱码
            response.encoding = response.apparent_encoding

            # 提取title
            title = ''
            if response.text:
                try:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    title = soup.title.string if soup.title and soup.title.string else ''
                except:
                    pass

            # 计算HTML的MD5
            html_md5 = ''
            html_len = len(response.text)
            html_text = response.text if response.text else ''
            if response.text:
                html_md5 = hashlib.md5(response.text.encode()).hexdigest()

            # 判断http_type
            content_type = getattr(response, 'headers', {}).get('Content-Type', '') if response else ''
            file_extension = traffic.get('file_extension', '')
            http_type = self._get_http_type(content_type, file_extension)

            # 返回完整数据结构（遵循数据库表结构）
            return {
                'url': url,
                'method': method,
                'body': body,
                'headers': headers,
                'subdomain': self.core_function.callback_split_url(url, 1),
                'domain': self._extract_domain(url),
                'website': self.core_function.callback_split_url(url, 0),
                'waf': 0,
                'title': title[:200],
                'port': self.core_function.callback_port_number(url),
                'current_url': response.url,
                'headers_response': dict(response.headers),
                'server': response.headers.get('Server', ''),
                'web_fingerprint': 'Null',
                'screenshot': '',
                'describe': 'Null',
                'tag': [],
                'html_md5': html_md5,
                'html_browser_md5': '',
                'html_len': html_len,
                'time_first': traffic.get('time', self.core_function.callback_time(0)),
                'time_update': self.core_function.callback_time(0),
                'http_status_code': response.status_code,
                'status': 0,
                # 标准化字段（从traffic中获取）
                'url_path': traffic.get('url_path', ''),
                'url_generalization': traffic.get('url_generalization', ''),
                'param_feature': traffic.get('param_feature', ''),
                'key': traffic.get('key', ''),
                'http_type': http_type,
                'file_extension': traffic.get('file_extension', ''),
                # HTML字段（用于保存到html表，不入库http表）
                '_html': html_text
            }

        except Exception as e:
            return None

    def _process_single_http(self, traffic):
        """
        处理单个HTTP请求

        Args:
            traffic: 流量数据

        Returns:
            dict: 处理结果
        """
        return self._replay_request(traffic)

    def collect_and_save(self, http_requests):
        """
        收集并保存HTTP请求响应
        1. 对list_http进行标准化处理，用key进行内存去重和数据库去重
        2. 多线程重放请求获取响应
        3. 保存到数据库

        Args:
            http_requests: 已提取的HTTP请求列表（来自project_{name}_traffic）

        Returns:
            dict: {'success': bool, 'count': int, 'new_count': int, 'message': str}
        """
        try:
            # 1. 标准化处理 + 内存去重 + 数据库去重
            key_set = set()  # 内存去重集合
            new_http_requests = []

            for traffic in http_requests:
                # 标准化请求获取key
                std_result = standardize_request(traffic)
                key = std_result.get('key', '')

                # 内存去重：同一个key只处理一次
                if key in key_set:
                    continue
                key_set.add(key)

                # 数据库去重：查询数据库判断是否存在
                if not self.http_db.exists_by_key(key):
                    # 合并标准化结果到原始数据
                    traffic['key'] = key
                    traffic['url_path'] = std_result.get('url_path', '')
                    traffic['url_generalization'] = std_result.get('url_generalization', '')
                    traffic['param_feature'] = std_result.get('param_feature', '')
                    traffic['file_extension'] = std_result.get('file_extension', '')
                    new_http_requests.append(traffic)

            if not new_http_requests:
                return {
                    'success': True,
                    'count': len(http_requests),
                    'new_count': 0,
                    'message': '没有新的HTTP请求需要处理'
                }

            # 2. 使用标准函数多线程处理HTTP请求
            processed_data = []

            def process_wrapper(traffic):
                """包装函数，用于多线程调用"""
                result = self._process_single_http(traffic)
                if result:
                    processed_data.append(result)

            self.core_function.threadpool_Core_Function(process_wrapper, new_http_requests, self.http_thread)

            # 3. 保存到数据库
            saved_count = 0
            html_saved_count = 0
            for data in processed_data:
                try:
                    # 提取HTML字段（不入库http表）
                    html_text = data.pop('_html', '')
                    
                    # 保存HTTP数据
                    if self.http_db.import_http(data):
                        saved_count += 1
                        
                        # 保存HTML数据到html表（所有响应都保存）
                        if data.get('html_md5') and html_text:
                            result = self.html_db.import_html({
                                'html': html_text,
                                'html_md5': data['html_md5'],
                                'html_len': data.get('html_len', 0)
                            })
                            if result:
                                html_saved_count += 1
                except:
                    pass

            return {
                'success': True,
                'count': len(http_requests),
                'new_count': saved_count,
                'html_count': html_saved_count,
                'message': f'成功保存 {saved_count} 个新HTTP响应，{html_saved_count} 个HTML（总接收 {len(http_requests)} 个）'
            }

        except Exception as e:
            return {
                'success': False,
                'count': 0,
                'new_count': 0,
                'message': f'收集HTTP请求失败: {str(e)}'
            }
