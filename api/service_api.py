# coding: utf-8
"""
服务管理API（代理模式）
@Time :    3/16/2026
@Author:  facai
@File: service_api.py
@Software: VSCode

说明：
此API作为代理，将请求转发到独立服务管理器（service_manager.py，端口5002）
Flask代码修改不会影响服务的运行
"""

from flask import Blueprint, jsonify, request
import requests
from service.Class_Core_Function import Class_Core_Function
from database.project_database import ProjectDatabase

service_api = Blueprint('service_api', __name__)

# 服务管理器 API 地址
SERVICE_MANAGER_URL = "http://127.0.0.1:5002"


class ServiceAPI:
    """服务管理API类（代理模式）"""

    def __init__(self):
        self.core_function = Class_Core_Function()

    def get_config(self):
        """获取配置文件"""
        return self.core_function.callback_config()

    def get_service_status(self):
        """获取服务状态（从独立服务管理器获取）"""
        # 获取基础服务状态
        base_status = {
            'mitmproxy': False,
            'mitmproxy_port': None,
            'chrome_headless': False,
            'chrome_headless_port': None,
            'chrome_normal': False,
            'chrome_normal_port': None,
            'burp': False,
            'spider': False
        }
        
        try:
            response = requests.get(f"{SERVICE_MANAGER_URL}/api/service/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                base_status = {
                    'mitmproxy': data.get('mitmproxy', {}).get('running', False),
                    'mitmproxy_port': data.get('mitmproxy', {}).get('port'),
                    'chrome_headless': data.get('chrome_headless', {}).get('running', False),
                    'chrome_headless_port': data.get('chrome_headless', {}).get('port'),
                    'chrome_normal': data.get('chrome_normal', {}).get('running', False),
                    'chrome_normal_port': data.get('chrome_normal', {}).get('port'),
                    'burp': data.get('burp', {}).get('running', False),
                    'spider': False
                }
        except Exception as e:
            print(f"获取服务状态失败: {e}")
        
        # 获取当前运行项目的服务锁状态
        service_lock = {
            'spider_service': 0,
            'monitor_service': 0,
            'scaner_service': 0
        }
        
        # 使用 callback_project_config 获取当前运行项目
        running_project = self.core_function.callback_project_config()
        if running_project and 'service_lock' in running_project:
            service_lock = running_project['service_lock']
            print(f"[DEBUG] Got service_lock from running project: {service_lock}")
        
        return {**base_status, **service_lock}


service_handler = ServiceAPI()


