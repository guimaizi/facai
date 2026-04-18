# coding: utf-8
"""
漏洞扫描器API接口
"""
from flask import Blueprint, request, jsonify
import os
import sys
import threading
import time
import json
from bson import ObjectId

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from service.scaner.vuln_core import VulnerabilityScanner
from database.vuln_database import VulnDatabase

scaner_api = Blueprint('scaner', __name__, url_prefix='/api/scaner')

# 扫描器单例
_scanner_instance = None


def get_scanner():
    """获取扫描器单例（从项目配置获取dnslog设置）"""
    global _scanner_instance
    if _scanner_instance is None:
        # 从项目配置获取dnslog设置
        try:
            from service.Class_Core_Function import Class_Core_Function
            core_function = Class_Core_Function()
            project_config = core_function.callback_project_config()
            
            dnslog_domain = ''
            dnslog_url = ''
            project_name = ''
            
            if project_config:
                dnslog_domain = project_config.get('dnslog_domain', '')
                dnslog_url = project_config.get('dnslog_url', '')
                project_name = project_config.get('Project', '')
            
            print(f"[Scanner] 从项目配置获取dnslog_domain: {dnslog_domain}")
            print(f"[Scanner] 从项目配置获取dnslog_url: {dnslog_url}")
            print(f"[Scanner] 项目名称: {project_name}")
            
        except Exception as e:
            print(f"[Scanner] 获取项目配置失败: {e}")
            dnslog_domain = ''
            dnslog_url = ''
            project_name = ''
        
        _scanner_instance = VulnerabilityScanner(
            dnslog_domain=dnslog_domain,
            dnslog_url=dnslog_url,
            project_name=project_name
        )
    return _scanner_instance


def get_vuln_db():
    """获取漏洞数据库实例"""
    return VulnDatabase()


class JSONEncoder(json.JSONEncoder):
    """自定义JSON编码器，处理ObjectId等特殊类型"""
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return super().default(o)


def serialize_vuln(vuln):
    """序列化漏洞数据（标准格式）"""
    if not vuln:
        return None
    
    # 如果已经是字典，直接复制
    if isinstance(vuln, dict):
        serialized = vuln.copy()
    else:
        print(f"[Serialize] 警告: 漏洞数据不是字典类型: {type(vuln)}")
        print(f"[Serialize] 数据内容: {vuln}")
        return None
    
    # 转换ObjectId为字符串
    if '_id' in serialized:
        serialized['id'] = str(serialized['_id'])
        del serialized['_id']
    
    # 确保标准字段存在（按文档格式）
    serialized.setdefault('url', '')
    serialized.setdefault('method', '')
    serialized.setdefault('headers', {})
    serialized.setdefault('body', '')
    serialized.setdefault('website', '')
    serialized.setdefault('subdomain', '')
    serialized.setdefault('vuln_type', 'unknown')
    serialized.setdefault('vuln_type_detail', 'unknown')
    serialized.setdefault('level', 'medium')
    serialized.setdefault('paramname', '')
    serialized.setdefault('time', '')
    
    # 额外字段（可选）
    serialized.setdefault('payload', '')
    serialized.setdefault('evidence', '')
    serialized.setdefault('description', '')
    
    return serialized


# ==================== 参数提取 ====================

