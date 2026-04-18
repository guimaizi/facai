# coding: utf-8

"""
子域名收集模块
从流量数据中提取和收集子域名
功能：
1. 接收list_subdomain传参
2. 对list_subdomain进行数据库去重处理
3. 多线程获取子域名dns解析记录
4. 对域名进行端口扫描
5. 保存进入数据库
6. 非80/443端口导入traffic表
"""

import socket
import os
import threading
import dns.resolver
import nmap
from database.subdomain_database import SubdomainDatabase
from service.Class_Core_Function import Class_Core_Function
from api.import_traffic_api import ImportTrafficAPI


class SubdomainCollector:
    """子域名收集器"""

    def __init__(self, project_name):
        self.project_name = project_name
        self.subdomain_db = SubdomainDatabase(project_name)
        self.core_function = Class_Core_Function()
        self.import_traffic_api = ImportTrafficAPI()
        # 获取项目配置
        self.project_config = self.core_function.callback_project_config()
        self.dns_servers = self.project_config.get('dns_server', [['8.8.8.8', '8.8.4.4']]) if self.project_config else [['8.8.8.8', '8.8.4.4']]
        self.port_target = self.project_config.get('port_target', '80,443') if self.project_config else '80,443'
        self.timeout = self.project_config.get('timeout', 8) if self.project_config else 8
        self.http_thread = self.project_config.get('http_thread', 10) if self.project_config else 10
        self.domain_list = self.project_config.get('domain_list', []) if self.project_config else []
        # 泛解析域名黑名单缓存
        self.wildcard_domains = set()

    def _parse_ports(self, port_string):
        """
        解析端口字符串，支持单端口和范围

        Args:
            port_string: 如 "80,443,8080-8090"

        Returns:
            list: 端口列表
        """
        ports = []
        for part in port_string.split(','):
            part = part.strip()
            if '-' in part:
                # 端口范围
                start, end = map(int, part.split('-'))
                ports.extend(range(start, end + 1))
            else:
                # 单端口
                ports.append(int(part))
        return ports

    def _extract_domain(self, subdomain):
        """
        从子域名中提取主域名，基于project_config中的domain_list进行匹配

        Args:
            subdomain: 如 "www.molun.com"

        Returns:
            str: 匹配的主域名 如 "molun.com"，未匹配则返回原值
        """
        subdomain = subdomain.lower()
        
        if not self.domain_list:
            # 如果没有domain_list，使用默认逻辑（取后两级）
            parts = subdomain.split('.')
            if len(parts) >= 2:
                return '.'.join(parts[-2:])
            return subdomain

        # 从最长匹配开始（匹配更精确的域名优先）
        for domain in sorted(self.domain_list, key=len, reverse=True):
            domain_lower = domain.lower()
            if subdomain.endswith('.' + domain_lower) or subdomain == domain_lower:
                return domain_lower

        # 未匹配到任何domain_list，返回默认后两级
        parts = subdomain.split('.')
        if len(parts) >= 2:
            return '.'.join(parts[-2:])
        return subdomain

    def _get_parent_domain(self, subdomain):
        """
        获取父域名（去掉最左边一级）
        
        Args:
            subdomain: 如 "123123.qzone.molun.com"
            
        Returns:
            str: 父域名 如 "qzone.molun.com"，如果是二级域名则返回None
        """
        parts = subdomain.split('.')
        if len(parts) <= 2:
            # 已经是二级域名或顶级域名，没有父域名可检测
            return None
        return '.'.join(parts[1:])
    
    def _is_valid_domain(self, domain):
        """
        判断是否是有效的域名（至少两级）
        
        Args:
            domain: 如 "molun.com"
            
        Returns:
            bool: True表示是有效域名
        """
        parts = domain.split('.')
        return len(parts) >= 2

    def _check_wildcard_dns(self, domain):
        """
        检测域名是否开启泛解析

        Args:
            domain: 主域名 如 "qzone.molun.com"

        Returns:
            bool: True表示开启了泛解析
        """
        if domain in self.wildcard_domains:
            return True

        # 生成随机子域名进行测试
        random_prefix = self.core_function.callback_ranstr(12)
        test_subdomain = f"{random_prefix}.{domain}"

        try:
            resolver = dns.resolver.Resolver()
            resolver.nameservers = self.dns_servers[0]
            resolver.timeout = 3
            resolver.lifetime = 3

            # 查询A记录
            answer = resolver.resolve(test_subdomain, 'A')
            if answer and len(answer) > 0:
                # 随机子域名解析到了IP，说明开启了泛解析
                self.wildcard_domains.add(domain)
                return True
        except:
            pass

        return False

    def _add_to_blocklist_domain(self, domain):
        """
        将泛解析域名添加到blocklist_domain.txt黑名单
        格式: .domain.com（匹配所有子域名）

        Args:
            domain: 主域名
        """
        try:
            # 获取项目数据目录
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            blocklist_path = os.path.join(project_root, 'project_data', self.project_name, 'blocklist_domain.txt')

            # 确保文件存在
            os.makedirs(os.path.dirname(blocklist_path), exist_ok=True)
            if not os.path.exists(blocklist_path):
                with open(blocklist_path, 'w', encoding='utf-8') as f:
                    f.write('')

            # 读取现有内容
            with open(blocklist_path, 'r', encoding='utf-8') as f:
                existing_domains = set(line.strip() for line in f if line.strip())

            # 泛解析域名格式: .domain.com
            wildcard_domain = f".{domain}"
            
            # 如果不在黑名单中，则添加
            if wildcard_domain not in existing_domains:
                with open(blocklist_path, 'a', encoding='utf-8') as f:
                    f.write(f"{wildcard_domain}\n")
        except Exception as e:
            pass

    def _filter_wildcard_subdomains(self, subdomains):
        """
        过滤泛解析域名（多线程）
        
        检测逻辑：
        - 123123.qzone.molun.com → 检测 qzone.molun.com 是否泛解析
        - qzone.molun.com → 检测 molun.com 是否泛解析
        - molun.com → 已经是最小单位，不需要检测

        Args:
            subdomains: 子域名列表

        Returns:
            dict: {'valid_subdomains': list, 'wildcard_domains': set}
        """
        valid_subdomains = []
        wildcard_detected = set()
        wildcard_lock = threading.Lock()

        # 按父域名分组（用于检测泛解析）
        parent_domain_groups = {}
        for subdomain in subdomains:
            parent = self._get_parent_domain(subdomain)
            if parent:
                if parent not in parent_domain_groups:
                    parent_domain_groups[parent] = []
                parent_domain_groups[parent].append(subdomain)
            else:
                # 二级域名，直接保留，不需要泛解析检测
                valid_subdomains.append(subdomain)

        # 多线程对每个父域名进行泛解析测试
        wildcard_thread = min(self.http_thread * 2, len(parent_domain_groups)) if parent_domain_groups else 1

        wildcard_domains_list = []

        def check_wildcard_wrapper(parent_domain):
            """泛解析测试包装函数"""
            if self._check_wildcard_dns(parent_domain):
                # 该域名开启了泛解析，添加到黑名单
                self._add_to_blocklist_domain(parent_domain)
                with wildcard_lock:
                    wildcard_domains_list.append(parent_domain)

        self.core_function.threadpool_Core_Function(
            check_wildcard_wrapper,
            list(parent_domain_groups.keys()),
            max(wildcard_thread, 1)
        )

        wildcard_detected = set(wildcard_domains_list)

        # 过滤掉泛解析域名的子域名
        for parent_domain, domain_subdomains in parent_domain_groups.items():
            if parent_domain not in wildcard_detected:
                valid_subdomains.extend(domain_subdomains)

        return {
            'valid_subdomains': valid_subdomains,
            'wildcard_domains': wildcard_detected
        }

    def _query_dns(self, subdomain, dns_server):
        """
        查询DNS记录

        Args:
            subdomain: 子域名
            dns_server: DNS服务器列表 [primary, secondary]

        Returns:
            list: DNS记录列表
        """
        dns_data = []
        try:
            resolver = dns.resolver.Resolver()
            resolver.nameservers = dns_server
            resolver.timeout = self.timeout
            resolver.lifetime = self.timeout

            # 查询 A 记录
            try:
                answer = resolver.resolve(subdomain, 'A')
                for rdata in answer:
                    dns_data.append({'A': str(rdata)})
            except:
                pass

            # 查询 CNAME 记录
            try:
                answer = resolver.resolve(subdomain, 'CNAME')
                for rdata in answer:
                    dns_data.append({'CNAME': str(rdata)})
            except:
                pass

            # 查询 AAAA 记录
            try:
                answer = resolver.resolve(subdomain, 'AAAA')
                for rdata in answer:
                    dns_data.append({'AAAA': str(rdata)})
            except:
                pass

        except Exception as e:
            pass

        return dns_data

    def _query_dns_multi_server(self, subdomain):
        """
        多DNS服务器查询

        Args:
            subdomain: 子域名

        Returns:
            list: DNS记录列表
        """
        all_dns_data = []

        for dns_server in self.dns_servers:
            dns_data = self._query_dns(subdomain, dns_server)
            if dns_data:
                all_dns_data.extend(dns_data)
                break  # 成功查询则停止

        return all_dns_data

    def _scan_ports(self, subdomain):
        """
        端口扫描

        Args:
            subdomain: 子域名

        Returns:
            list: 开放端口列表 [{'port': 80, 'service': 'http', 'version': ''}]
        """
        port_list = []
        ports = self._parse_ports(self.port_target)
        time_now = self.core_function.callback_time(0)

        try:
            # 获取IP地址
            resolver = dns.resolver.Resolver()
            resolver.nameservers = self.dns_servers[0]
            resolver.timeout = self.timeout
            resolver.lifetime = self.timeout

            answer = resolver.resolve(subdomain, 'A')
            ip_address = str(answer[0])

            # 使用nmap扫描端口
            nm = nmap.PortScanner()
            scan_result = nm.scan(hosts=ip_address, ports=','.join(map(str, ports)),
                   arguments=f'-sS --version-intensity 3 -T4 --host-timeout {self.timeout}')

            if ip_address in scan_result['scan'] and 'tcp' in scan_result['scan'][ip_address]:
                for port in scan_result['scan'][ip_address]['tcp']:
                    if scan_result['scan'][ip_address]['tcp'][port]['state'] == 'open':
                        service = scan_result['scan'][ip_address]['tcp'][port].get('name', '')
                        version = scan_result['scan'][ip_address]['tcp'][port].get('product', '')
                        port_list.append({
                            'port': port,
                            'service': service,
                            'version': version,
                            'time': time_now
                        })

        except Exception as e:
            # 如果nmap失败，使用socket简单检测
            for port in ports:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(2)
                    result = sock.connect_ex((subdomain, port))
                    if result == 0:
                        port_list.append({
                            'port': port,
                            'service': 'unknown',
                            'version': '',
                            'time': time_now
                        })
                    sock.close()
                except:
                    pass

        return port_list[:20]

    def _process_single_subdomain(self, subdomain):
        """
        处理单个子域名（DNS查询 + 端口扫描）

        Args:
            subdomain: 子域名

        Returns:
            dict: 处理结果，DNS解析失败时返回None
        """
        try:
            # 确保子域名是小写
            subdomain = subdomain.lower()
            
            # DNS查询
            dns_data = self._query_dns_multi_server(subdomain)

            # DNS解析失败，跳过端口扫描
            if not dns_data:
                return None

            # 端口扫描
            port_list = self._scan_ports(subdomain)

            # 非80/443端口导入traffic表
            for port_info in port_list:
                port = port_info.get('port')
                if port and port not in [80, 443]:
                    # 拼成URL并导入traffic表
                    scheme = 'https' if port == 443 else 'http'
                    url = f"{scheme}://{subdomain}:{port}/"
                    try:
                        self.import_traffic_api.import_traffic_url(url, self.project_name)
                    except:
                        pass

            return {
                'subdomain': subdomain,
                'domain': self._extract_domain(subdomain).lower(),
                'time': self.core_function.callback_time(0),
                'port_list': port_list,
                'dns_data': dns_data,
                'status': 0,
                'subdomain_status': 'open'
            }
        except Exception as e:
            return None

    def collect_and_save(self, subdomains):
        """
        收集并保存子域名
        1. 数据库去重处理
        2. 泛解析测试（泛解析域名加入黑名单）
        3. 多线程DNS查询
        4. 多线程端口扫描
        5. 保存到数据库

        Args:
            subdomains: 已提取的子域名列表

        Returns:
            dict: {'success': bool, 'count': int, 'new_count': int, 'wildcard_count': int, 'message': str}
        """
        try:
            # 统一转为小写
            subdomains = [s.lower() for s in subdomains if s]
            
            # 1. 数据库去重处理 - 直接查询判断是否存在
            new_subdomains = []
            for subdomain in subdomains:
                existing = self.subdomain_db.db_handler.find_one(
                    self.subdomain_db.collection_name,
                    {'subdomain': subdomain}
                )
                if not existing:
                    new_subdomains.append(subdomain)

            if not new_subdomains:
                return {
                    'success': True,
                    'count': len(subdomains),
                    'new_count': 0,
                    'wildcard_count': 0,
                    'message': '没有新的子域名需要处理'
                }

            # 2. 泛解析测试
            filter_result = self._filter_wildcard_subdomains(new_subdomains)
            valid_subdomains = filter_result['valid_subdomains']
            wildcard_domains = filter_result['wildcard_domains']

            # 如果所有子域名都是泛解析，直接返回，不再进行后续处理
            if not valid_subdomains:
                return {
                    'success': True,
                    'count': len(subdomains),
                    'new_count': 0,
                    'wildcard_count': len(wildcard_domains),
                    'message': f'所有子域名对应的域名都开启了泛解析（{len(wildcard_domains)}个），已加入黑名单'
                }

            # 3. 使用标准函数多线程处理子域名（DNS查询 + 端口扫描）
            processed_data = []

            def process_wrapper(subdomain):
                """包装函数，用于多线程调用"""
                result = self._process_single_subdomain(subdomain)
                # 只要DNS解析成功就添加到结果中
                if result and result['dns_data']:
                    processed_data.append(result)

            self.core_function.threadpool_Core_Function(process_wrapper, valid_subdomains, self.http_thread)

            # 4. 保存到数据库
            saved_count = 0
            for data in processed_data:
                try:
                    self.subdomain_db.db_handler.insert_one(
                        self.subdomain_db.collection_name,
                        data
                    )
                    saved_count += 1
                except:
                    pass

            return {
                'success': True,
                'count': len(subdomains),
                'new_count': saved_count,
                'wildcard_count': len(wildcard_domains),
                'message': f'成功保存 {saved_count} 个新子域名（{len(wildcard_domains)} 个泛解析域名已加入黑名单）'
            }

        except Exception as e:
            return {
                'success': False,
                'count': 0,
                'new_count': 0,
                'wildcard_count': 0,
                'message': f'收集子域名失败: {str(e)}'
            }
