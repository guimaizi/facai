# coding: utf-8
"""
SQL注入基础检测模块（无害化）
@Time :    4/5/2026
@Author:  facai
@File: sql.py
@Software: VSCode

功能说明：
1. 统一接口格式：接受HTTP请求JSON和参数列表JSON
2. 使用对比测试确认注入类型
3. 不包含任何恶意SQL注入代码
4. 无害化检测，不触发WAF
5. 与异常检测联动，只测试异常参数

检测流程：
- 数字型: -0 相似 vs -1 不相似 → 数字型注入
- 字符型: 'lIke' 相似 vs 'xxx' 不相似 → 字符型注入
- LIKE型: %'aNd'1 相似 vs %'aNxd'1 不相似 → LIKE型注入
- ORDER BY: ,1 相似 vs ,999 不相似 → ORDER BY注入

接口格式：
HTTP请求：
{
   "url": "http://127.0.0.1/test631?name=1",
   "method": "POST",
   "headers": {
       "User-Agent": "Mozilla/5.0"
   },
   "body": "aa=1&bb=a"
}

参数列表：
[
  {"param_name":"name", "param_value":"1", "param_type":"int", "position":"GET"},
  {"param_name":"aa", "param_value":"1", "param_type":"int", "position":"POST"},
  {"param_name":"bb", "param_value":"a", "param_type":"string", "position":"POST"}
]
"""

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.preprocessing import StandardScaler
from scipy import spatial
from service.scaner.param_handler import ParamHandler
from service.libs.replay_request import send_http_request


