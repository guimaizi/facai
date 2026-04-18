# coding: utf-8
"""
HTML大文件管理API
@Time :    3/15/2026
@Author:  facai
@File: html_api.py
@Software: VSCode
"""
from flask import Blueprint, request, jsonify
from database.html_database import HtmlDatabase
from bson import ObjectId

html_api = Blueprint('html_api', __name__)


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


@html_api.route('/api/assets/html', methods=['GET'])
def get_html_list():
    """获取HTML列表"""
    try:
        # 获取当前运行的项目名称
        project_name = get_running_project_name()
        if not project_name:
            return jsonify({'htmls': [], 'total': 0, 'page': 1, 'page_size': 20, 'total_pages': 0})

        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        search_keyword = request.args.get('search_keyword', '')
        search_type = request.args.get('search_type', 'md5')
        sort_by = request.args.get('sort_by', 'time')
        sort_order = int(request.args.get('sort_order', -1))

        db = HtmlDatabase(project_name)
        htmls = db.get_all_html(page, page_size, sort_by, sort_order, search_keyword, search_type)
        total_count = db.count_html()

        # 转换ObjectId为字符串
        htmls = convert_objectid_to_str(htmls)

        # 计算总页数
        total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1

        return jsonify({
            'success': True,
            'htmls': htmls,
            'page': page,
            'page_size': page_size,
            'total_count': total_count,
            'total_pages': total_pages
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@html_api.route('/api/assets/html/<html_id>', methods=['GET'])
def get_html_detail(html_id):
    """获取HTML详情"""
    try:
        # 获取当前运行的项目名称
        project_name = get_running_project_name()
        if not project_name:
            return jsonify({'success': False, 'message': '请先选择项目'})

        db = HtmlDatabase(project_name)
        html = db.get_html_by_id(html_id)

        if html:
            # 转换ObjectId为字符串
            html = convert_objectid_to_str(html)
            return jsonify({'success': True, 'html': html})
        else:
            return jsonify({'success': False, 'message': 'HTML数据不存在'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@html_api.route('/api/assets/html', methods=['POST'])
def add_html():
    """添加HTML"""
    try:
        # 获取当前运行的项目名称
        project_name = get_running_project_name()
        if not project_name:
            return jsonify({'success': False, 'message': '请先选择项目'})

        data = request.get_json()

        html_data = {
            'html': data.get('html'),
            'html_md5': data.get('html_md5'),
            'html_len': data.get('html_len', 0)
        }

        db = HtmlDatabase(project_name)
        result = db.add_html(html_data)

        if result:
            return jsonify({'success': True, 'message': '添加成功', 'id': str(result)})
        else:
            return jsonify({'success': False, 'message': '添加失败'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@html_api.route('/api/assets/html/<html_id>', methods=['DELETE'])
def delete_html(html_id):
    """删除HTML"""
    try:
        # 获取当前运行的项目名称
        project_name = get_running_project_name()
        if not project_name:
            return jsonify({'success': False, 'message': '请先选择项目'})

        db = HtmlDatabase(project_name)
        result = db.delete_html(html_id)

        if result:
            return jsonify({'success': True, 'message': '删除成功'})
        else:
            return jsonify({'success': False, 'message': '删除失败'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@html_api.route('/api/assets/html/clear', methods=['POST'])
def clear_all_html():
    """清空所有HTML"""
    try:
        # 获取当前运行的项目名称
        project_name = get_running_project_name()
        if not project_name:
            return jsonify({'success': False, 'message': '请先选择项目'})

        db = HtmlDatabase(project_name)
        result = db.delete_all_html()

        if result:
            return jsonify({'success': True, 'message': '清空成功'})
        else:
            return jsonify({'success': False, 'message': '清空失败'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@html_api.route('/api/assets/html/count', methods=['GET'])
def get_html_count():
    """获取HTML总数"""
    try:
        # 获取当前运行的项目名称
        project_name = get_running_project_name()
        if not project_name:
            return jsonify({'success': True, 'count': 0})

        db = HtmlDatabase(project_name)
        count = db.count_html()

        return jsonify({'success': True, 'count': count})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
