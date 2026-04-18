# coding: utf-8
"""
请求参数处理模块
@Time :    4/5/2026
@Author:  facai
@File: param_handler.py
@Software: VSCode

功能说明：
1. callback_list_param  - 获取HTTP请求参数，返回参数列表
2. set_param_value      - 设置参数值，支持默认、追加、替换三种模式
3. get_param_value      - 获取参数值
4. get_param_type       - 获取参数类型
"""

import json
import re
import copy
import urllib.parse
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from service.Class_Core_Function import Class_Core_Function
from database.vuln_param_database import VulnParamDatabase
from service.spider.http_standardization import callback_pathname


class ParamHandler:
    """请求参数处理模块"""
    
    def __init__(self, project_name=None):
        self.Core_Function = Class_Core_Function()
        self.project_name = project_name
        self.vuln_param_db = VulnParamDatabase(project_name) if project_name else None
    
    # ==================== 核心功能接口 ====================
    
    def callback_list_param(self, request_data, enable_dedup=True):
        """
        获取HTTP请求参数，传输HTTP请求进去，返回参数列表
        
        Args:
            request_data: dict - HTTP请求数据
                {
                    "url": "http://127.0.0.1/test?name=1",
                    "method": "POST",
                    "headers": {"User-Agent": "Mozilla/5.0"},
                    "body": "aa=1&bb=a"
                }
            enable_dedup: bool - 是否启用参数去重（默认True）
        
        Returns:
            list - 参数列表
                [
                    {"param_name": "name", "param_value": "1", "param_type": "Int", "position": "GET"},
                    {"param_name": "aa", "param_value": "1", "param_type": "Int", "position": "POST"},
                    ...
                ]
        
        过滤规则:
            - 参数名长度大于30的参数将被过滤（避免文件上传等场景的误解析）
            - 最多返回30个参数
            - 如果启用去重，已扫描过的参数将被过滤
        """
        # 提取所有参数
        params = self._extract_params(request_data)
        
        # 如果启用去重且有数据库连接
        if enable_dedup and self.vuln_param_db:
            # 获取URL路径（使用 callback_pathname）
            url = request_data.get('url', '')
            parsed = urlparse(url)
            path_generalized = callback_pathname(parsed.path)
            
            # 获取网站URL（使用核心库）
            website = self.Core_Function.callback_split_url(url, 0)
            if not website:
                website = ''
            
            # 构建完整的 url_path（域名 + 泛化路径）
            url_path = website.rstrip('/') + path_generalized
            
            # 查询已扫描的参数
            scanned_params = self.vuln_param_db.get_scanned_params(url_path, website)
            
            print(f"[ParamHandler] 去重查询: url_path={url_path}, website={website}, 已扫描参数={scanned_params}")
            
            # 过滤掉已扫描的参数
            params = [p for p in params if p['param_name'] not in scanned_params]
        
        return params
    
    def set_param_value(self, request_data, param_name, new_value, mode=0):
        """
        设置参数值，传输HTTP请求参数，以及参数名，修改的参数值，参数修改方式，返回修改后的HTTP请求参数
        
        Args:
            request_data: dict - HTTP请求数据
            param_name: str - 参数名
            new_value: str - 修改的参数值
            mode: int - 参数修改方式
                0 - 追加（在原值后面追加）- 默认
                1 - 替换（完全替换原值）
                2 - 值前增加（在原值前面增加）
        
        Returns:
            dict - 修改后的HTTP请求数据
        """
        try:
            # 深拷贝请求数据，避免修改原始数据
            modified_request = copy.deepcopy(request_data)
            
            # 获取参数列表
            params_list = self.callback_list_param(request_data)
            
            # 查找目标参数
            target_param = None
            for param in params_list:
                if param['param_name'] == param_name:
                    target_param = param
                    break
            
            if not target_param:
                self.Core_Function.callback_logging().warning(f"参数 {param_name} 不存在")
                return modified_request
            
            # 计算新值
            old_value = target_param['param_value']
            position = target_param['position']
            
            if mode == 0:  # 追加（默认）
                final_value = old_value + new_value
            elif mode == 1:  # 替换
                final_value = new_value
            elif mode == 2:  # 值前增加
                final_value = new_value + old_value
            else:  # 兜底，默认追加
                final_value = old_value + new_value
            
            # 根据参数位置修改请求
            if position == 'GET':
                modified_request = self._set_get_param(modified_request, param_name, final_value)
            elif position == 'POST':
                modified_request = self._set_post_param(modified_request, param_name, final_value)
            elif position == 'JSON':
                modified_request = self._set_json_param(modified_request, param_name, final_value)
            
            return modified_request
        
        except Exception as e:
            self.Core_Function.callback_logging().error(f"设置参数值失败: {e}")
            return request_data
    
    def get_param_value(self, request_data, param_name):
        """
        获取参数值，传输HTTP请求参数，以及参数名，返回参数值
        
        Args:
            request_data: dict - HTTP请求数据
            param_name: str - 参数名
        
        Returns:
            str - 参数值（如果参数不存在，返回None）
        """
        try:
            params_list = self.callback_list_param(request_data)
            for param in params_list:
                if param['param_name'] == param_name:
                    return param['param_value']
            return None
        except Exception as e:
            self.Core_Function.callback_logging().error(f"获取参数值失败: {e}")
            return None
    
    def get_param_type(self, request_data, param_name):
        """
        获取参数类型，传输HTTP请求参数，以及参数名，返回参数类型
        
        Args:
            request_data: dict - HTTP请求数据
            param_name: str - 参数名
        
        Returns:
            str - 参数类型（如果参数不存在，返回None）
                可能的值: int, string, url
        """
        try:
            params_list = self.callback_list_param(request_data, enable_dedup=False)
            for param in params_list:
                if param['param_name'] == param_name:
                    return param['param_type']
            return None
        except Exception as e:
            self.Core_Function.callback_logging().error(f"获取参数类型失败: {e}")
            return None
    
    # ==================== 内部辅助方法 ====================
    
    def _extract_params(self, request_data):
        """
        从HTTP请求数据中提取所有参数
        :param request_data: dict - 包含url, method, headers, body等字段
        :return: list - 参数列表
        """
        params = []
        
        try:
            url = request_data.get('url', '')
            # method = request_data.get('method', 'GET').upper()  # 不再需要method判断
            body = request_data.get('body', '')
            
            # 1. GET参数
            parsed = urlparse(url)
            get_params = parse_qs(parsed.query)
            for param, values in get_params.items():
                param_value = values[0] if values else ''
                params.append({
                    'param_name': param,
                    'param_value': param_value,
                    'param_type': self._identify_param_type(param_value),
                    'position': 'GET'
                })
            
            # 2. Body参数（适用于所有方法：POST、PUT、PATCH、DELETE等）
            if body:
                # 智能识别body内容类型，按优先级尝试解析
                
                # 先判断body是否已经是字典/列表对象
                if isinstance(body, dict):
                    # 字典对象 -> JSON
                    params.extend(self._extract_json_params(body))
                elif isinstance(body, list):
                    # 列表对象 -> JSON数组
                    params.extend(self._extract_json_params(body))
                elif isinstance(body, str):
                    # 字符串格式，智能判断
                    
                    # 优先尝试解析为JSON
                    try:
                        json_data = json.loads(body.strip())
                        params.extend(self._extract_json_params(json_data))
                    except:
                        # JSON解析失败，尝试form-urlencoded
                        try:
                            post_params = parse_qs(body.strip())
                            if post_params:  # 确保解析出了参数
                                for param, values in post_params.items():
                                    param_value = values[0] if values else ''
                                    params.append({
                                        'param_name': param,
                                        'param_value': param_value,
                                        'param_type': self._identify_param_type(param_value),
                                        'position': 'POST'
                                    })
                        except:
                            pass
        
        except Exception as e:
            self.Core_Function.callback_logging().error(f"参数提取失败: {e}")
        
        # 过滤掉参数名长度大于30的参数（避免文件上传等场景的误解析）
        params = [p for p in params if len(p['param_name']) <= 30]
        
        return params[:30]
    
    def _extract_json_params(self, json_data, prefix=''):
        """递归提取JSON参数"""
        params = []
        
        if isinstance(json_data, dict):
            for key, value in json_data.items():
                param_name = f"{prefix}.{key}" if prefix else key
                if isinstance(value, (dict, list)):
                    params.extend(self._extract_json_params(value, param_name))
                else:
                    params.append({
                        'param_name': param_name,
                        'param_value': str(value),
                        'param_type': self._identify_param_type(str(value)),
                        'position': 'JSON'
                    })
        elif isinstance(json_data, list):
            for i, value in enumerate(json_data):
                param_name = f"{prefix}[{i}]"
                if isinstance(value, (dict, list)):
                    params.extend(self._extract_json_params(value, param_name))
                else:
                    params.append({
                        'param_name': param_name,
                        'param_value': str(value),
                        'param_type': self._identify_param_type(str(value)),
                        'position': 'JSON'
                    })
        
        return params
    
    def _identify_param_type(self, text):
        """
        识别参数类型（漏洞测试专用）
        
        简化类型：
        - int: 数字型（整数、浮点数）
        - string: 字符型（普通字符串、JSON、哈希等）
        - url: URL型（自动识别编码过的URL）
        
        Args:
            text: 参数值
        
        Returns:
            str - 参数类型 (int, string, url)
        """
        if text is None:
            return 'string'
        
        # 转为字符串并去除两端空白
        text_str = str(text).strip()
        if not text_str:
            return 'string'
        
        # 1. 判断是否为数字型（整数和浮点数）
        if text_str.isdigit() or (text_str.startswith('-') and text_str[1:].isdigit()):
            return 'int'
        
        try:
            float(text_str)
            return 'int'
        except ValueError:
            pass
        
        # 2. 判断是否为URL型（自动识别编码过的URL）
        # 先尝试URL解码
        decoded_text = text_str
        if '%' in text_str and re.search(r'%[0-9a-fA-F]{2}', text_str):
            try:
                unquoted = urllib.parse.unquote(text_str)
                if unquoted != text_str:
                    decoded_text = unquoted
            except Exception:
                pass
        
        # 判断解码后的文本是否为URL（兼容 http://, https://, //）
        if decoded_text.startswith(('http://', 'https://', '//')):
            return 'url'
        
        # 3. 兜底返回字符型
        return 'string'
    
    def _set_get_param(self, request_data, param_name, new_value):
        """设置GET参数"""
        url = request_data.get('url', '')
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        
        # 更新参数值
        query_params[param_name] = [new_value]
        
        # 重新构建URL
        new_query = urlencode(query_params, doseq=True)
        new_url = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment
        ))
        
        request_data['url'] = new_url
        return request_data
    
    def _set_post_param(self, request_data, param_name, new_value):
        """设置POST参数（application/x-www-form-urlencoded）"""
        body = request_data.get('body', '')
        
        # 智能判断body内容类型
        if isinstance(body, dict):
            # 字典格式，尝试form数据修改
            if param_name in body:
                body[param_name] = new_value
                request_data['body'] = body
        elif isinstance(body, str):
            # 字符串格式，尝试解析为form-urlencoded
            try:
                post_params = parse_qs(body.strip())
                if post_params and param_name in post_params:
                    # 确认是form-urlencoded格式且参数存在
                    post_params[param_name] = [new_value]
                    request_data['body'] = urlencode(post_params, doseq=True)
            except:
                pass
        
        return request_data
    
    def _set_json_param(self, request_data, param_name, new_value):
        """设置JSON参数"""
        body = request_data.get('body', '')
        try:
            # 智能识别body类型，优先尝试JSON解析
            is_string_body = isinstance(body, str)
            
            if isinstance(body, (dict, list)):
                # 字典/列表对象
                json_data = body
            else:
                # 字符串，尝试JSON解析
                json_data = json.loads(body.strip())
            
            # 解析参数名路径（如: user.profile.name）
            keys = param_name.split('.')
            current = json_data
            
            # 遍历到倒数第二层
            for key in keys[:-1]:
                if key.endswith(']'):
                    # 处理数组索引
                    match = re.match(r'^(.+)\[(\d+)\]$', key)
                    if match:
                        key_name = match.group(1)
                        index = int(match.group(2))
                        current = current[key_name][index]
                else:
                    current = current[key]
            
            # 设置最后一层的值
            final_key = keys[-1]
            if final_key.endswith(']'):
                # 处理数组索引
                match = re.match(r'^(.+)\[(\d+)\]$', final_key)
                if match:
                    key_name = match.group(1)
                    index = int(match.group(2))
                    current[key_name][index] = new_value
            else:
                current[final_key] = new_value
            
            # 保持原始格式：字符串还是对象
            if is_string_body:
                request_data['body'] = json.dumps(json_data, ensure_ascii=False)
            else:
                request_data['body'] = json_data
            
        except Exception as e:
            self.Core_Function.callback_logging().error(f"设置JSON参数失败: {e}")
        
        return request_data


if __name__ == "__main__":
    # 测试代码
    handler = ParamHandler()
    
    test_request = {
        'url': 'http://127.0.0.1/test631?name=1&id=123',
        'method': 'POST',
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        'body': 'aa=1&bb=a&url=http%3A%2F%2Fexample.com&json=%7B%22key%22%3A%22value%22%7D'
    }
    
    print("=" * 80)
    print("测试1: callback_list_param - 获取参数列表")
    print("=" * 80)
    params = handler.callback_list_param(test_request)
    print(f"提取到 {len(params)} 个参数:")
    for p in params:
        print(f"  [{p['position']:6}] {p['param_name']:20} = {p['param_value']:40} ({p['param_type']})")


