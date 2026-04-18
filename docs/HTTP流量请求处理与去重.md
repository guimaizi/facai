# HTTP流量请求处理与去重

## 概述

`service/spider/http_standardization.py` 模块用于对 `project_{name}_traffic` 表中的HTTP流量进行标准化处理，生成去重指纹，避免重复处理相同的接口请求。

### 核心原理

```
去重Key = MD5(请求方法 + 标准化URL + 参数特征)
```

**标准化流程**:
1. **路径参数化**: 将动态ID转为模板格式（`/user/123` → `/user/{Int-3}`）
2. **参数类型识别**: 识别参数值类型（Int、Float、Hash、URL、JSON等）
3. **特征提取**: 生成参数特征字符串
4. **指纹生成**: 计算MD5作为去重标识

---

## 使用方法

### 基础用法

```python
from service.spider.http_standardization import standardize_request

# 标准化单个请求
http_request = {
    'url': 'https://example.com/path/123?sada=21312',
    'method': 'GET',
    'body': '',
}

result = standardize_request(http_request)

# 返回结果
{
    'url': 'https://example.com/path/123?sada=21312',
    'method': 'GET',
    'body': '',
    'url_path': 'https://example.com/path/123',
    'url_generalization': 'https://example.com/path/{Int-3}?sada={Int-5}',
    'param_feature': 'sada={Int-5}',
    'file_extension': '',
    'key': 'e10adc3949ba59abbe56e057f20f883e'  # md5格式
}
```

### 去重实战

```python
from service.spider.http_standardization import standardize_request

# 场景：过滤重复请求
traffic_list = [...]  # 从数据库获取的HTTP流量
seen_keys = set()
unique_requests = []

for request in traffic_list:
    result = standardize_request(request)
    
    if result['key'] not in seen_keys:
        seen_keys.add(result['key'])
        unique_requests.append(request)

print(f"原始请求数: {len(traffic_list)}")
print(f"去重后数量: {len(unique_requests)}")
print(f"去重率: {(1 - len(unique_requests)/len(traffic_list))*100:.1f}%")
```

---

## 核心函数

### 1. standardize_request()

标准化HTTP请求，生成去重指纹。

**函数签名**:
```python
def standardize_request(http_request: dict, type_model: int = 1) -> dict
```

**参数**:
- `http_request` (dict): HTTP请求字典，包含 `url`、`method`、`body`
- `type_model` (int): 是否处理hash参数，`0`=不处理，`1`=处理（默认）

**返回值**:
```python
{
    'url': str,                      # 原始URL
    'method': str,                   # 请求方法
    'body': str/dict,                # 请求体
    'url_path': str,                 # 原始URL（不含查询参数）
    'url_generalization': str,       # 标准化URL（路径参数化 + URL查询参数 + Hash参数）
    'param_feature': str,            # 参数特征（包含所有参数：URL查询、Body、Hash）
    'file_extension': str,           # 文件扩展名
    'key': str                       # 去重key（md5格式）
}
```

**字段说明**:
- `url_path`: URL的路径部分，不含查询参数和hash（如 `https://example.com/path`）
- `url_generalization`: 标准化URL，包含路径参数化和URL查询参数、Hash参数，**不包含Body参数**
- `param_feature`: 所有参数的特征字符串（URL查询+Body+Hash），格式：`key={type-len}`
- `key`: 去重用的MD5值，格式：`md5(METHOD:url_generalization:param_feature)`

---

### 2. callback_pathname()

处理URL路径，将动态部分参数化。

**函数签名**:
```python
def callback_pathname(pathname: str) -> str
```

**示例**:
```
/admin/123/demo.jsp    → /admin/{Int-3}/demo.jsp
/admin/hello/world     → /admin/hello/world (保留英文单词)
/trpc.video.account/NewRefresh → /{String-18}/NewRefresh
```

**处理规则**:
- 纯数字 → `{Int-长度}`
- 浮点数 → `{Float-长度}`
- 英文单词（长度2-30，无连字符）→ 保留原值
- 其他字符串 → `{String-长度}`
- 文件扩展名 → 保留（长度≤7）

---

### 3. callback_request_param_list()

提取HTTP请求中的所有参数。

**函数签名**:
```python
def callback_request_param_list(http_request: dict, type_model: int = 0) -> list
```

**返回值**:
```python
[
    {
        'param_name': str,    # 参数名
        'value': any,         # 参数值
        'value_len': int,     # 参数长度（最大30）
        'value_type': str     # 参数类型
    },
    ...
]
```

