# coding: utf-8
"""
网站管理API
@Time :    3/15/2026
@Author:  facai
@File: website_api.py
@Software: VSCode
"""
from flask import Blueprint, request, jsonify
from database.website_database import WebsiteDatabase
from bson import ObjectId
import time

website_api = Blueprint('website_api', __name__)

def get_running_project_name():
    """获取当前运行的项目名称"""
    try:
        from service.Class_Core_Function import Class_Core_Function
        core = Class_Core_Function()
        project = core.callback_project_config()
        if project and 'Project' in project:
            return project['Project']
    except Exception as e:
        pass
    return None

def convert_objectid_to_str(data):
    """将数据中的ObjectId类型转换为字符串"""
    if isinstance(data, list):
        return [convert_objectid_to_str(item) for item in data]
    elif isinstance(data, dict):
        return {key: convert_objectid_to_str(value) if isinstance(value, ObjectId) else value for key, value in data.items()}
    elif isinstance(data, ObjectId):
        return str(data)
    return data

@website_api.route('/api/assets/websites', methods=['GET'])
def get_websites():
    """获取网站列表"""
    # 获取当前运行的项目名称
    project_name = get_running_project_name()
    if not project_name:
        return jsonify({'websites': [], 'total': 0, 'page': 1, 'page_size': 20, 'total_pages': 0})

    # 获取分页和排序参数
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 20))
    sort_by = request.args.get('sort_by', 'time_update')
    sort_order = int(request.args.get('sort_order', -1))
    search_keyword = request.args.get('search_keyword', '')
    search_field = request.args.get('search_field', 'url')

    # 创建数据库实例
    website_db = WebsiteDatabase(project_name)

    # 获取网站数据
    websites = website_db.get_all_websites(page, page_size, sort_by, sort_order, search_keyword, search_field)
    websites = convert_objectid_to_str(websites)

    # 获取总数
    if search_keyword:
        total = website_db.search_websites_count(search_keyword, search_field)
    else:
        total = website_db.count_websites()

    # 计算总页数
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

    return jsonify({
        'websites': websites,
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': total_pages
    })

@website_api.route('/api/assets/websites/<id>', methods=['GET'])
def get_website_detail(id):
    """获取网站详情"""
    try:
        website_id = ObjectId(id)
    except:
        return jsonify({'success': False, 'message': '无效的网站ID'})

    project_name = get_running_project_name()
    if not project_name:
        return jsonify({'success': False, 'message': '未找到运行中的项目'})

    website_db = WebsiteDatabase(project_name)
    website = website_db.get_website_by_id(website_id)
    if website:
        website = convert_objectid_to_str(website)
        return jsonify({'success': True, 'website': website})
    return jsonify({'success': False, 'message': '网站数据不存在'})

@website_api.route('/api/assets/websites', methods=['POST'])
def add_website():
    """添加网站"""
    project_name = get_running_project_name()
    if not project_name:
        return jsonify({'success': False, 'message': '未找到运行中的项目'})

    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': '请求数据不能为空'})

    # 验证必填字段
    if not data.get('url'):
        return jsonify({'success': False, 'message': 'URL不能为空'})

    website_db = WebsiteDatabase(project_name)

    website_data = {
        'url': data.get('url'),
        'method': data.get('method', 'GET'),
        'subdomain': data.get('subdomain', ''),
        'domain': data.get('domain', ''),
        'title': data.get('title', ''),
        'port': data.get('port', 80),
        'server': data.get('server', ''),
        'web_fingerprint': data.get('web_fingerprint', ''),
        'screenshot': data.get('screenshot', ''),
        'http_status_code': data.get('http_status_code', 0),
        'tag': data.get('tag', []),
        'html_md5': data.get('html_md5', ''),
        'html_len': data.get('html_len', 0),
        'time_first': time.strftime('%Y-%m-%d %H:%M:%S'),
        'time_update': time.strftime('%Y-%m-%d %H:%M:%S'),
        'status': 0
    }

    result = website_db.add_website(website_data)
    if result:
        return jsonify({'success': True, 'message': '网站添加成功'})
    return jsonify({'success': False, 'message': '网站添加失败'})

@website_api.route('/api/assets/websites/<id>', methods=['DELETE'])
def delete_website(id):
    """删除网站"""
    try:
        website_id = ObjectId(id)
    except:
        return jsonify({'success': False, 'message': '无效的网站ID'})

    project_name = get_running_project_name()
    if not project_name:
        return jsonify({'success': False, 'message': '未找到运行中的项目'})

    website_db = WebsiteDatabase(project_name)
    result = website_db.delete_website(website_id)
    if result:
        return jsonify({'success': True, 'message': '网站删除成功'})
    return jsonify({'success': False, 'message': '网站删除失败'})

@website_api.route('/api/assets/websites/clear', methods=['POST'])
def clear_websites():
    """清空所有网站"""
    project_name = get_running_project_name()
    if not project_name:
        return jsonify({'success': False, 'message': '未找到运行中的项目'})

    website_db = WebsiteDatabase(project_name)
    result = website_db.delete_all_websites()
    if result:
        return jsonify({'success': True, 'message': '网站清空成功'})
    return jsonify({'success': False, 'message': '网站清空失败'})

@website_api.route('/api/assets/websites/count', methods=['GET'])
def get_websites_count():
    """获取网站总数"""
    project_name = get_running_project_name()
    if not project_name:
        return jsonify({'count': 0})

    website_db = WebsiteDatabase(project_name)
    count = website_db.count_websites()
    return jsonify({'count': count})
