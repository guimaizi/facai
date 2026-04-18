# HTTP流量

## 概述

`api/import_traffic_api.py` 模块提供了将URL、子域名、HTTP请求导入到 `project_{name}_traffic` 表的API接口，支持Python代码调用和HTTP API调用两种方式。

---

## Traffic 导入 API

### ImportTrafficAPI 类

提供三个核心方法用于导入流量数据。

**文件**: `api/import_traffic_api.py`

#### 方法列表

| 方法 | 参数 | 返回值 | 功能 |
|------|------|--------|------|
| `import_traffic_url` | `url`, `project_name` | dict | 导入URL |
| `import_traffic_subdomain` | `subdomain`, `project_name` | dict | 导入子域名 |
| `import_traffic_request` | `list_request`, `project_name` | dict | 导入HTTP请求列表 |

---

### 1. import_traffic_url()

导入单个URL，自动转换为HTTP请求格式并存入数据库。

**函数签名**:
```python
def import_traffic_url(self, url, project_name=None)
```

**参数**:
- `url` (str): URL地址，如 `"https://www.molun.com/"`
- `project_name` (str, 可选): 指定项目名称，默认使用当前运行项目

**返回值**:
```python
{'success': bool, 'message': str}
```

**处理流程**:
1. URL格式检测 (`check_is_url`)
2. URL标准化 (`callback_url`)
3. 转换为HTTP请求 (`create_request`)
4. URL范围检测 (`check_traffic_url`)
5. 插入数据库

**示例**:
```python
from api.import_traffic_api import ImportTrafficAPI

api = ImportTrafficAPI()
result = api.import_traffic_url("https://www.molun.com/")
# result: {'success': True, 'message': 'URL导入成功'}
```

---

### 2. import_traffic_subdomain()

导入子域名，自动转换为URL和HTTP请求格式。

**函数签名**:
```python
def import_traffic_subdomain(self, subdomain, project_name=None)
```

**参数**:
- `subdomain` (str): 子域名，如 `"www.molun.com"`
- `project_name` (str, 可选): 指定项目名称，默认使用当前运行项目

**返回值**:
```python
{'success': bool, 'message': str}
```

**处理流程**:
1. 子域名格式检测 (`check_domain`)
2. 读取项目配置（scheme、port）
3. 子域名转URL：
   - `http://subdomain/` (默认)
   - `https://subdomain/` (scheme=https)
   - `http://subdomain:8080/` (port非标准)
4. 转换为HTTP请求
5. URL范围检测 (`check_traffic_url`)
6. 插入数据库

**示例**:
```python
from api.import_traffic_api import ImportTrafficAPI

api = ImportTrafficAPI()
result = api.import_traffic_subdomain("www.molun.com")
# result: {'success': True, 'message': '子域名导入成功'}
```

---

### 3. import_traffic_request()

批量导入HTTP请求列表。

**函数签名**:
```python
def import_traffic_request(self, list_request, project_name=None)
```

**参数**:
- `list_request` (list): HTTP请求列表，每个元素为字典
- `project_name` (str, 可选): 指定项目名称，默认使用当前运行项目

**返回值**:
```python
{
    'success': bool,
    'message': str,
    'total': int,        # 总数
    'imported': int,     # 成功导入数
    'skipped': int,      # 跳过数
    'errors': list       # 错误列表
}
```

**处理逻辑**:
- 自动识别URL或子域名（根据是否包含 `http://` 或 `https://`）
- URL类型：直接使用提供的请求数据
- 子域名类型：转换为URL后生成请求数据
- 每条记录插入前进行 `check_traffic_url` 检测

**示例**:
```python
from api.import_traffic_api import ImportTrafficAPI

api = ImportTrafficAPI()

# 导入URL请求
requests = [
    {
        'url': 'https://api.example.com/users',
        'method': 'GET',
        'headers': {'User-Agent': 'Mozilla/5.0'},
        'body': ''
    },
    {
        'url': 'https://api.example.com/login',
        'method': 'POST',
        'headers': {'Content-Type': 'application/json'},
        'body': '{"username":"admin","password":"123456"}'
    }
]

result = api.import_traffic_request(requests)
# result: {'success': True, 'message': '导入完成', 'total': 2, 'imported': 2, 'skipped': 0, 'errors': []}
```

---

## HTTP 请求数据格式

### 数据库字段

```json
{
  "url": "https://a.lunlun.com/auth/getAuthCodeInfoByCode",
  "headers": {
    "accept": "application/json, text/plain, */*",
    "content-type": "application/x-www-form-urlencoded",
    "user-agent": "Mozilla/5.0...",
    "cookie": "auth_sid=20000"
  },
  "method": "POST",
  "body": "code=1&client_id=65407",
  "time": "2025-11-14 17:20:26",
  "website": "http://a.lunlun.com/",
  "status": 0,
  "scaner_status": 0,
  "source": 0
}
```

### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| url | string | ✅ | 完整的请求URL |
| method | string | ✅ | 请求方法（GET/POST/PUT/DELETE等） |
| headers | dict | ❌ | HTTP请求头，默认为空字典 |
| body | string/dict | ❌ | 请求体内容，默认为空字符串 |
| time | string | ❌ | 请求时间，格式：YYYY-MM-DD HH:MM:SS，自动生成 |
| website | string | ❌ | 来源网站，自动从URL提取 |
| status | int | ❌ | 处理状态：0=未处理，1=已处理，默认为0 |
| scaner_status | int | ❌ | 扫描状态：0=未扫描，1=已扫描，默认为0 |
| source | int | ❌ | 来源类型：0=流量捕捉，1=URL生成，默认为0 |

---

## Web API 路由

提供三个HTTP接口供前端调用。

### 1. 导入URL

```
POST /api/import/url
Content-Type: application/json

Request Body:
{
  "url": "https://www.molun.com/"
}

Response:
{
  "success": true,
  "message": "URL导入成功"
}
```

### 2. 导入子域名

```
POST /api/import/subdomain
Content-Type: application/json

Request Body:
{
  "subdomain": "www.molun.com"
}

Response:
{
  "success": true,
  "message": "子域名导入成功"
}
```

### 3. 导入HTTP请求

```
POST /api/import/request
Content-Type: application/json

Request Body:
[
  {
    "url": "https://api.example.com/users",
    "method": "GET",
    "headers": {"User-Agent": "Mozilla/5.0"},
    "body": ""
  },
  {
    "url": "https://api.example.com/login",
    "method": "POST",
    "headers": {"Content-Type": "application/json"},
    "body": "{\"username\":\"admin\"}"
  }
]

Response:
{
  "success": true,
  "message": "导入完成",
  "total": 2,
  "imported": 2,
  "skipped": 0,
  "errors": []
}
```

---

## 导入流程

### 流程图

```
URL导入:
  URL → check_is_url → callback_url → create_request → check_traffic_url → 数据库

子域名导入:
  子域名 → check_domain → 读取项目配置 → 转URL → create_request → check_traffic_url → 数据库

HTTP请求导入:
  请求列表 → 遍历 → 识别URL/子域名 → 构建请求数据 → check_traffic_url → 数据库
```

### 重要规则

1. ✅ URL和子域名生成的HTTP请求，`source` 设置为 `1`
2. ✅ 最终必须以HTTP请求格式写入数据库
3. ✅ 写入到 `project_{name}_traffic` 表
4. ✅ `status` 设置为 `0`（未处理）
5. ✅ `scaner_status` 设置为 `0`（未扫描）
6. ✅ 在导入数据库的最后一步使用 `check_traffic_url` 函数进行URL有效性检查
7. ✅ 其他步骤不需要检测

---

## 使用示例

### Python 调用示例

#### 方式1：实例化调用

```python
from api.import_traffic_api import ImportTrafficAPI

# 创建实例
api = ImportTrafficAPI()

# 导入URL
result1 = api.import_traffic_url("https://www.molun.com/")
print(result1)

# 导入子域名
result2 = api.import_traffic_subdomain("www.molun.com")
print(result2)

# 导入HTTP请求列表
requests = [
    {
        'url': 'https://api.example.com/users',
        'method': 'GET',
        'headers': {'User-Agent': 'Mozilla/5.0'},
        'body': ''
    }
]
result3 = api.import_traffic_request(requests)
print(result3)
```

#### 方式2：单例模式调用（推荐）

```python
from api.import_traffic_api import get_import_api

# 获取单例实例
api = get_import_api()

# 导入URL
result = api.import_traffic_url("https://www.molun.com/")
```

#### 方式3：指定项目名称

```python
from api.import_traffic_api import ImportTrafficAPI

api = ImportTrafficAPI()

# 指定项目名称导入
result = api.import_traffic_url(
    url="https://www.molun.com/",
    project_name="Tencent"
)
```

---

### HTTP 调用示例

#### 使用 curl

```bash
# 导入URL
curl -X POST http://localhost:5000/api/import/url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.molun.com/"}'

# 导入子域名
curl -X POST http://localhost:5000/api/import/subdomain \
  -H "Content-Type: application/json" \
  -d '{"subdomain": "www.molun.com"}'

# 导入HTTP请求
curl -X POST http://localhost:5000/api/import/request \
  -H "Content-Type: application/json" \
  -d '[{"url": "https://api.example.com/test", "method": "GET"}]'
```