@scaner_api.route('/params/extract', methods=['POST'])
def extract_params():
    """提取HTTP请求中的参数"""
    try:
        data = request.get_json()
        request_data = data.get('request', {})
        
        # 验证必要字段
        if not request_data.get('url'):
            return jsonify({
                'success': False,
                'message': '缺少URL参数'
            }), 400
        
        # 提取参数
        scanner = get_scanner()
        params = scanner.param_handler.callback_list_param(request_data)
        
        # 格式化参数列表
        formatted_params = []
        for param in params:
            formatted_params.append({
                'name': param.get('param_name', ''),
                'value': param.get('param_value', ''),
                'type': param.get('param_type', 'String'),
                'position': param.get('position', 'GET')
            })
        
        return jsonify({
            'success': True,
            'data': {
                'total': len(formatted_params),
                'params': formatted_params
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'参数提取失败: {str(e)}'
        }), 500


# ==================== 手动扫描 ====================

@scaner_api.route('/params/clear', methods=['POST'])
def clear_scanned_params():
    """清空已扫描参数数据"""
    try:
        # 获取项目配置
        from service.Class_Core_Function import Class_Core_Function
        from database.vuln_param_database import VulnParamDatabase
        
        core_function = Class_Core_Function()
        project_config = core_function.callback_project_config()
        
        if not project_config:
            return jsonify({
                'success': False,
                'message': '没有运行中的项目'
            }), 400
        
        project_name = project_config.get('Project', '')
        if not project_name:
            return jsonify({
                'success': False,
                'message': '项目名称为空'
            }), 400
        
        # 清空已扫描参数数据
        vuln_param_db = VulnParamDatabase(project_name)
        deleted_count = vuln_param_db.delete_all_params()
        
        return jsonify({
            'success': True,
            'message': '已清空数据',
            'data': {
                'count': deleted_count
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'清空失败: {str(e)}'
        }), 500


@scaner_api.route('/manual/start', methods=['POST'])
def manual_scan_start():
    """手动模式扫描 - 参考test_vuln_scanner.py的标准用法"""
    try:
        data = request.get_json()
        
        # 获取请求数据
        request_data = data.get('request', {})
        
        # 验证必要字段
        if not request_data.get('url'):
            return jsonify({
                'success': False,
                'message': '缺少URL参数'
            }), 400
        
        print(f"[Manual Scan] ========== 扫描请求详情 ==========")
        print(f"[Manual Scan] URL: {request_data.get('url')}")
        print(f"[Manual Scan] Method: {request_data.get('method')}")
        print(f"[Manual Scan] Headers: {request_data.get('headers')}")
        print(f"[Manual Scan] Body: {request_data.get('body')}")
        print(f"[Manual Scan] ==============================")
        
        # 扫描选项（参考test_vuln_scanner.py）
        scan_options = {
            'anomaly': True,
            'xss': True,
            'sqli': True,
            'rce': True,
            'ssrf': True,
            'info_leak': True,
        }
        
        # 初始化扫描器并执行扫描（自动保存到数据库）
        scanner = get_scanner()
        vulnerabilities = scanner.scan(request_data, scan_options, save_to_db=True)
        
        print(f"[Manual Scan] 发现 {len(vulnerabilities)} 个漏洞")
        
        # 序列化结果（过滤掉 None）
        serialized_vulns = [serialize_vuln(v) for v in vulnerabilities]
        serialized_vulns = [v for v in serialized_vulns if v is not None]
        
        print(f"[Manual Scan] 序列化后漏洞数: {len(serialized_vulns)}")
        for idx, v in enumerate(serialized_vulns):
            print(f"  漏洞 {idx+1}: {v.get('vuln_type')} - {v.get('paramname')}")
        
        return jsonify({
            'success': True,
            'data': {
                'url': request_data.get('url'),
                'vulns': len(vulnerabilities),
                'details': serialized_vulns
            }
        })
    
    except Exception as e:
        print(f"[Manual Scan] 扫描失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'扫描失败: {str(e)}'
        }), 500


# ==================== 自动扫描 ====================
# 已移除，不需要


# ==================== 扫描结果 ====================

@scaner_api.route('/results', methods=['GET'])
def get_results():
    """获取扫描结果列表"""
    try:
        # 获取查询参数
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        level = request.args.get('level', '')  # 危害等级
        vuln_type = request.args.get('vuln_type', '')  # 漏洞大类
        search = request.args.get('search', '')
        search_type = request.args.get('search_type', 'url')  # 搜索类型
        
        # 排序参数
        sort_by = request.args.get('sort_by', 'time')
        sort_order = int(request.args.get('sort_order', -1))  # -1降序，1升序
        
        # 从数据库获取结果
        vuln_db = get_vuln_db()
        
        level_filter = level if level else None
        type_filter = vuln_type if vuln_type else None
        
        vulns = vuln_db.get_all_vuln(
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
            search_keyword=search,
            search_type=search_type,
            level=level_filter,
            vuln_type=type_filter
        )
        
        total = vuln_db.search_vuln_count(
            search_keyword=search,
            search_type=search_type,
            level=level_filter,
            vuln_type=type_filter
        )
        
        # 序列化结果
        results = [serialize_vuln(v) for v in vulns]
        
        return jsonify({
            'success': True,
            'data': {
                'results': results,
                'total': total,
                'page': page,
                'page_size': page_size
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取结果失败: {str(e)}'
        }), 500


@scaner_api.route('/results/<vuln_id>', methods=['GET'])
def get_result_detail(vuln_id):
    """获取单个漏洞详情"""
    try:
        vuln_db = get_vuln_db()
        vuln = vuln_db.get_vuln_by_id(vuln_id)
        
        if not vuln:
            return jsonify({
                'success': False,
                'message': '漏洞不存在'
            }), 404
        
        result = serialize_vuln(vuln)
        
        return jsonify({
            'success': True,
            'data': result
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取详情失败: {str(e)}'
        }), 500


@scaner_api.route('/results/clear', methods=['POST'])
def clear_results():
    """清空扫描结果"""
    try:
        vuln_db = get_vuln_db()
        vuln_db.delete_all_vuln()
        
        return jsonify({
            'success': True,
            'message': '结果已清空'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'清空失败: {str(e)}'
        }), 500


@scaner_api.route('/results/<vuln_id>', methods=['DELETE'])
def delete_result(vuln_id):
    """删除单个漏洞"""
    try:
        vuln_db = get_vuln_db()
        result = vuln_db.delete_vuln(vuln_id)
        
        if result:
            return jsonify({
                'success': True,
                'message': '漏洞已删除'
            })
        else:
            return jsonify({
                'success': False,
                'message': '删除失败'
            }), 400
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'删除失败: {str(e)}'
        }), 500


