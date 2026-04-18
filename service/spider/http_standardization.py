# HTTP请求标准化/去重模块
# 参考 112312.py 的 class_request_param 实现

import re,urllib.parse,json,os
from urllib.parse import urlparse, urlunparse, parse_qsl
from nltk.corpus import words
from service.Class_Core_Function import Class_Core_Function

# 初始化核心函数类
_core_func = Class_Core_Function()


# 英文单词集合
_word_list = set(words.words()) if hasattr(words, 'words') else set()


def _check_string_type(text):
    """
    判断HTTP请求参数值类型
    支持: Int, Float, Hash, URL_TYPE, EN_URL, JSON, EN_JSON, EN_String, String
    """
    if text is None:
        return 'String'

    # 转为字符串并去除两端空白
    text_str = str(text).strip()
    if not text_str:
        return 'String'

    # 1. 判断是否为纯整数 (兼容负数)
    if text_str.isdigit() or (text_str.startswith('-') and text_str[1:].isdigit()):
        return 'Int'

    # 2. 判断是否为浮点数 (如 3.14, -0.99)
    try:
        float(text_str)
        return 'Float'
    except ValueError:
        pass

    # 3. 判断是否为哈希值 (MD5: 32位, SHA1: 40位, SHA256: 64位)
    # 使用正则匹配纯十六进制字符，比 all() 遍历更高效严谨
    if len(text_str) in [32, 40, 64] and re.match(r'^[0-9a-fA-F]+$', text_str):
        return 'Hash'

    # 4. URL解码逻辑判断 (正如你提到的核心思路)
    is_url_encoded = False
    decoded_text = text_str

    # 只有当包含 % 且后面跟着两位十六进制字符时，才认为可能是URL编码
    if '%' in text_str and re.search(r'%[0-9a-fA-F]{2}', text_str):
        try:
            unquoted = urllib.parse.unquote(text_str)
            # 如果解码后的字符串与原字符串不同，说明确实被编码过
            if unquoted != text_str:
                is_url_encoded = True
                decoded_text = unquoted
        except Exception:
            pass

    # 5. 对【解码后的真实文本】进行特征判断

    # 判断是否为 URL (兼容 http://, https://, //)
    if decoded_text.startswith(('http://', 'https://', '//')):
        return 'EN_URL' if is_url_encoded else 'URL_TYPE'

    # 判断是否为 JSON (HTTP接口中经常把 JSON 字符串作为参数传递)
    if (decoded_text.startswith('{') and decoded_text.endswith('}')) or \
       (decoded_text.startswith('[') and decoded_text.endswith(']')):
        try:
            json.loads(decoded_text)
            return 'EN_JSON' if is_url_encoded else 'JSON'
        except json.JSONDecodeError:
            pass

    # 6. 如果是被编码过的其他文本，区分一下
    if is_url_encoded:
        # 有些特殊的场景下，Hash也会被莫名其妙 encode
        if len(decoded_text) in [32, 40, 64] and re.match(r'^[0-9a-fA-F]+$', decoded_text):
            return 'EN_Hash'
        return 'EN_String'

    # 7. 兜底返回普通字符串
    return 'String'


def _callback_length(text, max_length=30):
    """获取文本长度，最大30"""
    if text is None:
        return 0
    return min(len(str(text) if not isinstance(text, str) else text), max_length)


def callback_pathname(pathname: str) -> str:
    """
    处理路径
    /admin/123/demo.jsp → /admin/{Int-3}/demo.jsp
    /admin/hello/world → /admin/hello/world (保留英文单词)
    /trpc.video.account/NewRefresh → /{String-18}/NewRefresh
    """
    # 使用 os.path.splitext 判断文件扩展名（与 Class_Core_Function.callback_file_extensions 一致）
    type_file = ''
    path_without_ext = pathname
    
    # 提取文件扩展名
    ext = os.path.splitext(pathname)[1]
    if ext and len(ext) <= 7:  # 包括点号，最长如 .suffix (6+1=7)
        type_file = ext.lower()
        path_without_ext = pathname[:-len(ext)]
    
    # 分割路径为各个段
    list_path = []
    for line in path_without_ext.split('/'):
        if line == '':
            continue
        text_type = _check_string_type(line)
        # 保留有意义的英文单词
        if text_type != 'Int' and len(line) > 2 and len(line) < 30 and '-' not in line and line.lower() in _word_list:
            list_path.append(line)
        else:
            length = _callback_length(line)
            list_path.append(f'{{{text_type}-{length}}}')

    path = '/'.join(list_path)
    if type_file:
        path = path + type_file
    return path


