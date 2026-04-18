# coding: utf-8
"""
HTTP请求响应管理API
@Time :    3/22/2026
@Author:  facai
@File: http_api.py
@Software: VSCode
"""
from flask import Blueprint, request, jsonify
from database.http_database import HttpDatabase
from bson import ObjectId

http_api = Blueprint('http_api', __name__)


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


@http_api.route('/api/assets/http', methods=['GET'])
def get_http_list():
    """获取HTTP列表"""
    try:
        # 获取当前运行的项目名称
        project_name = get_running_project_name()
        if not project_name:
            return jsonify({'https': [], 'total': 0, 'page': 1, 'page_size': 20, 'total_pages': 0})

        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        search_keyword = request.args.get('search_keyword', '')
        search_type = request.args.get('search_type', 'url')
        sort_by = request.args.get('sort_by', 'time_first')
        sort_order = int(request.args.get('sort_order', -1))

        db = HttpDatabase(project_name)
        https = db.get_all_http(page, page_size, sort_by, sort_order, search_keyword, search_type)
        total_count = db.search_http_count(search_keyword, search_type)

        # 转换ObjectId为字符串
        https = convert_objectid_to_str(https)

        # 计算总页数
        total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1

        return jsonify({
            'success': True,
            'https': https,
            'page': page,
            'page_size': page_size,
            'total_count': total_count,
            'total_pages': total_pages
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@http_api.route('/api/assets/http/<http_id>', methods=['GET'])
def get_http_detail(http_id):
    """获取HTTP详情"""
    try:
        # 获取当前运行的项目名称
        project_name = get_running_project_name()
        if not project_name:
            return jsonify({'success': False, 'message': '请先选择项目'})

        db = HttpDatabase(project_name)
        http = db.get_http_by_id(http_id)

        if http:
            # 转换ObjectId为字符串
            http = convert_objectid_to_str(http)
            return jsonify({'success': True, 'http': http})
        else:
            return jsonify({'success': False, 'message': 'HTTP数据不存在'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@http_api.route('/api/assets/http/key/<key>', methods=['GET'])
def get_http_by_key(key):
    """根据key获取HTTP详情"""
    try:
        # 获取当前运行的项目名称
        project_name = get_running_project_name()
        if not project_name:
            return jsonify({'success': False, 'message': '请先选择项目'})

        db = HttpDatabase(project_name)
        http = db.get_http_by_key(key)

        if http:
            # 转换ObjectId为字符串
            http = convert_objectid_to_str(http)
            return jsonify({'success': True, 'http': http})
        else:
            return jsonify({'success': False, 'message': 'HTTP数据不存在'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@http_api.route('/api/assets/http', methods=['POST'])
def add_http():
    """添加HTTP"""
    try:
        # 获取当前运行的项目名称
        project_name = get_running_project_name()
        if not project_name:
            return jsonify({'success': False, 'message': '请先选择项目'})

        data = request.get_json()

        db = HttpDatabase(project_name)
        result = db.add_http(data)

        if result:
            return jsonify({'success': True, 'message': '添加成功', 'id': str(result)})
        else:
            return jsonify({'success': False, 'message': '添加失败或key已存在'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@http_api.route('/api/assets/http/<http_id>', methods=['DELETE'])
def delete_http(http_id):
    """删除HTTP"""
    try:
        # 获取当前运行的项目名称
        project_name = get_running_project_name()
        if not project_name:
            return jsonify({'success': False, 'message': '请先选择项目'})

        db = HttpDatabase(project_name)
        result = db.delete_http(http_id)

        if result:
            return jsonify({'success': True, 'message': '删除成功'})
        else:
            return jsonify({'success': False, 'message': '删除失败'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@http_api.route('/api/assets/http/clear', methods=['POST'])
def clear_all_http():
    """清空所有HTTP"""
    try:
        # 获取当前运行的项目名称
        project_name = get_running_project_name()
        if not project_name:
            return jsonify({'success': False, 'message': '请先选择项目'})

        db = HttpDatabase(project_name)
        result = db.delete_all_http()

        if result:
            return jsonify({'success': True, 'message': '清空成功'})
        else:
            return jsonify({'success': False, 'message': '清空失败'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@http_api.route('/api/assets/http/count', methods=['GET'])
def get_http_count():
    """获取HTTP总数"""
    try:
        # 获取当前运行的项目名称
        project_name = get_running_project_name()
        if not project_name:
            return jsonify({'success': True, 'count': 0})

        db = HttpDatabase(project_name)
        count = db.count_http()

        return jsonify({'success': True, 'count': count})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