**过滤规则**:
- 参数名长度大于30的参数将被过滤（避免文件上传等场景的误解析）
- 最多返回100个参数

---

### 4. _check_string_type()

判断HTTP请求参数值类型。

**函数签名**:
```python
def _check_string_type(text) -> str
```

**支持类型**:

| 类型 | 判断条件 | 示例 |
|-----|---------|------|
| Int | 纯整数（含负数） | `123`, `-456` |
| Float | 浮点数 | `3.14`, `-0.99` |
| Hash | 32/40/64位十六进制 | `a1b2c3...` (MD5/SHA) |
| URL_TYPE | 以http(s)://或//开头 | `https://example.com` |
| EN_URL | URL编码的URL（含`%XX`） | `https%3A%2F%2Fexample.com` |
| JSON | 以`{}`或`[]`包裹的有效JSON | `{"a":1}` |
| EN_JSON | URL编码的JSON | `%7B%22a%22%3A1%7D` |
| EN_Hash | URL编码的哈希值 | `a1b2c3...` (编码后) |
| EN_String | URL编码的字符串 | `%E4%B8%AD%E6%96%87` |
| String | 其他所有情况 | 任意文本 |

**URL编码处理**:
- 自动检测并解码URL编码参数
- 解码后重新判断类型
- 保留编码标识（如 `EN_URL`, `EN_JSON`）

---

## 参数来源处理

### URL查询参数
```
?id=123&type=user → id={Int-3}&type={String-4}
```

### Hash参数（type_model=1时处理）
```
#/page?url=https://... → #/{String-4}?url={URL_TYPE-20}
```

处理规则：
- Hash路径参数化：`#/dasdsa/2131` → `#/{String-6}/{Int-3}`
- Hash查询参数处理：`#/aaa/?das=1` → `#/aaa/?das={Int-1}`
- Hash参数与主URL参数分开处理，互不影响

### POST Body - JSON格式
```python
body = {'a': 1, 'b': 2, 'c': {'d': 3}}
→ a={Int-1}&b={Int-1}&c.d={Int-1}
```

**嵌套JSON处理**:
- 支持最多3层深度解析
- 使用点号标记嵌套路径（如 `user.profile.name`）
- 数组使用索引标记（如 `items[0]`, `items[1]`）

### POST Body - Form格式
```
aaa=dasdsa&dadada=1&url=https://example.com/
→ aaa={String-6}&dadada={Int-1}&url={URL_TYPE-20}
```

---

## 特殊场景处理

### JS文件特殊处理

如果文件扩展名为 `.js`，则：
- 剔除参数查询，只保留 `?` 前部分
- `url_generalization` 不进行路径参数化处理
- `param_feature` 为空

**示例**:
```
原始URL: https://example.com/static/app.abc123.js?v=1.0
url_path: https://example.com/static/app.abc123.js
url_generalization: https://example.com/static/app.abc123.js
param_feature: 
file_extension: .js
key: md5(GET:https://example.com/static/app.abc123.js:)
```

### 文件扩展名提取

提取URL路径中的文件扩展名，如 `/static/123.html` → `.html`

支持扩展名长度：≤7（包括点号）

---

## 测试示例

### 1. GET请求 - 无参数
```
原始URL: https://example.com/path
Method: GET
Body: 
url_path: https://example.com/path
url_generalization: https://example.com/path
param_feature: 
file_extension: 
key: md5(GET:https://example.com/path:)
```

### 2. GET请求 - URL参数
```
原始URL: https://example.com/path?sada=21312
Method: GET
Body: 
url_path: https://example.com/path
url_generalization: https://example.com/path?sada={Int-5}
param_feature: sada={Int-5}
file_extension: 
key: md5(GET:https://example.com/path?sada={Int-5}:sada={Int-5})
```

### 3. GET请求 - 路径参数 + URL参数
```
原始URL: https://example.com/path/123?sada=21312
Method: GET
Body: 
url_path: https://example.com/path/123
url_generalization: https://example.com/path/{Int-3}?sada={Int-5}
param_feature: sada={Int-5}
file_extension: 
key: md5(GET:https://example.com/path/{Int-3}?sada={Int-5}:sada={Int-5})
```

### 4. GET请求 - 保留英文单词
```
原始URL: https://example.com/admin/hello/demo
Method: GET
Body: 
url_path: https://example.com/admin/hello/demo
url_generalization: https://example.com/admin/hello/demo
param_feature: 
file_extension: 
key: md5(GET:https://example.com/admin/hello/demo:)
```

