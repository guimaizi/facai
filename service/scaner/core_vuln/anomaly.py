# coding: utf-8
"""
异常参数检测模块（基于机器学习）
@Time :    4/7/2026
@Author:  facai
@File: anomaly.py
@Software: VSCode

功能说明：
1. 获取原始响应作为基准（重放4次）
2. 对参数进行单引号、双引号测试
3. 使用CountVectorizer + StandardScaler标准化
4. 使用余弦距离对比响应差异
5. 检测修改参数后是否出现页面异常

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


class AnomalyScanner:
    """异常参数检测扫描器"""
    
    def __init__(self, timeout=5):
        self.timeout = timeout
        self.param_handler = ParamHandler()
        self.vectorizer = CountVectorizer()
        self.scaler = StandardScaler()
    
    def _get_baseline_responses(self, request_data, num_requests=4):
        """
        获取原始响应列表（重放多次）
        :param request_data: 原始请求
        :param num_requests: 重放次数（默认4次）
        :return: HTTP响应对象列表
        """
        responses = []
        for i in range(num_requests):
            response = send_http_request(request_data, timeout=self.timeout)
            responses.append(response)
        return responses
    
    def _calculate_similarities(self, baseline_html_list, test_html_list):
        """
        计算基准HTML列表与测试HTML列表的相似度
        :param baseline_html_list: 基准HTML文本列表
        :param test_html_list: 测试HTML文本列表
        :return: 相似度分数列表 (0-1, 1表示完全相同)
        """
        # 检查列表是否为空
        if not baseline_html_list or not test_html_list:
            return [0.0] * len(test_html_list)
        
        # 将基准和所有测试HTML放在一起进行向量化
        all_html = baseline_html_list + test_html_list
        
        try:
            # CountVectorizer转换
            data = self.vectorizer.fit_transform(all_html)
            
            # StandardScaler标准化
            data_scaled = self.scaler.fit_transform(data.toarray())
            
            # 计算每个测试HTML与第一个基准的余弦距离
            baseline_vector = data_scaled[0]
            similarities = []
            
            for i in range(len(baseline_html_list), len(data_scaled)):
                test_vector = data_scaled[i]
                # 余弦距离: 0表示完全相同, 1表示完全不同
                distance = spatial.distance.cosine(baseline_vector, test_vector)
                # 转换为相似度: 1表示完全相同, 0表示完全不同
                similarity = 1 - distance
                similarities.append(max(0.0, min(1.0, similarity)))
            
            return similarities
        
        except Exception as e:
            print(f"  [!] 计算相似度失败: {str(e)}")
            return [0.0] * len(test_html_list)
    
    def scan(self, request_data, params_list, send_request_func=None):
        """
        执行异常参数检测
        :param request_data: HTTP请求数据
        :param params_list: 参数列表
        :param send_request_func: 发送请求的函数（可选）
        :return: dict - {
            'vulnerabilities': 漏洞列表,
            'anomaly_params': 异常参数列表,
            'baseline_responses': 基准响应对象列表
        }
        """
        vulnerabilities = []
        anomaly_params = []  # 异常参数列表
        
        print(f"\n[异常检测] 开始检测，共 {len(params_list)} 个参数")
        
        # 1. 获取原始响应基准（重放4次）
        print("[异常检测] 正在获取原始响应基准...")
        baseline_responses = self._get_baseline_responses(request_data, num_requests=4)
        
        # 提取基准HTML列表
        baseline_html_list = []
        for resp in baseline_responses:
            if resp is None:
                baseline_html_list.append("")
            else:
                baseline_html_list.append(resp.text)
        
        print(f"[异常检测] 获取到 {len([h for h in baseline_html_list if h])} 个有效响应")
        
        # 2. 遍历每个参数，单独添加引号测试
        test_payload = "'\""
        
        for param_info in params_list:
            param_name = param_info.get('param_name')
            param_value = param_info.get('param_value')
            param_type = param_info.get('param_type')
            position = param_info.get('position')
            
            print(f"\n[异常检测] 测试参数: {param_name} ({position})")
            
            # 修改参数值（追加模式）
            modified_request = self.param_handler.set_param_value(
                request_data.copy(),
                param_name,
                test_payload,
                mode=0  # mode=0 追加（默认）
            )
            
            if modified_request is None:
                continue
            
            # 发送测试请求
            if send_request_func:
                response = send_request_func(modified_request)
            else:
                response = send_http_request(modified_request, timeout=self.timeout)
            
            test_html = response.text if response else ""
            
            # 计算相似度（baseline_html_list + test_html）
            similarities = self._calculate_similarities(baseline_html_list, [test_html])
            # similarities包含：[baseline之间的相似度..., test_html相似度]
            # 取最后一个作为测试payload的相似度
            similarity = similarities[-1]
            
            print(f"  相似度: {similarity:.4f}")
            
            # 判断是否异常
            # 参考逻辑：1/distance * 100 < 80
            # distance = 1 - similarity
            # 1/distance * 100 < 80 等价于 distance > 0.0125
            # 即 similarity < 0.9875
            # 但我们用更宽松的标准：< 0.95 为异常
            
            if similarity < 0.85:
                from service.Class_Core_Function import Class_Core_Function
                core_func = Class_Core_Function()
                
                # 明显异常（改为低危）
                severity = 'low'
                description = f"参数 {param_name} 添加引号后响应明显异常，相似度: {similarity:.4f}"
                
                url = request_data.get('url', '')
                vuln = {
                    'url': url,
                    'method': request_data.get('method'),
                    'headers': request_data.get('headers', {}),
                    'body': request_data.get('body', ''),
                    'website': core_func.callback_split_url(url, 0),
                    'subdomain': core_func.callback_split_url(url, 2),
                    'vuln_type': 'anomaly',
                    'vuln_type_detail': 'parameter-anomaly',
                    'level': severity,
                    'paramname': param_name,
                    'param_value': param_value,
                    'payload': test_payload,
                    'similarity': similarity,
                    'description': description,
                    'time': core_func.callback_time(0)
                }
                
                vulnerabilities.append(vuln)
                anomaly_params.append(param_info)
                
                print(f"  [!] 发现异常! 严重程度: {severity}")
            
            elif similarity < 0.95:
                from service.Class_Core_Function import Class_Core_Function
                core_func = Class_Core_Function()
                
                # 轻微异常（改为低危）
                severity = 'low'
                description = f"参数 {param_name} 添加引号后响应轻微异常，相似度: {similarity:.4f}"
                
                url = request_data.get('url', '')
                vuln = {
                    'url': url,
                    'method': request_data.get('method'),
                    'headers': request_data.get('headers', {}),
                    'body': request_data.get('body', ''),
                    'website': core_func.callback_split_url(url, 0),
                    'subdomain': core_func.callback_split_url(url, 2),
                    'vuln_type': 'anomaly',
                    'vuln_type_detail': 'parameter-anomaly',
                    'level': severity,
                    'paramname': param_name,
                    'param_value': param_value,
                    'payload': test_payload,
                    'similarity': similarity,
                    'description': description,
                    'time': core_func.callback_time(0)
                }
                
                vulnerabilities.append(vuln)
                anomaly_params.append(param_info)
                
                print(f"  [!] 发现异常! 严重程度: {severity}")
        
        print(f"\n[异常检测] 检测完成，发现 {len(vulnerabilities)} 个异常")
        
        return {
            'vulnerabilities': vulnerabilities,
            'anomaly_params': anomaly_params,
            'baseline_responses': baseline_responses
        }
