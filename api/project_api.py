from flask import Blueprint, request, jsonify
import os
import shutil
from database.project_database import ProjectDatabase

project_api = Blueprint('project_api', __name__)
project_db = ProjectDatabase()

@project_api.route('/api/projects/list', methods=['GET'])
def get_projects():
    """获取项目列表"""
    projects = project_db.get_all_projects()
    return jsonify({'projects': projects})

@project_api.route('/api/projects/add', methods=['POST'])
def add_project():
    """添加项目"""
    project_data = request.json
    result = project_db.add_project(project_data)
    if result:
        return jsonify({'success': True, 'message': '项目添加成功'})
    return jsonify({'success': False, 'message': '项目添加失败'})

@project_api.route('/api/projects/update', methods=['POST'])
def update_project():
    """更新项目"""
    project_data = request.json
    project_name = project_data.get('Project')
    
    print(f"\n[API] ===== 更新项目请求 =====")
    print(f"[API] 项目名称: {project_name}")
    print(f"[API] 接收到的数据字段: {list(project_data.keys())}")
    print(f"[API] personal_info字段内容: {project_data.get('personal_info')}")
    print(f"[API] personal_info类型: {type(project_data.get('personal_info'))}")
    
    if not project_name:
        return jsonify({'success': False, 'message': '项目名称不能为空'})
    result = project_db.update_project(project_name, project_data)
    
    print(f"[API] 更新结果: {result}")
    print(f"[API] ===== 更新项目请求结束 =====\n")
    
    if result:
        return jsonify({'success': True, 'message': '项目更新成功'})
    return jsonify({'success': False, 'message': '项目更新失败'})

@project_api.route('/api/projects/delete', methods=['POST'])
def delete_project():
    """删除项目"""
    project_name = request.json.get('Project')
    if not project_name:
        return jsonify({'success': False, 'message': '项目名称不能为空'})
    
    # 删除数据库中的项目
    result = project_db.delete_project(project_name)
    if result:
        # 删除项目数据目录
        project_dir = os.path.join(os.path.dirname(__file__), '..', 'project_data', project_name)
        if os.path.exists(project_dir):
            try:
                shutil.rmtree(project_dir)
            except Exception as e:
                print(f"删除项目目录失败: {e}")
        return jsonify({'success': True, 'message': '项目删除成功'})
    return jsonify({'success': False, 'message': '项目删除失败'})

@project_api.route('/api/projects/start', methods=['POST'])
def start_project():
    """启动项目"""
    project_name = request.json.get('Project')
    if not project_name:
        return jsonify({'success': False, 'message': '项目名称不能为空'})
    
    # 确保项目数据目录存在
    project_dir = os.path.join(os.path.dirname(__file__), '..', 'project_data', project_name)
    
    # 创建必要的目录
    dirs_to_create = [
        project_dir,
        os.path.join(project_dir, 'images'),
        os.path.join(project_dir, 'logs'),
        os.path.join(project_dir, 'chrome_data'),
        os.path.join(project_dir, 'chrome_data', 'headless'),
        os.path.join(project_dir, 'chrome_data', 'normal'),
    ]
    
    for dir_path in dirs_to_create:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
    
    # 创建必要的文件
    files_to_create = [
        os.path.join(project_dir, 'whitelist_domain.txt'),
        os.path.join(project_dir, 'blocklist_domain.txt'),
        os.path.join(project_dir, 'blocklist_url.txt'),
    ]
    
    for file_path in files_to_create:
        if not os.path.exists(file_path):
            open(file_path, 'w', encoding='utf-8').close()
    
    result = project_db.start_project(project_name)
    if result:
        return jsonify({'success': True, 'message': '项目启动成功'})
    return jsonify({'success': False, 'message': '项目启动失败'})

@project_api.route('/api/projects/stop', methods=['POST'])
def stop_project():
    """停止项目"""
    project_name = request.json.get('Project')
    if not project_name:
        return jsonify({'success': False, 'message': '项目名称不能为空'})
    result = project_db.stop_project(project_name)
    if result:
        return jsonify({'success': True, 'message': '项目停止成功'})
    return jsonify({'success': False, 'message': '项目停止失败'})

@project_api.route('/api/projects/status', methods=['GET'])
def get_project_status():
    """获取项目状态"""
    project_name = request.args.get('Project')
    if project_name:
        status = project_db.get_project_status(project_name)
        return jsonify({'status': status})
    # 获取运行中的项目
    running_project = project_db.get_running_project()
    if running_project:
        return jsonify({'running_project': running_project})
    return jsonify({'running_project': None})

@project_api.route('/api/projects/count', methods=['GET'])
def get_project_count():
    """获取项目总数"""
    count = project_db.get_project_count()
    return jsonify({'count': count})