# coding: utf-8
"""
子域名管理API
@Time :    3/15/2026
@Author:  facai
@File: subdomain_api.py
@Software: VSCode
"""
from flask import Blueprint, request, jsonify
from database.subdomain_database import SubdomainDatabase
from bson import ObjectId
import time

subdomain_api = Blueprint('subdomain_api', __name__)

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

@subdomain_api.route('/api/assets/subdomains', methods=['GET'])
def get_subdomains():
    """获取子域名列表"""
    # 获取当前运行的项目名称
    project_name = get_running_project_name()
    if not project_name:
        return jsonify({'subdomains': [], 'total': 0, 'page': 1, 'page_size': 20, 'total_pages': 0})

    # 获取分页和排序参数
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 20))
    sort_by = request.args.get('sort_by')
    sort_order = int(request.args.get('sort_order', 1))
    search_keyword = request.args.get('search_keyword', '')

    # 创建数据库实例
    subdomain_db = SubdomainDatabase(project_name)

    # 获取子域名数据
    subdomains = subdomain_db.get_all_subdomains(page, page_size, sort_by, sort_order, search_keyword)
    subdomains = convert_objectid_to_str(subdomains)

    # 获取总数
    if search_keyword:
        total = subdomain_db.search_subdomains_count(search_keyword)
    else:
        total = subdomain_db.count_subdomains()

    # 计算总页数
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

    return jsonify({
        'subdomains': subdomains,
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': total_pages
    })

@subdomain_api.route('/api/assets/subdomains/<id>', methods=['GET'])
def get_subdomain_detail(id):
    """获取子域名详情"""
    try:
        subdomain_id = ObjectId(id)
    except:
        return jsonify({'success': False, 'message': '无效的子域名ID'})

    project_name = get_running_project_name()
    if not project_name:
        return jsonify({'success': False, 'message': '未找到运行中的项目'})

    subdomain_db = SubdomainDatabase(project_name)
    subdomain = subdomain_db.get_subdomain_by_id(subdomain_id)
    if subdomain:
        subdomain = convert_objectid_to_str(subdomain)
        return jsonify({'success': True, 'subdomain': subdomain})
    return jsonify({'success': False, 'message': '子域名数据不存在'})

@subdomain_api.route('/api/assets/subdomains', methods=['POST'])
def add_subdomain():
    """添加子域名"""
    project_name = get_running_project_name()
    if not project_name:
        return jsonify({'success': False, 'message': '未找到运行中的项目'})

    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': '请求数据不能为空'})

    # 验证必填字段
    if not data.get('subdomain'):
        return jsonify({'success': False, 'message': '子域名不能为空'})

    subdomain_db = SubdomainDatabase(project_name)

    subdomain_data = {
        'subdomain': data.get('subdomain'),
        'domain': data.get('domain', ''),
        'ip_list': data.get('ip_list', []),
        'port_list': data.get('port_list', []),
        'time': time.strftime('%Y-%m-%d %H:%M:%S'),
        'time_update': time.strftime('%Y-%m-%d %H:%M:%S')
    }

    result = subdomain_db.add_subdomain(subdomain_data)
    if result:
        return jsonify({'success': True, 'message': '子域名添加成功'})
    return jsonify({'success': False, 'message': '子域名添加失败'})

@subdomain_api.route('/api/assets/subdomains/<id>', methods=['DELETE'])
def delete_subdomain(id):
    """删除子域名"""
    try:
        subdomain_id = ObjectId(id)
    except:
        return jsonify({'success': False, 'message': '无效的子域名ID'})

    project_name = get_running_project_name()
    if not project_name:
        return jsonify({'success': False, 'message': '未找到运行中的项目'})

    subdomain_db = SubdomainDatabase(project_name)
    result = subdomain_db.delete_subdomain(subdomain_id)
    if result:
        return jsonify({'success': True, 'message': '子域名删除成功'})
    return jsonify({'success': False, 'message': '子域名删除失败'})

@subdomain_api.route('/api/assets/subdomains/clear', methods=['POST'])
def clear_subdomains():
    """清空所有子域名"""
    project_name = get_running_project_name()
    if not project_name:
        return jsonify({'success': False, 'message': '未找到运行中的项目'})

    subdomain_db = SubdomainDatabase(project_name)
    result = subdomain_db.delete_all_subdomains()
    if result:
        return jsonify({'success': True, 'message': '子域名清空成功'})
    return jsonify({'success': False, 'message': '子域名清空失败'})

@subdomain_api.route('/api/assets/subdomains/count', methods=['GET'])
def get_subdomains_count():
    """获取子域名总数"""
    project_name = get_running_project_name()
    if not project_name:
        return jsonify({'count': 0})

    subdomain_db = SubdomainDatabase(project_name)
    count = subdomain_db.count_subdomains()
    return jsonify({'count': count})
