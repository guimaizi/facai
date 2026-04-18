# coding: utf-8
"""
Agent API接口
"""
from flask import Blueprint, request, jsonify, Response
import os
import sys
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from service.agent import AgentCore

agent_bp = Blueprint('agent', __name__, url_prefix='/api/agent')

# Agent单例
_agent_instance = None

def get_agent():
    """获取Agent单例"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = AgentCore()
    return _agent_instance

@agent_bp.route('/status', methods=['GET'])
def get_status():
    """获取Agent状态"""
    try:
        agent = get_agent()
        status = agent.get_model_status()
        return jsonify({
            "success": True,
            "data": status
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@agent_bp.route('/test_connection', methods=['POST'])
def test_connection():
    """测试模型连接"""
    try:
        data = request.get_json() or {}
        model_name = data.get('model')
        
        agent = get_agent()
        
        # 如果指定了模型，先切换
        if model_name:
            agent.change_model(model_name)
        
        success, message = agent.test_connection()
        
        return jsonify({
            "success": success,
            "message": message
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@agent_bp.route('/models', methods=['GET'])
def get_models():
    """获取可用模型列表"""
    try:
        agent = get_agent()
        models = agent.get_available_models()
        return jsonify({
            "success": True,
            "data": models
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@agent_bp.route('/change_model', methods=['POST'])
def change_model():
    """切换模型"""
    try:
        data = request.get_json()
        model_name = data.get('model')
        
        if not model_name:
            return jsonify({
                "success": False,
                "error": "缺少模型名称"
            }), 400
        
        agent = get_agent()
        success = agent.change_model(model_name)
        
        return jsonify({
            "success": success,
            "message": f"模型已切换为 {model_name}" if success else "切换失败"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@agent_bp.route('/audit/file', methods=['POST'])
def audit_file():
    """审计单个文件"""
    try:
        data = request.get_json()
        file_path = data.get('file_path')
        model_name = data.get('model')
        
        if not file_path:
            return jsonify({
                "success": False,
                "error": "缺少文件路径"
            }), 400
        
        agent = get_agent()
        
        # 如果指定了模型，先切换
        if model_name:
            agent.change_model(model_name)
        
        result = agent.audit_file(file_path)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@agent_bp.route('/audit/code', methods=['POST'])
def audit_code():
    """审计代码片段"""
    try:
        data = request.get_json()
        code = data.get('code')
        language = data.get('language', 'python')
        model_name = data.get('model')
        stream = data.get('stream', False)  # 是否流式输出
        
        if not code:
            return jsonify({
                "success": False,
                "error": "缺少代码内容"
            }), 400
        
        agent = get_agent()
        
        # 如果指定了模型，先切换
        if model_name:
            agent.change_model(model_name)
        
        # 流式输出
        if stream:
            def generate():
                result = agent.audit_code_stream(code, language)
                if result['success']:
                    for chunk in result['result']:
                        yield f"data: {json.dumps({'content': chunk})}\n\n"
                    yield "data: [DONE]\n\n"
                else:
                    yield f"data: {json.dumps({'error': result['error']})}\n\n"
            
            return Response(
                generate(),
                mimetype='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache',
                    'X-Accel-Buffering': 'no'
                }
            )
        
        # 非流式输出
        result = agent.audit_code(code, language)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@agent_bp.route('/audit/project', methods=['POST'])
def audit_project():
    """审计整个项目"""
    try:
        data = request.get_json()
        project_path = data.get('project_path')
        recursive = data.get('recursive', True)
        model_name = data.get('model')
        
        if not project_path:
            return jsonify({
                "success": False,
                "error": "缺少项目路径"
            }), 400
        
        agent = get_agent()
        
        # 如果指定了模型，先切换
        if model_name:
            agent.change_model(model_name)
        
        result = agent.audit_project(project_path, recursive)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500



