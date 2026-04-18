from flask import Blueprint, request, jsonify
from database.traffic_database import TrafficDatabase
from bson import ObjectId
import os

traffic_api = Blueprint('traffic_api', __name__)

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

@traffic_api.route('/api/traffic/list', methods=['GET'])
def get_traffic():
    """获取流量列表"""
    # 获取当前运行的项目名称
    project_name = get_running_project_name()
    if not project_name:
        return jsonify({'traffic': [], 'total': 0, 'page': 1, 'page_size': 20, 'total_pages': 0})

    # 获取分页和排序参数
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 20))
    sort_by = request.args.get('sort_by')
    sort_order = int(request.args.get('sort_order', 1))
    search_url = request.args.get('search_url', '')

    # 创建数据库实例
    traffic_db = TrafficDatabase(project_name)

    # 获取流量数据
    traffic, total = traffic_db.get_all_traffic(page, page_size, sort_by, sort_order, search_url)
    traffic = convert_objectid_to_str(traffic)

    # 计算总页数
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

    return jsonify({
        'traffic': traffic,
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': total_pages
    })

@traffic_api.route('/api/traffic/detail/<id>', methods=['GET'])
def get_traffic_detail(id):
    """获取流量详情"""
    try:
        traffic_id = ObjectId(id)
    except Exception as e:
        return jsonify({'success': False, 'message': f'无效的流量ID: {str(e)}'})

    project_name = get_running_project_name()
    if not project_name:
        return jsonify({'success': False, 'message': '未找到运行中的项目'})

    traffic_db = TrafficDatabase(project_name)
    traffic = traffic_db.get_traffic_by_id(traffic_id)
    if traffic:
        traffic = convert_objectid_to_str(traffic)
        return jsonify({'success': True, 'traffic': traffic})
    
    # 调试信息：记录查询失败的原因
    print(f"[DEBUG] 流量查询失败 - ID: {id}, ObjectId: {traffic_id}, Collection: {traffic_db.collection_name}")
    return jsonify({'success': False, 'message': f'流量数据不存在 (ID: {id}, Collection: {traffic_db.collection_name})'})

@traffic_api.route('/api/traffic/delete/<id>', methods=['POST'])
def delete_traffic(id):
    """删除流量数据"""
    try:
        traffic_id = ObjectId(id)
    except:
        return jsonify({'success': False, 'message': '无效的流量ID'})

    project_name = get_running_project_name()
    if not project_name:
        return jsonify({'success': False, 'message': '未找到运行中的项目'})

    traffic_db = TrafficDatabase(project_name)
    result = traffic_db.delete_traffic(traffic_id)
    if result:
        return jsonify({'success': True, 'message': '流量删除成功'})
    return jsonify({'success': False, 'message': '流量删除失败'})

@traffic_api.route('/api/traffic/clear', methods=['POST'])
def clear_traffic():
    """清空流量数据"""
    project_name = get_running_project_name()
    if not project_name:
        return jsonify({'success': False, 'message': '未找到运行中的项目'})

    traffic_db = TrafficDatabase(project_name)
    result = traffic_db.delete_all_traffic()
    if result:
        return jsonify({'success': True, 'message': '流量清空成功'})
    return jsonify({'success': False, 'message': '流量清空失败'})

@traffic_api.route('/api/traffic/count', methods=['GET'])
def get_traffic_count():
    """获取流量总数"""
    project_name = get_running_project_name()
    if not project_name:
        return jsonify({'count': 0})

    traffic_db = TrafficDatabase(project_name)
    count = traffic_db.count_traffic()
    return jsonify({'count': count})