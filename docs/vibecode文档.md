# vibe code文档

facai 是这个项目的名字，这是一个 Flask 项目，数据库使用 MongoDB，所有功能围绕着 mitmproxy HTTP 代理、Chrome CDP 控制，并且前后端分离，具体功能为网络安全资产管理系统。

---

## 项目依赖

```
Flask              # Web框架
pymongo            # MongoDB数据库驱动
requests           # HTTP请求库
python-nmap        # Nmap端口扫描
psutil             # 系统进程管理
mitmproxy          # HTTP/HTTPS代理
beautifulsoup4     # HTML解析
playwright         # 浏览器自动化
urlextract         # URL提取
openai             # OpenAI API调用
sklearn            # 机器学习库（文本相似度计算）
```

**安装依赖**:
```bash
pip install -r requirements.txt
```

---

## 代码目录结构

```
facai/
├── app.py                      # Flask应用入口，路由注册
├── config.json                 # 全局配置文件
├── requirements.txt            # 项目依赖列表
├── mitmproxy_service.py        # mitmproxy代理服务
├── service_manager.py          # 系统服务管理器
├── start.bat                   # Windows启动脚本
│
├── api/                        # 前后端接口通信
│   ├── agent_api.py            # AI Agent接口
│   ├── assets_config_api.py    # 资产配置接口
│   ├── highlight_api.py        # 高亮标记接口
│   ├── html_api.py             # HTML解析接口
│   ├── http_api.py             # HTTP请求接口
│   ├── import_traffic_api.py   # 流量导入接口
│   ├── mcp_api.py              # MCP协议接口
│   ├── overview_api.py         # 总览接口
│   ├── project_api.py          # 项目管理接口
│   ├── scaner_api.py           # 漏洞扫描接口
│   ├── service_api.py          # 服务管理接口
│   ├── subdomain_api.py        # 子域名接口
│   ├── tools_api.py            # 工具接口
│   ├── traffic_api.py          # 流量管理接口
│   └── website_api.py          # 站点接口
│
├── database/                   # MongoDB数据库处理
│   ├── mongodb_handler.py      # MongoDB连接处理器
│   ├── project_database.py     # 项目数据库
│   ├── traffic_database.py     # 流量数据库
│   ├── subdomain_database.py   # 子域名数据库
│   ├── website_database.py     # 站点数据库
│   ├── vuln_database.py        # 漏洞数据库
│   ├── vuln_log_database.py    # 漏洞日志数据库
│   ├── assets_config_database.py # 资产配置数据库
│   ├── highlight_database.py   # 高亮标记数据库
│   ├── html_database.py        # HTML数据库
│   └── http_database.py        # HTTP数据库
│
├── service/                    # 系统后端功能
│   ├── Class_check.py          # 数据验证库
│   ├── Class_Core_Function.py  # 核心功能库
│   │
│   ├── libs/                   # 常用功能库
│   │   ├── replay_request.py   # HTTP请求重放
│   │   ├── port_scan.py        # 端口扫描
│   │   ├── clipboard_monitor.py # 剪贴板监控
│   │   └── ...                 # 其他工具库
│   │
│   ├── spider/                 # 爬虫功能
│   │   ├── core.py             # 爬虫核心
│   │   ├── subdomain.py        # 子域名发现
│   │   ├── html.py             # HTML解析爬虫
│   │   ├── dynamic_crawler.py  # 动态爬虫
│   │   ├── http_standardization.py # HTTP请求标准化/去重
│   │   └── ...                 # 其他爬虫模块
│   │
│   ├── scaner/                 # 扫描器功能
│   │   ├── vuln_core.py        # 漏洞扫描核心
│   │   ├── core_vuln/          # 漏洞检测模块
│   │   │   ├── sqli.py         # SQL注入检测
│   │   │   ├── xss.py          # XSS检测
│   │   │   ├── rce.py          # 命令执行检测
│   │   │   ├── ssrf.py         # SSRF检测
│   │   │   ├── anomaly.py      # 异常检测
│   │   │   ├── info_leak.py    # 信息泄露检测
│   │   │   └── fuzz_paramname.py # 参数名爆破
│   │   └── ...                 # 其他扫描模块
│   │
│   └── agent/                  # AI Agent功能
│       ├── mcp_client.py       # MCP协议客户端
│       ├── agent_core.py       # Agent核心
│       └── ...                 # 其他Agent模块
│
├── static/                     # 前端静态文件
│   ├── js/                     # JavaScript文件
│   │   ├── pageup.js           # 分页组件
│   │   ├── traffic/            # 流量管理模块
│   │   ├── scaner/             # 扫描器模块
│   │   ├── spider/             # 爬虫模块
│   │   ├── assets/             # 资产管理模块
│   │   ├── projects/           # 项目管理模块
│   │   ├── services/           # 服务管理模块
│   │   ├── tools/              # 工具模块
│   │   └── ...                 # 其他模块
│   │
│   └── css/                    # 样式文件
│       ├── traffic/
│       ├── scaner/
│       ├── spider/
│       └── ...
│
├── templates/                  # HTML模板文件
│   └── index.html              # 主页面模板
│
├── project_data/               # 项目静态文件
│   └── {project_name}/         # 根据项目名生成
│       ├── images/             # 项目图片
│       │   └── 2026-03-11/     # 日期目录
│       ├── whitelist_domain.txt # 域名白名单
│       ├── blocklist_domain.txt # 域名黑名单
│       ├── blocklist_url.txt   # URL黑名单
│       └── logs/               # 日志保存
│           └── debug.log       # 调试日志
│
├── docs/                       # 文档说明
│   ├── vibecode文档.md         # 项目概述文档
│   ├── 数据库结构.md           # 数据库结构说明
│   ├── HTTP流量.md             # HTTP流量说明
│   ├── HTTP流量请求处理与去重.md # HTTP去重方案
│   ├── 漏洞扫描服务.md         # 漏洞扫描说明
│   ├── 资产监控.md             # 资产监控说明
│   └── ...                     # 其他文档
│
└── test_*.py                   # 测试脚本
    ├── test_vuln_scanner.py    # 漏洞扫描测试
    ├── test_spider_core.py     # 爬虫核心测试
    └── ...                     # 其他测试
```

