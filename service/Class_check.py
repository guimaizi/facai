"""
@Time :    12/1/2024 15:02
@Author:  fff
@File: class_check.py
@Software: PyCharm
;验证域名、站点、url、http是否符合项目配置标准
"""
from re import S
from urllib.parse import urlparse

from jinja2.utils import F
from service.Class_Core_Function import Class_Core_Function
import os


class class_check:
    """项目配置验证类 - 重构版"""

    def __init__(self):
        self.Core_Function = Class_Core_Function()
        self.config = None
        self.whitelist_domains = []
        self.blocklist_domains = []
        self.blocklist_urls = []
        self._load_config()
        self._load_lists()

    def _load_config(self):
        """加载项目配置"""
        try:
            # 获取当前运行的项目配置
            config = self.Core_Function.callback_project_config()
            if config:
                self.config = config
        except Exception as e:
            print(f"加载项目配置失败: {str(e)}")

    def _load_lists(self):
        """加载白名单和blocklist文件"""
        try:
            # 获取当前运行的项目配置
            config = self.Core_Function.callback_project_config()
            if not config:
                return
            project_name = config.get('Project', 'default')

            project_data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'project_data', project_name)

            # 加载域名白名单
            whitelist_domain_file = os.path.join(project_data_dir, 'whitelist_domain.txt')
            if os.path.exists(whitelist_domain_file):
                with open(whitelist_domain_file, 'r', encoding='utf-8') as f:
                    self.whitelist_domains = [line.strip().lower() for line in f if line.strip()]

            # 加载域名blocklist
            blocklist_domain_file = os.path.join(project_data_dir, 'blocklist_domain.txt')
            if os.path.exists(blocklist_domain_file):
                with open(blocklist_domain_file, 'r', encoding='utf-8') as f:
                    self.blocklist_domains = [line.strip().lower() for line in f if line.strip()]

            # 加载URL blocklist
            blocklist_url_file = os.path.join(project_data_dir, 'blocklist_url.txt')
            if os.path.exists(blocklist_url_file):
                with open(blocklist_url_file, 'r', encoding='utf-8') as f:
                    self.blocklist_urls = [line.strip().lower() for line in f if line.strip()]
        except Exception as e:
            print(f"加载列表文件失败: {str(e)}")
    
    def check_is_url(self,text):
        '''
        检查文本是否为URL
        :param text:
        :return:
        '''
        try:
            # 解析URL
            result = urlparse(text)
            # 有效URL需满足：有协议（scheme）且有域名/IP（netloc）
            return True
        except Exception:
            # 解析失败则判定为非URL
            return False

    def check_file_ext(self, url):
        """
        URL后缀名检测
        :param url: URL地址
        :return: True表示通过检测，False表示不通过
        """
        if not self.config:
            return False

        file_ext = self.Core_Function.callback_file_extensions(url)

        # 如果url没有文件后缀名，通过
        if not file_ext:
            return True

        # 检查文件后缀名是否在禁止列表中
        file_type_disallowed = self.config.get('file_type_disallowed', [])
        if file_ext.lower() not in file_type_disallowed:
            return True

        return False

    def check_traffic_domain(self, domain):
        """
        流量域名检测 - 检查域名是否在项目配置的domain_list范围内
        :param domain: 域名
        :return: True表示在范围内，False表示不在
        """
        if not self.config:
            return False

        domain = domain.lower()
        domain_list = self.config.get('domain_list', [])

        for allowed_domain in domain_list:
            allowed_domain = allowed_domain.lower()
            # 支持子域名匹配和完全匹配
            if domain.endswith('.' + allowed_domain) or domain == allowed_domain or domain in self.whitelist_domains:
                return True
        return False

    def check_traffic_url(self, url):
        """
        流量URL检测
        :param url: URL地址
        :return: True表示通过检测，False表示不通过
        """
        # 先检查是否为有效URL
        if not self.check_is_url(url):
            return False

        # 提取域名
        domain = self.Core_Function.callback_split_url(url, 2)
        if not domain:
            return False

        # 域名检测 + 文件后缀检测
        return self.check_traffic_domain(domain) and self.check_file_ext(url)

    def check_domain(self, domain):
        """
        域名检测：白名单 + blocklist检测
        :param domain: 域名
        :return: True表示通过检测，False表示不通过
        """
        domain = domain.lower()
        if self.check_traffic_domain(domain):
            return True

        # 第一优先级：检查是否在白名单内（whitelist_domain.txt），存在则直接返回True
        for whitelist_domain in self.whitelist_domains:
            whitelist_domain = whitelist_domain.lower()
            # 支持子域名匹配和完全匹配
            if domain.endswith('.' + whitelist_domain) or domain == whitelist_domain:
                return True

        # 白名单检测未通过，检查blocklist
        # 第二优先级：blocklist检测 - 不在blocklist内（blocklist_domain.txt）
        for blocklist_domain in self.blocklist_domains:
            # blocklist域名以.开头，匹配子域名
            if blocklist_domain.startswith('.'):
                if domain.endswith(blocklist_domain) or domain == blocklist_domain[1:]:
                    return False
            # 完全匹配
            elif domain == blocklist_domain:
                return False

        return True

    def check_site(self, site):
        """
        站点检测
        :param site: 站点地址
        :return: True表示通过检测，False表示不通过
        """
        if not self.check_is_url(site):
            return False

        domain = self.Core_Function.callback_split_url(site, 2)
        if domain:
            return self.check_domain(domain)

        return False

    def check_url(self, url):
        """
        ;读取流量表时去重
        ;URL检测：白名单域名全局绕过、黑名单域名过滤、url黑名单过滤 
        :param url: URL地址
        :return: True表示通过检测，False表示不通过
        """
        #检测是否为url
        if not self.check_is_url(url):
            return False
        #域名检测
        domain = self.Core_Function.callback_split_url(url, 2)
        #print(domain)
        #白名单检测
        if domain in self.whitelist_domains:
            return True
        #黑名单检测
        for subdomain in self.blocklist_domains:
            if domain.endswith(subdomain):
                return False
        #url黑名单检测
        for url_blocklist in self.blocklist_urls:
            if url.startswith(url_blocklist):
                return False
        return True





if __name__ == '__main__':
    check_instance = class_check()

    # 测试文件后缀检测
    print("=== 测试文件后缀检测 ===")
    print(f"https://example.com/test.php: {check_instance.check_file_ext('https://example.com/test.php')}")
    print(f"https://example.com/test.exe: {check_instance.check_file_ext('https://example.com/test.exe')}")
    print(f"https://example.com/path: {check_instance.check_file_ext('https://example.com/path')}")

    # 测试流量域名检测
    print("\n=== 测试流量域名检测 ===")
    print(f"www.molun.com: {check_instance.check_traffic_domain('www.molun.com')}")

    # 测试域名检测（组合检测）
    print("\n=== 测试域名检测 ===")
    print(f"www.molun.com: {check_instance.check_domain('www.molun.com')}")

    # 测试站点检测
    print("\n=== 测试站点检测 ===")
    print(f"https://www.molun.com: {check_instance.check_site('https://www.molun.com')}")

    # 测试URL检测
    print("\n=== 测试URL检测 ===")
    print(f"https://www.molun.com/test.php: {check_instance.check_url('https://www.molun.com/test.php')}")