# ==================== 统计数据 ====================

@scaner_api.route('/stats', methods=['GET'])
def get_stats():
    """获取扫描统计信息"""
    try:
        vuln_db = get_vuln_db()
        stats = vuln_db.get_vuln_statistics()
        
        # 确保by_level是字典类型
        by_level = stats.get('by_level', {})
        if not isinstance(by_level, dict):
            by_level = {}
        
        # 获取已扫描接口数量（从 vuln_param_database 表）
        scanned_count = 0
        try:
            from service.Class_Core_Function import Class_Core_Function
            from database.vuln_param_database import VulnParamDatabase
            
            core_function = Class_Core_Function()
            project_config = core_function.callback_project_config()
            
            if project_config:
                project_name = project_config.get('Project', '')
                if project_name:
                    vuln_param_db = VulnParamDatabase(project_name)
                    scanned_count = vuln_param_db.count_params()
        except Exception as e:
            print(f"[Stats] 获取已扫描接口数失败: {e}")
        
        return jsonify({
            'success': True,
            'data': {
                'scanned_count': scanned_count,
                'total_vulns': stats.get('total', 0),
                'high_vulns': by_level.get('high', 0),
                'medium_vulns': by_level.get('medium', 0),
                'low_vulns': by_level.get('low', 0),
                'by_type': stats.get('by_type', {}),
                'by_type_detail': stats.get('by_type_detail', {}),
                'by_level': by_level
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取统计失败: {str(e)}'
        }), 500


# ==================== 扫描设置 ====================
# 已移除，不需要


# ==================== 扫描器状态 ====================
# 已移除，不需要



# ==================== 盲打日志 ====================

def get_vuln_log_db(project_name):
    """获取漏洞日志数据库实例"""
    from database.vuln_log_database import VulnLogDatabase
    return VulnLogDatabase(project_name)


def serialize_vuln_log(log):
    """序列化盲打日志数据（处理ObjectId等特殊类型）"""
    if not log:
        return None

    # 如果已经是字典，直接复制
    if isinstance(log, dict):
        serialized = log.copy()
    else:
        print(f"[Serialize] 警告: 日志数据不是字典类型: {type(log)}")
        return None

    # 转换ObjectId为字符串
    if '_id' in serialized:
        serialized['id'] = str(serialized['_id'])
        del serialized['_id']

    return serialized


@scaner_api.route('/logs', methods=['GET'])
def get_vuln_logs():
    """获取盲打日志列表"""
    try:
        # 获取项目配置
        from service.Class_Core_Function import Class_Core_Function
        core_function = Class_Core_Function()
        project_config = core_function.callback_project_config()

        if not project_config:
            return jsonify({
                'success': False,
                'message': '没有运行中的项目'
            }), 400

        project_name = project_config.get('Project', '')
        if not project_name:
            return jsonify({
                'success': False,
                'message': '项目名称为空'
            }), 400

        # 获取查询参数
        status = request.args.get('status', '')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        
        # 计算 skip
        skip = (page - 1) * page_size

        # 获取日志
        vuln_log_db = get_vuln_log_db(project_name)

        if status:
            # 按状态过滤
            status_int = int(status)
            query = {'status': status_int}
            logs = vuln_log_db.db_handler.find(
                vuln_log_db.collection_name,
                query,
                limit=page_size,
                skip=skip,
                sort=[('time', -1)]
            )
            # 获取总数
            total = vuln_log_db.db_handler.count_documents(
                vuln_log_db.collection_name,
                query
            )
        else:
            # 获取所有日志
            logs = vuln_log_db.db_handler.find(
                vuln_log_db.collection_name,
                {},
                limit=page_size,
                skip=skip,
                sort=[('time', -1)]
            )
            # 获取总数
            total = vuln_log_db.db_handler.count_documents(
                vuln_log_db.collection_name,
                {}
            )

        # 序列化日志数据
        serialized_logs = [serialize_vuln_log(log) for log in logs]
        serialized_logs = [log for log in serialized_logs if log is not None]

        # 计算总页数
        import math
        total_pages = math.ceil(total / page_size)

        return jsonify({
            'success': True,
            'data': {
                'logs': serialized_logs,
                'page': page,
                'page_size': page_size,
                'total': total,
                'total_pages': total_pages
            }
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'获取日志失败: {str(e)}'
        }), 500


@scaner_api.route('/logs/search', methods=['GET'])
def search_vuln_log():
    """搜索盲打日志"""
    try:
        # 获取项目配置
        from service.Class_Core_Function import Class_Core_Function
        core_function = Class_Core_Function()
        project_config = core_function.callback_project_config()

        if not project_config:
            return jsonify({
                'success': False,
                'message': '没有运行中的项目'
            }), 400

        project_name = project_config.get('Project', '')
        if not project_name:
            return jsonify({
                'success': False,
                'message': '项目名称为空'
            }), 400

        # 获取搜索参数
        vuln_hash = request.args.get('vuln_hash', '')

        if not vuln_hash:
            return jsonify({
                'success': False,
                'message': '缺少 vuln_hash 参数'
            }), 400

        # 搜索日志
        vuln_log_db = get_vuln_log_db(project_name)
        log = vuln_log_db.get_log_by_hash(vuln_hash)

        if not log:
            return jsonify({
                'success': False,
                'message': '未找到该日志'
            }), 404

        # 序列化日志数据
        serialized_log = serialize_vuln_log(log)

        return jsonify({
            'success': True,
            'data': serialized_log
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'搜索失败: {str(e)}'
        }), 500


@scaner_api.route('/logs/<vuln_hash>/verify', methods=['POST'])
def verify_vuln_log(vuln_hash):
    """验证盲打日志"""
    try:
        # 获取项目配置
        from service.Class_Core_Function import Class_Core_Function
        core_function = Class_Core_Function()
        project_config = core_function.callback_project_config()

        if not project_config:
            return jsonify({
                'success': False,
                'message': '没有运行中的项目'
            }), 400

        project_name = project_config.get('Project', '')
        if not project_name:
            return jsonify({
                'success': False,
                'message': '项目名称为空'
            }), 400

        # 验证日志
        vuln_log_db = get_vuln_log_db(project_name)
        result = vuln_log_db.verify_log(vuln_hash)

        if result:
            return jsonify({
                'success': True,
                'message': '已标记为验证'
            })
        else:
            return jsonify({
                'success': False,
                'message': '验证失败'
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'验证失败: {str(e)}'
        }), 500


@scaner_api.route('/logs/clear', methods=['POST'])
def clear_vuln_logs():
    """清空盲打日志"""
    try:
        # 获取项目配置
        from service.Class_Core_Function import Class_Core_Function
        core_function = Class_Core_Function()
        project_config = core_function.callback_project_config()

        if not project_config:
            return jsonify({
                'success': False,
                'message': '没有运行中的项目'
            }), 400

        project_name = project_config.get('Project', '')
        if not project_name:
            return jsonify({
                'success': False,
                'message': '项目名称为空'
            }), 400

        # 清空日志
        vuln_log_db = get_vuln_log_db(project_name)
        result = vuln_log_db.clear_all_logs()

        return jsonify({
            'success': True,
            'message': f'已清空 {result} 条日志'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'清空失败: {str(e)}'
        }), 500
