# coding: utf-8
"""
@Time :    1/17/2025 17:47
@Author:  fff
@File: mitmproxy_service.py
@Software: PyCharm
@Desc: Mitmproxy流量监测服务管理类
"""
import subprocess
import time
import sys
import os
import socket
from typing import Any
from mitmproxy import http
from mitmproxy.tools.main import mitmdump

# 导入必要的类
from service.Class_Core_Function import Class_Core_Function
from service.Class_check import class_check
from database.mongodb_handler import MongoDBHandler

# 全局变量 - 缓存配置和实例
_core_function = Class_Core_Function()
_class_check = None
_db_handler = None
_running_project_config = None


def get_running_config():
    """获取运行中的项目配置(带缓存)"""
    global _running_project_config
    if _running_project_config is None:
        _running_project_config = _core_function.callback_project_config()
    return _running_project_config


def get_class_check():
    """获取class_check实例(单例)"""
    global _class_check
    if _class_check is None:
        _class_check = class_check()
    return _class_check


def get_db_handler():
    """获取MongoDB handler实例(单例)"""
    global _db_handler
    if _db_handler is None:
        _db_handler = MongoDBHandler()
    return _db_handler


class MitmproxyService:
    """Mitmproxy流量捕捉服务管理类"""

    def __init__(self):
        self.Core_Function = Class_Core_Function()
        self.class_check = class_check()
        self.db_handler = MongoDBHandler()
        self.process = None
        self.is_running = False
        self.port = None

    def get_port(self):
        """获取配置的mitmproxy端口"""
        try:
            config = self.Core_Function.callback_config()
            if config:
                return config.get('mitmproxy_port', 18081)
        except Exception as e:
            print(f"获取端口配置失败: {str(e)}")
        return 18081

    def check_port_in_use(self, port):
        """检查端口是否被占用"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex(('localhost', port)) == 0
        except:
            return False

    def start(self):
        """启动Mitmproxy服务"""
        try:
            if self.is_running:
                return {'success': False, 'message': 'Mitmproxy已在运行中'}

            port = self.get_port()
            if self.check_port_in_use(port):
                return {'success': False, 'message': f'端口 {port} 已被占用'}

            # 启动mitmproxy - 不传参数，子进程内部从配置获取
            script_path = os.path.abspath(__file__)
            
            cmd = [sys.executable, script_path]

            # 设置环境变量
            env = os.environ.copy()
            project_root = os.path.dirname(script_path)
            env['PYTHONPATH'] = project_root + os.pathsep + env.get('PYTHONPATH', '')

            # 启动进程
            print(f"启动命令: {' '.join(cmd)}")
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env
            )

            # 等待启动
            time.sleep(3)

            if self.process.poll() is None:
                self.is_running = True
                self.port = port
                return {'success': True, 'message': f'Mitmproxy启动成功，端口: {port}'}
            else:
                _, stderr = self.process.communicate()
                error_msg = stderr.strip() if stderr else '未知错误'
                print(f"Mitmproxy启动失败详情: {error_msg}")
                return {'success': False, 'message': f'Mitmproxy启动失败: {error_msg}'}
        except Exception as e:
            return {'success': False, 'message': f'启动失败: {str(e)}'}

    def stop(self):
        """停止Mitmproxy服务"""
        try:
            if not self.is_running:
                return {'success': False, 'message': 'Mitmproxy未运行'}

            if self.process:
                self.process.terminate()
                self.process.wait(timeout=5)
                self.process = None

            self.is_running = False
            self.port = None
            return {'success': True, 'message': 'Mitmproxy已停止'}
        except Exception as e:
            return {'success': False, 'message': f'停止失败: {str(e)}'}

    def restart(self):
        """重启Mitmproxy服务"""
        stop_result = self.stop()
        if not stop_result['success']:
            return {'success': False, 'message': f'停止失败: {stop_result["message"]}'}

        time.sleep(1)
        return self.start()

    def get_status(self):
        """获取服务状态 - 通过端口检测实际运行状态"""
        port = self.port or self.get_port()
        actual_running = self.check_port_in_use(port)
        self.is_running = actual_running
        
        return {
            'is_running': actual_running,
            'port': port
        }


# Mitmproxy addon - 当作为脚本执行时，这些函数会被mitmproxy调用
def request(flow: http.HTTPFlow) -> None:
    """
    Mitmproxy请求回调函数
    把http请求写入mongodb数据库project_{name}_traffic表
    """
    try:
        running_project = get_running_config()
        if not running_project:
            return

        project_name = running_project.get('Project', 'default')

        check_instance = get_class_check()
        
        try:
            fetch_dest = flow.request.headers.get("sec-fetch-dest", "").lower()
            if fetch_dest in ["image", "style", "font"]:
                return
        except:
            pass
        
        if not check_instance.check_traffic_url(flow.request.url):
            return

        try:
            headers = dict(flow.request.headers)
            for header in ['Host', 'Connection', 'Content-Length']:
                if header in headers:
                    del headers[header]

            request_task = {
                'url': flow.request.url,
                'website': _core_function.callback_split_url(flow.request.url, 0),
                'method': flow.request.method,
                'headers': headers,
                'body': flow.request.content.decode('utf-8', errors='ignore'),
                'time': _core_function.callback_time(0),
                'scaner_status':0,
                'status': 0,
                'source': 0
            }

            db_handler = get_db_handler()
            collection_name = f"project_{project_name}_traffic"
            db_handler.insert_one(collection_name, request_task)

        except Exception as insert_error:
            print(f"数据库插入错误: {str(insert_error)}")
        
    except Exception as e:
        pass


if __name__ == '__main__':
    # 从配置获取端口和项目信息
    config = _core_function.callback_config()
    port = config.get('mitmproxy_port', 18081) if config else 18081
    
    project_config = _core_function.callback_project_config()
    project_name = project_config.get('Project', 'default') if project_config else 'default'
    
    print(f"启动Mitmproxy代理服务: project={project_name}, port={port}")
    
    args = [
        '-s', __file__,
        '-p', str(port),
        '--set', 'stream_large_bodies=50m',
        '--set', 'ssl_insecure=true',
        '--set', 'tcp_keepalive=60',
        '--set', 'timeout=300',
        '--set', 'connection_strategy=eager',
        '--set', 'dns_fail_mode=abort',
        '--set', 'http2=false',
        '--quiet',
    ]
    
    mitmdump(args)