### 5. GET请求 - 路径数字 + 扩展名
```
原始URL: https://example.com/static/12321321.html
Method: GET
Body: 
url_path: https://example.com/static/12321321.html
url_generalization: https://example.com/static/{Int-8}.html
param_feature: 
file_extension: .html
key: md5(GET:https://example.com/static/{Int-8}.html:)
```

### 6. POST请求 - JSON Body
```
原始URL: https://example.com/path?v=21312
Method: POST
Body: {'a': 1, 'b': 2, 'c': {'d': 3}}
url_path: https://example.com/path
url_generalization: https://example.com/path?v={Int-5}
param_feature: a={Int-1}&b={Int-1}&c.d={Int-1}&v={Int-5}
file_extension: 
key: md5(POST:https://example.com/path?v={Int-5}:a={Int-1}&b={Int-1}&c.d={Int-1}&v={Int-5})
```

### 7. POST请求 - Form Body
```
原始URL: https://example.com/path?a=21312
Method: POST
Body: aaa=dasdsa&dadada=1&url=https://example.com/
url_path: https://example.com/path
url_generalization: https://example.com/path?a={Int-5}
param_feature: a={Int-5}&aaa={String-6}&dadada={Int-1}&url={URL_TYPE-20}
file_extension: 
key: md5(POST:https://example.com/path?a={Int-5}:a={Int-5}&aaa={String-6}&dadada={Int-1}&url={URL_TYPE-20})
```

### 8. POST请求 - JSON Body (URL参数与Body参数同名)
```
原始URL: https://example.com/path?a=21312
Method: POST
Body: {'a': 1, 'b': 2, 'c': {'d': 'asadada', 'url': 'http://www.qq.axc'}, 'int1': 1}
url_path: https://example.com/path
url_generalization: https://example.com/path?a={Int-5}
param_feature: a={Int-1}&a={Int-5}&b={Int-1}&c.d={String-7}&c.url={URL_TYPE-17}&int1={Int-1}
file_extension: 
key: md5(...)
```

### 9. PUT请求 - Form Body
```
原始URL: https://example.com/path/dasda?a=21312
Method: PUT
Body: aaa=dasdsa&dadada=12131
url_path: https://example.com/path/dasda
url_generalization: https://example.com/path/{String-5}?a={Int-5}
param_feature: a={Int-5}&aaa={String-6}&dadada={Int-5}
file_extension: 
key: md5(...)
```

### 10. GET请求 - JS文件
```
原始URL: https://example.com/static/app.abc123.js?v=1.0
Method: GET
Body: 
url_path: https://example.com/static/app.abc123.js
url_generalization: https://example.com/static/app.abc123.js
param_feature: 
file_extension: .js
key: md5(GET:https://example.com/static/app.abc123.js:)
```

### 11. GET请求 - Hash参数处理
```
原始URL: https://example.com/static/12321321.html?#/dasdsa/2131?21321a=232
Method: GET
Body: 
url_path: https://example.com/static/12321321.html
url_generalization: https://example.com/static/{Int-8}.html?#/{String-6}/{Int-3}?21321a={Int-3}
param_feature: 21321a={Int-3}
file_extension: .html
key: md5(...)
```

### 12. GET请求 - 主URL参数 + Hash参数
```
原始URL: https://example.com/path/a?sada=21312#/aaa/?das=1
Method: GET
Body: 
url_path: https://example.com/path/a
url_generalization: https://example.com/path/{String-1}?sada={Int-5}#/aaa/?das={Int-1}
param_feature: das={Int-1}&sada={Int-5}
file_extension: 
key: md5(...)
```

---

## 去重效果分析

### 相同接口的不同ID

```
原始请求:
  GET /user/1/profile
  GET /user/2/profile
  GET /user/100/profile

标准化后:
  GET /user/{Int-1}/profile
  GET /user/{Int-1}/profile
  GET /user/{Int-3}/profile

去重结果: 识别为3个不同的请求 (长度不同)
```

### 不同参数值的相同接口

```
原始请求:
  GET /api/search?keyword=apple&page=1
  GET /api/search?keyword=banana&page=2
  GET /api/search?keyword=orange&page=3

标准化后:
  GET /api/search?keyword=String-5&page=Int-1
  GET /api/search?keyword=String-6&page=Int-1
  GET /api/search?keyword=String-6&page=Int-1

去重结果: 识别为2个不同的请求
  (banana和orange长度相同，被归为一类)
```

