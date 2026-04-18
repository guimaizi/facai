# coding: utf-8
"""
重点资产管理API
@Time :    3/24/2026
@Author:  facai
@File: highlight_api.py
@Software: VSCode
"""
from flask import Blueprint, request, jsonify
from database.highlight_database import HighlightDatabase
from bson import ObjectId

highlight_api = Blueprint('highlight_api', __name__)


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


@highlight_api.route('/api/assets/highlights', methods=['GET'])
def get_highlight_list():
    """获取重点资产列表"""
    try:
        # 获取当前运行的项目名称
        project_name = get_running_project_name()
        if not project_name:
            return jsonify({'data': [], 'total': 0, 'page': 1, 'page_size': 20, 'total_pages': 0})

        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        search_keyword = request.args.get('search_keyword', '')
        search_type = request.args.get('search_type', 'url')
        sort_by = request.args.get('sort_by', 'time')
        sort_order = int(request.args.get('sort_order', -1))

        db = HighlightDatabase(project_name)
        highlights = db.get_all_highlights(page, page_size, sort_by, sort_order, search_keyword, search_type)
        total_count = db.search_highlights_count(search_keyword, search_type)

        # 转换ObjectId为字符串
        highlights = convert_objectid_to_str(highlights)

        # 计算总页数
        total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1

        return jsonify({
            'success': True,
            'data': highlights,
            'page': page,
            'page_size': page_size,
            'total_count': total_count,
            'total_pages': total_pages
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@highlight_api.route('/api/assets/highlights/<highlight_id>', methods=['GET'])
def get_highlight_detail(highlight_id):
    """获取重点资产详情"""
    try:
        # 获取当前运行的项目名称
        project_name = get_running_project_name()
        if not project_name:
            return jsonify({'success': False, 'message': '请先选择项目'})

        db = HighlightDatabase(project_name)
        highlight = db.get_highlight_by_id(highlight_id)

        if highlight:
            # 转换ObjectId为字符串
            highlight = convert_objectid_to_str(highlight)
            return jsonify({'success': True, 'highlight': highlight})
        else:
            return jsonify({'success': False, 'message': '重点资产不存在'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@highlight_api.route('/api/assets/highlights', methods=['POST'])
def add_highlight():
    """添加重点资产"""
    try:
        # 获取当前运行的项目名称
        project_name = get_running_project_name()
        if not project_name:
            return jsonify({'success': False, 'message': '请先选择项目'})

        data = request.get_json()

        db = HighlightDatabase(project_name)
        result = db.add_highlight(data)

        if result:
            return jsonify({'success': True, 'message': '添加成功', 'id': str(result)})
        else:
            return jsonify({'success': False, 'message': '添加失败'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@highlight_api.route('/api/assets/highlights/<highlight_id>', methods=['POST'])
def update_highlight(highlight_id):
    """更新重点资产"""
    try:
        # 获取当前运行的项目名称
        project_name = get_running_project_name()
        if not project_name:
            return jsonify({'success': False, 'message': '请先选择项目'})

        data = request.get_json()

        db = HighlightDatabase(project_name)
        result = db.update_highlight(highlight_id, data)

        if result:
            return jsonify({'success': True, 'message': '更新成功'})
        else:
            return jsonify({'success': False, 'message': '更新失败'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@highlight_api.route('/api/assets/highlights/<highlight_id>', methods=['DELETE'])
def delete_highlight(highlight_id):
    """删除重点资产"""
    try:
        # 获取当前运行的项目名称
        project_name = get_running_project_name()
        if not project_name:
            return jsonify({'success': False, 'message': '请先选择项目'})

        db = HighlightDatabase(project_name)
        result = db.delete_highlight(highlight_id)

        if result:
            return jsonify({'success': True, 'message': '删除成功'})
        else:
            return jsonify({'success': False, 'message': '删除失败'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@highlight_api.route('/api/assets/highlights/clear', methods=['POST'])
def clear_all_highlights():
    """清空所有重点资产"""
    try:
        # 获取当前运行的项目名称
        project_name = get_running_project_name()
        if not project_name:
            return jsonify({'success': False, 'message': '请先选择项目'})

        db = HighlightDatabase(project_name)
        result = db.delete_all_highlights()

        if result:
            return jsonify({'success': True, 'message': '清空成功'})
        else:
            return jsonify({'success': False, 'message': '清空失败'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@highlight_api.route('/api/assets/highlights/count', methods=['GET'])
def get_highlight_count():
    """获取重点资产总数"""
    try:
        # 获取当前运行的项目名称
        project_name = get_running_project_name()
        if not project_name:
            return jsonify({'success': True, 'count': 0})

        db = HighlightDatabase(project_name)
        count = db.count_highlights()

        return jsonify({'success': True, 'count': count})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@highlight_api.route('/api/assets/highlights/stats', methods=['GET'])
def get_highlight_stats():
    """获取重点资产统计信息"""
    try:
        # 获取当前运行的项目名称
        project_name = get_running_project_name()
        if not project_name:
            return jsonify({'success': True, 'stats': {}})

        db = HighlightDatabase(project_name)
        stats = db.get_type_statistics()

        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
