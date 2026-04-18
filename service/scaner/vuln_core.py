# coding: utf-8
"""
漏洞扫描器调度中心
@Time :    4/5/2026
@Author:  facai
@File: vul_core.py
@Software: VSCode

功能说明：
1. 接受HTTP请求
2. 调度各漏洞扫描模块
3. 统一发送请求、记录结果
"""

import time
from urllib.parse import urlparse
from service.Class_Core_Function import Class_Core_Function
from service.libs.replay_request import send_http_request
from service.spider.http_standardization import callback_pathname

# 导入参数处理模块
from .param_handler import ParamHandler

# 导入核心漏洞扫描模块
from .core_vuln import XSSScanner, SQLInjectionScanner, RCEScanner, SSRFScanner, ParamNameFuzzer, AnomalyScanner

# 导入其他扫描模块
from .info_leak import InfoLeakScanner

# 导入漏洞数据库
from database.vuln_database import VulnDatabase
from database.traffic_database import TrafficDatabase


class VulnerabilityScanner:
    """漏洞扫描器调度中心"""
    
    def __init__(self, dnslog_domain="", dnslog_url="", project_name=""):
        self.Core_Function = Class_Core_Function()
        
        # 扫描配置
        self.dnslog_domain = dnslog_domain
        self.dnslog_url = dnslog_url
        self.project_name = project_name
        
        # 从项目配置中获取 timeout
        project_config = self.Core_Function.callback_project_config()
        if project_config and 'timeout' in project_config:
            self.timeout = project_config['timeout']
        else:
            self.timeout = 5  # 默认超时
        
        self.max_redirects = 3
        
        # 初始化参数处理模块（传入project_name以支持去重功能）
        self.param_handler = ParamHandler(project_name=project_name)
        
        # 初始化核心漏洞扫描模块（传入timeout）
        self.xss_scanner = XSSScanner(timeout=self.timeout)
        self.sqli_scanner = SQLInjectionScanner(timeout=self.timeout)
        self.rce_scanner = RCEScanner(dnslog_domain, project_name, timeout=self.timeout)  # RCE使用dnslog_domain
        self.ssrf_scanner = SSRFScanner(dnslog_url, project_name, timeout=self.timeout)   # SSRF使用dnslog_url
        self.anomaly_scanner = AnomalyScanner(timeout=self.timeout)
        self.param_fuzzer = ParamNameFuzzer(timeout=self.timeout)
        
        # 初始化其他扫描模块
        self.info_leak_scanner = InfoLeakScanner()
        
        # 初始化漏洞数据库
        self.vuln_db = VulnDatabase()
        
        # 初始化流量数据库
        self.traffic_db = TrafficDatabase(project_name)
        
        # 扫描结果
        self.scan_results = []
    
    # ==================== 数据库操作 ====================
    
    def _extract_website_info(self, url):
        """
        从URL提取website和subdomain
        :param url: 完整URL
        :return: (website, subdomain)
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            # website格式: scheme://domain/
            website = f"{parsed.scheme}://{domain}/"
            # subdomain就是域名部分
            subdomain = domain
            return website, subdomain
        except:
            return url, ''
    
    def _extract_vuln_category(self, vuln_type_detail):
        """
        从详细漏洞类型提取大类
        :param vuln_type_detail: 详细漏洞类型（如 xss-reflect, sqli-blind）
        :return: 漏洞大类（xss/sql/rce/ssrf/leak-info）
        """
        if not vuln_type_detail:
            return 'unknown'
        
        vuln_type_lower = vuln_type_detail.lower()
        
        # XSS类型
        if vuln_type_lower.startswith('xss'):
            return 'xss'
        
        # SQL注入类型
        if any(prefix in vuln_type_lower for prefix in ['sql', 'sqli']):
            return 'sql'
        
        # RCE类型
        if any(prefix in vuln_type_lower for prefix in ['rce', 'command', 'code-inject']):
            return 'rce'
        
        # SSRF类型
        if 'ssrf' in vuln_type_lower:
            return 'ssrf'
        
        # 信息泄露类型
        if any(prefix in vuln_type_lower for prefix in ['leak', 'info', 'disclosure', 'sensitive']):
            return 'leak-info'
        
        return 'unknown'
    
    def _determine_vuln_level(self, vuln_type, vuln_type_detail=''):
        """
        根据漏洞类型确定危害等级
        :param vuln_type: 漏洞大类
        :param vuln_type_detail: 漏洞详细类型
        :return: 危害等级 (high/medium/low)
        """
        # 高危漏洞
        high_types = ['sql', 'rce', 'ssrf']
        high_details = [
            'arbitrary-file-read', 'arbitrary-file-write', 'arbitrary-file-upload',
            'path-traversal', 'directory-traversal'
        ]
        
        # 中危漏洞
        medium_types = ['xss']
        medium_details = ['xxe', 'csrf', 'lfi']
        
        # 低危漏洞
        low_types = ['leak-info', 'anomaly']
        
        # 先根据详细类型判断
        if vuln_type_detail:
            detail_lower = vuln_type_detail.lower()
            
            if any(v in detail_lower for v in high_details):
                return 'high'
            
            if any(v in detail_lower for v in medium_details):
                return 'medium'
        
        # 再根据大类判断
        if vuln_type in high_types:
            return 'high'
        elif vuln_type in medium_types:
            return 'medium'
        elif vuln_type in low_types:
            return 'low'
        else:
            return 'medium'  # 默认中危
    
    def _convert_vuln_to_db_format(self, vuln_data, request_data):
        """
        将扫描结果转换为数据库格式
        :param vuln_data: 扫描器返回的漏洞数据
        :param request_data: 原始HTTP请求数据
        :return: 数据库格式的漏洞数据（严格按照文档定义的字段）
        """
        url = vuln_data.get('url', request_data.get('url', ''))
        website, subdomain = self._extract_website_info(url)
        
        # 构建数据库格式（严格按照文档定义，不添加任何额外字段）
        db_vuln = {
            'url': url,
            'method': vuln_data.get('method', request_data.get('method', 'GET')),
            'headers': vuln_data.get('headers', request_data.get('headers', {})),
            'body': vuln_data.get('body', request_data.get('body', '')),
            'website': website,
            'subdomain': subdomain,
            'vuln_type': vuln_data.get('vuln_type', 'unknown'),
            'vuln_type_detail': vuln_data.get('vuln_type_detail', 'unknown'),
            'level': vuln_data.get('level', 'medium'),
            'paramname': vuln_data.get('paramname', ''),
            'time': vuln_data.get('time', time.strftime('%Y-%m-%d %H:%M:%S'))
        }
        
        return db_vuln
    
    def _save_vuln_to_db(self, vuln_data, request_data):
        """
        保存漏洞到数据库
        :param vuln_data: 扫描器返回的漏洞数据
        :param request_data: 原始HTTP请求数据
        :return: 是否保存成功
        """
        try:
            db_vuln = self._convert_vuln_to_db_format(vuln_data, request_data)
            result = self.vuln_db.add_vuln(db_vuln)
            
            if result:
                self.Core_Function.callback_logging().info(
                    f"[漏洞入库] {db_vuln['vuln_type']} - {db_vuln['url']} - 参数: {db_vuln['paramname']}"
                )
                return True
            return False
        except Exception as e:
            self.Core_Function.callback_logging().error(f"漏洞入库失败: {e}")
            return False
    
    # ==================== 扫描调度 ====================
    
    def scan(self, request_data, scan_options=None, save_to_db=True, enable_dedup=False):
        """
        扫描入口
        :param request_data: dict - HTTP请求数据
        :param scan_options: dict - 扫描选项 {'xss': True, 'sqli': True, ...}
        :param save_to_db: bool - 是否自动保存到数据库（默认True）
        :param enable_dedup: bool - 是否启用参数去重（默认False，只有自动扫描时为True）
        :return: list - 漏洞列表
        """
        vulnerabilities = []
        scanned_params = []  # 记录本次扫描的参数
        
        # 默认扫描选项
        if scan_options is None:
            scan_options = {
                'anomaly': True,    # 异常检测
                'xss': True,        # XSS检测
                'sqli': True,       # SQL注入检测
                'rce': True,        # 命令执行检测
                'ssrf': True,       # SSRF检测
                'info_leak': False,  # 信息泄露检测
            }
        
        # 用于存储URL标准化信息
        std_result = None
        
        try:
            # 0. 验证目标可达性
            print("[Scanner] 验证目标可达性...")
            test_response = send_http_request(request_data, timeout=self.timeout)
            if test_response is None:
                print("[Scanner] 目标不可达，无法进行扫描")
                return vulnerabilities
            print(f"[Scanner] 目标可达，状态码: {test_response.status_code}")
            
            # 1. 提取参数（自动模式启用去重，手动模式不去重）
            params = self.param_handler.callback_list_param(request_data, enable_dedup=enable_dedup)
            print(f"[Scanner] 提取到 {len(params) if params else 0} 个参数" + (" (已启用去重)" if enable_dedup else ""))
            if params:
                for p in params:
                    print(f"  - {p.get('param_name', 'N/A')}: {p.get('param_value', 'N/A')} ({p.get('position', 'N/A')})")
            
            if not params:
                print("[Scanner] 没有提取到参数，跳过扫描")
                return vulnerabilities
            
            # 记录本次扫描的参数
            scanned_params = [p.get('param_name') for p in params if p.get('param_name')]
            
            # 2. 异常检测（基于机器学习）
            anomaly_params = None
            baseline_responses = None
            
            if scan_options.get('anomaly'):
                anomaly_result = self.anomaly_scanner.scan(
                    request_data, 
                    params, 
                    lambda req: send_http_request(req, timeout=self.timeout)
                )
                
                if anomaly_result and anomaly_result.get('vulnerabilities'):
                    # 异常检测结果不保存到数据库，只添加到结果列表
                    vulnerabilities.extend(anomaly_result['vulnerabilities'])
                    anomaly_params = anomaly_result.get('anomaly_params', [])
                    baseline_responses = anomaly_result.get('baseline_responses')
            
            # 3. SQL注入检测（只测试异常参数，使用相似度判断）
            if scan_options.get('sqli') and anomaly_params:
                print(f"[Scanner] 开始SQL注入检测，异常参数: {[p.get('param_name') for p in anomaly_params]}")
                vulns = self.sqli_scanner.scan(
                    request_data, 
                    params_list=params,
                    send_request_func=lambda req: send_http_request(req, timeout=self.timeout),
                    anomaly_params=anomaly_params,
                    baseline_responses=baseline_responses
                )
                
                if vulns:
                    print(f"[Scanner] SQL注入检测发现 {len(vulns)} 个漏洞")
                    for vuln in vulns:
                        if save_to_db:
                            self._save_vuln_to_db(vuln, request_data)
                        vulnerabilities.append(vuln)
            elif scan_options.get('sqli') and not anomaly_params:
                print("[Scanner] SQL注入检测：没有异常参数，跳过检测")
            
            # 4. 对每个参数进行其他扫描（XSS、RCE、SSRF等）
            print(f"[Scanner] 开始对 {len(params)} 个参数进行扫描")
            for param_info in params:
                param_name = param_info.get('param_name', 'unknown')
                print(f"[Scanner] 扫描参数: {param_name}")
                
                # 命令执行
                if scan_options.get('rce'):
                    vuln = self.rce_scanner.scan(
                        request_data, 
                        [param_info], 
                        lambda req: send_http_request(req, timeout=self.timeout)
                    )
                    if vuln:
                        print(f"[Scanner] RCE检测发现漏洞: {param_name}")
                        if save_to_db:
                            self._save_vuln_to_db(vuln, request_data)
                        vulnerabilities.append(vuln)
                        continue
                
                # XSS
                if scan_options.get('xss'):
                    vulns = self.xss_scanner.scan(
                        request_data, 
                        [param_info], 
                        lambda req: send_http_request(req, timeout=self.timeout)
                    )
                    if vulns:
                        print(f"[Scanner] XSS检测发现 {len(vulns)} 个漏洞: {param_name}")
                        for vuln in vulns:
                            if save_to_db:
                                self._save_vuln_to_db(vuln, request_data)
                            vulnerabilities.append(vuln)
                
                # SSRF
                if scan_options.get('ssrf'):
                    vuln = self.ssrf_scanner.scan(
                        request_data, 
                        [param_info], 
                        lambda req: send_http_request(req, timeout=self.timeout)
                    )
                    if vuln:
                        print(f"[Scanner] SSRF检测发现漏洞: {param_name}")
                        if save_to_db:
                            self._save_vuln_to_db(vuln, request_data)
                        vulnerabilities.append(vuln)
            
            # 5. 信息泄露检测（响应级别）
            if scan_options.get('info_leak'):
                print("[Scanner] 开始信息泄露检测")
                response = send_http_request(request_data, timeout=self.timeout)
                if response:
                    leaks = self.info_leak_scanner.scan_response(response.text, request_data.get('url', ''))
                    print(f"[Scanner] 信息泄露检测发现 {len(leaks)} 个泄露")
                    # 保存所有信息泄露漏洞到数据库
                    if save_to_db:
                        for leak in leaks:
                            self._save_vuln_to_db(leak, request_data)
                    vulnerabilities.extend(leaks)
                else:
                    print("[Scanner] 信息泄露检测：无法获取响应")
        
        except Exception as e:
            self.Core_Function.callback_logging().error(f"扫描失败: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # 6. 将扫描的参数写入去重表（仅自动模式）
            if enable_dedup and scanned_params:
                try:
                    url = request_data.get('url', '')
                    
                    # 获取 website（使用核心库）
                    website = self.Core_Function.callback_split_url(url, 0)
                    if not website:
                        website = ''
                    
                    # 获取 url_path（域名 + 泛化后的路径）
                    parsed = urlparse(url)
                    path_generalized = callback_pathname(parsed.path)
                    url_path = website.rstrip('/') + path_generalized
                    
                    # 写入去重表
                    from database.vuln_param_database import VulnParamDatabase
                    vuln_param_db = VulnParamDatabase(self.project_name)
                    vuln_param_db.add_scanned_param(url_path, scanned_params, website)
                    print(f"[Scanner] 已记录 {len(scanned_params)} 个参数到去重表")
                except Exception as e:
                    self.Core_Function.callback_logging().error(f"记录参数失败: {e}")
        
        print(f"[Scanner] 扫描完成，共发现 {len(vulnerabilities)} 个漏洞")
        return vulnerabilities
    
    def scan_batch(self, request_list, scan_options=None, save_to_db=True):
        """
        批量扫描
        :param request_list: list - HTTP请求数据列表
        :param scan_options: dict - 扫描选项
        :param save_to_db: bool - 是否自动保存到数据库（默认True）
        :return: dict - {'total': int, 'vulns': list}
        """
        all_vulns = []
        
        for request_data in request_list:
            vulns = self.scan(request_data, scan_options, save_to_db)
            all_vulns.extend(vulns)
        
        return {
            'total': len(request_list),
            'vuln_count': len(all_vulns),
            'vulnerabilities': all_vulns
        }
    
    def fuzz_params(self, request_data):
        """
        参数名爆破
        :param request_data: HTTP请求数据
        :return: dict - 发现的参数
        """
        return self.param_fuzzer.scan(
            request_data, 
            send_request_func=lambda req: send_http_request(req, timeout=self.timeout)
        )
    
    def auto_scan(self, batch_size=10, scan_options=None):
        """
        自动扫描模式：持续从流量表读取未扫描流量并执行漏洞检测
        
        流程：
        1. 检查 scaner_service 是否为 1（扫描服务是否开启）
           - 如果不为 1，睡眠 10 秒后重新判断
           - 如果为 1，执行扫描
        2. 读取流量表中 scaner_status 为 0 的流量（未扫描）
        3. 进行漏洞检测
        4. 检测完成后设置 scaner_status 为 1（已扫描）
        5. 继续下一轮循环
        
        :param batch_size: 每批次处理的流量数量（默认10）
        :param scan_options: 扫描选项
        """
        import time
        
        print(f"[AutoScan] 启动自动扫描服务，批次大小 {batch_size}")
        
        while True:
            try:
                # 1. 检查扫描服务是否开启
                project_config = self.Core_Function.callback_project_config()
                if not project_config:
                    print("[AutoScan] 无法获取项目配置，等待重试...")
                    time.sleep(10)
                    continue
                
                service_lock = project_config.get('service_lock', {})
                scaner_service = service_lock.get('scaner_service', 0)
                
                # 如果服务未开启，睡眠 10 秒后重新判断
                if scaner_service != 1:
                    time.sleep(10)
                    continue
                
                # 2. 获取未扫描流量（scaner_status=0）
                traffic_list = self.traffic_db.get_unscanned_traffic(limit=batch_size)
                if not traffic_list:
                    # 没有未扫描流量，等待 10 秒后继续
                    time.sleep(10)
                    continue
                
                print(f"[AutoScan] 获取到 {len(traffic_list)} 条未扫描流量")
                
                # 3. 遍历每条流量进行扫描
                for traffic in traffic_list:
                    traffic_id = traffic.get('_id')
                    url = traffic.get('url', 'Unknown')
                    
                    try:
                        print(f"[AutoScan] 开始扫描: {url}")
                        
                        # 3.1 构造请求数据
                        request_data = {
                            'url': traffic.get('url', ''),
                            'method': traffic.get('method', 'GET'),
                            'headers': traffic.get('headers', {}),
                            'body': traffic.get('body', '')
                        }
                        
                        # 3.2 执行扫描（自动模式启用去重）
                        vulns = self.scan(request_data, scan_options=scan_options, save_to_db=True, enable_dedup=True)
                        
                        print(f"[AutoScan] 扫描完成: {url}，发现 {len(vulns)} 个漏洞")
                        
                        # 3.3 扫描完成，标记为已扫描
                        self.traffic_db.mark_traffic_as_scanned(traffic_id)
                        
                    except Exception as e:
                        error_msg = f"扫描失败 [{url}]: {str(e)}"
                        print(f"[AutoScan] {error_msg}")
                        self.Core_Function.callback_logging().error(error_msg)
                        # 扫描失败也标记为已扫描，避免重复扫描
                        self.traffic_db.mark_traffic_as_scanned(traffic_id)
                
            except KeyboardInterrupt:
                print("\n[AutoScan] 接收到停止信号，退出自动扫描")
                break
            except Exception as e:
                error_msg = f"自动扫描异常: {str(e)}"
                print(f"[AutoScan] {error_msg}")
                self.Core_Function.callback_logging().error(error_msg)
                time.sleep(5)  # 异常后等待5秒重试


# 兼容旧接口
Scanner = VulnerabilityScanner


if __name__ == "__main__":
    # 测试代码
    scanner = VulnerabilityScanner()
    
    test_request = {
        'url': 'http://testphp.vulnweb.com/artists.php?artist=1',
        'method': 'GET',
        'headers': {
            'User-Agent': 'Mozilla/5.0'
        }
    }
    
    results = scanner.scan(test_request)
    print(f"发现 {len(results)} 个漏洞:")
    for vuln in results:
        print(f"  [{vuln['vuln_type']}] {vuln.get('param', 'N/A')} - {vuln.get('payload', 'N/A')}")