---

## 配置文件说明

`config.json` 是项目的全局配置文件，包含以下配置项：

```json
{
    "flask_port": 5001,
    "chrome_path": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "burp_path": "D:\\hack_tools\\burp\\",
    "chrome_cdp_port": 19227,
    "chrome_spider_cdp_port": 19228,
    "mitmproxy_port": 18081,
    "burp_port": 8080,
    "mongodb": {
        "ip": "127.0.0.1",
        "port": 27017,
        "dbname": "facai",
        "username": "",
        "password": ""
    },
    "AI_model": {
        "model_name": "",
        "API": "",
        "API_KEY": ""
    }
}
```

### 配置项详解

| 配置项 | 类型 | 说明 | 默认值 |
|--------|------|------|--------|
| **flask_port** | int | Flask Web服务端口 | 5001 |
| **chrome_path** | string | Chrome浏览器可执行文件路径 | - |
| **burp_path** | string | Burp Suite工具路径 | - |
| **chrome_cdp_port** | int | Chrome CDP调试端口（监控） | 19227 |
| **chrome_spider_cdp_port** | int | Chrome CDP调试端口（爬虫） | 19228 |
| **mitmproxy_port** | int | mitmproxy代理端口 | 18081 |
| **burp_port** | int | Burp Suite代理端口 | 8080 |

### MongoDB 配置

| 配置项 | 类型 | 说明 | 默认值 |
|--------|------|------|--------|
| **mongodb.ip** | string | MongoDB服务器地址 | 127.0.0.1 |
| **mongodb.port** | int | MongoDB服务端口 | 27017 |
| **mongodb.dbname** | string | 数据库名称 | facai |
| **mongodb.username** | string | 用户名（可选） | - |
| **mongodb.password** | string | 密码（可选） | - |

### AI Model 配置