def callback_request_param_list(http_request: dict, type_model: int = 0) -> list:
    """
    返回http请求参数列表
    
    过滤规则:
        - 参数名长度大于30的参数将被过滤（避免文件上传等场景的误解析）
        - 最多返回100个参数
    """
    list_param = []
    try:
        urlparse_url = urlparse(http_request.get('url', ''))
        
        # 处理URL查询参数
        for line, key in dict(parse_qsl(urlparse_url.query)).items():
            # 过滤参数名长度大于30的参数
            if len(line) <= 30:
                list_param.append({
                    "param_name": line,
                    "value": key,
                    "value_len": _callback_length(key),
                    "value_type": _check_string_type(key)
                })
        
        # 处理hash参数
        if type_model == 1 and urlparse_url.fragment:
            # 正确解析hash中的查询参数
            fragment = urlparse_url.fragment
            if '?' in fragment:
                _, hash_query = fragment.split('?', 1)
                for line, key in dict(parse_qsl(hash_query)).items():
                    # 过滤参数名长度大于30的参数
                    if len(line) <= 30:
                        list_param.append({
                            "param_name": line,
                            "value": key,
                            "value_len": _callback_length(key),
                            "value_type": _check_string_type(key)
                        })
        
        # 处理body参数（非GET请求）
        method = http_request.get('method', 'GET').upper()
        if method != 'GET':
            body = http_request.get('body', '')
            if isinstance(body, dict):
                # JSON body（已经是dict类型）
                list_param.extend(_process_json_param(body))
            elif isinstance(body, str) and body:
                # 判断是否为JSON字符串
                if (body.startswith('{') and body.endswith('}')) or \
                   (body.startswith('[') and body.endswith(']')):
                    try:
                        json_body = json.loads(body)
                        list_param.extend(_process_json_param(json_body))
                    except json.JSONDecodeError:
                        # JSON解析失败，当作普通form body处理
                        if not body.startswith('------') and not body.startswith('<'):
                            for line, key in dict(parse_qsl(body)).items():
                                # 过滤参数名长度大于30的参数
                                if len(line) <= 30:
                                    list_param.append({
                                        "param_name": line,
                                        "value": key,
                                        "value_len": _callback_length(key),
                                        "value_type": _check_string_type(key)
                                    })
                elif not body.startswith('------') and not body.startswith('<'):
                    # 普通form body
                    for line, key in dict(parse_qsl(body)).items():
                        # 过滤参数名长度大于30的参数
                        if len(line) <= 30:
                            list_param.append({
                                "param_name": line,
                                "value": key,
                                "value_len": _callback_length(key),
                                "value_type": _check_string_type(key)
                            })
        
        # 再次过滤：确保所有参数名长度不超过30（包括JSON嵌套参数）
        list_param = [p for p in list_param if len(p['param_name']) <= 30]
        
        return list_param[:100]  # 限制参数数量
    except Exception:
        return []


def _process_json_param(data, prefix='', depth=1, max_depth=3):
    """
    处理JSON参数
    
    过滤规则:
        - 参数名长度大于30的参数将被过滤
    """
    result = []
    if isinstance(data, dict):
        for k, v in data.items():
            new_prefix = f"{prefix}.{k}" if prefix else k
            # 过滤参数名长度大于30的参数
            if len(new_prefix) > 30:
                continue
            if isinstance(v, (dict, list)) and depth < max_depth:
                result.extend(_process_json_param(v, new_prefix, depth + 1))
            else:
                result.append({
                    "param_name": new_prefix,
                    "value": v,
                    "value_len": _callback_length(v),
                    "value_type": _check_string_type(v)
                })
    elif isinstance(data, list):
        for i, item in enumerate(data):
            new_prefix = f"{prefix}[{i}]"
            # 过滤参数名长度大于30的参数
            if len(new_prefix) > 30:
                continue
            if isinstance(item, (dict, list)) and depth < max_depth:
                result.extend(_process_json_param(item, new_prefix, depth + 1))
            else:
                result.append({
                    "param_name": new_prefix,
                    "value": item,
                    "value_len": _callback_length(item),
                    "value_type": _check_string_type(item)
                })
    return result


def _get_json_keys(data, prefix='', depth=1, max_depth=3):
    """获取JSON中的所有键名"""
    keys = []
    if isinstance(data, dict):
        for k, v in data.items():
            new_prefix = f"{prefix}.{k}" if prefix else k
            if isinstance(v, (dict, list)) and depth < max_depth:
                keys.extend(_get_json_keys(v, new_prefix, depth + 1))
            else:
                keys.append(new_prefix)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            new_prefix = f"{prefix}[{i}]"
            if isinstance(item, (dict, list)) and depth < max_depth:
                keys.extend(_get_json_keys(item, new_prefix, depth + 1))
            else:
                keys.append(new_prefix)
    return keys


