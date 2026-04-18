# coding: utf-8
"""
核心漏洞扫描模块
@Time :    4/5/2026
@Author:  facai
@File: __init__.py
@Software: VSCode

功能说明：
1. 提供统一的核心漏洞扫描接口
2. 所有模块统一使用 ParamHandler 处理参数
3. 采用无害化检测策略

统一特性：
- 使用 ParamHandler.callback_list_param 提取参数
- 使用 ParamHandler.set_param_value 修改参数（默认追加模式）
- 支持 int、string、url 三种参数类型
- 支持 GET、POST、JSON 三种参数位置

检测模块：
- xss.py        - XSS扫描（无害化）
- sql.py        - SQL注入扫描（无害化）
- rce.py        - 命令执行扫描（无害化）
- ssrf.py       - SSRF扫描（无害化）
- anomaly.py    - 异常参数检测（机器学习）
- fuzz_paramname.py - 参数名爆破
"""

from .xss import XSSScanner
from .sql import SQLInjectionScanner
from .rce import RCEScanner
from .ssrf import SSRFScanner
from .anomaly import AnomalyScanner
from .fuzz_paramname import ParamNameFuzzer

__all__ = [
    'XSSScanner',
    'SQLInjectionScanner',
    'RCEScanner',
    'SSRFScanner',
    'AnomalyScanner',
    'ParamNameFuzzer',
]


# 无害化检测策略说明
SCAN_POLICY = """
=====================================
    无害化检测策略
=====================================

1. XSS检测
   - Payload: test631'">
   - 仅检测参数值是否被回显
   - 不包含恶意XSS代码

2. SQL注入检测
   - Payload: '、''、'like'
   - 仅检测是否触发SQL错误
   - 不执行实际SQL注入

3. 命令执行检测
   - Payload: `curl dnslog`
   - 仅发送DNS查询请求
   - 不执行实际系统命令

4. SSRF检测
   - Payload: http://dnslog.com
   - 仅发送DNS查询请求
   - 不使用file://等危险协议

=====================================
    重要说明
=====================================

所有检测均采用默认追加模式：
- 保留原参数值
- 不破坏业务逻辑
- 更隐蔽，不易触发WAF
- 需人工验证结果

请确保在合法授权范围内使用！
"""


def print_scan_policy():
    """打印无害化检测策略"""
    print(SCAN_POLICY)


if __name__ == "__main__":
    # 打印无害化检测策略
    print_scan_policy()
    
    # 测试所有模块是否正常导入
    print("\n模块导入测试:")
    print(f"  XSSScanner: {XSSScanner}")
    print(f"  SQLInjectionScanner: {SQLInjectionScanner}")
    print(f"  RCEScanner: {RCEScanner}")
    print(f"  SSRFScanner: {SSRFScanner}")
    print(f"  ParamNameFuzzer: {ParamNameFuzzer}")
    
    print("\n所有模块导入成功！")