class SQLInjectionScanner:
    """SQL注入扫描器（无害化检测）"""
    
    def __init__(self, timeout=5):
        self.timeout = timeout
        self.param_handler = ParamHandler()
        
        # 对比测试payload配置
        self.test_payloads = {
            'int': {
                'normal': '-0',      # 数字运算，如果SQL注入会恢复正常
                'abnormal': '-1',    # 异常值，应该不相似
                'type': 'int-injection',
                'description': '数字型注入'
            },
            'string': {
                'normal': "'lIke'",      # 字符串闭合测试
                'abnormal': "'xxx'",     # 异常闭合
                'type': 'string-injection',
                'description': '字符型注入'
            },
            'like': {
                'normal': "%'aNd'1",     # LIKE语句闭合测试
                'abnormal': "%'aNxd'1",  # 异常闭合
                'type': 'like-injection',
                'description': 'LIKE型注入'
            },
            'orderby': {
                'normal': ',1',      # ORDER BY测试
                'abnormal': ',999',  # 超出范围的列数
                'type': 'orderby-injection',
                'description': 'ORDER BY注入'
            }
        }
    
    def _calculate_similarities(self, baseline_html, test_html_list):
        """
        计算基准HTML与测试HTML列表的相似度
        :param baseline_html: 基准HTML文本列表
        :param test_html_list: 测试HTML文本列表
        :return: 相似度分数列表 (0-1, 1表示完全相同)
        """
        # 将基准和所有测试HTML放在一起进行向量化
        all_html = baseline_html + test_html_list
        #print(all_html)
        # CountVectorizer转换
        vectorizer = CountVectorizer()
        data = vectorizer.fit_transform(all_html)  # type: ignore
        
        # StandardScaler标准化
        scaler = StandardScaler()
        data_scaled = scaler.fit_transform(data.toarray())  # pyright: ignore[reportAttributeAccessIssue]
        
        # 计算每个测试HTML与基准的余弦距离
        baseline_vector = data_scaled[0]
        similarities = []
        
        for i in range(1, len(data_scaled)):
            test_vector = data_scaled[i]
            # 余弦距离: 0表示完全相同, 1表示完全不同
            distance = spatial.distance.cosine(baseline_vector, test_vector)
            # 转换为相似度: 1表示完全相同, 0表示完全不同
            similarity = 1 - distance
            similarities.append(max(0.0, min(1.0, similarity)))
        
        return similarities
    
    def _test_injection_type(self, request_data, param_name, test_type, baseline_responses, send_request_func):
        """
        测试特定类型的SQL注入
        :param request_data: 原始请求
        :param param_name: 参数名
        :param test_type: 测试类型 (int/string/like/orderby)
        :param baseline_responses: 原始HTTP响应对象列表
        :param send_request_func: 发送请求函数
        :return: dict 或 None
        """
        # 提取基准HTML列表
        baseline_html_list = []
        if baseline_responses:
            for resp in baseline_responses:
                if resp is None:
                    baseline_html_list.append("")
                else:
                    baseline_html_list.append(resp.text)
        
        payload_config = self.test_payloads.get(test_type)
        if not payload_config:
            return None
        
        normal_payload = payload_config['normal']
        abnormal_payload = payload_config['abnormal']
        
        # 测试正常payload（追加模式）
        test_request_normal = self.param_handler.set_param_value(
            request_data, param_name, normal_payload, mode=0  # mode=0 追加（默认）
        )
        response_normal = send_request_func(test_request_normal)
        
        if not response_normal:
            html_normal = ""
        else:
            html_normal = response_normal.text
        
        # 测试异常payload（追加模式）
        test_request_abnormal = self.param_handler.set_param_value(
            request_data, param_name, abnormal_payload, mode=0  # mode=0 追加（默认）
        )
        response_abnormal = send_request_func(test_request_abnormal)
        
        if not response_abnormal:
            html_abnormal = ""
        else:
            html_abnormal = response_abnormal.text
        # 计算相似度（baseline_html_list + normal + abnormal）
        similarities = self._calculate_similarities(baseline_html_list, [html_normal, html_abnormal])
        # similarities包含：[baseline之间的相似度..., html_normal相似度, html_abnormal相似度]
        # 取最后两个作为测试payload的相似度
        similarity_normal = similarities[-2]
        similarity_abnormal = similarities[-1]
        
        print(f"    [{test_type}] 正常payload '{normal_payload}': {similarity_normal:.4f}, 异常payload '{abnormal_payload}': {similarity_abnormal:.4f}")
        
        # 判断逻辑：正常payload相似度 >= 0.95 且 异常payload相似度 < 0.95
        if similarity_normal >= 0.95 and similarity_abnormal < 0.95:
            from service.Class_Core_Function import Class_Core_Function
            core_func = Class_Core_Function()
            
            url = request_data.get('url', '')
            return {
                'url': url,
                'method': request_data.get('method'),
                'headers': request_data.get('headers', {}),
                'body': request_data.get('body', ''),
                'website': core_func.callback_split_url(url, 0),
                'subdomain': core_func.callback_split_url(url, 2),
                'vuln_type': 'sql',
                'vuln_type_detail': payload_config['type'],
                'level': 'high',
                'paramname': param_name,
                'payload': normal_payload,
                'similarity_normal': similarity_normal,
                'similarity_abnormal': similarity_abnormal,
                'evidence': f"正常payload相似度 {similarity_normal:.4f}, 异常payload相似度 {similarity_abnormal:.4f}",
                'description': payload_config['description'],
                'time': core_func.callback_time(0)
            }
        
        return None
    
    def scan(self, request_data, params_list=None, send_request_func=None, anomaly_params=None, baseline_responses=None):
        """
        SQL注入基础检测（无害化，与异常检测联动）
        
        Args:
            request_data: dict - HTTP请求数据
            params_list: list - 参数列表
            send_request_func: function - 发送请求的函数
            anomaly_params: list - 异常参数列表（只测试这些参数）
            baseline_responses: list - 原始HTTP响应对象列表
        
        Returns:
            list - 发现的漏洞列表
        """
        vulnerabilities = []
        
        if params_list is None:
            params_list = []
        
        # 如果没有提供发送请求函数，使用默认
        if send_request_func is None:
            send_request_func = lambda req: send_http_request(req, timeout=self.timeout)
        
        # 如果提供了异常参数列表，只测试这些参数
        test_params = anomaly_params if anomaly_params else params_list
        
        print(f"\n[SQL注入检测] 开始检测，共 {len(test_params)} 个参数需要测试")
        
        # 遍历参数进行检测
        for param_info in test_params:
            param_name = param_info.get('param_name')
            param_type = param_info.get('param_type', 'string').lower()  # 统一转为小写
            position = param_info.get('position', 'UNKNOWN')
            
            print(f"[SQL注入检测] 测试参数: {param_name} ({position}), 类型: {param_type}")
            
            found_vuln = None
            
            # 根据参数类型决定检测顺序
            if param_type == 'int':
                # 数字型参数：先测试数字型注入（使用mode=1替换）
                print(f"  测试数字型注入...")
                found_vuln = self._test_injection_type(
                    request_data, param_name, 'int', baseline_responses, send_request_func
                )
                
                if not found_vuln:
                    # 如果失败，尝试字符型注入
                    print(f"  测试字符型注入...")
                    found_vuln = self._test_injection_type(
                        request_data, param_name, 'string', baseline_responses, send_request_func
                    )
            else:
                # 字符串/URL/其他类型：直接测试字符型注入（使用mode=1替换）
                print(f"  测试字符型注入...")
                found_vuln = self._test_injection_type(
                    request_data, param_name, 'string', baseline_responses, send_request_func
                )
            
            # 如果还没找到，继续测试 LIKE 和 ORDER BY
            if not found_vuln:
                print(f"  测试LIKE型注入...")
                found_vuln = self._test_injection_type(
                    request_data, param_name, 'like', baseline_responses, send_request_func
                )
            
            if not found_vuln:
                print(f"  测试ORDER BY注入...")
                found_vuln = self._test_injection_type(
                    request_data, param_name, 'orderby', baseline_responses, send_request_func
                )
            
            # 如果发现漏洞，添加到列表
            if found_vuln:
                found_vuln['url'] = request_data.get('url')
                found_vuln['method'] = request_data.get('method')
                found_vuln['position'] = position
                vulnerabilities.append(found_vuln)
                print(f"  [!] 发现{found_vuln['description']}!")
        
        print(f"[SQL注入检测] 检测完成，发现 {len(vulnerabilities)} 个SQL注入漏洞")
        
        return vulnerabilities
