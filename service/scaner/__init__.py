# coding: utf-8
"""
漏洞扫描器模块

目录结构：
scaner/
   lib_vul/           # CVE漏洞库
      cve-....py
      ...   
   core_vul/          # 核心漏洞扫描模块
      xss.py          # XSS扫描
      sql.py          # SQL注入扫描
      rce.py          # 命令执行扫描
      ssrf.py         # SSRF扫描
      fuzz_paramname.py # 参数名爆破
   param_handler.py   # 参数处理模块
   vul_core.py        # 调度中心
   file_vuln.py       # 文件漏洞扫描
   info_leak.py       # 信息泄露扫描
   vul_config.json    # 配置文件
"""

from .vuln_core import VulnerabilityScanner, Scanner
from .param_handler import ParamHandler

# 核心漏洞扫描模块
from .core_vuln import (
    XSSScanner,
    SQLInjectionScanner,
    RCEScanner,
    SSRFScanner,
    ParamNameFuzzer
)

# 其他扫描模块
from .info_leak import InfoLeakScanner

__all__ = [
    # 主扫描器
    'VulnerabilityScanner',
    'Scanner',
    
    # 参数处理
    'ParamHandler',
    
    # 核心漏洞扫描
    'XSSScanner',
    'SQLInjectionScanner',
    'RCEScanner',
    'SSRFScanner',
    'ParamNameFuzzer',
    
    # 其他扫描
    'FileVulnScanner',
    'InfoLeakScanner',
]
