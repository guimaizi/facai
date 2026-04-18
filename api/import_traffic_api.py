# coding: utf-8
'''
导入Traffic API,导入url、子域名、http请求
@Time :    3/15/2026
@Author:  facai
@File: import_traffic_api.py
@Software: VSCode
'''

from flask import Blueprint, request, jsonify
from database.mongodb_handler import MongoDBHandler
from database.project_database import ProjectDatabase
from service.Class_check import class_check
from service.Class_Core_Function import Class_Core_Function
import time


import_traffic_api = Blueprint('import_traffic_api', __name__)


class ImportTrafficAPI:
    """HTTP临时数据导入API - 可供其他Python代码直接调用"""

    def __init__(self):
        self.Core_Function = Class_Core_Function()
        self.class_check = class_check()
        self.project_db = ProjectDatabase()
        self.db_handler = MongoDBHandler()

    def _get_traffic_db(self, project_name=None):
        """获取traffic数据库实例和collection名称"""
        if not project_name:
            running_project = self.project_db.get_running_project()
            if running_project and 'Project' in running_project:
                project_name = running_project['Project']
            else:
                return None, None

        return self.db_handler, f"project_{project_name}_traffic"

    def _get_project_config(self, project_name=None):
        """获取项目配置"""
        if not project_name:
            running_project = self.project_db.get_running_project()
            if running_project and 'Project' in running_project:
                project_name = running_project['Project']
            else:
                return None
        return self.project_db.get_project_by_name(project_name)

    def import_traffic_url(self, url, project_name=None):
        """
        导入URL（接口1）
        :param url: URL地址，例如 "https://www.molun.com/"
        :param project_name: 可选，指定项目名称
        :return: {'success': bool, 'message': str}
        """
        try:
            url = url.strip()
            if not url:
                return {'success': False, 'message': 'URL不能为空'}

            db_handler, collection_name = self._get_traffic_db(project_name)
            if not db_handler or not collection_name:
                return {'success': False, 'message': '未找到运行中的项目'}

            # URL检测
            if not self.class_check.check_is_url(url):
                return {'success': False, 'message': 'URL格式错误'}

            # URL标准化
            url = self.Core_Function.callback_url(url)

            # URL转换为HTTP请求
            request_data = self.Core_Function.create_request(url)
            request_data['source'] = 1  # url生成
            request_data['status'] = 0  # 未处理

            # 插入数据库前进行check_traffic_url检测
            if not self.class_check.check_traffic_url(url):
                return {'success': False, 'message': 'URL不在流量范围内'}

            # 插入数据库到project_{name}_traffic表
            db_handler.insert_one(collection_name, request_data)

            return {'success': True, 'message': 'URL导入成功'}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    def import_traffic_subdomain(self, subdomain, project_name=None):
        """
        导入子域名（接口2）
        :param subdomain: 子域名，例如 "www.molun.com"
        :param project_name: 可选，指定项目名称
        :return: {'success': bool, 'message': str}
        """
        try:
            subdomain = subdomain.strip()
            if not subdomain:
                return {'success': False, 'message': '子域名不能为空'}

            db_handler, collection_name = self._get_traffic_db(project_name)
            if not db_handler or not collection_name:
                return {'success': False, 'message': '未找到运行中的项目'}

            # 子域名检测
            if not self.class_check.check_domain(subdomain):
                return {'success': False, 'message': '子域名格式错误'}

            # 子域名转为URL，再转为http请求
            project_config = self._get_project_config(project_name)
            scheme = 'http'
            port = 80
            if project_config:
                scheme = project_config.get('scheme', 'http')
                port = project_config.get('port', 80)

            # 子域名转为URL
            url = f"{scheme}://{subdomain}/"
            if scheme == 'http' and port != 80:
                url = f"{scheme}://{subdomain}:{port}/"
            elif scheme == 'https' and port != 443:
                url = f"{scheme}://{subdomain}:{port}/"

            # URL转换为HTTP请求
            request_data = self.Core_Function.create_request(url)
            request_data['source'] = 1  # url生成
            request_data['status'] = 0  # 未处理

            # 插入数据库前进行check_traffic_url检测
            if not self.class_check.check_traffic_url(url):
                return {'success': False, 'message': 'URL不在流量范围内'}

            # 插入数据库到project_{name}_traffic表
            db_handler.insert_one(collection_name, request_data)

            return {'success': True, 'message': '子域名导入成功'}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    def import_traffic_request(self, list_request, project_name=None):
        """
        导入HTTP请求列表（接口3）
        :param list_request: HTTP请求列表，每个请求为字典
        :param project_name: 可选，指定项目名称
        :return: {'success': bool, 'total': int, 'imported': int, 'skipped': int, 'errors': list}
        """
        try:
            if not list_request or not isinstance(list_request, list):
                return {'success': False, 'message': '请求列表为空或格式错误'}

            db_handler, collection_name = self._get_traffic_db(project_name)
            if not db_handler or not collection_name:
                return {'success': False, 'message': '未找到运行中的项目'}

            total = len(list_request)
            imported = 0
            skipped = 0
            errors = []

            for request_item in list_request:
                if not isinstance(request_item, dict):
                    skipped += 1
                    continue

                try:
                    # 提取URL或子域名
                    url_input = request_item.get('url', '').strip()
                    if not url_input:
                        skipped += 1
                        continue

                    # 判断是否为URL（包含http://或https://）或子域名
                    if url_input.startswith('http://') or url_input.startswith('https://'):
                        # URL处理
                        if not self.class_check.check_url(url_input):
                            skipped += 1
                            continue

                        # 标准化URL
                        url = self.Core_Function.callback_url(url_input)

                        # 构建请求数据
                        request_data = {
                            'url': url,
                            'website': request_item.get('website', self.Core_Function.callback_split_url(url, 0)),
                            'method': request_item.get('method', 'GET'),
                            'headers': request_item.get('headers', {}),
                            'body': request_item.get('body', ''),
                            'time': request_item.get('time', self.Core_Function.callback_time(0)),
                            'status': 0,  # 未处理
                            'scaner_status':0,
                            'source': request_item.get('source', 0)  # 0=流量捕捉, 1=url生成
                        }
                    else:
                        # 子域名处理
                        subdomain = url_input
                        if not self.class_check.check_domain(subdomain):
                            skipped += 1
                            continue

                        # 子域名转为URL
                        project_config = self._get_project_config(project_name)
                        scheme = 'http'
                        port = 80
                        if project_config:
                            scheme = project_config.get('scheme', 'http')
                            port = project_config.get('port', 80)

                        # 子域名转为URL
                        url = f"{scheme}://{subdomain}/"
                        if scheme == 'http' and port != 80:
                            url = f"{scheme}://{subdomain}:{port}/"
                        elif scheme == 'https' and port != 443:
                            url = f"{scheme}://{subdomain}:{port}/"

                        # URL转换为HTTP请求
                        request_data = self.Core_Function.create_request(url)
                        request_data['source'] = request_item.get('source', 1)  # url生成
                        request_data['status'] = 0  # 未处理
                        request_data['scaner_status']=0

                    # 插入数据库前进行check_traffic_url检测
                    if not self.class_check.check_traffic_url(url):
                        skipped += 1
                        continue

                    # 插入数据库到project_{name}_traffic表
                    db_handler.insert_one(collection_name, request_data)
                    imported += 1
                except Exception as e:
                    skipped += 1
                    errors.append(str(e))
                    continue

            return {
                'success': True,
                'message': f'导入完成',
                'total': total,
                'imported': imported,
                'skipped': skipped,
                'errors': errors
            }
        except Exception as e:
            return {'success': False, 'message': str(e)}


