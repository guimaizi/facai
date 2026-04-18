# coding: utf-8
"""
资产总览API
@Time :    3/24/2026
@Author:  facai
@File: overview_api.py
@Software: VSCode
"""
from flask import Blueprint, jsonify
from database.subdomain_database import SubdomainDatabase
from database.website_database import WebsiteDatabase
from database.http_database import HttpDatabase
from database.html_database import HtmlDatabase
from database.highlight_database import HighlightDatabase

overview_api = Blueprint('overview_api', __name__)


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


@overview_api.route('/api/assets/overview', methods=['GET'])
def get_overview():
    """获取资产总览数据"""
    try:
        project_name = get_running_project_name()
        if not project_name:
            return jsonify({
                'success': True,
                'overview': {
                    'subdomains': 0,
                    'websites': 0,
                    'http': 0,
                    'html': 0,
                    'highlights': 0,
                    'ip_cidr': 0,
                    'ip': 0
                }
            })

        # 获取各类型资产数量
        subdomain_db = SubdomainDatabase(project_name)
        website_db = WebsiteDatabase(project_name)
        http_db = HttpDatabase(project_name)
        html_db = HtmlDatabase(project_name)
        highlight_db = HighlightDatabase(project_name)

        overview = {
            'subdomains': subdomain_db.count_subdomains(),
            'websites': website_db.count_websites(),
            'http': http_db.count_http(),
            'html': html_db.count_html(),
            'highlights': highlight_db.count_highlights(),
            'ip_cidr': 0,  # TODO: 添加IP C段数据库后实现
            'ip': 0  # TODO: 添加IP数据库后实现
        }

        return jsonify({
            'success': True,
            'overview': overview
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@overview_api.route('/api/assets/overview/detail', methods=['GET'])
def get_overview_detail():
    """获取资产总览详细数据"""
    try:
        project_name = get_running_project_name()
        if not project_name:
            return jsonify({
                'success': True,
                'detail': {
                    'subdomain_status': {},
                    'website_status': {},
                    'http_type': {},
                    'highlight_type': {}
                }
            })

        # 获取详细统计数据
        subdomain_db = SubdomainDatabase(project_name)
        website_db = WebsiteDatabase(project_name)
        http_db = HttpDatabase(project_name)
        highlight_db = HighlightDatabase(project_name)

        detail = {
            'subdomain_status': subdomain_db.get_status_statistics() if hasattr(subdomain_db, 'get_status_statistics') else {},
            'website_status': website_db.get_status_statistics() if hasattr(website_db, 'get_status_statistics') else {},
            'http_type': {},  # TODO: 实现HTTP类型统计
            'highlight_type': highlight_db.get_type_statistics()
        }

        return jsonify({
            'success': True,
            'detail': detail
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
