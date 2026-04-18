# coding: utf-8
"""
资产管理配置API
@Time :    3/11/2026
@Author:  facai
@File: assets_config_api.py
@Software: VSCode
"""
from flask import Blueprint, request, jsonify
from database.assets_config_database import AssetsConfigDatabase
from database.project_database import ProjectDatabase

assets_config_bp = Blueprint('assets_config', __name__)
assets_db = AssetsConfigDatabase()
project_db = ProjectDatabase()


@assets_config_bp.route('/api/assets/config/whitelist/domain', methods=['GET', 'POST'])
def whitelist_domain():
    """
    域名白名单 - 读取和保存
    """
    # 获取当前项目
    project = request.args.get('project') or request.form.get('project')
    if not project:
        running_project = project_db.get_running_project()
        if running_project and 'Project' in running_project:
            project = running_project['Project']
    
    if not project:
        return jsonify({'success': False, 'message': '未指定项目'})
    
    if request.method == 'GET':
        # 读取域名白名单
        domains = assets_db.read_whitelist_domain(project)
        return jsonify({
            'success': True,
            'data': domains,
            'project': project
        })
    elif request.method == 'POST':
        # 保存域名白名单
        data = request.get_json()
        domains = data.get('domains', [])
        if isinstance(domains, str):
            domains = domains.split('\n')
        
        result = assets_db.write_whitelist_domain(project, domains)
        if result:
            return jsonify({'success': True, 'message': '域名白名单保存成功'})
        else:
            return jsonify({'success': False, 'message': '域名白名单保存失败'})


@assets_config_bp.route('/api/assets/config/blocklist/domain', methods=['GET', 'POST'])
def blocklist_domain():
    """
    域名黑名单 - 读取和保存
    """
    # 获取当前项目
    project = request.args.get('project') or request.form.get('project')
    if not project:
        running_project = project_db.get_running_project()
        if running_project and 'Project' in running_project:
            project = running_project['Project']
    
    if not project:
        return jsonify({'success': False, 'message': '未指定项目'})
    
    if request.method == 'GET':
        # 读取域名黑名单
        domains = assets_db.read_blocklist_domain(project)
        return jsonify({
            'success': True,
            'data': domains,
            'project': project
        })
    elif request.method == 'POST':
        # 保存域名黑名单
        data = request.get_json()
        domains = data.get('domains', [])
        if isinstance(domains, str):
            domains = domains.split('\n')
        
        result = assets_db.write_blocklist_domain(project, domains)
        if result:
            return jsonify({'success': True, 'message': '域名黑名单保存成功'})
        else:
            return jsonify({'success': False, 'message': '域名黑名单保存失败'})


@assets_config_bp.route('/api/assets/config/blocklist/url', methods=['GET', 'POST'])
def blocklist_url():
    """
    URL黑名单 - 读取和保存
    """
    # 获取当前项目
    project = request.args.get('project') or request.form.get('project')
    if not project:
        running_project = project_db.get_running_project()
        if running_project and 'Project' in running_project:
            project = running_project['Project']
    
    if not project:
        return jsonify({'success': False, 'message': '未指定项目'})
    
    if request.method == 'GET':
        # 读取URL黑名单
        urls = assets_db.read_blocklist_url(project)
        return jsonify({
            'success': True,
            'data': urls,
            'project': project
        })
    elif request.method == 'POST':
        # 保存URL黑名单
        data = request.get_json()
        urls = data.get('urls', [])
        if isinstance(urls, str):
            urls = urls.split('\n')
        
        result = assets_db.write_blocklist_url(project, urls)
        if result:
            return jsonify({'success': True, 'message': 'URL黑名单保存成功'})
        else:
            return jsonify({'success': False, 'message': 'URL黑名单保存失败'})


@assets_config_bp.route('/api/assets/config/import/domains', methods=['POST'])
def import_domains():
    """
    导入域名到HTTP临时表
    """
    # 获取当前项目
    project = request.args.get('project') or request.form.get('project')
    if not project:
        running_project = project_db.get_running_project()
        if running_project and 'Project' in running_project:
            project = running_project['Project']
    
    if not project:
        return jsonify({'success': False, 'message': '未指定项目'})
    
    data = request.get_json()
    domains = data.get('domains', [])
    if isinstance(domains, str):
        domains = domains.split('\n')
    domains = [d.strip() for d in domains if d.strip()]
    
    source = data.get('source', 1)
    
    result = assets_db.import_domains_to_http(project, domains, source)
    return jsonify(result)


@assets_config_bp.route('/api/assets/config/import/urls', methods=['POST'])
def import_urls():
    """
    导入URL到HTTP临时表
    """
    # 获取当前项目
    project = request.args.get('project') or request.form.get('project')
    if not project:
        running_project = project_db.get_running_project()
        if running_project and 'Project' in running_project:
            project = running_project['Project']
    
    if not project:
        return jsonify({'success': False, 'message': '未指定项目'})
    
    data = request.get_json()
    urls = data.get('urls', [])
    if isinstance(urls, str):
        urls = urls.split('\n')
    urls = [u.strip() for u in urls if u.strip()]
    
    source = data.get('source', 1)
    
    result = assets_db.import_urls_to_http(project, urls, source)
    return jsonify(result)


@assets_config_bp.route('/api/assets/config/all', methods=['GET'])
def get_all_config():
    """
    获取所有配置
    """
    # 获取当前项目
    project = request.args.get('project')
    if not project:
        running_project = project_db.get_running_project()
        if running_project and 'Project' in running_project:
            project = running_project['Project']
    
    if not project:
        return jsonify({'success': False, 'message': '未指定项目'})
    
    # 读取所有配置
    whitelist_domains = assets_db.read_whitelist_domain(project)
    blocklist_domains = assets_db.read_blocklist_domain(project)
    blocklist_urls = assets_db.read_blocklist_url(project)
    
    return jsonify({
        'success': True,
        'data': {
            'whitelist_domain': whitelist_domains,
            'blocklist_domain': blocklist_domains,
            'blocklist_url': blocklist_urls
        },
        'project': project
    })
