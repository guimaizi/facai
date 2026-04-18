# coding: utf-8
"""
@Time :    3/17/2026
@Author:  facai
@File: chrome_manage.py
@Software: VSCode
@Desc: Chrome CDP服务管理类
"""
import subprocess
import time
import sys
import os
import socket
import signal
import psutil
from service.Class_Core_Function import Class_Core_Function


class ChromeService:
    """Chrome CDP服务管理类"""

    def __init__(self):
        self.Core_Function = Class_Core_Function()
        self.process = None
        self.is_running = False
        self.port = None
        self.mode = 'normal'  # normal 或 headless

    def get_config(self):
        """获取Chrome配置"""
        try:
            config = self.Core_Function.callback_config()
            if config:
                return {
                    'chrome_path': config.get('chrome_path', ''),
                    'chrome_cdp_port': config.get('chrome_cdp_port', 19227),
                    'burp_port': config.get('burp_port', 8080)
                }
        except Exception as e:
            print(f"获取Chrome配置失败: {str(e)}")
        return {
            'chrome_path': '',
            'chrome_cdp_port': 19227,
            'burp_port': 8080
        }

    def check_port_in_use(self, port):
        """检查端口是否被占用"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex(('localhost', port)) == 0
        except:
            return False

    def kill_existing_chrome(self, port):
        """杀掉占用指定端口的Chrome进程"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] and 'chrome' in proc.info['name'].lower():
                        cmdline = proc.info['cmdline']
                        if cmdline and any(f'--remote-debugging-port={port}' in arg for arg in cmdline):
                            print(f"杀掉现有Chrome进程: PID={proc.info['pid']}")
                            proc.terminate()
                            time.sleep(1)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            print(f"清理Chrome进程失败: {str(e)}")

    def start(self, mode='normal'):
        """启动Chrome服务"""
        try:
            if self.is_running:
                return {'success': False, 'message': 'Chrome已在运行中'}

            config = self.get_config()
            chrome_path = config.get('chrome_path', '')
            cdp_port = config.get('chrome_cdp_port', 19227)
            proxy_port = config.get('burp_port', 8080)

            # 检查Chrome路径
            if not chrome_path or not os.path.exists(chrome_path):
                return {'success': False, 'message': f'Chrome路径不存在或未配置: {chrome_path}'}

            # 检查端口是否被占用
            if self.check_port_in_use(cdp_port):
                # 尝试清理占用端口的进程
                self.kill_existing_chrome(cdp_port)
                time.sleep(1)

                if self.check_port_in_use(cdp_port):
                    return {'success': False, 'message': f'端口 {cdp_port} 已被占用且无法清理'}

            # 构建Chrome启动参数
            chrome_args = [
                chrome_path,
                f'--remote-debugging-port={cdp_port}',  # CDP端口
                '--remote-allow-origins=*',  # 允许所有来源连接
                f'--proxy-server=127.0.0.1:{proxy_port}',  # 设置Mitmproxy代理
                '--allow-running-insecure-content',  # 允许运行不安全内容
                '--window-size=1280,1080',
                "--no-sandbox",
                "--disable-gpu",
                "--disable-software-rasterizer",
                "--disable-gpu-compositing",
                "--disable-extensions",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
            ]

            # 根据模式添加参数
            if mode == 'headless':
                chrome_args.extend([
                    '--headless',
                    '--disable-gpu',
                    '--window-size=1280,1080'
                ])
            else:
                chrome_args.extend([
                    '--start-maximized',  # 最大化窗口
                ])

            # Windows系统特殊参数
            if sys.platform == 'win32':
                chrome_args.extend([
                    '--disable-features=IsolateOrigins,site-per-process',  # 禁用某些功能
                ])

            # 启动Chrome进程
            print(f"启动Chrome: {' '.join(chrome_args)}")
            self.process = subprocess.Popen(
                chrome_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
            )

            # 等待启动
            time.sleep(3)

            # 验证端口是否监听
            if self.check_port_in_use(cdp_port):
                self.is_running = True
                self.port = cdp_port
                self.mode = mode
                return {
                    'success': True,
                    'message': f'Chrome启动成功，CDP端口: {cdp_port}, 代理端口: {proxy_port}, 模式: {mode}'
                }
            else:
                # 启动失败
                if self.process:
                    self.process.terminate()
                    self.process = None
                return {'success': False, 'message': 'Chrome启动失败，端口未监听'}

        except Exception as e:
            return {'success': False, 'message': f'启动失败: {str(e)}'}

    def stop(self):
        """停止Chrome服务"""
        try:
            if not self.is_running:
                return {'success': False, 'message': 'Chrome未运行'}

            # 先尝试优雅终止
            if self.process:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # 强制终止
                    if sys.platform == 'win32':
                        self.process.send_signal(signal.CTRL_BREAK_EVENT)
                    else:
                        self.process.kill()
                    self.process.wait()

            # 确保清理所有相关进程
            if self.port:
                self.kill_existing_chrome(self.port)

            self.process = None
            self.is_running = False
            self.port = None

            return {'success': True, 'message': 'Chrome已停止'}

        except Exception as e:
            return {'success': False, 'message': f'停止失败: {str(e)}'}

    def restart(self, mode='normal'):
        """重启Chrome服务"""
        stop_result = self.stop()
        if not stop_result['success']:
            # 如果停止失败但进程不存在，可以继续启动
            if '未运行' not in stop_result['message']:
                return {'success': False, 'message': f'停止失败: {stop_result["message"]}'}

        time.sleep(2)
        return self.start(mode)

    def get_status(self):
        """获取服务状态 - 通过端口检测实际运行状态"""
        config = self.get_config()
        port = config.get('chrome_cdp_port', 19227)

        # 通过端口检查实际运行状态
        actual_running = self.check_port_in_use(port)
        # 同步内部状态
        self.is_running = actual_running
        
        return {
            'is_running': actual_running,
            'port': port,
            'mode': self.mode
        }
