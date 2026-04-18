# coding: utf-8
"""
独立服务管理器
@Time :    4/9/2026
@Author:  facai
@File: service_manager.py
@Software: VSCode

功能说明：
1. 独立于 Flask 运行，修改 Flask 代码不会影响服务
2. 管理 Chrome(headless/normal)、Burp 的启动和停止
3. 提供状态监测 HTTP API（端口 5002）
4. Mitmproxy 由 start.bat 独立启动

启动顺序：
1. 等待项目运行
2. 启动 Chrome headless（CDP: chrome_cdp_port, 代理: mitmproxy_port）
3. 启动 Chrome normal（CDP: chrome_spider_cdp_port, 代理: burp_port）
4. 启动 Burp
"""

import time
import json
import subprocess
import sys
import os
import socket
import threading
import psutil
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# 导入核心功能类
from service.Class_Core_Function import Class_Core_Function
from service.scaner.vuln_core import VulnerabilityScanner
from service.spider.asset_monitor import AssetMonitor


class ServiceManager:
    """服务管理器"""
    
    def __init__(self):
        self.Core_Function = Class_Core_Function()
        
        # 服务进程
        self.chrome_headless_process = None
        self.chrome_normal_process = None
        self.burp_process = None
        self.auto_scan_thread = None
        self.auto_scan_running = False
        self.asset_monitor = None
        self.asset_monitor_thread = None
        self.asset_monitor_running = False
        
        # 服务状态
        self.services_status = {
            'mitmproxy': {'running': False, 'port': None},
            'chrome_headless': {'running': False, 'port': None},
            'chrome_normal': {'running': False, 'port': None},
            'burp': {'running': False},
            'auto_scan': {'running': False},
            'asset_monitor': {'running': False}
        }
        
        # 配置
        self.config = None
        self.load_config()
    
    def load_config(self):
        """加载配置"""
        try:
            self.config = self.Core_Function.callback_config()
            if not self.config:
                print("[配置] 未找到配置文件，使用默认配置")
                self.config = {
                    'chrome_path': '',
                    'burp_path': '',
                    'chrome_cdp_port': 19227,
                    'chrome_spider_cdp_port': 19228,
                    'mitmproxy_port': 18081,
                    'burp_port': 8080
                }
        except Exception as e:
            print(f"[配置] 加载配置失败: {e}")
            self.config = {}
    
    def check_port_in_use(self, port):
        """检查端口是否被占用"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex(('localhost', port)) == 0
        except:
            return False
    
    def wait_for_project(self, timeout=300):
        """
        等待项目运行
        :param timeout: 超时时间（秒）
        :return: 是否成功
        """
        print("[项目] 等待项目运行...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                project_config = self.Core_Function.callback_project_config()
                if project_config and project_config.get('Project'):
                    project_name = project_config.get('Project')
                    print(f"[项目] 检测到运行项目: {project_name}")
                    return True
            except:
                pass
            
            print("[项目] 未检测到运行项目，10秒后重试...")
            time.sleep(10)
        
        print(f"[项目] 等待超时（{timeout}秒），退出")
        return False
    
    def start_chrome(self, mode='headless'):
        """启动 Chrome"""
        try:
            chrome_path = self.config.get('chrome_path', '')
            mitmproxy_port = self.config.get('mitmproxy_port', 18081)
            burp_port = self.config.get('burp_port', 8080)
            
            if not chrome_path or not os.path.exists(chrome_path):
                print(f"[Chrome {mode}] Chrome路径不存在: {chrome_path}")
                return False
            
            # 获取项目配置
            project_name = 'default'
            user_agent = None
            try:
                project_config = self.Core_Function.callback_project_config()
                if project_config:
                    project_name = project_config.get('Project', 'default')
                    user_agent = project_config.get('user_agent', '')
            except:
                pass
            
            # 根据模式选择端口和代理
            if mode == 'headless':
                cdp_port = self.config.get('chrome_cdp_port', 19227)
                proxy_port = mitmproxy_port  # 无头模式使用 mitmproxy
                process_key = 'chrome_headless'
                chrome_subdir = 'headless'
            else:
                cdp_port = self.config.get('chrome_spider_cdp_port', 19228)
                # 如果 burp_path 和 burp_port 同时为空，使用 mitmproxy
                burp_path = self.config.get('burp_path', '')
                if not burp_path and not burp_port:
                    proxy_port = mitmproxy_port
                    print(f"[Chrome {mode}] Burp未配置，使用 mitmproxy 代理")
                else:
                    proxy_port = burp_port  # 正常模式使用 burp
                process_key = 'chrome_normal'
                chrome_subdir = 'normal'
            
            # Chrome 数据目录: project_data/{项目名}/chrome_data/{headless|normal}
            project_root = os.path.dirname(__file__)
            user_data_dir = os.path.join(project_root, 'project_data', project_name, 'chrome_data', chrome_subdir)
            
            if self.check_port_in_use(cdp_port):
                print(f"[Chrome {mode}] 端口 {cdp_port} 已被占用")
                self.services_status[process_key]['running'] = True
                self.services_status[process_key]['port'] = cdp_port
                return True
            
            # 确保用户数据目录存在
            os.makedirs(user_data_dir, exist_ok=True)
            
            # 构建启动命令
            cmd_parts = [
                f'"{chrome_path}"',
                f'--remote-debugging-port={cdp_port}',
                f'--proxy-server=127.0.0.1:{proxy_port}',
                f'--user-data-dir="{user_data_dir}"',
            ]
            
            # 设置 User-Agent（如果有）
            if user_agent:
                cmd_parts.append(f'--user-agent="{user_agent}"')
                print(f"[Chrome {mode}] UA: {user_agent[:50]}...")
            
            # headless 模式
            if mode == 'headless':
                cmd_parts.append('--headless')
                cmd_parts.append('--disable-gpu')
            
            # 构建完整命令
            cmd = ' '.join(cmd_parts)
            print(f"[Chrome {mode}] 启动命令: CDP={cdp_port}, Proxy=127.0.0.1:{proxy_port}")
            
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # 保存进程引用
            if mode == 'headless':
                self.chrome_headless_process = process
            else:
                self.chrome_normal_process = process
            
            # 等待启动
            time.sleep(3)
            
            if self.check_port_in_use(cdp_port):
                print(f"[Chrome {mode}] 启动成功，CDP端口: {cdp_port}")
                self.services_status[process_key]['running'] = True
                self.services_status[process_key]['port'] = cdp_port
                return True
            else:
                print(f"[Chrome {mode}] 启动失败，端口未监听")
                return False
                
        except Exception as e:
            print(f"[Chrome {mode}] 启动失败: {e}")
            return False
    
    def start_burp(self):
        """启动 Burp Suite"""
        try:
            burp_path = self.config.get('burp_path', '')
            burp_port = self.config.get('burp_port', 8080)
            
            # 如果 burp_path 和 burp_port 同时为空，则不启动 Burp
            if not burp_path and not burp_port:
                print("[Burp] burp_path 和 burp_port 均为空，跳过 Burp 启动")
                return True
            
            if not burp_path or not os.path.exists(burp_path):
                print(f"[Burp] Burp路径不存在: {burp_path}")
                return False
            
            # 检查是否已在运行
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] and 'java' in proc.info['name'].lower():
                        cmdline = proc.info['cmdline']
                        if cmdline and 'burpsuite' in ' '.join(cmdline).lower():
                            print("[Burp] Burp Suite 已在运行")
                            self.services_status['burp']['running'] = True
                            return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # 构建启动命令
            burp_command = (
                f'java --add-opens=java.desktop/javax.swing=ALL-UNNAMED '
                f'--add-opens=java.base/java.lang=ALL-UNNAMED '
                f'--add-opens=java.base/jdk.internal.org.objectweb.asm=ALL-UNNAMED '
                f'--add-opens=java.base/jdk.internal.org.objectweb.asm.tree=ALL-UNNAMED '
                f'--add-opens=java.base/jdk.internal.org.objectweb.asm.Opcodes=ALL-UNNAMED '
                f'-javaagent:{burp_path}\\BurpLoaderKeygen.jar '
                f'-noverify -jar {burp_path}\\burpsuite_pro.jar'
            )
            
            print(f"[Burp] 启动 Burp Suite")
            self.burp_process = subprocess.Popen(
                burp_command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # 等待启动
            time.sleep(3)
            
            if self.burp_process.poll() is None:
                print("[Burp] Burp Suite 启动成功")
                self.services_status['burp']['running'] = True
                return True
            else:
                print("[Burp] Burp Suite 启动失败，进程已退出")
                return False
                
        except Exception as e:
            print(f"[Burp] 启动失败: {e}")
            return False
    
    def start_auto_scan(self, batch_size=10):
        """启动自动扫描服务"""
        try:
            # 获取项目配置
            project_config = self.Core_Function.callback_project_config()
            if not project_config:
                print("[AutoScan] 无法获取项目配置，跳过自动扫描")
                return False
            
            project_name = project_config.get('Project', '')
            if not project_name:
                print("[AutoScan] 项目名称为空，跳过自动扫描")
                return False
            
            dnslog_domain = project_config.get('dnslog_domain', '')
            dnslog_url = project_config.get('dnslog_url', '')
            
            # 创建扫描器实例
            scanner = VulnerabilityScanner(
                dnslog_domain=dnslog_domain,
                dnslog_url=dnslog_url,
                project_name=project_name
            )
            
            print(f"[AutoScan] 初始化自动扫描服务，批次大小 {batch_size}")
            
            # 在后台线程运行自动扫描
            self.auto_scan_running = True
            self.auto_scan_thread = threading.Thread(
                target=scanner.auto_scan,
                args=(batch_size,),
                daemon=True
            )
            self.auto_scan_thread.start()
            
            print("[AutoScan] 自动扫描服务已启动")
            self.services_status['auto_scan']['running'] = True
            return True
            
        except Exception as e:
            print(f"[AutoScan] 启动失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def stop_auto_scan(self):
        """停止自动扫描服务"""
        print("[AutoScan] 停止自动扫描服务...")
        self.auto_scan_running = False
        self.auto_scan_thread = None
        self.services_status['auto_scan']['running'] = False
        print("[AutoScan] 自动扫描服务已停止")
    
    def start_asset_monitor(self):
        """启动资产监控服务"""
        try:
            print("[AssetMonitor] 初始化资产监控服务...")
            
            # 创建资产监控实例
            self.asset_monitor = AssetMonitor()
            
            # 在后台线程运行
            self.asset_monitor_running = True
            self.asset_monitor_thread = threading.Thread(
                target=self.asset_monitor.run,
                daemon=True
            )
            self.asset_monitor_thread.start()
            
            print("[AssetMonitor] 资产监控服务已启动")
            self.services_status['asset_monitor']['running'] = True
            return True
            
        except Exception as e:
            print(f"[AssetMonitor] 启动失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def stop_asset_monitor(self):
        """停止资产监控服务"""
        print("[AssetMonitor] 停止资产监控服务...")
        self.asset_monitor_running = False
        if hasattr(self, 'asset_monitor') and self.asset_monitor:
            self.asset_monitor.is_running = False
        self.asset_monitor_thread = None
        self.asset_monitor = None
        self.services_status['asset_monitor']['running'] = False
        print("[AssetMonitor] 资产监控服务已停止")
    
    def start_all(self):
        """启动所有服务"""
        print("\n" + "=" * 60)
        print("开始启动服务...")
        print("=" * 60)
        
        # 1. 等待项目运行
        if not self.wait_for_project():
            print("\n启动失败：未检测到运行项目")
            return False
        
        # 2. 启动 Chrome headless
        print("\n[1/3] 启动 Chrome (headless)...")
        if not self.start_chrome('headless'):
            print("Chrome headless 启动失败")
        
        # 3. 启动 Chrome normal
        print("\n[2/3] 启动 Chrome (normal)...")
        if not self.start_chrome('normal'):
            print("Chrome normal 启动失败")
        
        # 4. 启动 Burp（如果配置了）
        burp_path = self.config.get('burp_path', '')
        burp_port = self.config.get('burp_port', 8080)
        if not burp_path and not burp_port:
            print("\n[3/3] 跳过 Burp Suite（未配置 burp_path 和 burp_port）")
        else:
            print("\n[3/3] 启动 Burp Suite...")
            if not self.start_burp():
                print("Burp Suite 启动失败")
        
        # 5. 启动自动扫描服务
        print("\n[4/4] 启动自动扫描服务...")
        if not self.start_auto_scan(batch_size=10):
            print("自动扫描服务启动失败（不影响其他服务）")
        
        # 6. 启动资产监控服务
        print("\n[5/5] 启动资产监控服务...")
        if not self.start_asset_monitor():
            print("资产监控服务启动失败（不影响其他服务）")
        
        print("\n" + "=" * 60)
        print("服务启动完成！")
        self.print_status()
        print("=" * 60)
        
        return True
    
    def stop_all(self):
        """停止所有服务"""
        print("\n停止所有服务...")
        
        # 停止资产监控
        self.stop_asset_monitor()
        
        # 停止自动扫描
        self.stop_auto_scan()
        
        # 停止 Burp
        if self.burp_process:
            try:
                self.burp_process.terminate()
                print("[Burp] 已停止")
            except:
                pass
        
        # 停止 Chrome normal
        if self.chrome_normal_process:
            try:
                self.chrome_normal_process.terminate()
                print("[Chrome normal] 已停止")
            except:
                pass
        
        # 停止 Chrome headless
        if self.chrome_headless_process:
            try:
                self.chrome_headless_process.terminate()
                print("[Chrome headless] 已停止")
            except:
                pass
        
        # 更新状态
        for key in self.services_status:
            self.services_status[key]['running'] = False
        
        print("所有服务已停止")
    
    def get_status(self):
        """获取所有服务状态"""
        # 更新实际运行状态
        mitmproxy_port = self.config.get('mitmproxy_port', 18081)
        self.services_status['mitmproxy']['running'] = self.check_port_in_use(mitmproxy_port)
        self.services_status['mitmproxy']['port'] = mitmproxy_port
        
        chrome_cdp_port = self.config.get('chrome_cdp_port', 19227)
        self.services_status['chrome_headless']['running'] = self.check_port_in_use(chrome_cdp_port)
        self.services_status['chrome_headless']['port'] = chrome_cdp_port
        
        chrome_spider_cdp_port = self.config.get('chrome_spider_cdp_port', 19228)
        self.services_status['chrome_normal']['running'] = self.check_port_in_use(chrome_spider_cdp_port)
        self.services_status['chrome_normal']['port'] = chrome_spider_cdp_port
        
        # 检查 Burp 进程
        burp_running = False
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] and 'java' in proc.info['name'].lower():
                    cmdline = proc.info['cmdline']
                    if cmdline and 'burpsuite' in ' '.join(cmdline).lower():
                        burp_running = True
                        break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        self.services_status['burp']['running'] = burp_running
        
        return self.services_status
    
    def print_status(self):
        """打印服务状态"""
        status = self.get_status()
        print("\n服务状态:")
        for service, info in status.items():
            running = "运行中" if info.get('running') else "已停止"
            port = f" (端口: {info['port']})" if info.get('port') else ""
            print(f"  - {service}: {running}{port}")
    
    def monitor_chrome(self):
        """监控 Chrome 状态，每10秒检测一次，异常则重启"""
        # 首次等待服务完全启动
        time.sleep(30)
        print("[监控] 开始检测 Chrome 状态...")
        
        while True:
            time.sleep(10)  # 每10秒检测一次
            
            try:
                # 检测 Chrome headless
                chrome_cdp_port = self.config.get('chrome_cdp_port', 19227)
                if not self.check_port_in_use(chrome_cdp_port):
                    print(f"[监控] Chrome headless 端口 {chrome_cdp_port} 未监听，正在重启...")
                    self.start_chrome('headless')
                
                # 检测 Chrome normal
                chrome_spider_cdp_port = self.config.get('chrome_spider_cdp_port', 19228)
                if not self.check_port_in_use(chrome_spider_cdp_port):
                    print(f"[监控] Chrome normal 端口 {chrome_spider_cdp_port} 未监听，正在重启...")
                    self.start_chrome('normal')
                    
            except Exception as e:
                print(f"[监控] 检测异常: {e}")


class StatusAPIHandler(BaseHTTPRequestHandler):
    """状态监测 HTTP API 处理器"""
    
    def log_message(self, format, *args):
        """禁用默认日志"""
        pass
    
    def do_GET(self):
        """处理 GET 请求"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == '/api/service/status':
            # 获取服务状态
            status = service_manager.get_status()
            self.send_json_response(status)
        
        elif path == '/api/service/start':
            # 启动所有服务
            result = service_manager.start_all()
            self.send_json_response({'success': result})
        
        elif path == '/api/service/stop':
            # 停止所有服务
            service_manager.stop_all()
            self.send_json_response({'success': True})
        
        elif path == '/api/service/restart':
            # 重启所有服务
            service_manager.stop_all()
            time.sleep(2)
            result = service_manager.start_all()
            self.send_json_response({'success': result})
        
        else:
            self.send_error(404, "Not Found")
    
    def send_json_response(self, data):
        """发送 JSON 响应"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))


def run_api_server(port=5002):
    """运行状态监测 API 服务器"""
    server = HTTPServer(('0.0.0.0', port), StatusAPIHandler)
    print(f"\n[API] 状态监测 API 已启动: http://127.0.0.1:{port}")
    print(f"[API] 接口列表:")
    print(f"  - GET /api/service/status  - 获取服务状态")
    print(f"  - GET /api/service/start   - 启动所有服务")
    print(f"  - GET /api/service/stop    - 停止所有服务")
    print(f"  - GET /api/service/restart - 重启所有服务")
    server.serve_forever()


# 全局服务管理器实例
service_manager = None


def main():
    """主函数"""
    global service_manager
    
    print("=" * 60)
    print("独立服务管理器")
    print("=" * 60)
    
    # 创建服务管理器
    service_manager = ServiceManager()
    
    # 启动所有服务
    service_manager.start_all()
    
    # 在后台线程运行 API 服务器
    api_thread = threading.Thread(target=run_api_server, args=(5002,), daemon=True)
    api_thread.start()
    
    # 启动 Chrome 监控线程
    monitor_thread = threading.Thread(target=service_manager.monitor_chrome, daemon=True)
    monitor_thread.start()
    
    print("\n服务管理器已就绪，按 Ctrl+C 退出...")
    print("[监控] Chrome 状态监控已启动（每10秒检测一次）")
    
    try:
        # 保持运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n收到退出信号，正在停止服务...")
        service_manager.stop_all()
        print("服务管理器已退出")


if __name__ == '__main__':
    main()