def standardize_request(http_request: dict, type_model: int = 1) -> dict:
    """
    标准化HTTP请求，生成去重指纹

    Args:
        http_request: HTTP请求字典 {'url': str, 'method': str, 'body': str/dict}
        type_model: 是否处理hash参数，0=不处理hash，1=处理hash

    Returns:
        dict: {
            'url': str,  # 原始URL
            'method': str,  # 请求方法
            'body': str/dict,  # 请求体
            'url_path': str,  # 原始URL（不含查询参数），如 https://example.com/path
            'url_generalization': str,  # 标准化路径+参数
            'param_feature': str,  # 参数特征
            'file_extension': str,  # 文件扩展名
            'key': str  # 去重key（md5格式）
        }
    """
    try:
        url = http_request.get('url', '')
        method = http_request.get('method', 'GET').upper()
        body = http_request.get('body', '')

        url_parse = urlparse(url)

        # 原始URL（不含查询参数），如 https://example.com/path
        url_path = _core_func.callback_split_url(url, 3)

        # 获取文件扩展名
        file_extension = _core_func.callback_file_extensions(url)

        # 判断是否为.js文件，如果是则不进行路径参数化处理，也不处理查询参数
        if file_extension == '.js':
            # JS文件：直接返回原始URL（不含查询参数）
            url_generalization = url_path
            param_feature_str = ''
            key = _core_func.md5_convert(f"{method}:{url_path}")

            return {
                'url': url_path,
                'method': method,
                'body': body,
                'url_path': url_path,
                'url_generalization': url_generalization,
                'param_feature': param_feature_str,
                'file_extension': file_extension,
                'key': key
            }

        # 非JS文件：正常进行路径参数化处理
        # 标准化路径
        if url_parse.path:
            path_generalization = callback_pathname(url_parse.path)
        else:
            path_generalization = ''

        # 提取参数特征（用于 param_feature，包含所有参数）
        list_param = callback_request_param_list(http_request, type_model)

        # url_generalization 只包含 URL 查询参数（直接从 URL 查询字符串提取）
        param_std_list = []
        if url_parse.query:
            for line, key in dict(parse_qsl(url_parse.query)).items():
                param_std_list.append(f"{line}={_check_string_type(key)}-{_callback_length(key)}")
        param_std_list.sort()
        param_std_str = '&'.join(param_std_list)

        # 构建标准化URL
        url_generalization = urlunparse(url_parse._replace(
            query='',
            params='',
            fragment='',
            path=path_generalization
        ))

        # 添加主URL查询参数
        if param_std_str:
            url_generalization += '?' + param_std_str

        # 处理hash参数 (当type_model=1时)
        if type_model == 1 and url_parse.fragment:
            # 正确解析hash中的路径和查询参数
            # 例如：#/aaa/?das=1 -> path=/aaa/, query=das=1
            fragment = url_parse.fragment
            if '?' in fragment:
                hash_path_str, hash_query_str = fragment.split('?', 1)
            else:
                hash_path_str = fragment
                hash_query_str = ''

            # 处理hash中的路径参数化
            if hash_path_str:
                hash_path = callback_pathname(hash_path_str)
            else:
                hash_path = ''

            # 处理hash中的查询参数
            hash_params = []
            if hash_query_str:
                for line, key in dict(parse_qsl(hash_query_str)).items():
                    hash_params.append(f"{line}={_check_string_type(key)}-{_callback_length(key)}")
                hash_params.sort()

            # 构建hash标准化字符串
            hash_generalization = '#' + hash_path
            if hash_params:
                hash_generalization += '?' + '&'.join(hash_params)

            url_generalization += hash_generalization

        # 参数特征（包含所有参数：URL查询、body、hash）
        param_features = []
        for p in list_param:
            param_features.append(f"{p['param_name']}={p['value_type']}-{p['value_len']}")
        param_features.sort()
        param_feature_str = '&'.join(param_features)

        # 去重key: method + 标准化URL + param_feature_str，然后转为md5
        key_str = f"{method}:{url_generalization}:{param_feature_str}"
        key = _core_func.md5_convert(key_str)

        return {
            'url': url,
            'method': method,
            'body': body,
            'url_path': url_path,
            'url_generalization': url_generalization,
            'param_feature': param_feature_str,
            'file_extension': file_extension,
            'key': key
        }
        
    except Exception:
        url = http_request.get('url', '')
        method = http_request.get('method', 'GET').upper()
        body = http_request.get('body', '')
        url_parse = urlparse(url)

        # 获取文件扩展名
        file_extension = _core_func.callback_file_extensions(url)

        return {
            'url': url,
            'method': method,
            'body': body,
            'url_path': _core_func.callback_split_url(url, 3),
            'url_generalization': url,
            'param_feature': '',
            'file_extension': file_extension,
            'key': _core_func.md5_convert(f"{method}:{url}")
        }





# 测试
if __name__ == '__main__':
    test_requests = [
        {'url': 'https://example.com/path/dasdas', 'method': 'GET', 'body': ''},
        {'url': 'https://example.com/path?sada=21312', 'method': 'GET', 'body': ''},
        {'url': 'https://example.com/path/123?sada=21312', 'method': 'GET', 'body': ''},
        {'url': 'https://example.com/admin/hello/demo', 'method': 'GET', 'body': ''},
        {'url': 'https://example.com/admin/123/demo.jsp', 'method': 'GET', 'body': ''},
    ]

    print("=== HTTP请求标准化测试 ===\n")
    for req in test_requests:
        std = standardize_request(req)
        print(f"原始: {req['url']}")
        print(f"标准化路径: {std['url_generalization']}")
        print(f"Key: {std['key']}")
        print('-' * 60)

    print("\n=== 去重测试 ===")
    unique = deduplicate_requests(test_requests)
    print(f"原始数量: {len(test_requests)}, 去重后: {len(unique)}")