# 全局实例，避免每次请求都重新连接数据库
_import_api_instance = None

def get_import_api():
    """获取ImportTrafficAPI单例实例"""
    global _import_api_instance
    if _import_api_instance is None:
        _import_api_instance = ImportTrafficAPI()
    return _import_api_instance


# Web API路由 - 供HTTP调用
@import_traffic_api.route('/api/import/url', methods=['POST'])
def web_import_url():
    """
    导入URL（Web接口1）
    POST /api/import/url
    Body: {"url": "https://www.molun.com/"}
    """
    try:
        data = request.get_json()
        url = data.get('url', '')
        result = get_import_api().import_traffic_url(url)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@import_traffic_api.route('/api/import/subdomain', methods=['POST'])
def web_import_subdomain():
    """
    导入子域名（Web接口2）
    POST /api/import/subdomain
    Body: {"subdomain": "www.molun.com"}
    """
    try:
        data = request.get_json()
        subdomain = data.get('subdomain', '')
        result = get_import_api().import_traffic_subdomain(subdomain)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@import_traffic_api.route('/api/import/request', methods=['POST'])
def web_import_request():
    """
    导入HTTP请求（Web接口3）
    POST /api/import/request
    Body: JSON数组，每个元素为HTTP请求对象
    """
    try:
        list_request = request.get_json()
        result = get_import_api().import_traffic_request(list_request)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
