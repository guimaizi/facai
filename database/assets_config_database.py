# coding: utf-8
"""
资产管理配置数据库操作
@Time :    3/11/2026
@Author:  facai
@File: assets_config_database.py
@Software: VSCode
"""
import os
from database.mongodb_handler import MongoDBHandler


class AssetsConfigDatabase:
    def __init__(self):
        self.db = MongoDBHandler()
    
    def get_project_data_path(self, project_name):
        """
        获取项目数据目录路径
        :param project_name: 项目名称
        :return: 项目数据目录路径
        """
        try:
            from service.Class_Core_Function import Class_Core_Function
            core = Class_Core_Function()
            root_path = core.Path.replace('service', '')
            return os.path.join(root_path, 'project_data', project_name)
        except Exception as e:
            print(f'获取项目数据路径失败: {str(e)}')
            return None
    
    def read_whitelist_domain(self, project_name):
        """
        读取域名白名单
        :param project_name: 项目名称
        :return: 域名列表
        """
        project_path = self.get_project_data_path(project_name)
        if not project_path:
            return []
        
        file_path = os.path.join(project_path, 'whitelist_domain.txt')
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    domains = [line.strip() for line in f.readlines() if line.strip()]
                return domains
        except Exception as e:
            print(f'读取域名白名单失败: {str(e)}')
        return []
    
    def write_whitelist_domain(self, project_name, domains):
        """
        写入域名白名单
        :param project_name: 项目名称
        :param domains: 域名列表
        :return: 成功返回True，失败返回False
        """
        project_path = self.get_project_data_path(project_name)
        if not project_path:
            return False
        
        file_path = os.path.join(project_path, 'whitelist_domain.txt')
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                for domain in domains:
                    f.write(domain.strip() + '\n')
            return True
        except Exception as e:
            print(f'写入域名白名单失败: {str(e)}')
            return False
    
    def read_blocklist_domain(self, project_name):
        """
        读取域名黑名单
        :param project_name: 项目名称
        :return: 域名列表
        """
        project_path = self.get_project_data_path(project_name)
        if not project_path:
            return []
        
        file_path = os.path.join(project_path, 'blocklist_domain.txt')
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    domains = [line.strip() for line in f.readlines() if line.strip()]
                return domains
        except Exception as e:
            print(f'读取域名黑名单失败: {str(e)}')
        return []
    
    def write_blocklist_domain(self, project_name, domains):
        """
        写入域名黑名单
        :param project_name: 项目名称
        :param domains: 域名列表
        :return: 成功返回True，失败返回False
        """
        project_path = self.get_project_data_path(project_name)
        if not project_path:
            return False
        
        file_path = os.path.join(project_path, 'blocklist_domain.txt')
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                for domain in domains:
                    f.write(domain.strip() + '\n')
            return True
        except Exception as e:
            print(f'写入域名黑名单失败: {str(e)}')
            return False
    
    def read_blocklist_url(self, project_name):
        """
        读取URL黑名单
        :param project_name: 项目名称
        :return: URL列表
        """
        project_path = self.get_project_data_path(project_name)
        if not project_path:
            return []
        
        file_path = os.path.join(project_path, 'blocklist_url.txt')
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    urls = [line.strip() for line in f.readlines() if line.strip()]
                return urls
        except Exception as e:
            print(f'读取URL黑名单失败: {str(e)}')
        return []
    
    def write_blocklist_url(self, project_name, urls):
        """
        写入URL黑名单
        :param project_name: 项目名称
        :param urls: URL列表
        :return: 成功返回True，失败返回False
        """
        project_path = self.get_project_data_path(project_name)
        if not project_path:
            return False
        
        file_path = os.path.join(project_path, 'blocklist_url.txt')
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                for url in urls:
                    f.write(url.strip() + '\n')
            return True
        except Exception as e:
            print(f'写入URL黑名单失败: {str(e)}')
            return False
    
    def import_domains_to_http(self, project_name, domains, source=1):
        """
        导入域名到HTTP临时表
        :param project_name: 项目名称
        :param domains: 域名列表
        :param source: 来源标识，默认为1
        :return: 成功返回True，失败返回False
        """
        try:
            from service.Class_Core_Function import Class_Core_Function
            from urllib.parse import urlparse
            
            core = Class_Core_Function()
            collection_name = f'project_{project_name}_traffic'
            
            success_count = 0
            for domain in domains:
                if not domain.strip():
                    continue
                
                # 标准化URL
                url = core.callback_url(domain)
                parsed = urlparse(url)
                
                if not parsed.scheme:
                    url = 'http://' + url
                    parsed = urlparse(url)
                
                data = {
                    'url': url,
                    'website': core.callback_split_url(url, 0),
                    'domain': parsed.netloc,
                    'method': 'GET',
                    'status': 0,
                    'source': source,
                    'time': core.callback_time(0)
                }
                
                result = self.db.insert_one(collection_name, data)
                if result:
                    success_count += 1
            
            return {
                'success': True,
                'total': len([d for d in domains if d.strip()]),
                'imported': success_count
            }
        except Exception as e:
            print(f'导入域名到HTTP表失败: {str(e)}')
            return {
                'success': False,
                'message': str(e)
            }
    
    def import_urls_to_http(self, project_name, urls, source=1):
        """
        导入URL到HTTP临时表
        :param project_name: 项目名称
        :param urls: URL列表
        :param source: 来源标识，默认为1
        :return: 成功返回True，失败返回False
        """
        try:
            from service.Class_Core_Function import Class_Core_Function
            
            core = Class_Core_Function()
            collection_name = f'project_{project_name}_traffic'
            
            success_count = 0
            for url in urls:
                if not url.strip():
                    continue
                
                # 标准化URL
                url = core.callback_url(url)
                
                request = core.create_request(url)
                
                data = {
                    'url': url,
                    'website': request['website'],
                    'method': request['method'],
                    'headers': request['headers'],
                    'body': request['body'],
                    'status': 0,
                    'source': source,
                    'time': core.callback_time(0)
                }
                
                result = self.db.insert_one(collection_name, data)
                if result:
                    success_count += 1
            
            return {
                'success': True,
                'total': len([u for u in urls if u.strip()]),
                'imported': success_count
            }
        except Exception as e:
            print(f'导入URL到HTTP表失败: {str(e)}')
            return {
                'success': False,
                'message': str(e)
            }