### POST请求的JSON Body

```
原始请求:
  POST /api/update (body: {"id":1,"name":"Alice"})
  POST /api/update (body: {"id":2,"name":"Bob"})
  POST /api/update (body: {"id":3,"name":"Charlie"})

标准化后:
  param_feature: "id=Int-1&name=String-5"
  param_feature: "id=Int-1&name=String-3"
  param_feature: "id=Int-1&name=String-7"

去重结果: 识别为3个不同的请求
```

---

## 方案优缺点

### 优点

✅ **结构相似性识别**: 能识别相同接口的不同参数实例  
✅ **类型覆盖全面**: 支持Int、Float、Hash、URL、JSON等10种类型  
✅ **嵌套JSON支持**: 可解析最多3层深度的JSON结构  
✅ **URL编码识别**: 自动解码并标记编码类型  
✅ **JS文件特殊处理**: 避免对JS资源文件过度参数化  
✅ **英文单词保留**: 有意义的路径段保持原样

### 局限性

⚠️ **版本号识别不足**: `/api/v1/users` 和 `/api/v2/users` 可能被归为一类  
⚠️ **参数顺序丢失**: 无法识别参数顺序敏感的API签名场景  
⚠️ **单词词典依赖**: 业务术语（如upload、signin）可能被错误参数化  
⚠️ **过度去重风险**: 日期、UUID等特殊格式可能被过度归一化  
⚠️ **请求头缺失**: 无法区分基于Accept头的不同响应格式请求

---

## 集成到爬虫系统

### 在流量收集时去重

```python
# service/spider/http.py
from service.spider.http_standardization import standardize_request

class HTTPCollector:
    def collect_and_save(self, http_requests):
        seen_keys = set()
        unique_count = 0
        
        for request in http_requests:
            result = standardize_request(request)
            
            # 去重检查
            if result['key'] not in seen_keys:
                seen_keys.add(result['key'])
                self.save_to_database(request, result)
                unique_count += 1
        
        return {
            'success': True,
            'total': len(http_requests),
            'unique': unique_count,
            'message': f'保存{unique_count}个唯一请求（过滤{len(http_requests)-unique_count}个重复）'
        }
```

### 在爬虫核心流程中调用

```python
# service/spider/core.py
from service.spider.http_standardization import standardize_request

class SpiderCore:
    def fetch_unprocessed_traffic(self, limit=200):
        # ... 获取流量数据 ...
        
        # 去重处理
        seen_keys = set()
        unique_http = []
        
        for traffic in traffic_list:
            result = standardize_request(traffic)
            if result['key'] not in seen_keys:
                seen_keys.add(result['key'])
                unique_http.append(traffic)
        
        # 返回去重后的数据
        return {
            'success': True,
            'count': len(unique_http),
            'http_requests': unique_http,
            'message': f'获取{len(unique_http)}个唯一请求'
        }
```

---

## 测试验证

### 单元测试

```bash
# 运行测试
python test_http_standardization.py
```

### 测试覆盖场景

| 场景 | 测试用例 | 预期结果 |
|-----|---------|---------|
| GET无参数 | `/path` | key生成正确 |
| GET带参数 | `/path?id=123` | 参数正确标准化 |
| POST JSON | body为字典 | 嵌套解析正确 |
| POST Form | body为字符串 | 参数提取正确 |
| JS文件 | `/app.js?v=1` | 不处理查询参数 |
| Hash参数 | `#/page?id=1` | hash解析正确 |
| URL编码 | `%E4%B8%AD%E6%96%87` | 解码并标记 |

### 性能测试

```python
import time
from service.spider.http_standardization import standardize_request

# 生成测试数据
test_requests = [
    {'url': f'https://example.com/api/user/{i}', 'method': 'GET', 'body': ''}
    for i in range(10000)
]

# 性能测试
start = time.time()
for req in test_requests:
    standardize_request(req)
elapsed = time.time() - start

print(f"处理{len(test_requests)}个请求耗时: {elapsed:.2f}秒")
print(f"平均速度: {len(test_requests)/elapsed:.0f}请求/秒")
```

---

## 总结

本模块通过**路径参数化**和**参数特征提取**实现了中等粒度的HTTP请求去重，适用于：

✅ **快速探索阶段**: 识别站点接口结构  
✅ **流量归档场景**: 减少存储空间占用  
✅ **统计分析场景**: 统计接口调用频率

对于需要**精确测试**的场景，建议结合使用多层去重策略，或保留原始URL作为兜底方案。