@service_api.route('/api/services/config', methods=['GET'])
def get_config():
    """获取配置信息"""
    try:
        config = service_handler.get_config()
        if config:
            return jsonify({'success': True, 'data': config})
        else:
            return jsonify({'success': False, 'message': '读取配置失败'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@service_api.route('/api/services/status', methods=['GET'])
def get_service_status():
    """获取服务状态"""
    try:
        status = service_handler.get_service_status()
        print(f"[DEBUG] API returning status: {status}")
        return jsonify({'success': True, 'data': status})
    except Exception as e:
        print(f"[DEBUG] Error in get_service_status: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@service_api.route('/api/services/mitmproxy/start', methods=['POST'])
def start_mitmproxy():
    """启动Mitmproxy（由服务管理器管理，此接口保留兼容性）"""
    return jsonify({'success': False, 'message': '服务由独立服务管理器管理，请使用 /api/services/penetration/start'})


@service_api.route('/api/services/mitmproxy/stop', methods=['POST'])
def stop_mitmproxy():
    """停止Mitmproxy（由服务管理器管理，此接口保留兼容性）"""
    return jsonify({'success': False, 'message': '服务由独立服务管理器管理，请使用 /api/services/penetration/stop'})


@service_api.route('/api/services/mitmproxy/restart', methods=['POST'])
def restart_mitmproxy():
    """重启Mitmproxy（由服务管理器管理，此接口保留兼容性）"""
    return jsonify({'success': False, 'message': '服务由独立服务管理器管理，请使用 /api/services/penetration/restart'})


@service_api.route('/api/services/chrome/start', methods=['POST'])
def start_chrome():
    """启动Chrome（由服务管理器管理，此接口保留兼容性）"""
    return jsonify({'success': False, 'message': '服务由独立服务管理器管理，请使用 /api/services/penetration/start'})


@service_api.route('/api/services/chrome/stop', methods=['POST'])
def stop_chrome():
    """停止Chrome（由服务管理器管理，此接口保留兼容性）"""
    return jsonify({'success': False, 'message': '服务由独立服务管理器管理，请使用 /api/services/penetration/stop'})


@service_api.route('/api/services/chrome/restart', methods=['POST'])
def restart_chrome():
    """重启Chrome（由服务管理器管理，此接口保留兼容性）"""
    return jsonify({'success': False, 'message': '服务由独立服务管理器管理，请使用 /api/services/penetration/restart'})


@service_api.route('/api/services/spider/start', methods=['POST'])
def start_spider():
    """启动爬虫服务"""
    try:
        running_project = service_handler.core_function.callback_project_config()
        if not running_project:
            return jsonify({'success': False, 'message': '没有运行中的项目'})
        
        project_name = running_project['Project']
        project_db = ProjectDatabase()
        project_db.update_service_lock(project_name, 'spider_service', 1)
        return jsonify({'success': True, 'message': '爬虫服务已启动'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@service_api.route('/api/services/spider/stop', methods=['POST'])
def stop_spider():
    """停止爬虫服务"""
    try:
        running_project = service_handler.core_function.callback_project_config()
        if not running_project:
            return jsonify({'success': False, 'message': '没有运行中的项目'})
        
        project_name = running_project['Project']
        project_db = ProjectDatabase()
        project_db.update_service_lock(project_name, 'spider_service', 0)
        return jsonify({'success': True, 'message': '爬虫服务已关闭'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@service_api.route('/api/services/spider/restart', methods=['POST'])
def restart_spider():
    """重启爬虫服务"""
    try:
        running_project = service_handler.core_function.callback_project_config()
        if not running_project:
            return jsonify({'success': False, 'message': '没有运行中的项目'})
        
        project_name = running_project['Project']
        project_db = ProjectDatabase()
        # 重启就是先关闭再开启
        project_db.update_service_lock(project_name, 'spider_service', 0)
        project_db.update_service_lock(project_name, 'spider_service', 1)
        return jsonify({'success': True, 'message': '爬虫服务已重启'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@service_api.route('/api/services/monitor/start', methods=['POST'])
def start_monitor():
    """启动资产监控服务"""
    try:
        running_project = service_handler.core_function.callback_project_config()
        if not running_project:
            return jsonify({'success': False, 'message': '没有运行中的项目'})
        
        project_name = running_project['Project']
        project_db = ProjectDatabase()
        project_db.update_service_lock(project_name, 'monitor_service', 1)
        return jsonify({'success': True, 'message': '资产监控服务已启动'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@service_api.route('/api/services/monitor/stop', methods=['POST'])
def stop_monitor():
    """停止资产监控服务"""
    try:
        running_project = service_handler.core_function.callback_project_config()
        if not running_project:
            return jsonify({'success': False, 'message': '没有运行中的项目'})
        
        project_name = running_project['Project']
        project_db = ProjectDatabase()
        project_db.update_service_lock(project_name, 'monitor_service', 0)
        return jsonify({'success': True, 'message': '资产监控服务已关闭'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@service_api.route('/api/services/scanner/start', methods=['POST'])
def start_scanner():
    """启动漏洞扫描服务"""
    try:
        running_project = service_handler.core_function.callback_project_config()
        if not running_project:
            return jsonify({'success': False, 'message': '没有运行中的项目'})
        
        project_name = running_project['Project']
        project_db = ProjectDatabase()
        project_db.update_service_lock(project_name, 'scaner_service', 1)
        return jsonify({'success': True, 'message': '漏洞扫描服务已启动'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@service_api.route('/api/services/scanner/stop', methods=['POST'])
def stop_scanner():
    """停止漏洞扫描服务"""
    try:
        running_project = service_handler.core_function.callback_project_config()
        if not running_project:
            return jsonify({'success': False, 'message': '没有运行中的项目'})
        
        project_name = running_project['Project']
        project_db = ProjectDatabase()
        project_db.update_service_lock(project_name, 'scaner_service', 0)
        return jsonify({'success': True, 'message': '漏洞扫描服务已关闭'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@service_api.route('/api/services/penetration/start', methods=['POST'])
def start_penetration():
    """启动渗透环境"""
    try:
        response = requests.get(f"{SERVICE_MANAGER_URL}/api/service/start", timeout=30)
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'success': False, 'message': '服务管理器请求失败'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'连接服务管理器失败: {str(e)}'}), 500


@service_api.route('/api/services/penetration/stop', methods=['POST'])
def stop_penetration():
    """停止渗透环境"""
    try:
        response = requests.get(f"{SERVICE_MANAGER_URL}/api/service/stop", timeout=10)
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'success': False, 'message': '服务管理器请求失败'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'连接服务管理器失败: {str(e)}'}), 500


@service_api.route('/api/services/penetration/restart', methods=['POST'])
def restart_penetration():
    """重启渗透环境"""
    try:
        response = requests.get(f"{SERVICE_MANAGER_URL}/api/service/restart", timeout=60)
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'success': False, 'message': '服务管理器请求失败'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'连接服务管理器失败: {str(e)}'}), 500