#### 使用 requests 库

```python
import requests

# 导入URL
response = requests.post(
    'http://localhost:5000/api/import/url',
    json={'url': 'https://www.molun.com/'}
)
print(response.json())

# 导入HTTP请求
response = requests.post(
    'http://localhost:5000/api/import/request',
    json=[
        {
            'url': 'https://api.example.com/users',
            'method': 'GET',
            'headers': {'User-Agent': 'Mozilla/5.0'}
        }
    ]
)
print(response.json())
```

---

## HTTP流量前端显示

### 数据库连接
- 连接到 `project_{name}_traffic` 表
- `name` 为当前运行的项目名称

### 前端显示列

| 列名 | 说明 |
|------|------|
| 时间 | 请求时间 |
| 方法 | HTTP方法（GET/POST等） |
| URL | 请求URL（超长自动省略） |
| Website | 来源网站 |
| 状态 | 处理状态 |
| 扫描状态 | 漏洞扫描状态 |
| 操作 | 详情、重放、删除按钮 |

### 状态显示

**status 字段**:
- `0`: 未处理
- `1`: 已处理

**scaner_status 字段**:
- `0`: 未扫描（黄色显示）
- `1`: 已扫描（绿色显示）

**source 字段**:
- `0`: 流量捕捉
- `1`: URL生成

### 操作功能

- **查看详情**: 
  - JSON模式：以JSON格式展示完整请求
  - Burp模式：以Burp请求包格式展示
- **重放请求**: 跳转到HTTP请求重放工具
- **删除**: 删除单条流量数据

### 功能按钮

- **刷新**: 刷新当前列表
- **清空**: 清空所有流量数据
- **搜索**: 按URL搜索
- **排序**: 支持时间、方法、URL、Website列排序
- **翻页**: 使用 `pageup.js` 标准分页组件

---

## 与其他模块的集成

### 1. 爬虫模块调用

```python
# service/spider/subdomain.py
from api.import_traffic_api import ImportTrafficAPI

class SubdomainScanner:
    def __init__(self):
        self.import_traffic_api = ImportTrafficAPI()
    
    def save_found_subdomain(self, subdomain):
        result = self.import_traffic_api.import_traffic_subdomain(
            subdomain, 
            self.project_name
        )
        return result['success']
```

### 2. 动态爬虫调用

```python
# service/spider/dynamic_crawler.py
from api.import_traffic_api import ImportTrafficAPI

class DynamicCrawler:
    def __init__(self):
        self.import_traffic = ImportTrafficAPI()
    
    def save_crawled_url(self, url):
        result = self.import_traffic.import_traffic_url(
            url, 
            self.project_name
        )
        return result['success']
```

### 3. 静态爬虫调用

```python
# service/spider/html.py
from api.import_traffic_api import ImportTrafficAPI

class HTMLParser:
    def save_requests(self, request_list):
        importer = ImportTrafficAPI()
        result = importer.import_traffic_request(
            request_list, 
            self.project_name
        )
        return result
```

---

## 注意事项

### 1. URL范围检测

所有导入操作在最后一步都会调用 `check_traffic_url` 进行URL有效性检查：
- 检查URL是否在项目配置的域名范围内
- 如果不在范围内，该请求将被跳过

### 2. 数据去重

导入API本身不做去重，如果需要去重，请使用：
- `service/spider/http_standardization.py` 模块
- 调用 `standardize_request()` 生成去重key

### 3. 单例模式

推荐使用 `get_import_api()` 获取单例实例，避免重复连接数据库：
```python
# 推荐
from api.import_traffic_api import get_import_api
api = get_import_api()

# 不推荐（每次都创建新实例）
from api.import_traffic_api import ImportTrafficAPI
api = ImportTrafficAPI()
```

### 4. 错误处理

所有方法都有完善的错误处理机制：
- 返回值中包含 `success` 字段标识是否成功
- 失败时返回详细的错误信息 `message`
- 批量导入时会统计跳过数和错误列表

---

## 总结

Traffic导入API是系统中HTTP流量的入口点，提供了灵活的导入方式：

✅ **多种导入方式**: URL、子域名、HTTP请求  
✅ **双重调用接口**: Python API 和 HTTP API  
✅ **自动数据转换**: URL/域名自动转为标准HTTP请求格式  
✅ **完善的状态管理**: status、scaner_status 字段支持后续处理流程  
✅ **灵活的项目指定**: 支持默认项目和指定项目  
✅ **完善的错误处理**: 详细的返回信息和错误统计

通过该API，爬虫模块、漏洞扫描模块等可以方便地将发现的URL和请求导入到流量表中进行统一管理。