| 配置项 | 类型 | 说明 | 默认值 |
|--------|------|------|--------|
| **AI_model.model_name** | string | AI模型名称 | - |
| **AI_model.API** | string | AI API地址 | - |
| **AI_model.API_KEY** | string | API密钥 | - |

---

## 快速启动

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动 MongoDB

确保 MongoDB 服务已启动，默认连接 `127.0.0.1:27017`。

### 3. 配置文件

修改 `config.json` 中的配置项，特别是：
- `chrome_path`: Chrome浏览器路径
- `mongodb`: MongoDB连接配置

### 4. 启动项目

**Windows**:
```bash
start.bat
```

**或手动启动**:
```bash
python app.py
```

### 5. 访问系统

浏览器访问: `http://localhost:5001`

---

## 核心功能模块

### 1. 流量捕获

通过 mitmproxy 捕获 HTTP/HTTPS 流量，自动存入 `project_{name}_traffic` 表。

**启动命令**:
```bash
python mitmproxy_service.py
```

### 2. 爬虫系统

- **子域名发现**: 多种子域名枚举技术
- **HTML解析爬虫**: 静态HTML页面爬取
- **动态爬虫**: 基于Playwright的动态页面爬取
- **URL去重**: 基于请求标准化的智能去重

### 3. 漏洞扫描

支持多种漏洞类型检测：
- SQL注入
- XSS跨站脚本
- 命令执行（RCE）
- SSRF服务端请求伪造
- 信息泄露
- 异常检测

### 4. 资产管理

- 子域名管理
- 站点管理
- 端口服务管理
- IP/CIDR管理
- 高亮标记

### 5. AI Agent

基于 MCP 协议的 AI Agent，支持：
- 自然语言交互
- 自动化安全测试
- 漏洞分析

---

## 数据库表结构

### 核心表

| 表名 | 说明 |
|------|------|
| `project_config` | 项目配置表 |
| `project_{name}_traffic` | HTTP流量表 |
| `project_{name}_domain` | 子域名表 |
| `project_{name}_website` | 站点表 |
| `project_{name}_vuln` | 漏洞表 |
| `project_{name}_vuln_log` | 漏洞盲打日志表 |

详细表结构请参考: `docs/数据库结构.md`

---

## 开发指南

### 添加新的API接口

1. 在 `api/` 目录下创建新的 `*_api.py` 文件
2. 定义 Blueprint
3. 在 `app.py` 中注册 Blueprint

示例:
```python
# api/new_api.py
from flask import Blueprint, jsonify

new_api = Blueprint('new_api', __name__)

@new_api.route('/api/new/test', methods=['GET'])
def test():
    return jsonify({'success': True, 'message': 'Hello'})
```

```python
# app.py
from api.new_api import new_api
app.register_blueprint(new_api)
```

### 添加新的数据库表

1. 在 `database/` 目录下创建新的数据库类
2. 继承或使用 `MongoDBHandler`

示例:
```python
# database/new_database.py
from database.mongodb_handler import MongoDBHandler

class NewDatabase:
    def __init__(self, project_name):
        self.db_handler = MongoDBHandler()
        self.collection_name = f"project_{project_name}_new"
    
    def insert_data(self, data):
        return self.db_handler.insert_one(self.collection_name, data)
```

---

## 注意事项

1. **Chrome CDP 端口冲突**: 确保 `chrome_cdp_port` 和 `chrome_spider_cdp_port` 未被占用
2. **MongoDB 连接**: 首次启动需确保 MongoDB 服务已运行
3. **证书安装**: mitmproxy 首次使用需安装 CA 证书
4. **浏览器版本**: 建议使用 Chrome 90+ 版本
5. **Python 版本**: 推荐 Python 3.8+

---

## 相关文档

- [数据库结构说明](./数据库结构.md)
- [HTTP流量处理](./HTTP流量.md)
- [HTTP请求去重](./HTTP流量请求处理与去重.md)
- [漏洞扫描服务](./漏洞扫描服务.md)
- [资产监控](./资产监控.md)
- [前端开发指南](./前端开发.md)
